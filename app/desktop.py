"""Desktop process control; standard library only, including before setup."""
from __future__ import annotations

import json
import os
import queue
import subprocess
import sys
import threading
import time
import webbrowser
from collections import deque
from contextlib import suppress
from pathlib import Path
from urllib.request import ProxyHandler, build_opener

from app import __version__
from start import ROOT, data_directory

PHASE_TIMEOUTS = {"check": 90, "install": 600, "server": 90}
PHASE_LABELS = {"check": "Paketprüfung", "install": "Paketeinrichtung", "server": "Serverstart"}


class StartupTimeout(RuntimeError):
    """A startup phase exceeded its deadline; never interpreted as missing packages."""


def console_python(executable=None):
    path = Path(executable or sys.executable)
    if path.name.lower() == "pythonw.exe":
        candidate = path.with_name("python.exe")
        if candidate.is_file():
            return str(candidate)
        raise RuntimeError("Neben pythonw.exe wurde kein python.exe gefunden. "
                           "Bitte die Python-Dateizuordnung bzw. Installation prüfen.")
    return str(path)


def background_options():
    return {"creationflags": subprocess.CREATE_NO_WINDOW} if os.name == "nt" else {}


def installer_command(python, root, in_venv=None):
    if in_venv is None:
        in_venv = sys.prefix != sys.base_prefix
    args = [str(python), "-m", "pip", "--disable-pip-version-check", "--no-input",
            "install", "--only-binary=:all:", "--progress-bar", "off"]
    if not in_venv:
        args.append("--user")
    return args + ["-r", str(Path(root) / "requirements.txt")]


def existing_workspace(url, directory):
    """Only reuse an actual workspace serving the same local data directory."""
    try:
        with build_opener(ProxyHandler({})).open(url + "/api/bootstrap", timeout=1) as response:
            data = json.loads(response.read(8 * 1024 * 1024))
        return (isinstance(data, dict) and {"csrf", "models", "projects", "version", "data_dir"} <= data.keys()
                and Path(data["data_dir"]).resolve() == Path(directory).resolve())
    except (OSError, ValueError, TypeError):
        return False


def app_browser(environ=None):
    env = os.environ if environ is None else environ
    roots = [env.get(key) for key in ("ProgramFiles(x86)", "ProgramFiles", "LOCALAPPDATA")]
    for relative in ("Microsoft/Edge/Application/msedge.exe", "Google/Chrome/Application/chrome.exe"):
        for root in filter(None, roots):
            candidate = Path(root) / relative
            if candidate.is_file():
                return candidate
    return None


def open_workspace(url):
    executable = app_browser() if os.name == "nt" else None
    if executable:
        try:
            subprocess.Popen([str(executable), "--app=" + url], stdin=subprocess.DEVNULL,
                             stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL, **background_options())
            return True
        except OSError:
            pass
    return webbrowser.open(url)


def powershell_literal(value):
    return "'" + str(value).replace("'", "''") + "'"


def shortcut_script(python, root, directory, port):
    target = Path(python)
    windowed = target.with_name("pythonw.exe")
    if windowed.is_file():
        target = windowed
    arguments = subprocess.list2cmdline([str(Path(root) / "desktop.pyw"),
                                        "--data-dir", str(directory), "--port", str(port)])
    return "\n".join([
        "$ErrorActionPreference = 'Stop'",
        "$desktop = [Environment]::GetFolderPath('Desktop')",
        "if ([string]::IsNullOrWhiteSpace($desktop)) { throw 'Desktop nicht gefunden.' }",
        "$shell = New-Object -ComObject WScript.Shell",
        "$link = $shell.CreateShortcut([IO.Path]::Combine($desktop, 'GPUStack Arbeitsraum.lnk'))",
        "$link.TargetPath = " + powershell_literal(target),
        "$link.Arguments = " + powershell_literal(arguments),
        "$link.WorkingDirectory = " + powershell_literal(root),
        "$link.Description = 'GPUStack Arbeitsraum lokal starten'",
        "$link.IconLocation = " + powershell_literal(Path(root) / "web" / "arbeitsraum.ico"),
        "$link.WindowStyle = 7",
        "$link.Save()",
    ])


def create_shortcut(python, root, directory, port):
    if os.name != "nt":
        raise RuntimeError("Die Desktop-Verknüpfung ist für Windows vorgesehen.")
    result = subprocess.run(["powershell.exe", "-NoProfile", "-NonInteractive", "-Command",
                             shortcut_script(python, root, directory, port)],
                            stdin=subprocess.DEVNULL, capture_output=True, timeout=20, **background_options())
    if result.returncode:
        raise RuntimeError("Die Desktop-Verknüpfung konnte nicht angelegt werden. start.cmd bleibt verwendbar.")


