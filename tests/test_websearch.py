"""General search, public-page boundary and grounded chat; synthetic providers only."""
import asyncio
import json
import socket
import ssl
import time
from pathlib import Path

import httpx
import pytest
from app import gpu, limits, store, websearch
from tests.test_workroom import workspace, connect, thread, upload


@pytest.fixture(autouse=True)
def web_state(monkeypatch):
    monkeypatch.setattr(websearch, "_session_key", "")
    monkeypatch.setattr(websearch, "_snapshots", websearch.OrderedDict())
    monkeypatch.delenv("BRAVE_SEARCH_API_KEY", raising=False)


def setup(c, provider="searxng", **options):
    connect(c, internet_enabled=True)
    body={"provider":provider,"searxng_url":"https://searx.public.example","api_key":"",**options}
    response=c.post("/api/web/config",json=body)
    assert response.status_code==200,response.text
    return response.json()


def search_transport(monkeypatch, handler):
    captured=[]
    def wrapped(request):
        captured.append(request)
        return handler(request)
    original=websearch.search_client
    monkeypatch.setattr(websearch,"search_client",lambda:httpx.AsyncClient(
        transport=httpx.MockTransport(wrapped),follow_redirects=False,trust_env=False,headers={"User-Agent":websearch.AGENT,"Accept":"application/json"}))
    return captured


def searx_response(**extra):
    return {"results":[{"title":"<b>IIIF</b> – Spezifikation","url":"https://iiif.io/api/presentation/3.0/","content":"Offizielle Spezifikation."},
        {"title":"Lokaler Dienst","url":"https://127.0.0.1/private","content":"bad"},
        {"title":"Doppelt","url":"https://iiif.io/api/presentation/3.0/","content":"duplicate"}],**extra}


def test_no_implicit_search_and_disabled_boundaries(workspace,monkeypatch):
    c,calls=workspace
    requests=search_transport(monkeypatch,lambda r:httpx.Response(200,json=searx_response()))
    assert c.get("/api/bootstrap").json()["web_search"]["ready"] is False
    assert not requests and not calls
    assert c.post("/api/research",json={"query":"IIIF","source":"web"}).status_code==422
    assert c.post("/api/web/page",json={"url":"https://iiif.io/"}).status_code==422
    setup(c)
    connect(c,internet_enabled=False)
    t=thread(c)
    result=c.post(f"/api/threads/{t}/send",json={"content":"Frage","web_search":True,"web_query":"IIIF"})
    assert result.status_code==422
    assert not requests and not calls and not c.get(f"/api/threads/{t}").json()["messages"]


def test_searx_query_filters_provenance_and_source_snapshot(workspace,monkeypatch):
    c,_=workspace;setup(c)
    reqs=search_transport(monkeypatch,lambda r:httpx.Response(200,json=searx_response(unresponsive_engines=[["engine","timeout"]])))
    r=c.post("/api/research",json={"query":"IIIF","source":"web","language":"en","freshness":"month"})
    assert r.status_code==200,r.text
    result=r.json();assert len(result["results"])==1 and result["notes"]
    params=reqs[0].url.params
    assert params["q"]=="IIIF" and params["format"]=="json" and params["time_range"]=="month" and params["language"]=="en"
    assert reqs[0].headers.get("authorization") is None and reqs[0].headers.get("cookie") is None
    source=c.post("/api/web/source",json={"snapshot_id":result["snapshot_id"],"index":0,"project_id":"workspace"})
    assert source.status_code==200
    text=c.get(f"/api/documents/{source.json()['id']}/download").text
    assert "Suchauszug, kein gelesener Volltext" in text and "SearXNG" in text and "Suchtext: IIIF" in text
    assert "Offizielle Spezifikation" in text
    assert c.post("/api/web/source",json={"snapshot_id":"missing","index":0,"project_id":"workspace"}).status_code==422


