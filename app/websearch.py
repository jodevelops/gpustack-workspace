"""Explicit web search and public-page reading. No inference credentials or private context."""
import asyncio
import copy
import hashlib
import html
import http.client
import ipaddress
import json
import os
import re
import socket
import ssl
import time
from collections import OrderedDict
from html.parser import HTMLParser
from urllib.parse import quote, urljoin, urlsplit, urlunsplit
from urllib.robotparser import RobotFileParser

import httpx
from pydantic import BaseModel, Field
from . import gpu, limits, store

_session_key = ""
SERVICE = "gpustack-arbeitsraum-websearch"
ACCOUNT = "brave-search"
BRAVE = "https://api.search.brave.com/res/v1/web/search"
AGENT = "GPUStack-ArbeitsraumWebBot/0.1.7"
_snapshots = OrderedDict()


class Configuration(BaseModel):
    provider: str = "searxng"
    searxng_url: str = Field(default="", max_length=500)
    api_key: str = Field(default="", max_length=4096)
    persist_key: bool = False
    forget_key: bool = False


class Options(BaseModel):
    query: str = Field(min_length=2, max_length=300)
    freshness: str = "all"
    language: str = "de"


class PageRequest(BaseModel):
    url: str = Field(min_length=8, max_length=2048)


class SourceRequest(BaseModel):
    snapshot_id: str = Field(min_length=1, max_length=64)
    index: int = Field(default=0, ge=0, le=19)
    project_id: str = Field(min_length=1, max_length=64)


def config():
    saved = store.setting("web_search", {})
    return {"provider": saved.get("provider", "searxng"), "searxng_url": saved.get("searxng_url", "")}


def credential():
    if os.environ.get("BRAVE_SEARCH_API_KEY"):
        return os.environ["BRAVE_SEARCH_API_KEY"]
    if _session_key:
        return _session_key
    try:
        return gpu._vault().get_password(SERVICE, ACCOUNT) or ""
    except Exception:
        return ""


def key_status():
    if os.environ.get("BRAVE_SEARCH_API_KEY"):
        return "Umgebungsvariable"
    if _session_key:
        return "Nur diese Serversitzung"
    return "Betriebssystem-Schlüsselspeicher" if credential() else "Nicht hinterlegt"


def public_config():
    cfg = config()
    ready = bool(cfg["searxng_url"]) if cfg["provider"] == "searxng" else bool(credential())
    return {**cfg, "key_status": key_status(), "ready": ready,
            "provider_name": "SearXNG" if cfg["provider"] == "searxng" else "Brave Search"}


def normalize_instance(value):
    value = value.strip().rstrip("/")
    if not value:
        return ""
    try:
        parsed = urlsplit(value)
        port = parsed.port
    except ValueError:
        raise ValueError("SearXNG-Adresse ist ungültig.") from None
    if (parsed.scheme not in ("http", "https") or not parsed.hostname or parsed.username
            or parsed.password or parsed.query or parsed.fragment or any(ord(c) < 33 for c in value)):
        raise ValueError("SearXNG: Basis-URL ohne Zugangsdaten, Suchparameter oder Fragment eingeben.")
    if parsed.scheme == "http" and parsed.hostname not in ("localhost", "127.0.0.1", "::1"):
        raise ValueError("SearXNG benötigt ausserhalb von localhost HTTPS.")
    if port is not None and not 1 <= port <= 65535:
        raise ValueError("Ungültiger SearXNG-Port.")
    return value.removesuffix("/search")


