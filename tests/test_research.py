"""Provider contracts and explicit outbound-data boundaries, using synthetic API replies."""
import httpx
import pytest
from app import research
from .test_workroom import workspace, connect

RESPONSES = {
    "crossref": {"message": {"items": [{"title": ["Testpublikation"], "DOI": "10.1234/test",
                   "abstract": "<jats:p>Ein Abstract &amp; Beleg.</jats:p>"}]}},
    "wikidata": {"search": [{"id": "Q70", "label": "Bern", "description": "Stadt in der Schweiz"}]},
    "gnd": {"member": [{"gndIdentifier": "4005762-9", "preferredName": "Bern",
            "id": "http://d-nb.info/gnd/4005762-9"}]},
    "datacite": {"data": [{"id": "10.1234/data", "attributes": {"doi": "10.1234/data",
                "titles": [{"title": "Testdaten"}], "publisher": "Testarchiv", "publicationYear": 2026,
                "descriptions": [{"description": "Ein <b>Datensatz</b>."}]}}]},
}
EMPTY = {"crossref": {"message": {"items": []}}, "wikidata": {"search": []},
         "gnd": {"member": []}, "datacite": {"data": []}}
CONTACT = "mailto:operator@example.org"


def transport(monkeypatch, handler):
    calls = []
    original = research.client
    def record(request):
        calls.append(request)
        return handler(request)
    monkeypatch.setattr(research, "client",
        lambda contact: original(contact, transport=httpx.MockTransport(record)))
    return calls


def enable(client):
    connect(client, internet_enabled=True, research_contact=CONTACT,
            api_key="TEST_GPUSTACK_SECRET_NEVER_TO_RESEARCH")


@pytest.mark.parametrize("source", list(RESPONSES))
def test_provider_search_and_outbound_boundary(workspace, monkeypatch, source):
    client, gpu_calls = workspace
    enable(client)
    calls = transport(monkeypatch, lambda req: httpx.Response(200, json=RESPONSES[source]))
    response = client.post("/api/research", json={"query": "Bern", "source": source})
    assert response.status_code == 200, response.text
    body = response.json()
    assert body["source"] == source and body["sent_query"] == "Bern"
    assert body["retrieved_at"]
    assert len(body["results"]) == 1
    assert body["results"][0]["url"].startswith("https://")
    assert "<b>" not in body["results"][0]["text"]
    assert "<jats:" not in body["results"][0]["text"]
    assert not gpu_calls
    assert len(calls) == 1
    request = calls[0]
    assert str(request.url).startswith(research.SOURCES[source]["endpoint"])
    assert request.content == b""
    assert "authorization" not in request.headers and "cookie" not in request.headers
    assert "TEST_GPUSTACK_SECRET" not in str(request.headers) + str(request.url)
    assert CONTACT in request.headers["user-agent"]
    assert "ResearchBot/" in request.headers["user-agent"]
    query_key = {"wikidata": "search", "gnd": "q"}.get(source, "query")
    assert request.url.params[query_key] == "Bern"
    if source == "wikidata":
        assert request.url.params["action"] == "wbsearchentities"
        assert request.url.params["language"] == "de"
        assert request.url.params["type"] == "item"
    if source == "crossref":
        assert body["results"][0]["text"] == "Ein Abstract & Beleg."


@pytest.mark.parametrize("source", list(EMPTY))
def test_valid_empty_search_is_not_error(workspace, monkeypatch, source):
    client, _ = workspace
    enable(client)
    transport(monkeypatch, lambda req: httpx.Response(200, json=EMPTY[source]))
    response = client.post("/api/research", json={"query": "KeinTreffer", "source": source})
    assert response.status_code == 200, response.text
    assert response.json()["results"] == []


@pytest.mark.parametrize("response,expected", [
    (httpx.Response(403, text="private remote HTML"), "HTTP 403"),
    (httpx.Response(429, json={}), "HTTP 429"),
    (httpx.Response(503, json={}), "HTTP 503"),
    (httpx.Response(400, json={}), "HTTP 400"),
    (httpx.Response(200, text="<html>challenge</html>", headers={"content-type": "text/html"}), "HTML-Seite"),
    (httpx.Response(200, text="not json", headers={"content-type": "application/json"}), "Ungültige JSON"),
    (httpx.Response(200, json={}), "Suchformat"),
    (httpx.Response(200, json={"search": "wrong type"}), "Suchformat"),
])
def test_diagnostic_errors_preserve_source_and_reason(workspace, monkeypatch, response, expected):
    client, _ = workspace
    enable(client)
    transport(monkeypatch, lambda req: response)
    result = client.post("/api/research", json={"query": "Bern", "source": "wikidata"})
    assert result.status_code == 422, result.text
    assert "Wikidata" in result.json()["detail"] and expected in result.json()["detail"]
    assert "private remote HTML" not in result.text


