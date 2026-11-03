"""Regression tests for large originals, parser budgets and bounded RAG workflows."""
import asyncio
import hashlib
import io
import json
import subprocess
import zipfile
from pathlib import Path
import pytest
from app import documents, gpu, limits, retrieval, store
from app import main
from .test_workroom import workspace, connect, thread, upload


def configure(c, **values):
    r=c.put("/api/limits",json=values)
    assert r.status_code==200,r.text
    return r.json()


def test_resource_settings_persist_and_validate(workspace, monkeypatch):
    c,calls=workspace
    cfg=configure(c,file_mb=120,text_chars=30_000_000,pdf_pages=0,xlsx_rows=0,rag_hits=20)
    store.initialize()
    assert c.get("/api/bootstrap").json()["limits"]==cfg
    for values in ({"file_mb":0},{"text_chars":True},{"rag_hits":1.5},{"unknown":3}):
        assert c.put("/api/limits",json=values).status_code==422
    monkeypatch.setattr(main,"BUSY_LOCAL",1)
    assert c.put("/api/limits",json={"file_mb":130}).status_code==409
    assert limits.current()["file_mb"]==120
    assert not calls


@pytest.mark.parametrize("suffix",["csv","txt","xlsx"])
def test_large_tables_and_text_pass_old_million_and_row_limits(workspace,suffix):
    c,calls=workspace
    rows=31_005
    value="Messwert mit mathematischem Minus − und Zürich"
    if suffix=="xlsx":
        from openpyxl import Workbook
        book=Workbook(write_only=True);sheet=book.create_sheet("Daten")
        for i in range(rows): sheet.append([i,value])
        sheet.append(["Ende","EinzigartigerEndwert9901"])
        buffer=io.BytesIO();book.save(buffer);book.close();raw=buffer.getvalue()
    else:
        raw=("id;beschreibung\n"+"".join(f"{i};{value}\n" for i in range(rows))+"Ende;EinzigartigerEndwert9901\n").encode()
    ident=upload(c,"gross."+suffix,raw)
    assert c.get(f"/api/documents/{ident}/download").content==raw
    chars=store.one("SELECT sum(length(content)) AS n FROM chunks WHERE document_id=?",(ident,))["n"]
    assert chars>1_000_000
    docs=c.get("/api/documents").json()
    assert next(d for d in docs if d["id"]==ident)["status"]=="bereit"
    assert not calls
    connect(c)
    t=thread(c)
    response=c.post(f"/api/threads/{t}/send",json={"content":"Finde EinzigartigerEndwert9901.","document_ids":[ident]})
    assert '"type": "done"' in response.text,response.text
    payload=next(p for path,p,_ in calls if path.endswith("/chat/completions"))
    assert "EinzigartigerEndwert9901" in payload["messages"][-1]["content"]
    assert len(payload["messages"][-1]["content"])<40_000
    metadata=c.get(f"/api/threads/{t}").json()["messages"][0]["metadata"]
    assert any("keine vollständige Dokumentauswertung" in note for note in metadata["notes"])


def test_budget_overflow_archives_exact_original_and_can_reprocess(workspace):
    c,calls=workspace
    raw=("Start;Zürich −\n"*300+"EinzigartigesEnde771").encode()
    configure(c,text_chars=1000)
    ident=upload(c,"tabelle.csv",raw)
    doc=store.one("SELECT * FROM documents WHERE id=?",(ident,))
    assert doc["status"]=="ablage"
    assert "kein Teilindex" in doc["note"]
    assert c.get(f"/api/documents/{ident}/download").content==raw
    assert c.get(f"/api/documents/{ident}/text").json()["total"]==0
    connect(c);t=thread(c)
    assert c.post(f"/api/threads/{t}/send",json={"content":"Analysiere.","document_ids":[ident]}).status_code==422
    assert not calls
    configure(c,text_chars=10_000)
    assert c.post(f"/api/documents/{ident}/reprocess").json()["status"]=="bereit"
    assert store.one("SELECT * FROM documents WHERE id=?",(ident,))["sha256"]==hashlib.sha256(raw).hexdigest()
    configure(c,text_chars=1000)
    before=c.get(f"/api/documents/{ident}/text").json()
    assert c.post(f"/api/documents/{ident}/reprocess").status_code==422
    assert c.get(f"/api/documents/{ident}/text").json()==before
    assert c.get(f"/api/documents/{ident}/download").content==raw


def test_archive_only_skips_parser_and_is_available_to_runner(workspace,monkeypatch):
    c,calls=workspace
    monkeypatch.setattr(documents,"extract_guarded",lambda *args: (_ for _ in ()).throw(AssertionError("parser must not run")))
    raw=b"not parsed in archive-only mode"
    r=c.post("/api/documents",data={"project_id":"workspace","mode":"original"},files={"file":("daten.csv",raw)})
    assert r.status_code==200,r.text
    ident=r.json()["id"]
    assert r.json()["status"]=="ablage"
    assert documents.selected([ident],"workspace")[0]["id"]==ident
    async def runner(project,code,docs):
        assert docs[0]["status"]=="ablage"
        assert documents.path_for(docs[0]).read_bytes()==raw
        return {"status":"Testadapter","files":[]}
    monkeypatch.setattr(main.execution,"run_python",runner)
    assert c.post("/api/jobs",json={"project_id":"workspace","code":"print(1)","document_ids":[ident],"approved":True}).status_code==200
    assert not calls