def test_brave_key_separated_persistence_and_no_leak(workspace,monkeypatch):
    c,_=workspace
    connect(c,internet_enabled=True,api_key="GPU_PRIVATE_TEST_SECRET")
    r=c.post("/api/web/config",json={"provider":"brave","api_key":"BRAVE_PRIVATE_TEST_SECRET"})
    assert r.status_code==200 and "PRIVATE" not in r.text
    reqs=search_transport(monkeypatch,lambda r:httpx.Response(200,json={"web":{"results":[{"title":"Bericht","url":"https://public.example/report","description":"Auszug","extra_snippets":["Zweiter Auszug"]}]}}))
    r=c.post("/api/research",json={"source":"web","query":"öffentliche Frage","freshness":"day"})
    assert r.status_code==200
    assert reqs[0].url.host=="api.search.brave.com" and reqs[0].headers["X-Subscription-Token"]=="BRAVE_PRIVATE_TEST_SECRET"
    assert "GPU_PRIVATE" not in str(reqs[0].headers)
    bootstrap=c.get("/api/bootstrap");assert "PRIVATE" not in bootstrap.text
    assert "PRIVATE" not in str(store.rows("SELECT * FROM settings"))
    assert "PRIVATE" not in c.get("/api/backup").content.decode("latin1")
    assert gpu.credential()=="GPU_PRIVATE_TEST_SECRET"
    assert c.post("/api/web/config",json={"provider":"brave","forget_key":True}).status_code==200
    assert gpu.credential()=="GPU_PRIVATE_TEST_SECRET" and websearch.credential()==""
    before=len(reqs)
    assert c.post("/api/research",json={"source":"web","query":"Frage"}).status_code==422
    assert len(reqs)==before


def test_os_vault_and_environment_independent_of_gpu(workspace,monkeypatch):
    c,_=workspace;vault={}
    class Vault:
        def get_password(self,s,a):return vault.get((s,a))
        def set_password(self,s,a,v):vault[s,a]=v
        def delete_password(self,s,a):del vault[s,a]
    monkeypatch.setattr(gpu,"_vault",lambda:Vault())
    setup(c,provider="brave",api_key="SAVED_SEARCH_KEY",persist_key=True)
    assert websearch._session_key=="" and websearch.credential()=="SAVED_SEARCH_KEY"
    assert websearch.key_status()=="Betriebssystem-Schlüsselspeicher"
    assert gpu.credential()==""
    monkeypatch.setenv("BRAVE_SEARCH_API_KEY","ENV_SEARCH_KEY")
    assert websearch.key_status()=="Umgebungsvariable"
    assert c.post("/api/web/config",json={"provider":"brave","forget_key":True}).status_code==422
    assert c.post("/api/web/config",json={"provider":"brave","api_key":"OTHER"}).status_code==422


@pytest.mark.parametrize("body",[{"provider":"unknown"},{"provider":"searxng","searxng_url":"http://192.168.1.2"},{"provider":"searxng","searxng_url":"https://name:secret@public.example"},{"provider":"brave","api_key":"BAD\nKEY"}])
def test_invalid_configuration_does_not_echo_secrets(workspace,body):
    c,_=workspace
    r=c.post("/api/web/config",json=body)
    assert r.status_code==422 and "secret" not in r.text and "BAD" not in r.text


@pytest.mark.parametrize("status",[301,401,403,429,500])
def test_provider_errors_no_redirect_fallback_or_key_echo(workspace,monkeypatch,status):
    c,_=workspace;setup(c,provider="brave",api_key="TEST_SECRET")
    reqs=search_transport(monkeypatch,lambda r:httpx.Response(status,headers={"location":"https://evil.example/"},json={"error":"TEST_SECRET private input"}))
    result=c.post("/api/research",json={"source":"web","query":"Bern"})
    assert result.status_code==422 and "TEST_SECRET" not in result.text and "private input" not in result.text
    assert len(reqs)==1


@pytest.mark.parametrize("reply",[httpx.Response(200,text="<html>Login</html>",headers={"content-type":"text/html"}),httpx.Response(200,text="{bad",headers={"content-type":"application/json"}),httpx.Response(200,json={"results":{}}),httpx.Response(200,content=b"x"*(2*1024*1024+1),headers={"content-type":"application/json"})])
def test_malformed_and_oversized_provider_answers(workspace,monkeypatch,reply):
    c,_=workspace;setup(c)
    search_transport(monkeypatch,lambda r:reply)
    assert c.post("/api/research",json={"query":"Bern","source":"web"}).status_code==422