def save_config(body):
    global _session_key
    warning = ""
    if body.provider not in ("searxng", "brave"):
        raise ValueError("Websuche: SearXNG oder Brave Search auswählen.")
    cfg = {"provider": body.provider, "searxng_url": normalize_instance(body.searxng_url)}
    if body.api_key and any(ord(c) < 33 or ord(c) > 126 for c in body.api_key):
        raise ValueError("Websuchschlüssel enthält ungültige Zeichen.")
    if body.forget_key:
        if os.environ.get("BRAVE_SEARCH_API_KEY"):
            raise ValueError("BRAVE_SEARCH_API_KEY muss ausserhalb der App entfernt werden.")
        _session_key = ""
        try:
            vault = gpu._vault()
            if vault.get_password(SERVICE, ACCOUNT):
                vault.delete_password(SERVICE, ACCOUNT)
        except Exception:
            warning = "Sitzungsschlüssel entfernt. Betriebssystem-Schlüsselspeicher nicht erreichbar; ein dort vorhandener Suchschlüssel konnte nicht geprüft oder entfernt werden."
    if body.api_key:
        if os.environ.get("BRAVE_SEARCH_API_KEY"):
            raise ValueError("Der Websuchschlüssel ist durch BRAVE_SEARCH_API_KEY vorgegeben.")
        if body.persist_key:
            gpu._vault().set_password(SERVICE, ACCOUNT, body.api_key)
            _session_key = ""
        else:
            _session_key = body.api_key
    store.set_setting("web_search", cfg)
    return {**public_config(), "warning": warning}


def require_enabled():
    if not gpu.config().get("internet_enabled"):
        raise ValueError("Externe Recherche ist deaktiviert. Unter Einstellungen bewusst freigeben.")


def validate_options(options):
    options.query = options.query.strip()
    if len(options.query) < 2 or any(ord(c) < 32 for c in options.query):
        raise ValueError("Websuche: einen öffentlichen Suchtext ohne Steuerzeichen eingeben.")
    if options.freshness not in ("all", "day", "month", "year") or options.language not in ("all", "de", "en", "fr"):
        raise ValueError("Websuche: Sprache oder Zeitraum ist ungültig.")


def search_client():
    return httpx.AsyncClient(timeout=httpx.Timeout(limits.current()["web_timeout"], connect=10),
        trust_env=False, follow_redirects=False,
        verify=ssl.create_default_context(cafile=os.environ.get("SSL_CERT_FILE") or None),
        headers={"User-Agent": AGENT, "Accept": "application/json"})


def plain(value):
    return html.unescape(re.sub(r"<[^>]*>", "", value)) if isinstance(value, str) else ""


def normalize_public_url(value):
    if not isinstance(value, str) or not value or len(value) > 2048 or "\\" in value or any(ord(c) < 33 for c in value):
        raise ValueError("Webseite: eine vollständige öffentliche HTTPS-Adresse eingeben.")
    try:
        parsed = urlsplit(value)
        port = parsed.port
    except ValueError:
        raise ValueError("Webseite: ungültige Adresse.") from None
    if (parsed.scheme != "https" or not parsed.hostname or parsed.username or parsed.password
            or port not in (None, 443) or "%" in parsed.hostname):
        raise ValueError("Webseite: nur öffentliches HTTPS auf Port 443 ohne Zugangsdaten ist zugelassen.")
    host = parsed.hostname.lower().rstrip(".")
    if host == "localhost" or host.endswith((".localhost", ".local", ".internal", ".test", ".invalid")) or "." not in host and ":" not in host:
        raise ValueError("Lokale und interne Webseiten sind für den Webabruf gesperrt.")
    try:
        address = ipaddress.ip_address(host)
    except ValueError:
        address = None
    if address is not None and not is_public(address):
        raise ValueError("Lokale und interne Webseiten sind für den Webabruf gesperrt.")
    return urlunsplit(("https", parsed.netloc, parsed.path or "/", parsed.query, ""))


def is_public(address):
    # Block IPv4-mapped addresses and transition ranges as well as RFC1918/link-local.
    blocked = ("192.0.0.0/24", "64:ff9b::/96", "64:ff9b:1::/48", "2001::/23")
    if any(address.version == ipaddress.ip_network(net).version and address in ipaddress.ip_network(net) for net in blocked):
        return False
    return address.is_global and not address.is_multicast and not getattr(address, "ipv4_mapped", None) and not getattr(address, "sixtofour", None) and not getattr(address, "teredo", None)


def resolve_public(host):
    try:
        addresses = list(dict.fromkeys(x[4][0] for x in socket.getaddrinfo(host, 443, type=socket.SOCK_STREAM)))
    except OSError:
        raise ValueError("Webseite: DNS-Auflösung fehlgeschlagen.") from None
    if not addresses or any(not is_public(ipaddress.ip_address(address)) for address in addresses):
        raise ValueError("Webseite verweist auf eine lokale oder interne Netzwerkadresse; Abruf gesperrt.")
    return addresses