class DesktopService:
    def __init__(self, port=8765, directory=None, python=None, root=ROOT, phase_timeouts=None):
        self.port, self.root = port, Path(root)
        self.directory = data_directory(str(directory) if directory is not None else None)
        self.python = console_python(python)
        self.url = f"http://127.0.0.1:{port}"
        self.events = queue.Queue()
        self.cancelled = threading.Event()
        self.lock = threading.Lock()
        self.log_lock = threading.Lock()
        self.log_path = self.directory / "startprotokoll.log"
        self.log_file = None
        self.phase_timeouts = {**PHASE_TIMEOUTS, **(phase_timeouts or {})}
        self.process = None
        self.phase = ""
        self.running = False

    def emit(self, kind, value=""):
        self.events.put((kind, value))
        if kind == "log":
            with self.log_lock:
                if self.log_file:
                    try:
                        self.log_file.write(value)
                        self.log_file.flush()
                    except OSError:
                        with suppress(OSError):
                            self.log_file.close()
                        self.log_file = None
                        self.events.put(("log", "Die lokale Protokolldatei konnte nicht weitergeschrieben werden.\n"))

    @staticmethod
    def discard_process(process):
        """Dispose of a child which was created after its attempt was cancelled."""
        try:
            process.kill()
            process.wait(timeout=3)
        except (OSError, subprocess.TimeoutExpired):
            pass
        for stream in (process.stdin, process.stdout):
            if stream:
                try:
                    stream.close()
                except OSError:
                    pass

    def spawn(self, command, phase, env, deadline):
        # Windows process creation can itself block. Keep it out of the UI lock
        # and reap a late child instead of letting an abandoned attempt start it.
        completed = threading.Event()
        abandoned = threading.Event()
        result = {}

        def launch():
            try:
                process = subprocess.Popen(command, cwd=self.root, env=env,
                                           stdin=subprocess.PIPE if phase == "server" else subprocess.DEVNULL,
                                           stdout=subprocess.PIPE, stderr=subprocess.STDOUT,
                                           text=True, encoding="utf-8", errors="replace", bufsize=1,
                                           **background_options())
                with self.lock:
                    discard = abandoned.is_set() or self.cancelled.is_set()
                    if not discard:
                        self.process, self.phase = process, phase
                        result["process"] = process
                if discard:
                    self.discard_process(process)
            except Exception as exc:
                result["error"] = exc
            finally:
                completed.set()

        threading.Thread(target=launch, daemon=True).start()
        while not completed.wait(0.1):
            if self.cancelled.is_set() or time.monotonic() >= deadline:
                with self.lock:
                    abandoned.set()
                    process = result.get("process")
                    if self.process is process:
                        self.process = None
                if process:
                    self.discard_process(process)
                if self.cancelled.is_set():
                    return None
                raise StartupTimeout(f"{PHASE_LABELS[phase]}: Python reagiert beim Prozessstart nicht "
                                     f"innerhalb von {self.phase_timeouts[phase]:g} Sekunden. "
                                     "Python-Dateizuordnung und mögliche IT-Sperrmeldungen prüfen.")
        if "error" in result:
            raise result["error"]
        return result.get("process")

    def execute(self, command, phase):
        if self.cancelled.is_set():
            return -1, ""
        label = PHASE_LABELS[phase]
        started = time.monotonic()
        deadline = started + self.phase_timeouts[phase]
        self.emit("log", f"\n{label} beginnt (Zeitlimit {self.phase_timeouts[phase]:g} Sekunden).\n")
        env = {**os.environ, "PYTHONIOENCODING": "utf-8", "PYTHONUNBUFFERED": "1"}
        if phase == "install":
            env = {key: value for key, value in env.items() if not key.startswith("GPUSTACK_")}
        process = self.spawn(command, phase, env, deadline)
        if process is None:
            return -1, ""
        lines = queue.Queue()
        eof = object()

        def read_output():
            try:
                for line in process.stdout:
                    lines.put(line)
            except (OSError, ValueError) as exc:
                lines.put(f"Ausgabe konnte nicht vollständig gelesen werden: {exc}\n")
            finally:
                process.stdout.close()
                lines.put(eof)

        reader = threading.Thread(target=read_output, daemon=True)
        reader.start()
        tail = deque(maxlen=200)
        output_closed = False
        next_notice = started + 5
        stop_deadline = None
        try:
            while True:
                try:
                    line = lines.get(timeout=0.1)
                    if line is eof:
                        output_closed = True
                    else:
                        tail.append(line)
                        self.emit("log", line)
                        if phase == "server" and "Arbeitsraum bereit:" in line and not self.cancelled.is_set():
                            self.running = True
                            self.emit("ready", self.url)
                except queue.Empty:
                    pass
                now = time.monotonic()
                if output_closed and process.poll() is not None:
                    break
                if self.cancelled.is_set():
                    if stop_deadline is None:
                        stop_deadline = now + 10
                    if process.poll() is None and (phase != "server" or not self.running or now >= stop_deadline):
                        process.kill()
                    if now >= stop_deadline:
                        break
                waiting = not (phase == "server" and self.running)
                if waiting and not self.cancelled.is_set() and now >= deadline:
                    raise StartupTimeout(f"{label} wurde nach {self.phase_timeouts[phase]:g} Sekunden abgebrochen. "
                                         "Der letzte Protokolleintrag zeigt den ausstehenden Schritt.")
                if waiting and not self.cancelled.is_set() and now >= next_notice:
                    elapsed = int(now - started)
                    self.emit("status", f"{label} läuft seit {elapsed} Sekunden …")
                    self.emit("log", f"{label}: warte auf Abschluss, {elapsed} Sekunden vergangen.\n")
                    next_notice = now + 5
            code = process.wait()
            self.emit("log", f"{label} beendet (Exitcode {code}).\n")
            return code, "".join(tail)
        finally:
            if process.poll() is None:
                process.kill()
            try:
                process.wait(timeout=3)
            except subprocess.TimeoutExpired:
                pass
            reader.join(timeout=1)
            if process.stdin:
                try:
                    process.stdin.close()
                except OSError:
                    pass
            with self.lock:
                if self.process is process:
                    self.process = None

    def run(self, install=False):
        try:
            if self.cancelled.is_set():
                return
            header = (f"GPUStack Arbeitsraum {__version__} · lokaler Start\n"
                      f"Python: {self.python}\nProgrammordner: {self.root}\n"
                      f"Lokaler Datenordner: {self.directory}\nStartprotokoll: {self.log_path}\n"
                      f"Oberfläche: {self.url}\nGitHub erhält keine Projekte, Chats oder Dateien.\n")
            self.emit("log", header)
            self.emit("status", "Laufende lokale Instanz wird geprüft …")
            self.emit("log", "Prüfe vorhandenen Arbeitsraum auf 127.0.0.1 …\n")
            if existing_workspace(self.url, self.directory):
                self.emit("existing", self.url)
                return
            if self.cancelled.is_set():
                return
            try:
                self.directory.mkdir(parents=True, exist_ok=True)
                self.log_file = self.log_path.open("w", encoding="utf-8")
                self.log_file.write(header)
                self.log_file.flush()
            except OSError as exc:
                self.emit("log", f"Protokoll nur im Fenster verfügbar: {exc}\n")
            self.emit("status", "Installation wird geprüft …")
            check = [self.python, str(self.root / "start.py"), "--check", "--data-dir", str(self.directory)]
            code, output = self.execute(check, "check")
            if self.cancelled.is_set():
                return
            if not code and "Installation geprüft:" not in output:
                raise RuntimeError("Python hat die Startprüfung ohne Prüfergebnis beendet. "
                                   "Bitte den oben angezeigten Python-Pfad und die Dateizuordnung prüfen.")
            if code:
                if "Python-Pakete fehlen oder sind unvollständig" not in output:
                    self.emit("error", "Die Installation konnte nicht geprüft werden. Bitte die Details ansehen.")
                    return
                if not install:
                    self.emit("setup_required", "Für den ersten Start fehlen noch Python-Pakete.")
                    return
                self.emit("status", "Einrichtung läuft. Benötigte Pakete werden heruntergeladen …")
                code, _ = self.execute(installer_command(self.python, self.root), "install")
                if self.cancelled.is_set():
                    return
                if code:
                    self.emit("error", "Die Einrichtung ist fehlgeschlagen. Bitte die Details ansehen.")
                    return
                code, output = self.execute(check, "check")
                if code or "Installation geprüft:" not in output:
                    self.emit("error", "Die Einrichtung ist noch unvollständig. Bitte die Details ansehen.")
                    return
            if self.cancelled.is_set():
                return
            self.emit("status", "Arbeitsraum startet …")
            code, _ = self.execute([self.python, str(self.root / "start.py"), "--no-browser",
                                    "--desktop-control", "--port", str(self.port),
                                    "--data-dir", str(self.directory)], "server")
            if not self.cancelled.is_set():
                self.emit("error" if code else "stopped", "Der lokale Arbeitsraum wurde beendet." if not code
                          else "Der Arbeitsraum konnte nicht starten oder wurde unterbrochen. Bitte die Details ansehen.")
        except Exception as exc:
            if not self.cancelled.is_set():
                self.emit("log", str(exc) + "\n")
                self.emit("error", str(exc) if isinstance(exc, StartupTimeout) else
                          "Der Start konnte nicht abgeschlossen werden. Bitte das Protokoll ansehen.")
        finally:
            self.running = False
            if self.cancelled.is_set():
                self.emit("log", "Start bzw. lokaler Dienst wurde beendet.\n")
            with self.log_lock:
                if self.log_file:
                    with suppress(OSError):
                        self.log_file.close()
                    self.log_file = None
            self.emit("finished")

    def stop(self, force=False):
        self.cancelled.set()
        with self.lock:
            process, phase = self.process, self.phase
        if process is None or process.poll() is not None:
            return
        try:
            if force or phase != "server" or not self.running:
                process.kill()
            elif phase == "server":
                process.stdin.write("stop\n")
                process.stdin.flush()
        except (OSError, ValueError):
            pass
