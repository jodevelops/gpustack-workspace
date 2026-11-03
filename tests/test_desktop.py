"""Desktop lifecycle tests without a display, real localhost process included."""
import os
import queue
import subprocess
import sys
import threading
import time
from pathlib import Path

import httpx
import pytest

from app import desktop
from tests.test_start import available_port, stop, wait_until_ready

ROOT = Path(__file__).resolve().parent.parent


def collected(service):
    events = []
    while True:
        try:
            events.append(service.events.get_nowait())
        except queue.Empty:
            return events


@pytest.mark.parametrize("in_venv", [False, True])
def test_setup_targets_current_python_without_admin_install(in_venv, tmp_path):
    python = tmp_path / "Python mit Leerzeichen" / "python.exe"
    command = desktop.installer_command(python, tmp_path, in_venv=in_venv)
    assert command[0] == str(python)
    assert "--user" in command if not in_venv else "--user" not in command
    assert "--only-binary=:all:" in command
    assert command[-1] == str(tmp_path / "requirements.txt")


def test_desktop_control_imports_without_backend_packages():
    result = subprocess.run([sys.executable, "-S", "-c", "import app.desktop"], cwd=ROOT,
                            capture_output=True, text=True, timeout=10)
    assert result.returncode == 0, result.stderr


@pytest.mark.parametrize("consent", [False, True])
def test_packages_install_only_after_setup_button(consent, tmp_path, monkeypatch):
    service = desktop.DesktopService(directory=tmp_path)
    monkeypatch.setattr(desktop, "existing_workspace", lambda *args: False)
    installed = []
    def execute(command, phase):
        if phase == "check":
            return (0, "") if installed else (1, "Python-Pakete fehlen oder sind unvollständig: fastapi")
        if phase == "install":
            installed.append(command)
        return 0, ""
    monkeypatch.setattr(service, "execute", execute)
    service.run(install=consent)
    assert bool(installed) is consent
    if not consent:
        assert any(kind == "setup_required" for kind, _ in collected(service))


def test_failed_setup_does_not_launch_workspace(tmp_path, monkeypatch):
    service = desktop.DesktopService(directory=tmp_path)
    monkeypatch.setattr(desktop, "existing_workspace", lambda *args: False)
    def execute(command, phase):
        assert phase != "server", "A failed installation must not start the server"
        return (1, "Python-Pakete fehlen oder sind unvollständig: fastapi") if phase == "check" else (1, "Install blocked")
    monkeypatch.setattr(service, "execute", execute)
    service.run(install=True)
    assert any(kind == "error" for kind, _ in collected(service))


def test_cancel_before_start_never_installs_or_launches(tmp_path, monkeypatch):
    service = desktop.DesktopService(directory=tmp_path)
    monkeypatch.setattr(desktop.subprocess, "Popen", lambda *a, **k: pytest.fail("Unexpected subprocess"))
    service.stop()
    service.run(install=True)
    assert not service.running


def test_real_desktop_service_ready_reuse_and_graceful_stop(tmp_path):
    service = desktop.DesktopService(port=available_port(), directory=tmp_path / "data", python=sys.executable)
    worker = threading.Thread(target=service.run, daemon=True)
    worker.start()
    try:
        deadline = time.monotonic() + 30
        while time.monotonic() < deadline:
            kind, message = service.events.get(timeout=30)
            assert kind != "error", message
            if kind == "ready":
                break
        else:
            pytest.fail("Desktop service did not become ready")
        with httpx.Client(base_url=service.url, trust_env=False) as client:
            boot = client.get("/api/bootstrap")
            assert boot.status_code == 200
            assert boot.json()["data_dir"] == str(tmp_path / "data")
            assert client.get("/").status_code == 200
        owned = service.process
        other = desktop.DesktopService(port=service.port, directory=service.directory, python=sys.executable)
        other.run()
        assert any(kind == "existing" for kind, _ in collected(other))
        assert other.process is None
        assert service.process is owned and owned.poll() is None
        assert not desktop.existing_workspace(service.url, tmp_path / "different-data")
        service.stop()
        worker.join(timeout=15)
        assert not worker.is_alive()
        assert owned.returncode == 0
        assert not service.running
    finally:
        service.stop(force=True)
        worker.join(timeout=5)


def test_controller_pipe_eof_stops_actual_server(tmp_path):
    port = available_port()
    log = tmp_path / "controller.log"
    env = {k: v for k, v in os.environ.items() if not k.startswith(("GPUSTACK_", "WORKROOM_"))}
    env["PYTHONIOENCODING"] = "utf-8"
    with log.open("wb") as output:
        process = subprocess.Popen([sys.executable, str(ROOT / "start.py"), "--no-browser", "--desktop-control",
                                    "--port", str(port), "--data-dir", str(tmp_path / "data")],
                                   cwd=tmp_path, env=env, stdin=subprocess.PIPE, stdout=output, stderr=subprocess.STDOUT)
        try:
            wait_until_ready(process, log)
            process.stdin.close()
            assert process.wait(timeout=15) == 0
        finally:
            stop(process)


def test_shortcut_keeps_quotes_and_spaces_inside_literal_paths(tmp_path):
    root = tmp_path / "Sammlung O'Brien"
    script = desktop.shortcut_script(tmp_path / "python.exe", root, root / "Daten", 8765)
    assert "O''Brien" in script
    assert str(root).replace("'", "''") in script
    assert "--data-dir" in script
    assert "-ExecutionPolicy" not in script
