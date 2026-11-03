import hashlib
import io
import json
import mimetypes
import os
import re
import shutil
import subprocess
import sys
import tempfile
import zipfile
from pathlib import Path
from . import store, limits

ALLOWED = {".txt",".md",".csv",".tsv",".json",".pdf",".docx",".xlsx",".png",".jpg",".jpeg",".webp",".mp3",".wav",".m4a",".mp4",".ogg",".webm"}
IMAGES = {".png",".jpg",".jpeg",".webp"}
AUDIO = {".mp3",".wav",".m4a",".mp4",".ogg",".webm"}

def max_file():
    return limits.current()["file_mb"] * 1024 * 1024

def safe_name(name):
    name = Path(name.replace("\\","/")).name
    name = re.sub(r'[\x00-\x1f<>:"/\\|?*]', "_", name).strip(". ")
    return name[:160] or "datei"

def path_for(document):
    return store.DATA / "files" / (document["id"] + Path(document["name"]).suffix.lower())

def _extract(path, suffix, cfg=None):
    cfg = cfg or limits.current()
    parts, total = [], 0
    def add(location, text):
        nonlocal total
        total += len(text)
        if total > cfg["text_chars"]:
            raise limits.DocumentLimit(f"Extrahierter Text übersteigt die eingestellten {cfg['text_chars']:,} Zeichen.")
        parts.append((location, text))
    if suffix in {".docx", ".xlsx"}:
        with zipfile.ZipFile(path) as z:
            info = z.infolist()
            if len(info) > 50_000 or sum(x.file_size for x in info) > cfg["office_mb"] * 1024 * 1024:
                raise limits.DocumentLimit(f"Entpackte Office-Datei übersteigt {cfg['office_mb']} MiB oder 50.000 ZIP-Einträge.")
    if suffix == ".pdf":
        from pypdf import PdfReader
        reader = PdfReader(path)
        if reader.is_encrypted:
            raise ValueError("Verschlüsselte PDFs bitte vor dem Einlesen entschlüsseln oder nur das Original ablegen.")
        if cfg["pdf_pages"] and len(reader.pages) > cfg["pdf_pages"]:
            raise limits.DocumentLimit(f"PDF übersteigt die eingestellten {cfg['pdf_pages']:,} Seiten.")
        empty = 0
        for i, page in enumerate(reader.pages):
            text = page.extract_text() or ""
            empty += not text.strip()
            add(f"Seite {i+1}", text)
        return parts, f"{empty} Seite(n) ohne lesbare Textebene. Keine automatische OCR." if empty else ""
    if suffix == ".docx":
        from docx import Document
        d = Document(path)
        add("Absätze", "\n".join(p.text for p in d.paragraphs))
        for i, table in enumerate(d.tables):
            add(f"Tabelle {i+1}", "\n".join("\t".join(c.text for c in row.cells) for row in table.rows))
        return parts, "Text und Tabellen; Fußnoten, Textfelder und Layout werden nicht vollständig erfasst."
    if suffix == ".xlsx":
        from openpyxl import load_workbook
        book = load_workbook(path, read_only=True, data_only=True, keep_links=False)
        try:
            for sheet in book:
                # Ignore inflated dimensions left by formatting/export tools.
                sheet.reset_dimensions()
                text = io.StringIO()
                for i, row in enumerate(sheet.iter_rows(values_only=True), 1):
                    if cfg["xlsx_rows"] and i > cfg["xlsx_rows"]:
                        raise limits.DocumentLimit(f"Blatt {sheet.title} übersteigt die eingestellten {cfg['xlsx_rows']:,} Zeilen.")
                    values = list(row)
                    while values and values[-1] is None:
                        values.pop()
                    if not values:
                        continue
                    line = str(i) + ": " + "\t".join("" if v is None else str(v) for v in values) + "\n"
                    if total + text.tell() + len(line) > cfg["text_chars"]:
                        raise limits.DocumentLimit(f"Extrahierter Text übersteigt die eingestellten {cfg['text_chars']:,} Zeichen.")
                    text.write(line)
                add("Blatt " + sheet.title, text.getvalue())
        finally:
            book.close()
        return parts, "Gespeicherte Zellwerte; Formeln werden nicht neu berechnet. Für vollständige Statistik das Datenlabor nutzen."
    raw = path.read_bytes()
    if raw.startswith((b'\xff\xfe\x00\x00', b'\x00\x00\xfe\xff')):
        content, note = raw.decode("utf-32"), "Als UTF-32 eingelesen."
    elif raw.startswith((b'\xff\xfe', b'\xfe\xff')):
        content, note = raw.decode("utf-16"), "Als UTF-16 eingelesen."
    else:
        try:
            content, note = raw.decode("utf-8-sig"), ""
        except UnicodeDecodeError:
            content, note = raw.decode("cp1252"), "Als Windows-1252 eingelesen. Zeichencodierung bei Bedarf prüfen."
    if "\x00" in content:
        raise ValueError("Keine unterstützte Textdatei.")
    add("Text", content)
    return parts, note

