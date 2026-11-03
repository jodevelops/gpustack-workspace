"""Media, token budgets and transcripts, with synthetic endpoint responses."""
import io
import json
import asyncio
import httpx
import pytest
from PIL import Image
from pypdf import PdfWriter
from app import gpu, store, catalog
from .test_workroom import workspace, connect, thread, upload


def replace_transport(monkeypatch, handler):
    monkeypatch.setattr(gpu, "client", lambda: httpx.AsyncClient(transport=httpx.MockTransport(handler), base_url="https://gpu.test/v1/"))


def sse(events):
    return httpx.Response(200, text="".join("data: "+json.dumps(e)+"\n\n" for e in events)+"data: [DONE]\n\n", headers={"Content-Type":"text/event-stream"})


def test_inline_media_and_persistent_chat_attachments(workspace):
    c, calls=workspace; connect(c)
    im=io.BytesIO(); Image.new("RGB",(12,12),"red").save(im,"PNG")
    image=upload(c,"image.png",im.getvalue())
    pdf=PdfWriter();pdf.add_blank_page(width=100,height=100);out=io.BytesIO();pdf.write(out)
    pdfid=upload(c,"scan.pdf",out.getvalue())
    audio=upload(c,"record.webm",b"synthetic audio")
    txt=upload(c,"text.txt",b"text")
    for ident in [image,pdfid,audio]:
        response=c.get(f"/api/documents/{ident}/download?inline=true")
        assert response.status_code==200
        assert response.headers["content-disposition"].startswith("inline")
        assert response.headers["x-frame-options"]=="SAMEORIGIN"
        assert "frame-src 'self'" in response.headers["content-security-policy"]
    assert c.get(f"/api/documents/{txt}/download?inline=true").headers["content-disposition"].startswith("attachment")
    t=thread(c,model="internvl3-8b-instruct")
    c.post(f"/api/threads/{t}/send",json={"content":"Bild erklären", "document_ids":[image]})
    store.initialize()
    meta=c.get(f"/api/threads/{t}").json()["messages"][0]["metadata"]
    assert meta["documents"][0]["id"]==image
    assert meta["documents"][0]["mime"]=="image/png"


@pytest.mark.parametrize("structured",[True,False])
def test_reasoning_stream_usage_and_opt_in_export(workspace,monkeypatch,structured):
    c,_=workspace;connect(c)
    events=([{"choices":[{"delta":{"reasoning_content":"Prüfbare Modellbegründung"}}]},
             {"choices":[{"delta":{"content":"Antwort"},"finish_reason":"length"}]}] if structured else
            [{"choices":[{"delta":{"content":part}}]} for part in ["<thi","nk>Prüfbare Modell", "begründung</th", "ink>Antwort"]]+
            [{"choices":[{"delta":{},"finish_reason":"length"}]}])
    events.append({"choices":[],"usage":{"prompt_tokens":12,"completion_tokens":64,"completion_tokens_details":{"reasoning_tokens":40}}})
    requests=[]
    def handler(request):
        requests.append(json.loads(request.content));return sse(events)
    replace_transport(monkeypatch,handler)
    t=thread(c,max_tokens=64)
    result=c.post(f"/api/threads/{t}/send",json={"content":"Frage"})
    assert '"type": "reasoning"' in result.text
    message=c.get(f"/api/threads/{t}").json()["messages"][-1]
    assert message["content"]=="Antwort"
    assert message["metadata"]["reasoning"]=="Prüfbare Modellbegründung"
    assert message["metadata"]["usage"]["completion_tokens"]==64
    for fmt in ["json","md"]:
        excluded=c.get(f"/api/threads/{t}/export?format={fmt}").text
        included=c.get(f"/api/threads/{t}/export?format={fmt}&include_reasoning=true").text
        assert "Prüfbare Modellbegründung" not in excluded
        assert "Prüfbare Modellbegründung" in included
    c.post(f"/api/threads/{t}/send",json={"content":"Weiter"})
    assert "Prüfbare Modellbegründung" not in json.dumps(requests[-1])


