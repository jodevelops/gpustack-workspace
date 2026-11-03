"""Integration tests with synthetic data and a mocked GPUStack transport."""
import asyncio
import io
import json
import sqlite3
import zipfile
from datetime import datetime, timedelta, timezone
import httpx
import pytest
from fastapi.testclient import TestClient
from PIL import Image
from app import store, gpu, retrieval
from app.main import app

@pytest.fixture
def workspace(tmp_path,monkeypatch):
    monkeypatch.setattr(store,"DATA",tmp_path/"data")
    monkeypatch.setattr(gpu,"_session_key","")
    monkeypatch.delenv("GPUSTACK_API_KEY",raising=False)
    monkeypatch.delenv("GPUSTACK_BASE_URL",raising=False)
    monkeypatch.delenv("WORKROOM_ENABLE_RUNNER",raising=False)
    monkeypatch.delenv("WORKROOM_IMPORT_ROOT",raising=False)
    monkeypatch.setattr(gpu,"_vault",lambda: (_ for _ in ()).throw(ValueError("No keyring in tests")))
    calls=[]
    def handler(request):
        payload=json.loads(request.content) if request.content and request.headers.get("content-type","").startswith("application/json") else None
        calls.append((request.url.path,payload,dict(request.headers)))
        if request.url.path.endswith("/models"):
            return httpx.Response(200,json={"data":[{"id":"gpt-oss-120b"},{"id":"internvl3-8b-instruct"},{"id":"custom-test-model"}]})
        if request.url.path.endswith("/embeddings"):
            return httpx.Response(200,json={"data":[{"index":i,"embedding":[1.,.2 if "Bern" in x else .8,0.1]} for i,x in enumerate(payload["input"])]})
        if request.url.path.endswith("/rerank"):
            return httpx.Response(200,json={"results":[{"index":i,"relevance_score":.9} for i in range(min(6,len(payload["documents"])))]})
        if request.url.path.endswith("/audio/transcriptions"):
            return httpx.Response(200,text="Dies ist ein synthetisches Testtranskript.")
        if payload and payload.get("stream"):
            events=[{"choices":[{"delta":{"content":"Bern ist belegt "}}]},
                    {"choices":[{"delta":{"content":"[Q1]."},"finish_reason":"stop"}]}]
            return httpx.Response(200,text="".join("data: "+json.dumps(x)+"\n\n" for x in events)+"data: [DONE]\n\n",headers={"Content-Type":"text/event-stream"})
        return httpx.Response(200,json={"choices":[{"message":{"content":"Routine erfolgreich (Testtransport)."}}]})
    monkeypatch.setattr(gpu,"client",lambda:httpx.AsyncClient(transport=httpx.MockTransport(handler),base_url="https://gpu.test/v1/",headers={"Authorization":"Bearer "+gpu.credential()}))
    with TestClient(app,base_url="http://localhost") as client:
        csrf=client.get("/api/bootstrap").json()["csrf"]
        client.headers.update({"X-CSRF-Token":csrf})
        yield client,calls

def connect(c,**extra):
    body={"base_url":"https://gpu.test/v1","embedding_model":"qwen3-embedding-0.6b","rerank_model":"","internet_enabled":False,**extra}
    r=c.post("/api/connection",json=body)
    assert r.status_code==200,r.text

def test_endpoint_default_preserves_saved_configuration(workspace):
    c,calls=workspace
    assert c.get("/api/bootstrap").json()["connection"]["base_url"]=="https://gpustack.unibe.ch/v1"
    assert calls==[]  # Merely starting/opening the UI makes no GPUStack request.
    connect(c,base_url="https://other.test/v1")
    store.initialize()
    assert c.get("/api/bootstrap").json()["connection"]["base_url"]=="https://other.test/v1"
    connect(c,base_url="")
    assert c.get("/api/bootstrap").json()["connection"]["base_url"]==""

def thread(c,**extra):
    r=c.post("/api/threads",json={"project_id":"workspace",**extra})
    assert r.status_code==200,r.text
    return r.json()["id"]

def upload(c,name="beleg.txt",text=b"Bern ist die Hauptstadt. Thun liegt am See.",project="workspace"):
    r=c.post("/api/documents",data={"project_id":project},files={"file":(name,text)})
    assert r.status_code==200,r.text
    return r.json()["id"]