def extract_guarded(path, suffix):
    cfg = limits.current()
    # Large Unicode results go to a temporary UTF-8 file, not a Windows stdout pipe.
    with tempfile.TemporaryDirectory(prefix="parser-", dir=store.DATA) as temp:
        output = Path(temp) / "result.json"
        env = {**os.environ, "WORKROOM_PARSER_LIMITS": json.dumps(cfg)}
        try:
            result = subprocess.run([sys.executable, "-m", "app.extract", str(path), suffix, str(output)],
                cwd=store.ROOT, env=env, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL,
                timeout=cfg["parser_seconds"], check=False)
        except subprocess.TimeoutExpired:
            raise limits.DocumentLimit(f"Einlesen überschreitet {cfg['parser_seconds']} Sekunden.") from None
        if result.returncode != 0 or not output.exists():
            raise limits.DocumentLimit("Parser wurde beendet; möglicherweise RAM-/CPU-Grenze erreicht.")
        data = json.loads(output.read_text(encoding="utf-8"))
    if data.get("error"):
        error = limits.DocumentLimit if data.get("limited") else ValueError
        raise error(data["error"])
    return data["parts"], data["note"]

def process(path, suffix, mime, mode="text"):
    if mode not in ("text", "original"):
        raise ValueError("Unbekannter Importmodus.")
    if mode == "original":
        return [], "Original ohne Textindex abgelegt. Für Suche später erneut einlesen; für vollständige Tabellenanalyse im Datenlabor auswählen.", "ablage", mime
    if suffix in IMAGES:
        from PIL import Image
        with Image.open(path) as img:
            if img.width * img.height > limits.current()["image_pixels"]:
                raise limits.DocumentLimit(f"Bild übersteigt {limits.current()['image_pixels']:,} Pixel.")
            fmt = img.format
            if fmt not in ("PNG", "JPEG", "WEBP"):
                raise ValueError("Dateiendung und Bildformat prüfen.")
            img.verify()
            mime = Image.MIME[fmt]
        return [], "Wird nur nach Auswahl an ein Bildmodell übergeben.", "bild", mime
    if suffix in AUDIO:
        return [], "Transkription explizit unter Audio & Transkripte starten.", "audio", "audio/webm" if suffix==".webm" else mime
    parts, note = extract_guarded(path, suffix)
    status = "bereit" if any(text.strip() for _, text in parts) else "ohne_text"
    if status == "ohne_text":
        note = note or "Kein extrahierbarer Text. Scan/Bild separat an ein Bildmodell übergeben."
    return parts, note, status, mime

def process_or_archive(path, suffix, mime, mode):
    try:
        return process(path, suffix, mime, mode)
    except limits.DocumentLimit as exc:
        return [], str(exc) + " Original vollständig gespeichert, kein Teilindex. Unter Einstellungen → Ressourcengrenzen anpassen und erneut einlesen; alternativ vollständige Datei im Datenlabor verarbeiten.", "ablage", mime

