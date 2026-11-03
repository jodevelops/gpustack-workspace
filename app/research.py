"""Explicit, read-only searches. No GPUStack credentials, documents or chat context."""
import html
import json
import os
import re
import ssl
from urllib.parse import quote, urlsplit

import httpx

SOURCES = {
    "crossref": {"name": "Crossref", "endpoint": "https://api.crossref.org/works",
                "description": "Publikationsmetadaten und vorhandene Abstracts"},
    "wikidata": {"name": "Wikidata", "endpoint": "https://www.wikidata.org/w/api.php",
                "description": "Entitäten, Kennungen und kurze Beschreibungen"},
    "gnd": {"name": "GND / lobid", "endpoint": "https://lobid.org/gnd/search",
            "description": "Normdaten für Personen, Orte, Körperschaften und Begriffe"},
    "datacite": {"name": "DataCite", "endpoint": "https://api.datacite.org/dois",
                 "description": "DOI-Metadaten zu Forschungsdaten und weiteren Forschungsobjekten"},
}


def source_catalog():
    return [{"id": key, "name": value["name"], "description": value["description"]}
            for key, value in SOURCES.items()]


def normalize_contact(value):
    value = value.strip()
    if not value:
        return ""
    if len(value) > 200 or any(ord(ch) < 33 or ord(ch) > 126 or ch in "()" for ch in value):
        raise ValueError("Recherchekontakt: eine E-Mail-Adresse oder HTTPS-Kontaktseite ohne Leerzeichen eingeben.")
    email = value.removeprefix("mailto:")
    if re.fullmatch(r"[^@:/?#]+@[^@:/?#]+\.[A-Za-z]{2,}", email):
        return "mailto:" + email
    try:
        parsed = urlsplit(value)
        port = parsed.port
    except ValueError:
        raise ValueError("Recherchekontakt: ungültige HTTPS-Kontaktseite.") from None
    if (parsed.scheme == "https" and parsed.hostname and not parsed.username
            and not parsed.password and not parsed.query and not parsed.fragment
            and port in (None, 443)):
        return value
    raise ValueError("Recherchekontakt: eine E-Mail-Adresse oder HTTPS-Kontaktseite eingeben.")


def client(contact, *, transport=None):
    agent = "GPUStack-ArbeitsraumResearchBot/0.1.4"
    if contact:
        agent += " (" + contact + ")"
    agent += " httpx/" + httpx.__version__
    return httpx.AsyncClient(
        timeout=httpx.Timeout(25, connect=10), trust_env=False, follow_redirects=False,
        verify=ssl.create_default_context(cafile=os.environ.get("SSL_CERT_FILE") or None),
        transport=transport,
        headers={"User-Agent": agent, "Accept": "application/json"},
    )


def _text(value):
    return value if isinstance(value, str) else ""


def _plain(value):
    return html.unescape(re.sub(r"<[^>]*>", "", _text(value)))


def _result(title, url, text):
    title,text=_plain(title),_plain(text)
    return {"title": title[:2000] or "Ohne Titel", "url": url,
            "text": text[:20000], "truncated":len(title)>2000 or len(text)>20000}


def _invalid(source):
    return ValueError(SOURCES[source]["name"] + ": Die API-Antwort hat nicht das erwartete Suchformat.")


def _entries(data, source):
    try:
        if source == "crossref":
            items = data["message"]["items"]
        elif source == "wikidata":
            items = data["search"]
        elif source == "gnd":
            items = data["member"]
        else:
            items = data["data"]
        if not isinstance(items, list) or any(not isinstance(item, dict) for item in items):
            raise _invalid(source)
        return items[:8]
    except (KeyError, TypeError):
        raise _invalid(source) from None


def parse(data, source):
    results = []
    for item in _entries(data, source):
        if source == "crossref":
            titles = item.get("title")
            title = titles[0] if isinstance(titles, list) and titles else "Ohne Titel"
            doi = _text(item.get("DOI"))
            url = "https://doi.org/" + quote(doi, safe="/") if doi else _text(item.get("URL"))
            if url.startswith("http://doi.org/"):
                url = "https://" + url[7:]
            text = _plain(item.get("abstract")) or "Publikationsmetadaten · " + _text(item.get("publisher"))
            results.append(_result(title, url, text))
        elif source == "wikidata":
            ident = _text(item.get("id"))
            if not re.fullmatch(r"Q\d+", ident):
                raise _invalid(source)
            results.append(_result(item.get("label") or ident,
                "https://www.wikidata.org/wiki/" + ident,
                "Wikidata-ID: " + ident + " · " + _text(item.get("description"))))
        elif source == "gnd":
            ident = _text(item.get("gndIdentifier")) or _text(item.get("id")).rstrip("/").rsplit("/", 1)[-1]
            if not re.fullmatch(r"[0-9X-]{3,30}", ident):
                raise _invalid(source)
            details = ["GND-ID: " + ident]
            for field, label in (("dateOfBirth", "Geboren"), ("dateOfDeath", "Gestorben")):
                values = item.get(field, [])
                if isinstance(values, str):
                    values = [values]
                if isinstance(values, list):
                    values = [v for v in values if isinstance(v, str)]
                    if values:
                        details.append(label + ": " + ", ".join(values))
            occupations = item.get("professionOrOccupation", [])
            if isinstance(occupations, list):
                labels = [_text(x.get("label")) for x in occupations if isinstance(x, dict)]
                details.extend(label for label in labels if label)
            results.append(_result(item.get("preferredName") or ident,
                "https://lobid.org/gnd/" + ident, " · ".join(details)))
        else:
            attributes = item.get("attributes")
            if not isinstance(attributes, dict):
                raise _invalid(source)
            doi = _text(attributes.get("doi")) or _text(item.get("id"))
            if not re.fullmatch(r"10\.\d{4,9}/\S+", doi):
                raise _invalid(source)
            titles = attributes.get("titles", [])
            title = next((_text(x.get("title")) for x in titles if isinstance(x, dict)), doi) if isinstance(titles, list) else doi
            descriptions = attributes.get("descriptions", [])
            text = next((_text(x.get("description")) for x in descriptions if isinstance(x, dict)), "") if isinstance(descriptions, list) else ""
            if not text:
                text = "DOI: " + doi + " · " + _text(attributes.get("publisher"))
                if attributes.get("publicationYear") is not None:
                    text += " · " + str(attributes["publicationYear"])
            results.append(_result(title, "https://doi.org/" + quote(doi, safe="/"), text))
    return results