def test_security_boundary_and_no_key_leak(workspace):
    c,calls=workspace
    assert c.get("/api/bootstrap",headers={"Host":"evil.example"}).status_code==403
    assert c.get("/api/bootstrap",headers={"Sec-Fetch-Site":"cross-site"}).status_code==403
    assert c.post("/api/projects",json={"name":"bad"},headers={"X-CSRF-Token":""}).status_code==403
    assert c.post("/api/projects",json={"name":"bad"},headers={"Origin":"https://evil.example"}).status_code==403
    assert c.post("/api/connection",json={"base_url":"http://private.example/v1","embedding_model":"qwen3-embedding-0.6b"}).status_code==422
    secret="TEST_ONLY_PRIVATE_KEY_123"
    connect(c,api_key=secret)
    boot=c.get("/api/bootstrap")
    assert secret not in boot.text
    assert boot.json()["key_status"]=="Nur diese Serversitzung"
    assert secret.encode() not in (store.DATA/"workspace.sqlite3").read_bytes()
    assert c.post("/api/connection",json={"base_url":"https://gpu.test/v1","embedding_model":"qwen3-embedding-0.6b","api_key":secret*500}).status_code==422
    invalid=c.post("/api/connection",json={"base_url":"https://gpu.test/v1","embedding_model":"qwen3-embedding-0.6b","api_key":secret*500})
    assert secret not in invalid.text
    connect(c,base_url="https://other.test/v1")
    assert gpu.credential()==""
    assert "object-src 'none'" in boot.headers["content-security-policy"]

def test_crud_persistence_and_export(workspace):
    c,calls=workspace
    p=c.post("/api/projects",json={"name":"Testprojekt","memory":"Feste Regel"}).json()["id"]
    t=thread(c,project_id=p,system_prompt="Quellen prüfen",temperature=.2)
    d=upload(c,project=p)
    # Reinitialize must not erase persisted records.
    store.initialize()
    assert c.get("/api/threads/"+t).json()["thread"]["system_prompt"]=="Quellen prüfen"
    assert len(c.get("/api/documents?project_id="+p).json())==1
    assert c.get("/api/documents/"+d+"/download").content.startswith(b"Bern")
    backup=c.get("/api/backup")
    assert backup.status_code==200
    with zipfile.ZipFile(io.BytesIO(backup.content)) as z:
        assert "data/workspace.sqlite3" in z.namelist()
        assert any(x.startswith("data/files/") for x in z.namelist())
    assert c.delete("/api/projects/"+p).status_code==200
    assert c.get("/api/threads/"+t).status_code==404
    assert not store.rows("SELECT * FROM chunks")
    assert not store.rows("SELECT * FROM chunks_fts")

def test_text_rag_stream_history_and_audit(workspace):
    c,calls=workspace
    connect(c)
    doc=upload(c)
    t=thread(c,system_prompt="Nenne Belege")
    r=c.post(f"/api/threads/{t}/send",json={"content":"Was steht über Bern?","document_ids":[doc]})
    assert r.status_code==200,r.text
    assert '"type": "done"' in r.text
    data=c.get("/api/threads/"+t).json()
    assert [m["role"] for m in data["messages"]]==["user","assistant"]
    meta=data["messages"][0]["metadata"]
    assert meta["sources"][0]["name"]=="beleg.txt"
    assert "Nenne Belege" in meta["effective_system"]
    payload=calls[-1][1]
    assert payload["model"]=="gpt-oss-120b"
    assert "<QUELLEN>" in payload["messages"][-1]["content"]
    assert all("/embeddings" not in x[0] for x in calls)
    second=c.post(f"/api/threads/{t}/send",json={"content":"Und Thun?","document_ids":[doc]})
    assert second.status_code==200
    assert calls[-1][1]["messages"][2]["role"]=="assistant"
    assert c.get("/api/threads/"+t).json()["messages"][2]["metadata"]["sources"][0]["label"]=="Q2"
    export=c.get(f"/api/threads/{t}/export?format=json").json()
    assert len(export["messages"])==4
    assert "beleg.txt" in c.get(f"/api/threads/{t}/export").text

def test_scope_and_modality_guards(workspace):
    c,calls=workspace;connect(c)
    p=c.post("/api/projects",json={"name":"Separat"}).json()["id"]
    other=upload(c,project=p)
    t=thread(c)
    r=c.post(f"/api/threads/{t}/send",json={"content":"Geheim?","document_ids":[other]})
    assert r.status_code==422
    assert not calls
    assert c.post("/api/threads",json={"project_id":"workspace","model":"qwen3-embedding-0.6b"}).status_code==422
    im=io.BytesIO();Image.new("RGB",(20,20),"red").save(im,"PNG")
    image=upload(c,"bild.png",im.getvalue())
    assert c.post(f"/api/threads/{t}/send",json={"content":"Was ist im Bild?","document_ids":[image]}).status_code==422
    vision=thread(c,model="internvl3-8b-instruct")
    assert c.post(f"/api/threads/{vision}/send",json={"content":"Bild?","document_ids":[image]}).status_code==200
    assert calls[-1][1]["messages"][-1]["content"][1]["image_url"]["url"].startswith("data:image/png;base64,")