def test_chat_only_public_query_sent_sources_exported_unique_labels(workspace,monkeypatch):
    c,gpu_calls=workspace;setup(c)
    doc=upload(c,text=b"PROJECT_PRIVATE_DOCUMENT Bern")
    reqs=search_transport(monkeypatch,lambda r:httpx.Response(200,json=searx_response()))
    t=thread(c,system_prompt="PRIVATE_SYSTEM",context_chars=0)
    for i in range(2):
        response=c.post(f"/api/threads/{t}/send",json={"content":"CHAT_PRIVATE_QUESTION Bern", "document_ids":[doc],"web_search":True,"web_query":"IIIF"})
        assert response.status_code==200,response.text
    assert len(reqs)==2
    for req in reqs:
        assert req.url.params["q"]=="IIIF" and "PRIVATE" not in str(req.url) and not req.content
    payload=gpu_calls[-1][1]
    assert "PRIVATE_SYSTEM" in payload["messages"][0]["content"]
    assert "Suchauszüge sind kein gelesener Volltext" in payload["messages"][0]["content"]
    assert "W2" in payload["messages"][-1]["content"]
    row=c.get(f"/api/threads/{t}").json()["messages"][-2]
    assert row["metadata"]["web_search"]["sent_query"]=="IIIF"
    assert {s["label"] for s in row["metadata"]["sources"]}=={"Q2","W2"}
    assert "https://iiif.io/" in c.get(f"/api/threads/{t}/export").text
    assert "Abruf" in c.get(f"/api/threads/{t}/export").text


def test_chat_missing_query_empty_search_and_budget_are_local(workspace,monkeypatch):
    c,gpu_calls=workspace;setup(c)
    reqs=search_transport(monkeypatch,lambda r:httpx.Response(200,json={"results":[]}))
    t=thread(c)
    response=c.post(f"/api/threads/{t}/budget",json={"content":"Frage","web_search":True,"web_query":"IIIF"})
    assert response.status_code==200 and "Webtreffer" in response.json()["note"]
    assert not reqs and not gpu_calls
    assert c.post(f"/api/threads/{t}/send",json={"content":"Frage","web_search":True}).status_code==422
    assert not reqs
    assert c.post(f"/api/threads/{t}/send",json={"content":"Frage","web_search":True,"web_query":"IIIF"}).status_code==422
    assert len(reqs)==1 and not gpu_calls and c.get(f"/api/threads/{t}").json()["messages"]==[]


@pytest.mark.parametrize("url",["http://public.example/","https://localhost/","https://127.0.0.1/","https://169.254.169.254/","https://192.168.1.2/","https://100.64.0.1/","https://[::1]/","https://[::ffff:127.0.0.1]/","https://name:pass@public.example/","https://public.example:8443/","file:///etc/passwd","https://public.example\\@localhost/","https://internal.local/"])
def test_private_and_credential_urls_blocked_before_network(workspace,monkeypatch,url):
    c,_=workspace;setup(c)
    monkeypatch.setattr(websearch,"read_public",lambda *a:pytest.fail("blocked URL reached network"))
    assert c.post("/api/web/page",json={"url":url}).status_code==422


def test_dns_mixed_answers_blocked_and_public_ip_pinned(monkeypatch):
    def addr(ip):return (socket.AF_INET,socket.SOCK_STREAM,6,"",(ip,443))
    monkeypatch.setattr(socket,"getaddrinfo",lambda *a,**k:[addr("93.184.216.34"),addr("127.0.0.1")])
    with pytest.raises(ValueError,match="intern"):
        websearch.resolve_public("public.example")
    monkeypatch.setattr(socket,"getaddrinfo",lambda *a,**k:[addr("93.184.216.34")])
    connections=[]; tls_names=[]
    class Sock:
        def close(self):pass
    class Context:
        def wrap_socket(self,sock,server_hostname):tls_names.append(server_hostname);return sock
    monkeypatch.setattr(socket,"create_connection",lambda address,timeout:(connections.append(address) or Sock()))
    connection=websearch.PublicHTTPSConnection("public.example",context=ssl.create_default_context());connection._context=Context();connection.deadline=time.monotonic()+10
    connection.connect()
    assert connections==[("93.184.216.34",443)] and tls_names==["public.example"]
    connection.close()