@pytest.mark.parametrize("code,expected", [("maxlag", "ausgelastet"), ("ratelimited", "ausgelastet"),
                                        ("badvalue", "zurückgewiesen")])
def test_mediawiki_error_with_http_200_is_not_empty_success(workspace, monkeypatch, code, expected):
    client, _ = workspace
    enable(client)
    transport(monkeypatch, lambda req: httpx.Response(200, json={"error": {"code": code, "info": "not echoed"}}))
    response = client.post("/api/research", json={"query": "Bern", "source": "wikidata"})
    assert response.status_code == 422 and expected in response.text
    assert "not echoed" not in response.text


@pytest.mark.parametrize("exception,expected", [
    (httpx.ReadTimeout("timeout"), "Zeitüberschreitung"),
    (httpx.ConnectError("connection refused"), "Verbindung"),
    (httpx.ConnectError("CERTIFICATE_VERIFY_FAILED"), "TLS-Zertifikat"),
])
def test_transport_failures_are_distinguishable(workspace, monkeypatch, exception, expected):
    client, _ = workspace
    enable(client)
    def fail(request):
        raise exception
    transport(monkeypatch, fail)
    response = client.post("/api/research", json={"query": "Bern", "source": "wikidata"})
    assert response.status_code == 422 and expected in response.text


@pytest.mark.parametrize("location", ["https://evil.example/search", "http://www.wikidata.org/w/api.php"])
def test_redirect_does_not_send_query_to_another_provider(workspace, monkeypatch, location):
    client, _ = workspace
    enable(client)
    calls = transport(monkeypatch, lambda req: httpx.Response(302, headers={"location": location}))
    response = client.post("/api/research", json={"query": "Bern", "source": "wikidata"})
    assert response.status_code == 422 and "Weiterleitung" in response.text
    assert len(calls) == 1


def test_canonical_wikidata_redirect_is_supported(workspace, monkeypatch):
    client, _ = workspace
    enable(client)
    def handler(req):
        if req.url.host == "www.wikidata.org":
            return httpx.Response(301, headers={"location": "https://wikidata.org/w/api.php?" + req.url.query.decode()})
        return httpx.Response(200, json=RESPONSES["wikidata"])
    calls = transport(monkeypatch, handler)
    response = client.post("/api/research", json={"query": "Bern", "source": "wikidata"})
    assert response.status_code == 200, response.text
    assert len(calls) == 2 and calls[-1].url.params["search"] == "Bern"


def test_disabled_unknown_and_missing_contact_make_no_request(workspace, monkeypatch):
    client, _ = workspace
    calls = transport(monkeypatch, lambda req: httpx.Response(200, json={}))
    assert client.post("/api/research", json={"query": "Bern", "source": "wikidata"}).status_code == 422
    connect(client, internet_enabled=True)
    missing = client.post("/api/research", json={"query": "Bern", "source": "wikidata"})
    assert missing.status_code == 422 and "Recherchekontakt" in missing.text
    unknown = client.post("/api/research", json={"query": "Bern", "source": "https://evil.example"})
    assert unknown.status_code == 422 and "Unbekannte" in unknown.text
    assert not calls


@pytest.mark.parametrize("contact", ["a@example.org\r\nAuthorization: bad",
                                   "https://example.org:invalid", "http://example.org",
                                   "https://user:password@example.org"])
def test_invalid_contact_cannot_become_a_header(workspace, contact):
    client, _ = workspace
    body={"base_url":"https://gpu.test/v1", "embedding_model":"qwen3-embedding-0.6b",
          "research_contact":contact}
    response=client.post("/api/connection",json=body)
    assert response.status_code == 422
    assert not client.get("/api/bootstrap").json()["connection"].get("research_contact")


def test_long_metadata_is_preserved_beyond_old_2000_and_truncation_is_explicit(workspace,monkeypatch):
    client,_=workspace;enable(client)
    data={"message":{"items":[{"title":["Langes Abstract"],"DOI":"10.1234/test","abstract":"A"*25000}]}}
    transport(monkeypatch,lambda req:httpx.Response(200,json=data))
    result=client.post("/api/research",json={"query":"Test","source":"crossref"}).json()["results"][0]
    assert len(result["text"])==20000 and result["truncated"] is True