def test_embeddings_hybrid_reranking_and_stale_index(workspace):
    c,calls=workspace;connect(c,rerank_model="jina-reranker-v2-base-multilingual")
    doc=upload(c)
    assert c.post(f"/api/documents/{doc}/index").json()["chunks"]>0
    t=thread(c)
    r=c.post(f"/api/threads/{t}/send",json={"content":"Bern","document_ids":[doc],"semantic":True})
    assert r.status_code==200,r.text
    assert any(x[0].endswith("/embeddings") for x in calls)
    assert any(x[0].endswith("/rerank") for x in calls)
    connect(c,embedding_model="granite-embedding-107m-multilingual")
    assert c.get("/api/documents").json()[0]["indexed"]==0
    hits,notes=asyncio.run(retrieval.retrieve("Bern",[doc],semantic=True))
    assert hits and any("Nicht alle Quellen" in n for n in notes)

def test_failures_not_committed_as_success(workspace,monkeypatch):
    c,calls=workspace;connect(c)
    async def broken(payload):
        yield {"text":"Anfang"}
        raise ValueError("Synthetischer Verbindungsabbruch")
    monkeypatch.setattr(gpu,"stream",broken)
    t=thread(c)
    r=c.post(f"/api/threads/{t}/send",json={"content":"Frage"})
    assert '"type": "error"' in r.text
    data=c.get("/api/threads/"+t).json()["messages"]
    assert data[1]["metadata"]["status"]=="error"
    assert data[0]["metadata"]["status"]=="error"
    # No silent truncation: oversize input is refused without a new stored message.
    r=c.post(f"/api/threads/{t}/send",json={"content":"a"*50000})
    assert r.status_code==422
    assert len(c.get("/api/threads/"+t).json()["messages"])==2

def test_research_and_execution_default_denied(workspace):
    c,calls=workspace
    assert c.post("/api/research",json={"query":"Bern","source":"wikidata"}).status_code==422
    assert c.post("/api/jobs",json={"project_id":"workspace","code":"print(1)","approved":True}).status_code==422
    assert not calls

def test_models_profiles_and_prompt_crud(workspace):
    c,calls=workspace;connect(c)
    assert c.post("/api/connection/test").json()["count"]==3
    data=c.get("/api/bootstrap").json()
    assert next(x for x in data["models"] if x["id"]=="custom-test-model")["type"]=="unclassified"
    assert c.post("/api/models",json={"id":"custom-test-model","type":"chat"}).status_code==200
    assert thread(c,model="custom-test-model")
    p=c.post("/api/prompts",json={"name":"Prüfen","kind":"skill","content":"Ausschließlich Quellen"}).json()["id"]
    assert c.put("/api/prompts/"+p,json={"name":"Prüfen","kind":"skill","content":"Ausführlich prüfen"}).status_code==200
    assert c.delete("/api/prompts/"+p).status_code==200

def test_routines_create_run_and_pause(workspace):
    c,calls=workspace;connect(c)
    r=c.post("/api/routines",json={"project_id":"workspace","name":"Prüfung","prompt":"Nenne die Regel.","model":"gpt-oss-120b",
        "interval_days":7,"next_run":(datetime.now(timezone.utc)+timedelta(days=3)).isoformat(),"enabled":False})
    assert r.status_code==200,r.text
    ident=r.json()["id"]
    executed=c.post(f"/api/routines/{ident}/run").json()
    assert executed["status"]=="Fertig"
    assert len(c.get("/api/threads/"+executed["thread_id"]).json()["messages"])==2
    assert c.post(f"/api/routines/{ident}/toggle").status_code==200
    assert c.get("/api/bootstrap").json()["routines"][0]["enabled"]==1
    assert c.delete("/api/routines/"+ident).status_code==200

def test_connector_cannot_escape_root(workspace,tmp_path,monkeypatch):
    c,calls=workspace
    root=tmp_path/"import";root.mkdir()
    (root/"ok.txt").write_text("öffentliche Testdatei")
    (tmp_path/"secret.txt").write_text("sensitive test")
    (root/"link.txt").symlink_to(tmp_path/"secret.txt")
    monkeypatch.setenv("WORKROOM_IMPORT_ROOT",str(root))
    files=c.get("/api/connector").json()["files"]
    assert [f["path"] for f in files]==["ok.txt"]
    assert c.post("/api/connector/import",json={"project_id":"workspace","path":"../secret.txt"}).status_code==422
    assert c.post("/api/connector/import",json={"project_id":"workspace","path":"link.txt"}).status_code==422
    assert c.post("/api/connector/import",json={"project_id":"workspace","path":"ok.txt"}).status_code==200

