"""Only this adapter holds the GPUStack credential and sends inference requests."""
import hashlib
import ipaddress
import json
import os
import ssl
from urllib.parse import urlsplit
import httpx
from . import store, limits

_session_key = ""

def config():
    return store.setting("connection", {"base_url":"https://gpustack.unibe.ch/v1", "embedding_model":"qwen3-embedding-0.6b",
        "rerank_model":"", "internet_enabled":False})

def normalize_url(value):
    value = value.strip().rstrip("/")
    parsed = urlsplit(value)
    if parsed.scheme not in ("https", "http") or not parsed.hostname or parsed.username or parsed.password or parsed.query or parsed.fragment:
        raise ValueError("Bitte eine vollständige HTTPS-Basis-URL ohne Zugangsdaten, Query oder Fragment eingeben.")
    loopback = parsed.hostname in ("localhost", "127.0.0.1", "::1")
    if parsed.scheme != "https" and not loopback:
        raise ValueError("Außerhalb von localhost ist HTTPS erforderlich. VPN ersetzt keine TLS-Prüfung.")
    return value

def _vault():
    import keyring
    backend = keyring.get_keyring()
    # Fail closed: never accept keyrings.alt plaintext/file backends.
    name = backend.__class__.__module__
    if not any(name.startswith(p) for p in (
        "keyring.backends.Windows", "keyring.backends.macOS",
        "keyring.backends.SecretService", "keyring.backends.kwallet")):
        raise ValueError("Kein freigegebener Betriebssystem-Schlüsselspeicher verfügbar. Bitte Sitzungsspeicher verwenden.")
    return backend

def _account(base_url=None):
    return hashlib.sha256((base_url or config()["base_url"]).encode()).hexdigest()

def credential():
    if os.environ.get("GPUSTACK_API_KEY"):
        return os.environ["GPUSTACK_API_KEY"]
    if _session_key:
        return _session_key
    try:
        return _vault().get_password("gpustack-arbeitsraum", _account()) or ""
    except Exception:
        return ""

def key_status():
    if os.environ.get("GPUSTACK_API_KEY"):
        return "Umgebungsvariable"
    if _session_key:
        return "Nur diese Serversitzung"
    return "Betriebssystem-Schlüsselspeicher" if credential() else "Nicht hinterlegt"

def set_key(key, persist=False):
    global _session_key
    if persist:
        _vault().set_password("gpustack-arbeitsraum", _account(), key)
        _session_key = ""
    else:
        _session_key = key

def forget_key():
    global _session_key
    _session_key = ""
    try:
        vault = _vault()
        if vault.get_password("gpustack-arbeitsraum", _account()):
            vault.delete_password("gpustack-arbeitsraum", _account())
    except Exception:
        pass

def client():
    base = config()["base_url"]
    if not base:
        raise ValueError("Bitte zuerst den GPUStack-Endpunkt unter Einstellungen verbinden.")
    context = ssl.create_default_context(cafile=os.environ.get("SSL_CERT_FILE") or None)
    key = credential()
    return httpx.AsyncClient(base_url=base + "/", headers={"Authorization":"Bearer " + key} if key else {},
        verify=context, timeout=httpx.Timeout(limits.current()["gpu_timeout"], connect=15), follow_redirects=False, trust_env=False)

def check(response):
    if response.is_success:
        return
    if response.status_code in (401,403):
        raise ValueError("GPUStack verweigert den Zugriff. API-Schlüssel und Modellberechtigung prüfen.")
    if response.status_code == 404:
        raise ValueError("GPUStack-Pfad nicht gefunden. Basis-URL einschließlich /v1 bzw. /v1-openai prüfen.")
    if response.status_code == 429:
        raise ValueError("GPUStack ist ausgelastet oder das Kontingent ist erreicht. Später erneut versuchen.")
    if response.status_code in (400, 422):
        # Classify only; never echo upstream errors containing prompts or keys.
        try:
            detail = json.dumps(response.json()).lower()
        except Exception:
            detail = ""
        if any(x in detail for x in ("context_length", "max_model_len", "context window", "context length", "maximum context")):
            raise ValueError("Das Kontextfenster des GPUStack-Deployments ist überschritten. Input und Ausgabetokens teilen diesen Platz. Neuen Chat starten, Ausgabebudget reduzieren oder Deployment-Kontext mit der IT prüfen.")
        if any(x in detail for x in ("max_tokens", "max_completion_tokens")):
            raise ValueError("GPUStack lehnt das Ausgabetoken-Budget ab. Das Deployment kann kleinere Grenzen als das Referenzmodell haben; Modellprofil und verbleibenden Input-Platz prüfen.")
    raise ValueError(f"GPUStack antwortet mit HTTP {response.status_code}. Parameter und Modell prüfen.")

