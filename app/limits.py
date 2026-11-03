"""Persistent local resource budgets; never claim these are model token limits."""
from . import store

# key: (default, minimum, maximum, user-facing label)
FIELDS = {
    "file_mb": (100, 1, 2048, "Originaldatei · MiB"),
    "text_chars": (20_000_000, 1000, 200_000_000, "Extrahierter Text · Zeichen"),
    "pdf_pages": (0, 0, 100_000, "PDF-Seiten · 0 = kein Seitenlimit"),
    "xlsx_rows": (0, 0, 10_000_000, "Excel-Zeilen je Blatt · 0 = kein Zeilenlimit"),
    "office_mb": (512, 16, 8192, "Entpackte Office-Datei · MiB"),
    "parser_seconds": (180, 10, 3600, "Einlesen · Sekunden"),
    "parser_memory_mb": (1536, 512, 16384, "Parser-RAM unter Linux · MiB"),
    "rag_hits": (12, 1, 100, "RAG-Auszüge je Anfrage"),
    "chunk_chars": (1800, 500, 8000, "Neue Textabschnitte · Zeichen"),
    "message_chars": (500_000, 1000, 4_000_000, "Chatnachricht · Zeichen"),
    "prompt_chars": (200_000, 1000, 4_000_000, "Prompt / Projektnotizen · Zeichen"),
    "context_max_chars": (2_000_000, 4000, 16_000_000, "Einstellbares Chat-Eingabebudget · Zeichen"),
    "output_max_tokens": (262144, 128, 1_048_576, "Einstellbare Ausgabetokens"),
    "image_pixels": (50_000_000, 1_000_000, 80_000_000, "Bildpixel je Datei"),
    "image_count": (8, 1, 32, "Neue Bilder je Anfrage"),
    "image_mb": (32, 1, 256, "Neue Bilddaten je Anfrage · MiB"),
    "payload_mb": (64, 8, 512, "Modellanfrage inklusive Bildverlauf · MiB"),
    "gpu_timeout": (600, 30, 3600, "GPUStack-Lesezeitlimit · Sekunden"),
    "web_results": (5, 1, 20, "Websuchtreffer je Anfrage"),
    "web_timeout": (30, 10, 120, "Websuche / je Webseite · Sekunden"),
    "web_page_mb": (2, 1, 16, "Webseite beim Einlesen · MiB"),
    "web_page_chars": (8000, 1000, 100000, "Webtext je Seite · Zeichen"),
    "web_read_pages": (3, 1, 10, "Optional gelesene Webseiten im Chat"),
    "runner_seconds": (300, 10, 3600, "Datenlabor · Sekunden"),
    "runner_memory_mb": (2048, 256, 16384, "Datenlabor-RAM · MiB"),
    "runner_tmp_mb": (512, 64, 4096, "Datenlabor-Temporärspeicher · MiB"),
    "runner_output_mb": (100, 1, 2048, "Datenlabor-Ausgaben gesamt · MiB"),
}

def current():
    saved = store.setting("limits", {})
    return {key: saved.get(key, spec[0]) for key, spec in FIELDS.items()}

def validate(values):
    unknown = set(values) - FIELDS.keys()
    if unknown:
        raise ValueError("Unbekannte Ressourcengrenze.")
    result = current()
    for key, value in values.items():
        _, minimum, maximum, label = FIELDS[key]
        if isinstance(value, bool) or not isinstance(value, int) or not minimum <= value <= maximum:
            raise ValueError(f"{label}: Ganzzahl zwischen {minimum:,} und {maximum:,} erforderlich.")
        result[key] = value
    return result

def catalog():
    return [{"key": key, "default": s[0], "min": s[1], "max": s[2], "label": s[3]} for key, s in FIELDS.items()]

def check_text(text, key="prompt_chars"):
    maximum = current()[key]
    if len(text) > maximum:
        raise ValueError(f"Text enthält {len(text):,} Zeichen; eingestellt sind {maximum:,}. Unter Einstellungen → Ressourcengrenzen anpassen oder eine Datei in der Projektablage verwenden.")

class DocumentLimit(ValueError):
    """A readable original can be archived even if its searchable text is too large."""
