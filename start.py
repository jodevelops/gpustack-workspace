"""Start the single-user workspace on localhost, without installing anything."""
from __future__ import annotations

import argparse
import importlib
import os
import sqlite3
import sys
import tempfile
import threading
import webbrowser
from pathlib import Path

from app import __version__

ROOT = Path(__file__).resolve().parent
APP_NAME = "GPUStack-Arbeitsraum"
REQUIRED_MODULES = {
    "fastapi": "fastapi", "uvicorn": "uvicorn", "httpx": "httpx",
    "python_multipart": "python-multipart", "pydantic": "pydantic",
    "pypdf": "pypdf", "docx": "python-docx", "openpyxl": "openpyxl",
    "PIL": "Pillow", "keyring": "keyring",
}


def port_number(value: str) -> int:
    try:
        port = int(value)
    except ValueError:
        raise argparse.ArgumentTypeError("Der Port muss eine ganze Zahl sein.") from None
    if not 1 <= port <= 65535:
        raise argparse.ArgumentTypeError("Der Port muss zwischen 1 und 65535 liegen.")
    return port


def data_directory(explicit: str | None = None) -> Path:
    """Keep existing installations; use a stable user directory for new ones."""
    selected = explicit if explicit is not None else os.environ.get("WORKROOM_DATA_DIR")
    if selected:
        return Path(os.path.expandvars(selected)).expanduser().resolve()
    legacy = ROOT / "data"
    if (legacy / "workspace.sqlite3").is_file():
        return legacy.resolve()
    if sys.platform == "win32":
        base = Path(os.environ.get("LOCALAPPDATA") or Path.home() / "AppData" / "Local")
    elif sys.platform == "darwin":
        base = Path.home() / "Library" / "Application Support"
    else:
        base = Path(os.environ.get("XDG_DATA_HOME") or Path.home() / ".local" / "share")
    return (base / APP_NAME).expanduser().resolve()


class DataDirectoryLock:
    """An OS-managed lock is released even after a crash; keep its inode."""

    def __init__(self, directory: Path):
        self.path = directory / ".workroom.lock"
        self.handle = None

    def __enter__(self):
        handle = self.path.open("a+b")
        try:
            if os.name == "nt":
                import msvcrt
                if self.path.stat().st_size == 0:
                    handle.write(b"\0")
                    handle.flush()
                handle.seek(0)
                msvcrt.locking(handle.fileno(), msvcrt.LK_NBLCK, 1)
            else:
                import fcntl
                fcntl.flock(handle.fileno(), fcntl.LOCK_EX | fcntl.LOCK_NB)
        except OSError:
            handle.close()
            raise RuntimeError(
                "Dieser Datenordner wird bereits von einem Arbeitsraum verwendet. "
                "Die laufende Instanz öffnen oder zuerst beenden."
            ) from None
        self.handle = handle
        return self

    def __exit__(self, *exc):
        if self.handle is not None:
            self.handle.close()
            self.handle = None


def check_installation(directory: Path) -> None:
    missing = []
    for module, package in REQUIRED_MODULES.items():
        try:
            importlib.import_module(module)
        except ImportError:
            missing.append(package)
    if missing:
        raise RuntimeError(
            "Python-Pakete fehlen oder sind unvollständig: " + ", ".join(missing)
            + "\nMit demselben Python installieren:\n"
            + f'"{sys.executable}" -m pip install -r "{ROOT / "requirements.txt"}"'
        )
    directory.mkdir(parents=True, exist_ok=True)
    with tempfile.TemporaryFile(dir=directory):
        pass
    with sqlite3.connect(":memory:") as connection:
        try:
            connection.execute("CREATE VIRTUAL TABLE probe USING fts5(content)")
        except sqlite3.OperationalError:
            raise RuntimeError("Diese Python-Installation benötigt SQLite mit FTS5-Unterstützung.") from None
    for relative in ("web/index.html", "web/app.js", "web/style.css"):
        if not (ROOT / relative).is_file():
            raise RuntimeError(f"Programmdatei fehlt: {relative}. Das vollständige Paket entpacken.")