def fake_page(monkeypatch,body="<html><title>Unicode −</title><nav>Navigation</nav><main><h1>Bericht</h1><p>Inhalt − Bern.</p></main><script>SECRET_SCRIPT</script></html>".encode(),robots=b"User-agent: *\nAllow: /",status=200,headers=None):
    calls=[]
    def read(url,maximum,deadline):
        calls.append(url)
        if url.endswith("/robots.txt"):
            return 200,{"content-type":"text/plain; charset=utf-8"},robots
        return status,headers or {"content-type":"text/html; charset=utf-8"},body
    monkeypatch.setattr(websearch,"read_public",read)
    return calls


def test_page_extraction_provenance_and_local_save(workspace,monkeypatch):
    c,_=workspace;setup(c)
    calls=fake_page(monkeypatch,body="<html><title>Unicode −</title><nav>Navigation</nav><main><h1>Bericht</h1><p>Inhalt − Bern.</p></main><script>SECRET_SCRIPT</script></html>".encode())
    r=c.post("/api/web/page",json={"url":"https://public.example/report"})
    assert r.status_code==200,r.text
    result=r.json();row=result["results"][0]
    assert row["text"]=="Bericht\nInhalt − Bern." and "SECRET_SCRIPT" not in row["text"]
    assert row["title"]=="Unicode −" and row["kind"]=="page" and row["sha256"]
    before=len(calls)
    saved=c.post("/api/web/source",json={"snapshot_id":result["snapshot_id"],"index":0,"project_id":"workspace"})
    assert saved.status_code==200 and len(calls)==before
    assert "Extrahierter Webtext" in c.get(f"/api/documents/{saved.json()['id']}/download").text


def test_robots_disallow_and_redirect_to_private_are_blocked(workspace,monkeypatch):
    c,_=workspace;setup(c)
    calls=fake_page(monkeypatch,robots=b"User-agent: *\nDisallow: /")
    assert c.post("/api/web/page",json={"url":"https://public.example/report"}).status_code==422
    assert len(calls)==1
    calls=fake_page(monkeypatch,status=302,headers={"location":"https://127.0.0.1/private"})
    assert c.post("/api/web/page",json={"url":"https://public.example/report"}).status_code==422
    assert len(calls)==2


def test_unsupported_page_types_and_truncation_are_explicit(workspace,monkeypatch):
    c,_=workspace;setup(c)
    fake_page(monkeypatch,headers={"content-type":"application/pdf"})
    r=c.post("/api/web/page",json={"url":"https://public.example/a.pdf"})
    assert r.status_code==422 and "PDF" in r.text
    c.put("/api/limits",json={"web_page_chars":1000})
    fake_page(monkeypatch,body=b"<p>"+b"x"*3000+b"</p>")
    row=c.post("/api/web/page",json={"url":"https://public.example/report"}).json()["results"][0]
    assert row["truncated"] and len(row["text"])==1000


def test_chat_optional_page_failure_keeps_snippet_and_discloses(workspace,monkeypatch):
    c,calls=workspace;setup(c)
    search_transport(monkeypatch,lambda r:httpx.Response(200,json=searx_response()))
    async def denied(url):raise ValueError("Abruf untersagt")
    monkeypatch.setattr(websearch,"fetch_page",denied)
    t=thread(c,context_chars=0)
    r=c.post(f"/api/threads/{t}/send",json={"content":"Frage","web_search":True,"web_query":"IIIF","web_read_pages":True})
    assert r.status_code==200
    row=c.get(f"/api/threads/{t}").json()["messages"][0]
    assert row["metadata"]["sources"][0]["kind"]=="snippet"
    assert "Nur Suchauszug" in row["metadata"]["notes"][-1]