def test_pdf_docx_xlsx_and_scan_detection(workspace):
    from pypdf import PdfWriter
    from docx import Document
    from openpyxl import Workbook
    c,calls=workspace
    pdf=PdfWriter();pdf.add_blank_page(width=300,height=300)
    raw=io.BytesIO();pdf.write(raw)
    ident=upload(c,"scan.pdf",raw.getvalue())
    assert c.get("/api/documents/"+ident+"/text").json()["document"]["status"]=="ohne_text"
    doc=Document();doc.add_paragraph("Bern ist in diesem Word-Dokument belegt.")
    raw=io.BytesIO();doc.save(raw)
    ident=upload(c,"brief.docx",raw.getvalue())
    assert "Bern" in c.get("/api/documents/"+ident+"/text").text
    wb=Workbook();wb.active.append(["Ort","Jahr"]);wb.active.append(["Bern",1910])
    raw=io.BytesIO();wb.save(raw)
    ident=upload(c,"inventar.xlsx",raw.getvalue())
    assert "1910" in c.get("/api/documents/"+ident+"/text").text
    assert c.post("/api/documents",files={"file":("bad.html",b"<script>bad()</script>")}).status_code==422

def test_transcription_is_explicit(workspace):
    c,calls=workspace;connect(c)
    ident=upload(c,"aufnahme.wav",b"synthetic audio placeholder")
    assert not calls
    r=c.post(f"/api/documents/{ident}/transcribe")
    assert r.status_code==200,r.text
    assert r.json()["name"]=="aufnahme_transkript.txt"
    assert calls[-1][0].endswith("/audio/transcriptions")

@pytest.mark.parametrize("pipe_encoding",["cp1252","ascii"])
def test_unicode_upload_and_model_payload_survive_legacy_pipe(workspace,monkeypatch,pipe_encoding):
    from docx import Document
    from openpyxl import Workbook
    c,calls=workspace
    # Force the parser subprocess to use a restricted Windows-style stdout encoding.
    monkeypatch.setenv("PYTHONIOENCODING",pipe_encoding)
    text='<button title="Herauszoomen">−</button>\nBerechnung: 5 − 3 = 2; 中文; 🔬; α ≤ β; Grüße.'
    raw=text.encode("utf-8")
    ident=upload(c,"code.txt",raw)
    assert not calls  # Upload and parsing are local.
    assert c.get("/api/documents/"+ident+"/text").json()["chunks"][0]["content"]==text
    assert c.get("/api/documents/"+ident+"/download").content==raw
    doc=Document();doc.add_paragraph(text)
    word=io.BytesIO();doc.save(word)
    word_id=upload(c,"unicode.docx",word.getvalue())
    assert c.get("/api/documents/"+word_id+"/text").json()["chunks"][0]["content"]==text
    wb=Workbook();wb.active.title="中文";wb.active.append([text])
    excel=io.BytesIO();wb.save(excel);wb.close()
    excel_id=upload(c,"unicode.xlsx",excel.getvalue())
    sheet=c.get("/api/documents/"+excel_id+"/text").json()["chunks"][0]
    assert text in sheet["content"]
    assert "中文" in sheet["location"]
    connect(c)
    chat=thread(c,model="minimax-m2.7")
    response=c.post(f"/api/threads/{chat}/send",json={
        "content":"Verbessere den Code.", "document_ids":[ident],
    })
    assert '"type": "done"' in response.text,response.text
    payload=next(payload for path,payload,_ in calls if path.endswith("/chat/completions"))
    assert payload["model"]=="minimax-m2.7"
    assert text in payload["messages"][-1]["content"]
    saved=c.get("/api/threads/"+chat).json()["messages"][0]["metadata"]["sources"][0]["content"]
    assert saved==text

def test_history_search_finds_older_messages(workspace):
    c,calls=workspace;connect(c)
    first=thread(c,title="Erstes Gespräch")
    c.post(f"/api/threads/{first}/send",json={"content":"Einzigartiger Suchbegriff: Geodaten-731"})
    for i in range(14): thread(c,title=f"Späteres Gespräch {i}")
    result=c.get("/api/history",params={"project_id":"workspace","q":"Geodaten-731"})
    assert result.status_code==200,result.text
    assert [x["id"] for x in result.json()]==[first]
    assert c.get("/api/history",params={"project_id":"workspace","q":"%"}).json()==[]

def test_stream_requires_terminal_confirmation(workspace,monkeypatch):
    c,calls=workspace;connect(c)
    def handler(req):
        return httpx.Response(200,text='data: {"choices":[{"delta":{"content":"partial"}}]}\n\n')
    monkeypatch.setattr(gpu,"client",lambda:httpx.AsyncClient(transport=httpx.MockTransport(handler),base_url="https://gpu.test/v1/"))
    t=thread(c)
    r=c.post(f"/api/threads/{t}/send",json={"content":"Frage"})
    assert '"type": "error"' in r.text
    assert c.get("/api/threads/"+t).json()["messages"][-1]["metadata"]["status"]=="error"