def write_chunks(connection, ident, parts):
    width = limits.current()["chunk_chars"]
    step = max(1, width * 87 // 100)
    batch, ordinal = [], 0
    for location, text in parts:
        text = text.replace("\x00", "").strip()
        for start in range(0, len(text), step):
            chunk = text[start:start+width]
            if not chunk.strip():
                continue
            batch.append((store.uid(), ident, ordinal, f"{location} · Abschnitt {ordinal+1}", chunk))
            ordinal += 1
            if len(batch) >= 256:
                connection.executemany("INSERT INTO chunks(id,document_id,ordinal,location,content) VALUES(?,?,?,?,?)", batch)
                batch.clear()
    if batch:
        connection.executemany("INSERT INTO chunks(id,document_id,ordinal,location,content) VALUES(?,?,?,?,?)", batch)

def ingest_file(name, source, project_id=None, mode="text"):
    name = safe_name(name)
    suffix = Path(name).suffix.lower()
    if suffix not in ALLOWED:
        raise ValueError("Unterstützt: PDF, DOCX, XLSX, CSV, TSV, TXT, MD, JSON, PNG, JPEG, WebP und Audio.")
    size = source.stat().st_size
    if not size or size > max_file():
        raise ValueError(f"Datei ist leer oder größer als die eingestellten {limits.current()['file_mb']} MiB. Ressourcengrenzen in den Einstellungen anpassen.")
    if project_id and not store.one("SELECT id FROM projects WHERE id=?", (project_id,)):
        raise ValueError("Projekt nicht gefunden.")
    ident = store.uid()
    path = store.DATA / "files" / (ident + suffix)
    try:
        shutil.copyfile(source, path)
        size = path.stat().st_size
        if not size or size > max_file():
            raise ValueError("Originalgröße hat sich während des Imports geändert oder übersteigt die Uploadgrenze.")
        with path.open("rb") as f:
            digest = hashlib.file_digest(f, "sha256").hexdigest()
        mime = mimetypes.guess_type(name)[0] or "application/octet-stream"
        parts, note, status, mime = process_or_archive(path, suffix, mime, mode)
        with store.db() as c:
            c.execute("INSERT INTO documents VALUES(?,?,?,?,?,?,?,?,?)",
                (ident, project_id, name, mime, size, digest, status, note, store.now()))
            write_chunks(c, ident, parts)
        return store.one("SELECT * FROM documents WHERE id=?", (ident,))
    except BaseException:
        path.unlink(missing_ok=True)
        raise

def ingest(name, raw, project_id=None, mode="text"):
    # Internal generated texts and compatibility with existing callers.
    with tempfile.TemporaryDirectory(prefix="import-", dir=store.DATA) as temp:
        source = Path(temp) / "original"
        source.write_bytes(raw)
        return ingest_file(name, source, project_id, mode)

def reprocess(doc):
    path = path_for(doc)
    parts, note, status, mime = process(path, Path(doc["name"]).suffix.lower(), doc["mime"])
    # Old index survives failed extraction. A successful replacement is atomic.
    with store.db() as c:
        c.execute("DELETE FROM chunks WHERE document_id=?", (doc["id"],))
        write_chunks(c, doc["id"], parts)
        c.execute("UPDATE documents SET status=?,note=?,mime=? WHERE id=?", (status, note, mime, doc["id"]))
    return store.one("SELECT * FROM documents WHERE id=?", (doc["id"],))

def delete(ident):
    doc = store.one("SELECT * FROM documents WHERE id=?", (ident,))
    if doc:
        store.run("DELETE FROM documents WHERE id=?", (ident,))
        path_for(doc).unlink(missing_ok=True)

def selected(ids, project_id):
    output = []
    for ident in dict.fromkeys(ids):
        doc = store.one("SELECT * FROM documents WHERE id=? AND (project_id=? OR project_id IS NULL)", (ident, project_id))
        if not doc:
            raise ValueError("Eine ausgewählte Quelle gehört nicht zu diesem Projekt oder wurde gelöscht.")
        output.append(doc)
    return output