def test_file_size_guard_and_upload_above_old_25_mib(workspace):
    c,calls=workspace
    configure(c,file_mb=1)
    r=c.post("/api/documents",data={"mode":"original"},files={"file":("gross.txt",b"x"*(1024*1024+1))})
    assert r.status_code==422,r.text
    assert c.get("/api/documents").json()==[]
    assert not list(store.DATA.glob("upload-*"))
    configure(c,file_mb=32)
    raw=b"x"*(25*1024*1024+1)
    r=c.post("/api/documents",data={"mode":"original","project_id":"workspace"},files={"file":("gross.txt",raw)})
    assert r.status_code==200,r.text
    assert r.json()["size"]==len(raw)
    assert c.get("/api/documents/"+r.json()["id"]+"/download").content==raw
    assert not calls


def test_pdf_above_old_300_pages_and_optional_page_cap(workspace):
    from pypdf import PdfWriter
    c,calls=workspace
    pdf=PdfWriter()
    for _ in range(301): pdf.add_blank_page(width=300,height=300)
    buffer=io.BytesIO();pdf.write(buffer);raw=buffer.getvalue()
    ident=upload(c,"301.pdf",raw)
    assert store.one("SELECT status FROM documents WHERE id=?",(ident,))["status"]=="ohne_text"
    configure(c,pdf_pages=300)
    archived=upload(c,"begrenzt.pdf",raw)
    assert store.one("SELECT status FROM documents WHERE id=?",(archived,))["status"]=="ablage"
    assert c.get(f"/api/documents/{archived}/download").content==raw


@pytest.mark.parametrize("encoding",["utf-16","utf-32"])
def test_bom_text_encodings_preserve_unicode(workspace,encoding):
    c,_=workspace
    text="Zürich − 中文 🔬"
    ident=upload(c,"export.txt",text.encode(encoding))
    assert c.get(f"/api/documents/{ident}/text").json()["chunks"][0]["content"]==text


def test_parser_timeout_archives_original(workspace,monkeypatch):
    c,_=workspace
    def timeout(*args,**kwargs):
        raise subprocess.TimeoutExpired(args[0],kwargs["timeout"])
    monkeypatch.setattr(documents.subprocess,"run",timeout)
    raw=b"original content"
    ident=upload(c,"langsam.txt",raw)
    assert store.one("SELECT status,note FROM documents WHERE id=?",(ident,))["status"]=="ablage"
    assert c.get(f"/api/documents/{ident}/download").content==raw


def test_preview_paging_and_late_text_search(workspace):
    c,_=workspace
    configure(c,chunk_chars=500)
    ident=upload(c,"lang.txt",("Zeile Bern\n"*8000+"SpäterFund9981").encode())
    page=c.get(f"/api/documents/{ident}/text").json()
    assert page["next_offset"]==100 and page["total"]>100
    second=c.get(f"/api/documents/{ident}/text?offset=100").json()
    assert second["chunks"][0]["location"]!=page["chunks"][0]["location"]
    hits,notes=asyncio.run(retrieval.retrieve("SpäterFund9981",[ident]))
    assert any("SpäterFund9981" in h["content"] for h in hits)
    assert c.get(f"/api/documents/{ident}/text?offset=-1").status_code==422


def test_index_commits_batches_and_resumes_without_repeating_success(workspace,monkeypatch):
    c,calls=workspace;connect(c)
    configure(c,chunk_chars=500)
    ident=upload(c,"index.txt",("Bern Messung\n"*2200).encode())
    original=gpu.request
    attempts=0
    async def interrupted(path,payload=None):
        nonlocal attempts
        if path=="embeddings":
            attempts+=1
            if attempts==2: raise ValueError("Test: Verbindung unterbrochen")
        return await original(path,payload)
    monkeypatch.setattr(gpu,"request",interrupted)
    assert c.post(f"/api/documents/{ident}/index").status_code==422
    count=store.one("SELECT count(*) AS n FROM chunks WHERE document_id=? AND vector IS NOT NULL",(ident,))["n"]
    assert count==16
    assert c.post(f"/api/documents/{ident}/index").status_code==200
    docs=c.get("/api/documents").json();d=next(d for d in docs if d["id"]==ident)
    assert d["indexed"]==d["chunks"]>32
    assert sum(len(p["input"]) for path,p,_ in calls if path.endswith("/embeddings"))==d["chunks"]
    hits,notes=asyncio.run(retrieval.retrieve("Bern",[ident],semantic=True))
    assert len(hits)==limits.current()["rag_hits"]