class PublicHTTPSConnection(http.client.HTTPSConnection):
    """Connect to a vetted numeric address; TLS SNI and certificate retain the hostname."""
    def __init__(self, host, *, timeout=10, context=None):
        super().__init__(host, port=443, timeout=timeout, context=context)
        self.deadline = float("inf")

    def connect(self):
        if self._tunnel_host:
            raise ValueError("Webabruf über einen Tunnel ist nicht zugelassen.")
        addresses = resolve_public(self.host)
        if time.monotonic() >= self.deadline:
            raise ValueError("Webseitenabruf: Zeitlimit erreicht.")
        last_error = None
        for address in addresses:
            if time.monotonic() >= self.deadline:
                raise ValueError("Webseitenabruf: Zeitlimit erreicht.")
            try:
                sock = socket.create_connection((address, 443), timeout=max(.1, min(self.timeout, self.deadline-time.monotonic())))
                try:
                    self.sock = self._context.wrap_socket(sock, server_hostname=self.host)
                except BaseException:
                    sock.close()
                    raise
                return
            except OSError as exc:
                last_error = exc
        raise last_error or ValueError("Webseite ist nicht erreichbar.")


def read_public(url, max_bytes, deadline):
    """One request, no redirect, cookies, auth, proxy or JavaScript. Byte/deadline bounded."""
    url = normalize_public_url(url)
    parsed = urlsplit(url)
    timeout = max(.1, min(10, deadline - time.monotonic()))
    if deadline <= time.monotonic():
        raise ValueError("Webseitenabruf: Zeitlimit erreicht.")
    connection = PublicHTTPSConnection(parsed.hostname.encode("idna").decode(), timeout=timeout,
        context=ssl.create_default_context(cafile=os.environ.get("SSL_CERT_FILE") or None))
    connection.deadline = deadline
    path = quote(parsed.path or "/", safe="/%:@!$&'()*+,;=-._~")
    if parsed.query:
        path += "?" + quote(parsed.query, safe="=&%:@!$'()*+,;/?-._~")
    try:
        connection.request("GET", path, headers={"User-Agent": AGENT, "Accept": "text/html,text/plain;q=0.9", "Accept-Encoding": "identity"})
        response = connection.getresponse()
        headers = {k.lower(): v for k, v in response.getheaders()}
        status = response.status
        if 300 <= status < 400:
            return status, headers, b""
        if headers.get("content-encoding", "identity").lower() not in ("identity", ""):
            raise ValueError("Webseite liefert komprimierte Daten trotz identity-Anfrage; Abruf abgebrochen.")
        length = headers.get("content-length", "")
        if length.isdigit() and int(length) > max_bytes:
            raise ValueError("Webseite übersteigt die eingestellte Abrufgrenze.")
        data = bytearray()
        while True:
            if time.monotonic() >= deadline:
                raise ValueError("Webseitenabruf: Zeitlimit erreicht.")
            block = response.read1(min(65536, max_bytes - len(data) + 1))
            if not block:
                break
            data.extend(block)
            if len(data) > max_bytes:
                raise ValueError("Webseite übersteigt die eingestellte Abrufgrenze.")
        return status, headers, bytes(data)
    finally:
        connection.close()


class TextExtractor(HTMLParser):
    SKIP = {"script", "style", "noscript", "svg", "template", "nav", "footer", "header", "form"}
    BLOCK = {"p", "div", "li", "br", "h1", "h2", "h3", "h4", "article", "main", "section", "tr"}
    def __init__(self):
        super().__init__(convert_charrefs=True)
        self.parts, self.title_parts, self.skip = [], [], []
        self.in_title = False
    def handle_starttag(self, tag, attrs):
        if tag in self.SKIP:
            self.skip.append(tag)
        if tag == "title":
            self.in_title = True
        if tag in self.BLOCK and not self.skip:
            self.parts.append("\n")
    def handle_endtag(self, tag):
        if tag in self.skip:
            self.skip = self.skip[:self.skip.index(tag)]
        if tag == "title":
            self.in_title = False
        if tag in self.BLOCK and not self.skip:
            self.parts.append("\n")
    def handle_data(self, data):
        if self.in_title:
            self.title_parts.append(data)
        elif not self.skip:
            self.parts.append(data)
    def text(self):
        return "\n".join(line for line in (re.sub(r"\s+", " ", line).strip() for line in "".join(self.parts).splitlines()) if line)


