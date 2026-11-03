"""Test-only JSON/stdin bridge. No HTTP server and no real inference network."""
import io
import json
import sys
import tempfile
from pathlib import Path
from fastapi.testclient import TestClient
import httpx
from app import store,gpu
from app.main import app
from app import research,websearch

temporary=tempfile.TemporaryDirectory()
store.DATA=Path(temporary.name)/"data"
gpu._vault=lambda: (_ for _ in ()).throw(ValueError("No test vault"))

def handle(req):
    if req.url.path.endswith("/models"):
        return httpx.Response(200,json={"data":[{"id":"gpt-oss-120b"}]})
    if req.url.path.endswith("/audio/transcriptions"):
        return httpx.Response(200,json={"text":"Guten Morgen. Bericht prüfen.","language":"de","segments":[{"start":0,"end":1.5,"text":"Guten Morgen."},{"start":1.6,"end":3,"text":"Bericht prüfen."}]})
    if req.url.path.endswith("/chat/completions"):
        return httpx.Response(200,text='data: {"choices":[{"delta":{"reasoning_content":"Gelieferte Testbegründung"}}]}\n\ndata: {"choices":[{"delta":{"content":"Testantwort mit Beleg [Q1]."},"finish_reason":"stop"}]}\n\ndata: [DONE]\n\n',headers={"Content-Type":"text/event-stream"})
    return httpx.Response(200,json={})
gpu.client=lambda:httpx.AsyncClient(transport=httpx.MockTransport(handle),base_url="https://test.invalid/v1/")
original_research_client=research.client
research.client=lambda contact:original_research_client(contact,transport=httpx.MockTransport(
    lambda req:httpx.Response(200,json={"search":[{"id":"Q70","label":"Bern","description":"Test-Normdatentreffer"}]})))

websearch.search_client=lambda:httpx.AsyncClient(transport=httpx.MockTransport(
    lambda req:httpx.Response(200,json={"results":[{"title":"IIIF Webquelle","url":"https://public.example/iiif","content":"Öffentlicher Suchauszug"}]})))
def public_read(url,maximum,deadline):
    if url.endswith("/robots.txt"):return 200,{"content-type":"text/plain"},b"User-agent: *\nAllow: /"
    return 200,{"content-type":"text/html; charset=utf-8"},"<html><title>IIIF Webtext</title><main><p>Gelesener Inhalt − Unicode.</p></main><script>BAD_SCRIPT</script></html>".encode()
websearch.read_public=public_read

with TestClient(app,base_url="http://localhost") as client:
    for line in sys.stdin:
        data=json.loads(line)
        kwargs={"headers":data.get("headers",{})}
        if data.get("body") is not None: kwargs["content"]=data["body"]
        if data.get("multipart"):
            import base64
            multipart=data["multipart"]
            kwargs["data"]=multipart["fields"]
            kwargs["files"]=[(item["field"],(item["name"],base64.b64decode(item["base64"]),item["type"]))
                             for item in multipart["files"]]
        try:
            response=client.request(data["method"],data["path"],**kwargs)
            out={"id":data["id"],"status":response.status_code,"body":response.text,"headers":dict(response.headers)}
        except Exception as e:
            out={"id":data["id"],"status":500,"body":json.dumps({"detail":str(e)}),"headers":{}}
        print(json.dumps(out),flush=True)
temporary.cleanup()
