import hashlib
import heapq
import json
import math
import re
from . import store, gpu, catalog, limits

def embedding_key():
    cfg=gpu.config()
    return hashlib.sha256((cfg["base_url"]+"|"+cfg["embedding_model"]).encode()).hexdigest()

def normalize(vector):
    if not isinstance(vector,list) or not 1<=len(vector)<=65536 or not all(isinstance(x,(int,float)) and math.isfinite(x) for x in vector):
        raise ValueError("Ungültige Embedding-Antwort.")
    length=math.sqrt(sum(v*v for v in vector))
    if length==0:
        raise ValueError("Embedding enthält nur Nullwerte.")
    return [v/length for v in vector]

async def embed(texts):
    model=gpu.config()["embedding_model"]
    catalog.require(model,"embedding")
    response=await gpu.request("embeddings",{"model":model,"input":texts})
    data=sorted(response.get("data",[]),key=lambda x:x.get("index",0))
    if len(data)!=len(texts) or [x.get("index") for x in data]!=list(range(len(texts))):
        raise ValueError("GPUStack hat nicht alle Embeddings zurückgegeben.")
    return [normalize(x["embedding"]) for x in data]

async def index_document(ident):
    count=store.one("SELECT count(*) AS n FROM chunks WHERE document_id=?",(ident,))["n"]
    if not count:
        raise ValueError("Diese Datei enthält keinen indexierbaren Text. Nur abgelegte Originale zuerst erneut einlesen.")
    key=embedding_key()
    existing=store.one("SELECT vector FROM chunks WHERE document_id=? AND embedding_key=? AND vector IS NOT NULL LIMIT 1",(ident,key))
    dimension=len(json.loads(existing["vector"])) if existing else None
    while True:
        chunks=store.rows("SELECT id,content FROM chunks WHERE document_id=? AND (embedding_key IS NULL OR embedding_key!=? OR vector IS NULL) ORDER BY ordinal LIMIT 16",(ident,key))
        if not chunks: break
        vectors=await embed([x["content"] for x in chunks])
        dimension=dimension or len(vectors[0])
        if any(len(x)!=dimension for x in vectors):
            raise ValueError("Embedding-Dimension hat sich während der Indexierung geändert.")
        # Committed batches allow retry/resume after a network interruption.
        with store.db() as c:
            c.executemany("UPDATE chunks SET vector=?,embedding_key=? WHERE id=?",
                [(json.dumps(v),key,x["id"]) for x,v in zip(chunks,vectors)])
    return count

async def retrieve(question, ids, semantic=False, limit=None):
    if not ids:
        return [],[]
    limit=limit or limits.current()["rag_hits"]
    candidates=max(18,limit*3)
    marks=",".join("?" for _ in ids)
    count=store.one(f"SELECT count(*) AS n FROM chunks WHERE document_id IN ({marks})",ids)["n"]
    if not count:
        return [],["Die ausgewählten Dateien enthalten keine lesbaren Textabschnitte."]
    words=list(dict.fromkeys(w for w in re.findall(r"\w{2,}",question,re.UNICODE) if w.lower() not in {"und","oder","die","der","das","ein","eine","von","mit","was","ist","sind","bitte","den","dem"}))
    query=" OR ".join('"'+w+'"' for w in words[:64])
    notes=[]
    if len(words)>64:
        notes.append("Textsuche nutzt die ersten 64 unterschiedlichen Suchwörter. Für gezielte Treffer eine konkrete Frage stellen.")
    lexical=[]
    if query:
        lexical=store.rows(f"""
          SELECT c.id FROM chunks_fts f JOIN chunks c ON c.id=f.chunk_id
          WHERE chunks_fts MATCH ? AND c.document_id IN ({marks})
          ORDER BY bm25(chunks_fts) LIMIT ?""",[query,*ids,candidates])
    scores={x["id"]:1/(50+i) for i,x in enumerate(lexical)}
    if semantic:
        key=embedding_key()
        available=store.one(f"SELECT count(*) AS n FROM chunks WHERE document_id IN ({marks}) AND embedding_key=? AND vector IS NOT NULL",[*ids,key])["n"]
        if available:
            q=(await embed([question]))[0]
            best=[]
            # Bounded RAM: scan vectors in small DB batches; retain only candidates.
            with store.db() as c:
                cursor=c.execute(f"SELECT id,vector FROM chunks WHERE document_id IN ({marks}) AND embedding_key=? AND vector IS NOT NULL",[*ids,key])
                while rows:=cursor.fetchmany(128):
                    for x in rows:
                        vec=json.loads(x["vector"])
                        if len(vec)!=len(q):
                            raise ValueError("Index und Suchvektor haben unterschiedliche Dimensionen. Bitte neu einlesen und indexieren.")
                        item=(sum(a*b for a,b in zip(q,vec)),x["id"])
                        if len(best)<candidates: heapq.heappush(best,item)
                        elif item>best[0]: heapq.heapreplace(best,item)
            for i,(_,ident) in enumerate(sorted(best,reverse=True)):
                scores[ident]=scores.get(ident,0)+1/(50+i)
        if available<count:
            notes.append("Nicht alle Quellen sind mit dem aktuellen Modell indexiert; für diese gilt nur die Textsuche. Unterbrochene Indexierung kann in der Library fortgesetzt werden.")
    result=[]
    for ident in sorted(scores,key=scores.get,reverse=True)[:candidates]:
        result.append(store.one("SELECT c.id,c.document_id,c.location,c.content,d.name FROM chunks c JOIN documents d ON d.id=c.document_id WHERE c.id=?",(ident,)))
    if not result:
        sample=[]
        for position,ident in enumerate(ids):
            rows=store.rows("SELECT c.id,c.document_id,c.ordinal,c.location,c.content,d.name FROM chunks c JOIN documents d ON d.id=c.document_id WHERE c.document_id=? ORDER BY c.ordinal LIMIT ?",(ident,limit))
            sample.extend((x["ordinal"],position,x) for x in rows)
        result=[x for _,_,x in sorted(sample,key=lambda v:v[:2])[:limit]]
        notes.append("Keine Texttreffer: Die Auswahl zeigt Dokumentanfänge, keine vollständige Dokumentanalyse.")
    reranker=gpu.config().get("rerank_model")
    if semantic and reranker and result:
        catalog.require(reranker,"reranker")
        response=await gpu.request("rerank",{"model":reranker,"query":question,
            "documents":[x["content"] for x in result],"top_n":limit})
        indices=[r.get("index") for r in response.get("results",[])]
        if not indices or any(not isinstance(i,int) or i<0 or i>=len(result) for i in indices):
            raise ValueError("Ungültige Antwort des Rerankers.")
        result=[result[i] for i in dict.fromkeys(indices)]
    hits=[{"label":f"Q{i+1}","document_id":x["document_id"],"name":x["name"],
           "location":x["location"],"content":x["content"]} for i,x in enumerate(result[:limit])]
    notes.append(f"Übergeben werden {len(hits)} von {count:,} gespeicherten Textabschnitten; keine vollständige Dokumentauswertung. Für Gesamtzahlen die Originaldatei im Datenlabor berechnen.")
    return hits,notes