async def request(path, payload=None):
    try:
        async with client() as c:
            response = await (c.get(path) if payload is None else c.post(path, json=payload))
            check(response)
            return response.json()
    except (httpx.HTTPError, json.JSONDecodeError):
        raise ValueError("GPUStack ist nicht erreichbar oder liefert keine gültige Antwort. VPN, URL und Zertifikat prüfen.") from None

class ReasoningSplitter:
    """Separate an explicit leading <think> block, even across SSE chunks.

    Ordinary answer text mentioning <think> later is left untouched.
    This exposes only content sent by the endpoint, never inferred reasoning.
    """
    def __init__(self):
        self.mode = "start"
        self.pending = ""

    def feed(self, text, final=False):
        self.pending += text
        out = []
        if self.mode == "start":
            stripped = self.pending.lstrip()
            if stripped.startswith("<think>"):
                self.pending = stripped[7:]
                self.mode = "reasoning"
            elif not final and len(self.pending) < 64 and "<think>".startswith(stripped):
                return out
            else:
                self.mode = "text"
        if self.mode == "reasoning":
            end = self.pending.find("</think>")
            if end >= 0:
                out.append({"reasoning":self.pending[:end]})
                self.pending = self.pending[end+8:]
                self.mode = "text"
            else:
                keep = 0 if final else min(7, len(self.pending))
                count = len(self.pending) - keep
                if count:
                    out.append({"reasoning":self.pending[:count]})
                    self.pending = self.pending[count:]
                return out
        if self.pending:
            out.append({"text":self.pending})
            self.pending = ""
        return out

async def stream(payload):
    terminal=False
    splitter=ReasoningSplitter()
    try:
        async with client() as c:
            async with c.stream("POST", "chat/completions", json={**payload, "stream":True}) as response:
                if not response.is_success:
                    await response.aread()
                check(response)
                async for line in response.aiter_lines():
                    if not line.startswith("data:"):
                        continue
                    raw = line[5:].strip()
                    if raw == "[DONE]":
                        terminal=True
                        break
                    try:
                        data = json.loads(raw)
                    except json.JSONDecodeError:
                        continue
                    if data.get("error"):
                        raise ValueError("Das Modell hat die Anfrage abgebrochen. Parameter und Kontextbudget prüfen.")
                    if isinstance(data.get("usage"), dict):
                        yield {"usage":data["usage"]}
                    choices = data.get("choices") or []
                    if choices:
                        choice = choices[0]
                        delta = choice.get("delta") or {}
                        content = delta.get("content")
                        reasoning = delta.get("reasoning_content", delta.get("reasoning"))
                        if isinstance(reasoning, str) and reasoning:
                            yield {"reasoning":reasoning}
                        if isinstance(content,str) and content:
                            for part in splitter.feed(content):
                                yield part
                        if choice.get("finish_reason"):
                            terminal=True
                            yield {"finish_reason":choice["finish_reason"]}
                for part in splitter.feed("", final=True):
                    yield part
                if not terminal:
                    raise ValueError("Die Antwort endete ohne Abschlussbestätigung. Der Text kann unvollständig sein.")
    except ValueError:
        for part in splitter.feed("", final=True):
            yield part
        raise
    except httpx.HTTPError:
        for part in splitter.feed("", final=True):
            yield part
        raise ValueError("Die Modellverbindung wurde unterbrochen. VPN und GPUStack prüfen.") from None