def announce_when_ready(server, url: str, stopped: threading.Event, open_browser: bool) -> None:
    while not stopped.wait(0.05):
        if server.started:
            print(f"Arbeitsraum bereit: {url}", flush=True)
            if open_browser:
                try:
                    if not webbrowser.open(url):
                        print("Die Adresse bitte im Browser öffnen.", flush=True)
                except Exception:
                    print("Browser konnte nicht geöffnet werden. Die Adresse bitte manuell öffnen.", flush=True)
            return


def stop_when_controller_closes(server, stream) -> None:
    """The desktop parent owns this pipe; EOF also handles a crashed parent."""
    try:
        for line in stream:
            if line.strip() == "stop":
                break
    except (OSError, ValueError):
        pass
    finally:
        server.should_exit = True


def serve(directory: Path, port: int, open_browser: bool, desktop_control: bool = False) -> int:
    import uvicorn

    # Configure before importing app.store: never depend on the caller's cwd.
    os.environ["WORKROOM_DATA_DIR"] = str(directory)
    from app.main import app

    url = f"http://127.0.0.1:{port}"
    server = uvicorn.Server(uvicorn.Config(
        app, host="127.0.0.1", port=port, workers=1,
        access_log=False, log_level="info",
        timeout_graceful_shutdown=10 if desktop_control else None,
    ))
    stopped = threading.Event()
    monitor = threading.Thread(
        target=announce_when_ready, args=(server, url, stopped, open_browser), daemon=True,
    )
    print(f"Datenordner: {directory}", flush=True)
    print("Zum Beenden Strg+C drücken.", flush=True)
    monitor.start()
    if desktop_control:
        threading.Thread(target=stop_when_controller_closes, args=(server, sys.stdin), daemon=True).start()
    try:
        server.run()
    except SystemExit as exc:
        if exc.code:
            raise RuntimeError(
                f"Der lokale Server konnte nicht starten. Bei belegtem Port mit --port {port + 1 if port < 65535 else 8765} starten."
            ) from None
    except KeyboardInterrupt:
        pass
    finally:
        stopped.set()
        monitor.join(timeout=2)
    if not server.started:
        raise RuntimeError("Der lokale Server wurde nicht bereit. Die vorangehenden Fehlermeldungen prüfen.")
    return 0


def main(argv: list[str] | None = None) -> int:
    for stream in (sys.stdout, sys.stderr):
        if hasattr(stream, "reconfigure"):
            stream.reconfigure(encoding="utf-8", errors="replace")
    if sys.version_info < (3, 11):
        print("ERROR: Start fehlgeschlagen: Python 3.11 oder neuer wird benötigt.", file=sys.stderr)
        return 1
    parser = argparse.ArgumentParser(description="GPUStack Arbeitsraum lokal auf 127.0.0.1 starten.")
    parser.add_argument("--version", action="version", version=__version__)
    parser.add_argument("--port", type=port_number, default=8765, help="Lokaler Port (Standard: 8765).")
    parser.add_argument("--data-dir", metavar="ORDNER", help="Vorhandenen Datenordner verwenden; Vorrang vor WORKROOM_DATA_DIR.")
    parser.add_argument("--no-browser", action="store_true", help="Browser nicht automatisch öffnen.")
    parser.add_argument("--check", action="store_true", help="Installation und Datenordner prüfen, ohne Serverstart oder Modellanfrage.")
    parser.add_argument("--desktop-control", action="store_true", help=argparse.SUPPRESS)
    args = parser.parse_args(argv)
    try:
        directory = data_directory(args.data_dir)
        check_installation(directory)
        if args.check:
            print(f"Installation geprüft: Version {__version__}; Datenordner: {directory}", flush=True)
            return 0
        with DataDirectoryLock(directory):
            return serve(directory, args.port, not args.no_browser, args.desktop_control)
    except (OSError, RuntimeError, ImportError) as exc:
        print(f"ERROR: Start fehlgeschlagen: {exc}", file=sys.stderr, flush=True)
        return 1


if __name__ == "__main__":
    raise SystemExit(main())
