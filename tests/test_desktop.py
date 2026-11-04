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
            return (0, "Installation geprüft: Testinstallation") if installed else (1, "Python-Pakete fehlen oder sind unvollständig: fastapi")
        if phase == "install":
            installed.append(command)
        return 0, ""
    monkeypatch.setattr(service, "execute", execute)
    service.run(install=consent)
    assert bool(installed) is consent
    if not consent:
        assert any(kind == "setup_required" for kind, _ in collected(service))
    else:
        assert not any(kind == "error" and "Prüfergebnis" in message for kind, message in collected(service))


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
    service = desktop.DesktopService(port=available_port(), directory=tmp_path / "data", python=sys.executable,
                                     phase_timeouts={"server": 2})
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
        # The startup deadline must not stop a healthy, already-ready server.
        assert not service.cancelled.wait(2.1)
        assert owned.poll() is None
        original_log = service.log_path.read_text(encoding="utf-8")
        other = desktop.DesktopService(port=service.port, directory=service.directory, python=sys.executable)
        other.run()
        assert any(kind == "existing" for kind, _ in collected(other))
        assert other.process is None
        assert service.log_path.read_text(encoding="utf-8") == original_log
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


@pytest.mark.parametrize("partial_output", [False, True])
def test_silent_or_unterminated_output_cannot_hide_a_hung_check(tmp_path, partial_output):
    service = desktop.DesktopService(directory=tmp_path, phase_timeouts={"check": 0.4})
    code = "import time,sys; " + ("sys.stdout.write('ohne Zeilenende'); sys.stdout.flush(); " if partial_output else "") + "time.sleep(30)"
    started = time.monotonic()
    with pytest.raises(desktop.StartupTimeout):
        service.execute([sys.executable, "-c", code], "check")
    assert time.monotonic() - started < 3
    assert service.process is None
    events = collected(service)
    assert any(kind == "log" and "Paketprüfung beginnt" in message for kind, message in events)
    assert not any(kind == "ready" for kind, _ in events)


def test_blocked_process_creation_can_be_cancelled_and_late_child_is_reaped(tmp_path, monkeypatch):
    real_popen = subprocess.Popen
    release = threading.Event()
    created = queue.Queue()

    def delayed_popen(*args, **kwargs):
        release.wait(5)
        process = real_popen(*args, **kwargs)
        created.put(process)
        return process

    monkeypatch.setattr(desktop.subprocess, "Popen", delayed_popen)
    service = desktop.DesktopService(directory=tmp_path, phase_timeouts={"check": 0.2})
    process = None
    try:
        with pytest.raises(desktop.StartupTimeout, match="Prozessstart"):
            service.execute([sys.executable, "-c", "import time; time.sleep(30)"], "check")
        started = time.monotonic()
        service.stop()
        assert time.monotonic() - started < 0.5
        release.set()
        process = created.get(timeout=3)
        assert process.wait(timeout=3) != 0
        assert service.process is None
    finally:
        release.set()
        if process and process.poll() is None:
            process.kill()
            process.wait(timeout=3)


def test_cancel_stops_a_silent_server_before_its_control_reader_starts(tmp_path):
    service = desktop.DesktopService(directory=tmp_path)
    result = []
    worker = threading.Thread(target=lambda: result.append(service.execute(
        [sys.executable, "-c", "import time; time.sleep(30)"], "server")), daemon=True)
    worker.start()
    try:
        deadline = time.monotonic() + 3
        while service.process is None and time.monotonic() < deadline:
            time.sleep(0.01)
        assert service.process is not None
        service.stop()
        worker.join(timeout=3)
        assert not worker.is_alive()
        assert result[0][0] != 0
        assert service.process is None
    finally:
        service.stop(force=True)
        worker.join(timeout=3)


def test_empty_successful_check_is_not_treated_as_a_working_python(tmp_path, monkeypatch):
    service = desktop.DesktopService(directory=tmp_path)
    monkeypatch.setattr(desktop, "existing_workspace", lambda *args: False)
    phases = []

    def execute(command, phase):
        phases.append(phase)
        return 0, ""

    monkeypatch.setattr(service, "execute", execute)
    service.run(install=True)
    assert phases == ["check"]
    events = collected(service)
    assert any(kind == "error" for kind, _ in events)
    assert any(kind == "log" and "ohne Prüfergebnis" in message for kind, message in events)


def test_hung_import_reports_last_package_and_keeps_diagnostics_local(tmp_path, monkeypatch):
    stub = tmp_path / "stub"
    stub.mkdir()
    (stub / "fastapi.py").write_text("import time\ntime.sleep(30)\n", encoding="utf-8")
    monkeypatch.setenv("PYTHONPATH", str(stub))
    monkeypatch.setenv("GPUSTACK_API_KEY", "private-test-key-never-log")
    monkeypatch.setattr(desktop, "existing_workspace", lambda *args: False)
    service = desktop.DesktopService(directory=tmp_path / "local-data", python=sys.executable,
                                     phase_timeouts={"check": 2})
    service.run()
    events = collected(service)
    assert any(kind == "error" and "abgebrochen" in message for kind, message in events)
    assert not any(kind in ("ready", "setup_required") for kind, _ in events)
    log = service.log_path.read_text(encoding="utf-8")
    assert service.log_path.parent == tmp_path / "local-data"
    assert "GPUStack Arbeitsraum" in log
    assert "Prüfe Python-Paket fastapi" in log
    assert "Paketprüfung wurde nach" in log
    assert "private-test-key-never-log" not in log
    assert service.process is None
