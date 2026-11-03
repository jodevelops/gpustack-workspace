"""Desktop process control; standard library only, including before setup."""
from __future__ import annotations

import json
import os
import queue
import subprocess
import sys
import threading
import webbrowser
from collections import deque
from pathlib import Path
from urllib.request import ProxyHandler, build_opener

from start import ROOT, data_directory


def console_python(executable=None):
    path = Path(executable or sys.executable)
    if path.name.lower() == "pythonw.exe":
        candidate = path.with_name("python.exe")
        if candidate.is_file():
            return str(candidate)
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
    def __init__(self, port=8765, directory=None, python=None, root=ROOT):
        self.port, self.root = port, Path(root)
        self.directory = data_directory(str(directory) if directory is not None else None)
        self.python = console_python(python)
        self.url = f"http://127.0.0.1:{port}"
        self.events = queue.Queue()
        self.cancelled = threading.Event()
        self.lock = threading.Lock()
        self.process = None
        self.phase = ""
        self.running = False

    def emit(self, kind, value=""):
        self.events.put((kind, value))

    def execute(self, command, phase):
        env = {**os.environ, "PYTHONIOENCODING": "utf-8"}
        if phase == "install":
            env = {key: value for key, value in env.items() if not key.startswith("GPUSTACK_")}
        with self.lock:
            if self.cancelled.is_set():
                return -1, ""
            process = subprocess.Popen(command, cwd=self.root, env=env,
                                       stdin=subprocess.PIPE if phase == "server" else subprocess.DEVNULL,
                                       stdout=subprocess.PIPE, stderr=subprocess.STDOUT,
                                       text=True, encoding="utf-8", errors="replace", bufsize=1,
                                       **background_options())
            self.process, self.phase = process, phase
        tail = deque(maxlen=200)
        try:
            for line in process.stdout:
                tail.append(line)
                self.emit("log", line)
                if phase == "server" and "Arbeitsraum bereit:" in line and not self.cancelled.is_set():
                    self.running = True
                    self.emit("ready", self.url)
            code = process.wait()
            return code, "".join(tail)
        finally:
            process.stdout.close()
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
            if existing_workspace(self.url, self.directory):
                self.emit("existing", self.url)
                return
            self.emit("status", "Installation wird geprüft …")
            check = [self.python, str(self.root / "start.py"), "--check", "--data-dir", str(self.directory)]
            code, output = self.execute(check, "check")
            if self.cancelled.is_set():
                return
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
                code, _ = self.execute(check, "check")
                if code:
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
                self.emit("error", "Der Start konnte nicht abgeschlossen werden. Bitte die Details ansehen.")
        finally:
            self.running = False
            self.emit("finished")

    def stop(self, force=False):
        self.cancelled.set()
        with self.lock:
            process, phase = self.process, self.phase
        if process is None or process.poll() is not None:
            return
        try:
            if force:
                process.kill()
            elif phase == "server":
                process.stdin.write("stop\n")
                process.stdin.flush()
            else:
                process.terminate()
        except (OSError, ValueError):
            pass