def decode_page(raw, headers):
    encoding = re.search(r"charset\s*=\s*[\"']?([\w-]+)", headers.get("content-type", ""), re.I)
    if not encoding:
        encoding = re.search(rb"charset\s*=\s*[\"']?([\w-]+)", raw[:4096], re.I)
    charset = encoding.group(1) if encoding else "utf-8"
    if isinstance(charset, bytes):
        charset = charset.decode("ascii", errors="replace")
    try:
        return raw.decode(charset, errors="replace")
    except LookupError:
        return raw.decode("utf-8", errors="replace")


def fetch_sync(url):
    cfg = limits.current()
    deadline = time.monotonic() + cfg["web_timeout"]
    requested = normalize_public_url(url)
    current = requested
    # A robots check for each destination prevents cross-host redirects bypassing it.
    checked = set()
    try:
        for _ in range(4):
            normalize_public_url(current)
            origin = urlsplit(current).netloc
            if origin not in checked:
                robots_url = "https://" + origin + "/robots.txt"
                status, headers, raw = read_public(robots_url, 256 * 1024, deadline)
                if status == 200:
                    if "html" in headers.get("content-type", "").lower() or raw.lstrip().startswith(b"<"):
                        raise ValueError("Webseite: robots.txt liefert eine Zugriffsschutzseite.")
                    robot = RobotFileParser(); robot.parse(decode_page(raw, headers).splitlines())
                    if not robot.can_fetch(AGENT, current):
                        raise ValueError("Webseite untersagt diesen Abruf in robots.txt.")
                elif status not in (404, 410):
                    raise ValueError("Webseite: robots.txt konnte nicht verlässlich geprüft werden (HTTP " + str(status) + ").")
                checked.add(origin)
            status, headers, raw = read_public(current, cfg["web_page_mb"] * 1024 * 1024, deadline)
            if 300 <= status < 400:
                if not headers.get("location"):
                    raise ValueError("Webseite liefert eine ungültige Weiterleitung.")
                current = normalize_public_url(urljoin(current, headers["location"]))
                # Check the new path even on the same host.
                checked.discard(urlsplit(current).netloc)
                continue
            if status in (401, 403):
                raise ValueError("Webseite verweigert Zugriff. Anmeldung oder Zugriffsschutz wird nicht umgangen.")
            if status == 429:
                raise ValueError("Webseite meldet ein Anfragelimit (HTTP 429).")
            if status != 200:
                raise ValueError("Webseite meldet HTTP " + str(status) + ".")
            kind = headers.get("content-type", "").split(";", 1)[0].lower().strip()
            if kind not in ("text/html", "application/xhtml+xml", "text/plain"):
                raise ValueError("Nur HTML-/Textseiten können eingelesen werden. PDFs oder andere Dateien separat herunterladen und lokal hochladen.")
            decoded = decode_page(raw, headers)
            title = urlsplit(current).hostname
            if kind != "text/plain":
                parser = TextExtractor(); parser.feed(decoded); decoded = parser.text()
                title = " ".join(parser.title_parts).strip() or title
            if not decoded.strip():
                raise ValueError("Webseite enthält keinen lesbaren Text; möglicherweise ist JavaScript oder eine Anmeldung erforderlich.")
            maximum = cfg["web_page_chars"]
            return {"title": title[:2000], "url": current, "requested_url": requested,
                "text": decoded[:maximum], "truncated": len(decoded) > maximum, "kind": "page",
                "retrieved_at": store.now(), "sha256": hashlib.sha256(raw).hexdigest(),
                "note": "Extrahierter Webtext; Navigation, Skripte und Formulare entfernt. Kein Originalarchiv."}
        raise ValueError("Webseite: zu viele Weiterleitungen.")
    except (socket.timeout, TimeoutError):
        raise ValueError("Webseite antwortet nicht rechtzeitig.") from None
    except ssl.SSLError:
        raise ValueError("Webseite: TLS-Zertifikat konnte nicht geprüft werden; SSL_CERT_FILE wird unterstützt.") from None
    except (OSError, http.client.HTTPException):
        raise ValueError("Webseite ist nicht erreichbar oder liefert eine ungültige HTTP-Antwort.") from None