def test_reasoning_preserved_on_error_and_reasoning_only_length(workspace,monkeypatch):
    c,_=workspace;connect(c)
    async def broken(payload):
        yield {"reasoning":"Teilbegründung"}
        raise ValueError("Unterbrochen")
    monkeypatch.setattr(gpu,"stream",broken)
    t=thread(c)
    c.post(f"/api/threads/{t}/send",json={"content":"Test"})
    assert c.get(f"/api/threads/{t}").json()["messages"][-1]["metadata"]["reasoning"]=="Teilbegründung"
    async def limited(payload):
        yield {"reasoning":"Nur Reasoning"}
        yield {"finish_reason":"length"}
    monkeypatch.setattr(gpu,"stream",limited)
    t=thread(c,max_tokens=10)
    r=c.post(f"/api/threads/{t}/send",json={"content":"Test"})
    assert '"type": "done"' in r.text
    meta=c.get(f"/api/threads/{t}").json()["messages"][-1]["metadata"]
    assert meta["finish_reason"]=="length" and meta["reasoning"]=="Nur Reasoning"


def test_reference_limits_and_local_budget_can_be_disabled(workspace):
    c,calls=workspace;connect(c)
    m=next(m for m in c.get("/api/bootstrap").json()["models"] if m["id"]=="gpt-oss-120b")
    assert m["reference"]["context_tokens"]==131072 and m["deployment_context_tokens"] is None
    t=thread(c,context_chars=0)
    r=c.post(f"/api/threads/{t}/budget",json={"content":"X"*60_000,"semantic":True})
    assert r.json()["input_chars"]>60_000 and not calls
    assert c.get(f"/api/threads/{t}").json()["messages"]==[]
    assert c.post(f"/api/threads/{t}/send",json={"content":"X"*60_000}).status_code==200
    c.put("/api/limits",json={"message_chars":1000})
    assert c.post(f"/api/threads/{t}/send",json={"content":"X"*1001}).status_code==422
    r=c.post("/api/models",json={"id":"gpt-oss-120b","type":"chat","deployment_context_tokens":32000,"deployment_output_tokens":4096})
    assert r.status_code==200
    assert c.post("/api/threads",json={"project_id":"workspace","max_tokens":4097}).status_code==422
    t=thread(c)
    assert c.get(f"/api/threads/{t}").json()["thread"]["parameters"]["max_tokens"]==4096
    c.post("/api/models",json={"id":"gpt-oss-120b","type":"chat","description":"Edited"})
    assert catalog.require("gpt-oss-120b","chat")["deployment_context_tokens"]==32000
    assert c.post("/api/models",json={"id":"gpt-oss-120b","type":"chat","deployment_output_tokens":32000}).status_code==422


def test_model_list_exposes_deployment_limit_and_optional_usage(workspace,monkeypatch):
    c,_=workspace;connect(c)
    requests=[]
    def handler(r):
        if r.url.path.endswith("/models"):
            return httpx.Response(200,json={"data":[{"id":"gpt-oss-120b","max_model_len":65536}]})
        requests.append(json.loads(r.content));return sse([{"choices":[{"delta":{"content":"Antwort"},"finish_reason":"stop"}]}])
    replace_transport(monkeypatch,handler)
    c.post("/api/connection/test")
    m=c.get("/api/bootstrap").json()["models"][0]
    assert m["deployment_context_tokens"]==65536 and m["context_source"]=="/models · max_model_len"
    t=thread(c);c.post(f"/api/threads/{t}/send",json={"content":"Frage"})
    assert "stream_options" not in requests[-1]
    c.post("/api/models",json={"id":"gpt-oss-120b","type":"chat","stream_usage":True})
    c.post(f"/api/threads/{t}/send",json={"content":"Frage"})
    assert requests[-1]["stream_options"]=={"include_usage":True}
    connect(c,base_url="https://other.test/v1")
    m=catalog.require("gpt-oss-120b","chat")
    assert m["deployment_context_tokens"] is None and m["stream_usage"] is False and not m["verified"]


def transcript(c,monkeypatch):
    connect(c)
    doc=upload(c,"meeting.webm",b"synthetic recording")
    original={"text":"Guten Morgen. Wir prüfen den Bericht.","language":"de","duration":5,
        "segments":[{"start":0,"end":1.8,"text":"Guten Morgen.","speaker":"SPEAKER_00"},
        {"start":2,"end":5,"text":"Wir prüfen den Bericht.","speaker":"SPEAKER_01"}]}
    received=[]
    def handler(r):
        received.append(r.content)
        if r.url.path.endswith("/audio/transcriptions"):return httpx.Response(200,json=original)
        return sse([{"choices":[{"delta":{"content":"## Aufgaben\nBericht prüfen · nicht genannt"},"finish_reason":"stop"}]}])
    replace_transport(monkeypatch,handler)
    c.post("/api/models",json={"id":"whisper-test","type":"audio"})
    response=c.post(f"/api/documents/{doc}/transcribe",json={"model":"whisper-test","language":"de","response_format":"verbose_json","project_id":"workspace"})
    assert response.status_code==200,response.text
    assert b'whisper-test' in received[-1] and b'verbose_json' in received[-1]
    ident=response.json()["transcript_id"]
    return ident,doc,original,received