def test_connector_paging_search_and_oversized_original(workspace,monkeypatch,tmp_path):
    c,_=workspace
    root=tmp_path/"import";root.mkdir()
    for i in range(305): (root/f"daten-{i:03}.txt").write_text("Bern")
    monkeypatch.setenv("WORKROOM_IMPORT_ROOT",str(root))
    first=c.get("/api/connector").json()
    second=c.get("/api/connector?offset=200").json()
    assert len(first["files"])==200 and len(second["files"])==105
    assert {f["path"] for f in first["files"]}.isdisjoint(f["path"] for f in second["files"])
    assert c.get("/api/connector?q=daten-304").json()["files"][0]["path"]=="daten-304.txt"
    configure(c,text_chars=1000)
    big=root/"gross.csv";big.write_text("12345\n"*1000)
    r=c.post("/api/connector/import",json={"path":"gross.csv","project_id":"workspace"})
    assert r.status_code==200 and r.json()["status"]=="ablage"


def test_backup_exceeds_old_150_mib_and_removes_temp_files(workspace):
    c,_=workspace
    ident=upload(c,"original.txt",b"original")
    # Sparse synthetic original: exercises the actual ZIP path without 151-MiB RAM input.
    path=documents.path_for(store.one("SELECT * FROM documents WHERE id=?",(ident,)))
    with path.open("r+b") as f: f.truncate(151*1024*1024)
    r=c.get("/api/backup")
    assert r.status_code==200,r.text[:200]
    with zipfile.ZipFile(io.BytesIO(r.content)) as z:
        assert z.getinfo("data/files/"+path.name).file_size==151*1024*1024
        assert "data/workspace.sqlite3" in z.namelist()
    assert not list(store.DATA.glob("backup-*"))


def test_long_prompt_and_explicit_larger_chat_budget(workspace):
    c,calls=workspace;connect(c)
    prompt="Arbeitsweise beachten.\n"*1000
    assert c.post("/api/prompts",json={"name":"Lange Anweisung","kind":"system","content":prompt}).status_code==200
    t=thread(c,context_chars=300_000,max_tokens=50_000,system_prompt=prompt)
    text="A"*90_000
    assert '"type": "done"' in c.post(f"/api/threads/{t}/send",json={"content":text}).text
    configure(c,message_chars=1000)
    before=len(c.get(f"/api/threads/{t}").json()["messages"])
    assert c.post(f"/api/threads/{t}/send",json={"content":text}).status_code==422
    assert len(c.get(f"/api/threads/{t}").json()["messages"])==before


def test_routine_budget_is_explicit_and_survives_restart(workspace):
    c,calls=workspace;connect(c)
    r=c.post("/api/routines",json={"project_id":"workspace","name":"Langer Prompt","prompt":"A"*90_000,
        "model":"gpt-oss-120b","context_chars":200_000,"max_tokens":50_000,
        "next_run":"2099-01-01T08:00:00+01:00"})
    assert r.status_code==200,r.text
    ident=r.json()["id"]
    store.initialize()
    result=c.post(f"/api/routines/{ident}/run").json()
    t=c.get("/api/threads/"+result["thread_id"]).json()["thread"]
    assert t["parameters"]["context_chars"]==200_000 and t["parameters"]["max_tokens"]==50_000
    configure(c,output_max_tokens=128)
    result=c.post(f"/api/routines/{ident}/run").json()
    assert result["thread_id"] is None
    assert store.one("SELECT status FROM routines WHERE id=?",(ident,))["status"]!="Läuft"


def test_existing_v1_routines_migrate_without_losing_content(workspace):
    c,_=workspace
    r=c.post("/api/routines",json={"project_id":"workspace","name":"Bestehende Routine","prompt":"Bleibt erhalten",
        "model":"gpt-oss-120b","next_run":"2099-01-01T08:00:00+01:00"})
    ident=r.json()["id"]
    with store.db() as connection:
        connection.execute("ALTER TABLE routines DROP COLUMN parameters")
        connection.execute("PRAGMA user_version=1")
    store.initialize();store.initialize()
    row=store.one("SELECT * FROM routines WHERE id=?",(ident,))
    assert row["prompt"]=="Bleibt erhalten" and json.loads(row["parameters"])=={}
    with store.db() as connection: assert connection.execute("PRAGMA user_version").fetchone()[0]==3


def test_office_expansion_cap_archives_without_partial_index(workspace):
    from openpyxl import Workbook
    c,_=workspace
    book=Workbook();book.active.append(["Bern"])
    buffer=io.BytesIO();book.save(buffer);book.close()
    with zipfile.ZipFile(buffer,"a",zipfile.ZIP_DEFLATED) as archive:
        archive.writestr("unused-padding.txt",b"x"*(17*1024*1024))
    configure(c,office_mb=16)
    ident=upload(c,"entpackt.xlsx",buffer.getvalue())
    assert store.one("SELECT status FROM documents WHERE id=?",(ident,))["status"]=="ablage"
    assert c.get(f"/api/documents/{ident}/text").json()["total"]==0