def remember(data):
    now = time.monotonic()
    for ident in list(_snapshots):
        if now - _snapshots[ident][0] > 1800:
            del _snapshots[ident]
    ident = store.uid()
    _snapshots[ident] = (now, copy.deepcopy(data))
    while len(_snapshots) > 20:
        _snapshots.popitem(last=False)
    return {**data, "snapshot_id": ident}


def snapshot(ident, index):
    found = _snapshots.get(ident)
    if not found or time.monotonic() - found[0] > 1800:
        raise ValueError("Recherchestand ist abgelaufen oder der Dienst wurde neu gestartet. Erneut suchen bzw. Seite einlesen.")
    rows = found[1]["results"]
    if index >= len(rows):
        raise ValueError("Recherchetreffer nicht gefunden.")
    return copy.deepcopy(rows[index]), copy.deepcopy(found[1])


async def fetch_page(url):
    require_enabled()
    try:
        return await asyncio.wait_for(asyncio.to_thread(fetch_sync, url), timeout=limits.current()["web_timeout"]+1)
    except asyncio.TimeoutError:
        raise ValueError("Webseitenabruf: Zeitlimit erreicht.") from None


async def page_result(url):
    page = await fetch_page(url)
    return remember({"source": "web", "provider": "Direkter Webseitenabruf", "sent_query": "",
        "retrieved_at": page["retrieved_at"], "results": [page], "notes": []})