def edit_body(row):
    keys=["title","text","segments","notes","meeting_date","participants","agenda","minutes_md"]
    return {"version":row["version"],**{k:row["working"][k] for k in keys}}


def test_transcript_edit_version_original_export_and_project_source(workspace,monkeypatch):
    c,_=workspace
    ident,doc,original,_=transcript(c,monkeypatch)
    row=c.get(f"/api/transcripts/{ident}").json()
    assert row["original"]==original and all(not s["verified"] for s in row["working"]["segments"])
    body=edit_body(row);body["segments"][0].update(text="Guten Tag.",speaker="Anna (manuell)",verified=True)
    body.update(meeting_date="2026-10-07",participants="Anna",notes="Am Audio geprüft")
    r=c.put(f"/api/transcripts/{ident}",json=body)
    assert r.status_code==200,r.text
    row=r.json();assert row["version"]==2 and row["original"]==original
    assert row["working"]["text"].startswith("Guten Tag.")
    assert c.put(f"/api/transcripts/{ident}",json=body).status_code==409
    store.initialize()
    md=c.get(f"/api/transcripts/{ident}/export").text
    assert "Anna (manuell)" in md and "00:00:01.800" in md and "manuell geprüft" in md
    assert c.get(f"/api/transcripts/{ident}/export?format=json").json()["original"]==original
    source=c.post(f"/api/transcripts/{ident}/source")
    assert source.status_code==200,source.text
    assert c.get(f"/api/documents/{source.json()['id']}/download").content.decode()==md
    assert c.delete(f"/api/documents/{doc}").status_code==200
    assert c.get(f"/api/transcripts/{ident}").json()["audio_document_id"] is None
    assert "Original nicht mehr verfügbar" in c.get(f"/api/transcripts/{ident}/export").text


def test_meeting_full_source_provenance_staleness_and_no_truncation(workspace,monkeypatch):
    c,_=workspace
    ident,doc,original,received=transcript(c,monkeypatch)
    row=c.get(f"/api/transcripts/{ident}").json()
    r=c.post(f"/api/transcripts/{ident}/minutes",json={"version":1,"model":"gpt-oss-120b","context_chars":0})
    assert r.status_code==200,r.text
    payload=json.loads(received[-1]);assert "Wir prüfen den Bericht." in payload["messages"][-1]["content"]
    assert "Erfinde keine Fakten" in payload["messages"][0]["content"]
    row=r.json();assert row["working"]["minutes_version"]==1 and row["version"]==2
    assert "## Aufgaben" in c.get(f"/api/transcripts/{ident}/export").text
    body=edit_body(row);body["segments"][0]["text"]="Korrektur"
    changed=c.put(f"/api/transcripts/{ident}",json=body).json()
    assert changed["working"]["minutes_stale"] is True
    assert c.post(f"/api/transcripts/{ident}/minutes",json={"version":2,"model":"gpt-oss-120b"}).status_code==409
    before=len(received)
    assert c.post(f"/api/transcripts/{ident}/minutes",json={"version":3,"model":"gpt-oss-120b","context_chars":1}).status_code==422
    assert len(received)==before


def test_transcript_export_and_source_require_requested_version(workspace,monkeypatch):
    c,_=workspace
    ident,_,original,_=transcript(c,monkeypatch)
    row=c.get(f"/api/transcripts/{ident}").json()
    body=edit_body(row);body["notes"]="Aktuelle Fassung − Unicode"
    saved=c.put(f"/api/transcripts/{ident}",json=body).json()
    assert saved["version"]==2
    documents_before=c.get("/api/documents").json()
    for format in ("md","json"):
        assert c.get(f"/api/transcripts/{ident}/export?format={format}&version=1").status_code==409
        exported=c.get(f"/api/transcripts/{ident}/export?format={format}&version=2")
        assert exported.status_code==200
        assert "Aktuelle Fassung − Unicode" in exported.text
    assert c.post(f"/api/transcripts/{ident}/source",json={"version":1}).status_code==409
    assert c.get("/api/documents").json()==documents_before
    source=c.post(f"/api/transcripts/{ident}/source",json={"version":2})
    assert source.status_code==200
    assert "Aktuelle Fassung − Unicode" in c.get(f"/api/documents/{source.json()['id']}/download").text
    assert c.get(f"/api/transcripts/{ident}").json()["original"]==original