def test_search_timeout_and_snapshot_expiry(workspace,monkeypatch):
    c,_=workspace;setup(c)
    def timeout(r):raise httpx.ReadTimeout("PRIVATE_UPSTREAM",request=r)
    search_transport(monkeypatch,timeout)
    r=c.post("/api/research",json={"query":"Bern","source":"web"})
    assert r.status_code==422 and "PRIVATE_UPSTREAM" not in r.text
    snapshot=websearch.remember({"results":[{"text":"x"}]})
    stamp,data=websearch._snapshots[snapshot["snapshot_id"]]
    websearch._snapshots[snapshot["snapshot_id"]]=(stamp-1801,data)
    with pytest.raises(ValueError,match="abgelaufen"):
        websearch.snapshot(snapshot["snapshot_id"],0)


def test_stop_during_research_releases_thread_without_inference(workspace,monkeypatch):
    from fastapi import Request
    c,calls=workspace;setup(c);t=thread(c)
    cancelled=[]
    async def waiting(*args):
        try:await asyncio.sleep(10)
        finally:cancelled.append(True)
    async def disconnected(self):return True
    monkeypatch.setattr(websearch,"chat_context",waiting)
    monkeypatch.setattr(Request,"is_disconnected",disconnected)
    r=c.post(f"/api/threads/{t}/send",json={"content":"Frage","web_search":True,"web_query":"IIIF"})
    assert r.status_code==499 and cancelled and not calls
    assert c.get(f"/api/threads/{t}").json()["messages"]==[]
    from app.main import ACTIVE
    assert t not in ACTIVE


def test_actual_reader_byte_limit_and_no_sensitive_headers(monkeypatch):
    captured={};closed=[]
    class Response:
        status=200
        def getheaders(self):return [("content-type","text/plain")]
        def read1(self,size):return b"x"*size
    class Connection:
        def __init__(self,host,**kwargs):captured["host"]=host
        def request(self,method,path,headers):captured.update(method=method,path=path,headers=headers)
        def getresponse(self):return Response()
        def close(self):closed.append(True)
    monkeypatch.setattr(websearch,"PublicHTTPSConnection",Connection)
    with pytest.raises(ValueError,match="Abrufgrenze"):
        websearch.read_public("https://public.example/über?q=Bern",100,time.monotonic()+10)
    assert captured["method"]=="GET" and "%C3%BCber" in captured["path"]
    assert not any(k.lower() in ("authorization","cookie","x-subscription-token") for k in captured["headers"])
    assert closed


def test_redirect_rechecks_robots_and_preserves_final_url(workspace,monkeypatch):
    c,_=workspace;setup(c)
    calls=[]
    def read(url,maximum,deadline):
        calls.append(url)
        if url.endswith("/robots.txt"):return 404,{},b""
        if url=="https://first.example/page":return 302,{"location":"https://second.example/final"},b""
        return 200,{"content-type":"text/plain; charset=iso-8859-1"},b"B\xe4ren Bern"
    monkeypatch.setattr(websearch,"read_public",read)
    row=c.post("/api/web/page",json={"url":"https://first.example/page"}).json()["results"][0]
    assert row["text"]=="Bären Bern" and row["requested_url"]=="https://first.example/page" and row["url"]=="https://second.example/final"
    assert calls==["https://first.example/robots.txt","https://first.example/page","https://second.example/robots.txt","https://second.example/final"]


def test_adding_web_sources_cannot_overrun_chat_budget(workspace,monkeypatch):
    c,calls=workspace;setup(c)
    search_transport(monkeypatch,lambda r:httpx.Response(200,json={"results":[{"title":"Long","url":"https://public.example/long","content":"x"*3000}]}))
    t=thread(c,context_chars=1500)
    result=c.post(f"/api/threads/{t}/send",json={"content":"Frage","web_search":True,"web_query":"IIIF"})
    assert result.status_code==422 and "Eingabebudget" in result.text and not calls
    assert c.get(f"/api/threads/{t}").json()["messages"]==[]