def parameters(source, query):
    if source == "crossref":
        return {"query": query, "rows": 8}
    if source == "wikidata":
        return {"action": "wbsearchentities", "search": query, "language": "de",
                "uselang": "de", "type": "item", "format": "json", "limit": 8, "maxlag": 5}
    if source == "gnd":
        return {"q": query, "format": "json", "size": 8}
    return {"query": query, "page[size]": 8}


async def search(query, source, contact=""):
    if source not in SOURCES:
        raise ValueError("Unbekannte Datenquelle.")
    contact = normalize_contact(contact)
    name = SOURCES[source]["name"]
    if source == "wikidata" and not contact:
        raise ValueError("Wikidata: Bitte unter Einstellungen einen Recherchekontakt "
                         "(E-Mail oder HTTPS-Kontaktseite) für die API-Kennung hinterlegen.")
    endpoint = SOURCES[source]["endpoint"]
    allowed_hosts = {urlsplit(endpoint).hostname}
    if source == "wikidata":
        allowed_hosts.add("wikidata.org")
    params = parameters(source, query)
    try:
        async with client(contact) as connection:
            for redirect in range(3):
                response = await connection.get(endpoint, params=params)
                status = response.status_code
                if not 300 <= status < 400:
                    break
                location = response.headers.get("location")
                target = response.url.join(location) if location else None
                if (redirect == 2 or target is None or target.scheme != "https"
                        or target.host not in allowed_hosts or target.port not in (None, 443)
                        or target.username or target.password):
                    raise ValueError(f"{name}: HTTP {status} – nicht freigegebene oder wiederholte Weiterleitung.")
                endpoint, params = str(target), None
            if status in (401, 403):
                raise ValueError(f"{name}: Zugriff abgewiesen (HTTP {status}). "
                                 "API-Kontakt, Netzfreigabe oder Zugriffsschutz des Anbieters prüfen.")
            if status == 429:
                raise ValueError(f"{name}: Anfragelimit erreicht (HTTP 429). Bitte später erneut versuchen.")
            if status >= 500:
                raise ValueError(f"{name}: Dienst meldet einen Serverfehler (HTTP {status}). Bitte später erneut versuchen.")
            if not 200 <= status < 300:
                raise ValueError(f"{name}: Suchanfrage abgewiesen (HTTP {status}).")
            content_type = response.headers.get("content-type", "").lower()
            if "json" not in content_type:
                if "html" in content_type or response.content.lstrip().startswith(b"<"):
                    raise ValueError(f"{name}: Statt API-Daten wurde eine HTML-Seite geliefert. "
                                     "Möglicher Zugriffsschutz oder vorgeschaltete Anmeldeseite.")
                raise ValueError(f"{name}: Antwort enthält keine JSON-API-Daten.")
            try:
                data = response.json()
            except (json.JSONDecodeError, UnicodeDecodeError):
                raise ValueError(f"{name}: Ungültige JSON-Antwort.") from None
            if not isinstance(data, dict):
                raise _invalid(source)
            if data.get("error") or data.get("errors"):
                error = data.get("error")
                code = error.get("code") if isinstance(error, dict) else ""
                if code in ("maxlag", "ratelimited", "readonly"):
                    raise ValueError(f"{name}: API derzeit ausgelastet ({code}). Bitte später erneut versuchen.")
                raise ValueError(f"{name}: Die API hat die Suchanfrage zurückgewiesen.")
            try:
                return parse(data, source)
            except (TypeError, AttributeError, IndexError):
                raise _invalid(source) from None
    except httpx.TimeoutException:
        raise ValueError(f"{name}: Zeitüberschreitung. Die Quelle antwortet nicht rechtzeitig; bitte erneut versuchen.") from None
    except httpx.ConnectError as exc:
        if "CERTIFICATE_VERIFY_FAILED" in str(exc):
            raise ValueError(f"{name}: TLS-Zertifikat konnte nicht geprüft werden. "
                             "Die IT sollte die Zertifikatskette prüfen; SSL_CERT_FILE wird unterstützt.") from None
        raise ValueError(f"{name}: Verbindung zu {urlsplit(endpoint).hostname} fehlgeschlagen. "
                         "Netzfreigabe, VPN und gegebenenfalls institutionellen Proxy prüfen.") from None
    except httpx.HTTPError:
        raise ValueError(f"{name}: Fehler beim Übertragen der API-Antwort. Bitte erneut versuchen.") from None