@pytest.mark.parametrize("segment",[{"start":-1,"end":2,"text":"bad"},{"start":3,"end":1,"text":"bad"},{"start":"1","end":2,"text":"bad"}])
def test_invalid_segments_do_not_overwrite_original(workspace,monkeypatch,segment):
    c,_=workspace;ident,_,original,_=transcript(c,monkeypatch)
    row=c.get(f"/api/transcripts/{ident}").json();body=edit_body(row);body["segments"]=[segment]
    assert c.put(f"/api/transcripts/{ident}",json=body).status_code==422
    assert c.get(f"/api/transcripts/{ident}").json()["original"]==original


def test_plain_text_audio_has_no_fabricated_timestamps(workspace):
    c,calls=workspace;connect(c)
    doc=upload(c,"plain.wav",b"test")
    ident=c.post(f"/api/documents/{doc}/transcribe").json()["transcript_id"]
    row=c.get(f"/api/transcripts/{ident}").json()
    assert row["working"]["segments"]==[]
    assert "Keine Zeitsegmente" in row["working"]["segment_source"]
    assert "00:00:" not in c.get(f"/api/transcripts/{ident}/export").text


def test_error_classification_never_echoes_private_upstream_payload():
    for detail in ["context_length_exceeded", "max_tokens invalid"]:
        response=httpx.Response(400,json={"error":{"message":detail+" SECRET_PROMPT"}})
        with pytest.raises(ValueError) as error:gpu.check(response)
        assert "SECRET_PROMPT" not in str(error.value)
        assert "GPUStack" in str(error.value)


def test_pdf_preview_only_is_not_sent_as_model_context(workspace):
    c,calls=workspace;connect(c)
    pdf=PdfWriter();pdf.add_blank_page(width=100,height=100);out=io.BytesIO();pdf.write(out)
    ident=upload(c,"scan-preview.pdf",out.getvalue())
    t=thread(c)
    response=c.post(f"/api/threads/{t}/send",json={"content":"Meine Frage", "preview_ids":[ident]})
    assert response.status_code==200
    meta=c.get(f"/api/threads/{t}").json()["messages"][0]["metadata"]
    assert meta["documents"][0]["sent_as"]=="preview_only"
    assert meta["sources"]==[] and meta["images"]==[]
    assert "scan-preview.pdf" not in json.dumps(calls[-1][1])
    other=c.post("/api/projects",json={"name":"Anderes Projekt"}).json()["id"]
    unrelated=upload(c,"separat.pdf",out.getvalue(),project=other)
    assert c.post(f"/api/threads/{t}/send",json={"content":"Frage", "preview_ids":[unrelated]}).status_code==422


def test_literal_think_in_answer_is_not_hidden_and_partial_reasoning_survives(workspace,monkeypatch):
    c,_=workspace;connect(c)
    replace_transport(monkeypatch,lambda request:sse([{"choices":[{"delta":{"content":"HTML-Beispiel: <think>Text</think>"},"finish_reason":"stop"}]}]))
    t=thread(c);c.post(f"/api/threads/{t}/send",json={"content":"Beispiel"})
    assert c.get(f"/api/threads/{t}").json()["messages"][-1]["content"]=="HTML-Beispiel: <think>Text</think>"
    replace_transport(monkeypatch,lambda request:httpx.Response(200,text='data: {"choices":[{"delta":{"content":"<think>ab"}}]}\n\ndata: {"error":{"message":"SECRET"}}\n\n'))
    t=thread(c);c.post(f"/api/threads/{t}/send",json={"content":"Beispiel"})
    meta=c.get(f"/api/threads/{t}").json()["messages"][-1]["metadata"]
    assert meta["reasoning"]=="ab" and meta["status"]=="error"
    assert "SECRET" not in meta["error"]


def test_stream_context_error_is_classified_and_private_data_redacted(workspace,monkeypatch):
    c,_=workspace;connect(c)
    replace_transport(monkeypatch,lambda request:httpx.Response(400,json={"error":{"code":"context_length_exceeded","message":"SECRET_PRIVATE_CONTENT"}}))
    t=thread(c)
    result=c.post(f"/api/threads/{t}/send",json={"content":"Frage"})
    assert "Kontextfenster" in result.text and "SECRET_PRIVATE_CONTENT" not in result.text