async def search(options):
    require_enabled(); validate_options(options)
    cfg = config(); count = limits.current()["web_results"]
    name = "SearXNG" if cfg["provider"] == "searxng" else "Brave Search"
    if cfg["provider"] == "searxng":
        if not cfg["searxng_url"]:
            raise ValueError("Websuche noch nicht eingerichtet. Unter Einstellungen → Websuche eine SearXNG-Adresse oder Brave Search mit Schlüssel hinterlegen.")
        endpoint = cfg["searxng_url"] + "/search"
        params = {"q": options.query, "format": "json", "categories": "general", "safesearch": 1}
        if options.language != "all":
            params["language"] = options.language
        if options.freshness != "all":
            params["time_range"] = options.freshness
        headers = {}
    else:
        if len(options.query.split()) > 75:
            raise ValueError("Brave Search erlaubt höchstens 75 Wörter pro Suchtext; bitte Suchbegriffe kürzen.")
        key = credential()
        if not key:
            raise ValueError("Brave Search: separaten Websuchschlüssel unter Einstellungen → Websuche hinterlegen.")
        endpoint = BRAVE
        params = {"q": options.query, "count": count, "safesearch": "moderate", "extra_snippets": "true"}
        if options.language != "all":
            params["search_lang"] = options.language
        if options.freshness != "all":
            params["freshness"] = {"day": "pd", "month": "pm", "year": "py"}[options.freshness]
        headers = {"X-Subscription-Token": key}
    try:
        async with search_client() as client:
            async with client.stream("GET", endpoint, params=params, headers=headers) as response:
                status = response.status_code
                if status in (401, 403):
                    raise ValueError(name + ": Zugriff abgewiesen (HTTP " + str(status) + "). " + ("JSON-Format in SearXNG aktivieren und Netzfreigabe prüfen." if cfg["provider"] == "searxng" else "Suchschlüssel und API-Berechtigung prüfen."))
                if status == 429:
                    raise ValueError(name + ": Kontingent oder Anfragelimit erreicht (HTTP 429).")
                if status != 200:
                    raise ValueError(name + ": Suchdienst meldet HTTP " + str(status) + "; keine automatische Weiterleitung oder Ersatzsuche.")
                if "json" not in response.headers.get("content-type", "").lower():
                    raise ValueError(name + ": Keine JSON-Suchdaten erhalten; Konfiguration oder Zugriffsschutz prüfen.")
                raw = bytearray()
                async for block in response.aiter_bytes():
                    raw.extend(block)
                    if len(raw) > 2 * 1024 * 1024:
                        raise ValueError(name + ": Suchantwort übersteigt 2 MiB.")
        try:
            data = json.loads(raw)
            items = data.get("results") if cfg["provider"] == "searxng" else data.get("web", {}).get("results", [])
            if not isinstance(items, list) or any(not isinstance(item, dict) for item in items):
                raise ValueError
        except (ValueError, AttributeError, TypeError):
            raise ValueError(name + ": Ungültiges Suchformat.") from None
        results = []; seen = set()
        for item in items:
            try:
                url = normalize_public_url(item.get("url", ""))
            except ValueError:
                continue
            if url in seen:
                continue
            seen.add(url)
            text = plain(item.get("content") if cfg["provider"] == "searxng" else item.get("description"))
            extras = item.get("extra_snippets", [])
            if isinstance(extras, list):
                text += "\n" + "\n".join(plain(x) for x in extras[:3])
            results.append({"title": plain(item.get("title"))[:2000] or urlsplit(url).hostname,
                "url": url, "text": text.strip()[:3000], "truncated": len(text.strip()) > 3000,
                "kind": "snippet", "published": plain(item.get("age") or item.get("publishedDate"))[:100]})
            if len(results) >= count:
                break
        retrieved = store.now()
        for result in results:
            result["retrieved_at"] = retrieved
        notes = []
        if cfg["provider"] == "searxng" and data.get("unresponsive_engines"):
            notes.append("SearXNG meldet ausgefallene Suchmaschinen; diese Suche kann unvollständig sein.")
        return remember({"results": results, "source": "web", "provider": name, "sent_query": options.query,
            "language": options.language, "freshness": options.freshness, "retrieved_at": retrieved, "notes": notes})
    except httpx.TimeoutException:
        raise ValueError(name + ": Suchanfrage hat das Zeitlimit erreicht.") from None
    except httpx.HTTPError:
        raise ValueError(name + ": Suchdienst nicht erreichbar; Netzfreigabe und Zertifikatskette prüfen.") from None


async def chat_context(options, read_pages=False):
    result = await search(options)
    if not result["results"]:
        raise ValueError("Websuche hat keine verwertbaren HTTPS-Treffer geliefert. Suchtext ändern oder bewusst ohne Websuche senden; keine Modellanfrage gestartet.")
    if read_pages:
        for row in result["results"][:limits.current()["web_read_pages"]]:
            try:
                page = await fetch_page(row["url"])
                row.update(page)
            except ValueError as exc:
                result["notes"].append(row["url"] + ": " + str(exc) + " Nur Suchauszug verwendet.")
    hits = [{"label": "", "name": r["title"], "location": r["url"] + " · " + ("Webtext" if r["kind"] == "page" else "Suchauszug") + " · Abruf " + r["retrieved_at"],
        "content": r["text"], "url": r["url"], "kind": r["kind"], "retrieved_at": r["retrieved_at"],
        "truncated": r["truncated"], "source_type": "web"} for r in result["results"]]
    return hits, {k: result[k] for k in ("provider", "sent_query", "retrieved_at", "language", "freshness", "notes")}


def source_markdown(row, result):
    return "# " + row["title"] + "\n\nQuelle: " + row["url"] + "\nAbruf: " + row["retrieved_at"] + "\nAnbieter: " + result["provider"] + "\nSuchtext: " + result.get("sent_query", "") + "\nArt: " + ("Extrahierter Webtext" if row["kind"] == "page" else "Suchauszug, kein gelesener Volltext") + ("\nHinweis: Text gekürzt." if row["truncated"] else "") + "\n\n" + row["text"] + "\n\nWebinhalte sind externe, ungeprüfte Quellen. Inhalt und Modellantwort fachlich prüfen.\n"
