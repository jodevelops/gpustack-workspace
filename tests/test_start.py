"""Launcher regression tests: delayed startup, actual HTTP service, occupied port."""
import os
import socket
import subprocess
import sys
import threading
import time
from pathlib import Path
from types import SimpleNamespace
from urllib.request import ProxyHandler, build_opener

import pytest
import start
import httpx

ROOT = Path(__file__).resolve().parent.parent


@pytest.mark.parametrize("succeeds", [True, False])
def test_browser_waits_for_successful_startup(monkeypatch, succeeds):
    server = SimpleNamespace(started=False)
    stopped = threading.Event()
    opened = threading.Event()
    monkeypatch.setattr(start.webbrowser, "open", lambda url: opened.set() or True)
    monitor = threading.Thread(
        target=start.announce_when_ready,
        args=(server, "http://127.0.0.1:8765", stopped, True),
        daemon=True,
    )
    monitor.start()
    try:
        # The old launcher opened the browser after 1.5 seconds regardless of readiness.
        assert not opened.wait(1.8)
        if succeeds:
            server.started = True
            assert opened.wait(2)
        else:
            stopped.set()
        monitor.join(timeout=2)
        assert not monitor.is_alive()
        assert opened.is_set() == succeeds
    finally:
        stopped.set()
        monitor.join(timeout=2)


def launch(tmp_path, port, output):
    env = {k: v for k, v in os.environ.items()
           if not k.startswith(("GPUSTACK_", "WORKROOM_"))}
    env["PYTHONIOENCODING"] = "utf-8"
    return subprocess.Popen(
        [sys.executable, str(ROOT / "start.py"), "--no-browser", "--port", str(port),
         "--data-dir", str(tmp_path / "data")],
        cwd=tmp_path, env=env, stdout=output, stderr=subprocess.STDOUT,
    )


def stop(process):
    if process.poll() is None:
        process.terminate()
        try:
            process.wait(timeout=10)
        except subprocess.TimeoutExpired:
            process.kill()
            process.wait(timeout=5)


def test_real_launcher_serves_workspace(tmp_path):
    with socket.socket() as reservation:
        reservation.bind(("127.0.0.1", 0))
        port = reservation.getsockname()[1]
    log = tmp_path / "startup.log"
    with log.open("wb") as output:
        process = launch(tmp_path, port, output)
        try:
            deadline = time.monotonic() + 25
            while time.monotonic() < deadline:
                if process.poll() is not None or "Arbeitsraum bereit:" in log.read_text(encoding="utf-8"):
                    break
                time.sleep(0.1)
            text = log.read_text(encoding="utf-8")
            assert process.poll() is None, text
            assert "Arbeitsraum bereit:" in text, text
            assert text.index("Uvicorn running on") < text.index("Arbeitsraum bereit:")
            opener = build_opener(ProxyHandler({}))
            with opener.open(f"http://127.0.0.1:{port}/", timeout=5) as response:
                assert response.status == 200
                assert b"Arbeitsraum" in response.read()
            assert (tmp_path / "data" / "workspace.sqlite3").is_file()
        finally:
            stop(process)


def test_occupied_port_reports_failure_without_ready_message(tmp_path):
    with socket.socket() as reservation, (tmp_path / "startup.log").open("wb") as output:
        reservation.bind(("127.0.0.1", 0))
        reservation.listen(1)
        port = reservation.getsockname()[1]
        process = launch(tmp_path, port, output)
        try:
            assert process.wait(timeout=25) != 0
        finally:
            stop(process)
    text = (tmp_path / "startup.log").read_text(encoding="utf-8")
    assert "Start fehlgeschlagen" in text, text
    assert "Arbeitsraum bereit:" not in text
    assert "ERROR" in text


@pytest.mark.parametrize("option", ["--help", "--version"])
def test_help_and_version_work_before_installing_dependencies(option, tmp_path):
    result = subprocess.run(
        [sys.executable, "-S", str(ROOT / "start.py"), option],
        cwd=tmp_path, capture_output=True, text=True, encoding="utf-8", timeout=10,
    )
    assert result.returncode == 0, result.stderr
    assert ("--data-dir" in result.stdout) if option == "--help" else (start.__version__ in result.stdout)


def test_missing_dependencies_show_install_command(tmp_path):
    result = subprocess.run(
        [sys.executable, "-S", str(ROOT / "start.py"), "--check", "--data-dir", str(tmp_path / "data")],
        cwd=tmp_path, capture_output=True, text=True, encoding="utf-8", timeout=10,
    )
    assert result.returncode != 0
    assert "pip install -r" in result.stderr
    assert "requirements.txt" in result.stderr
    assert "Traceback" not in result.stderr


@pytest.mark.parametrize("port", ["0", "65536", "abc"])
def test_invalid_port_does_not_start_server(port, tmp_path):
    result = subprocess.run(
        [sys.executable, str(ROOT / "start.py"), "--port", port],
        cwd=tmp_path, capture_output=True, text=True, encoding="utf-8", timeout=10,
    )
    assert result.returncode == 2
    assert "Arbeitsraum bereit:" not in result.stdout


def test_explicit_data_directory_takes_priority_over_environment_and_legacy(tmp_path, monkeypatch):
    monkeypatch.setattr(start, "ROOT", tmp_path)
    legacy = tmp_path / "data"
    legacy.mkdir()
    (legacy / "workspace.sqlite3").touch()
    selected = tmp_path / "aus Umgebung"
    monkeypatch.setenv("WORKROOM_DATA_DIR", str(selected))
    assert start.data_directory() == selected
    assert start.data_directory(str(tmp_path / "aus Argument")) == tmp_path / "aus Argument"
    monkeypatch.delenv("WORKROOM_DATA_DIR")
    assert start.data_directory() == legacy


@pytest.mark.parametrize("platform", ["win32", "darwin", "linux"])
def test_new_installation_uses_stable_user_directory(platform, tmp_path, monkeypatch):
    monkeypatch.setattr(start, "ROOT", tmp_path / "download")
    monkeypatch.setattr(start.sys, "platform", platform)
    monkeypatch.setattr(start.Path, "home", lambda: tmp_path)
    monkeypatch.delenv("WORKROOM_DATA_DIR", raising=False)
    monkeypatch.setenv("LOCALAPPDATA", str(tmp_path / "local"))
    monkeypatch.setenv("XDG_DATA_HOME", str(tmp_path / "xdg"))
    expected = {
        "win32": tmp_path / "local", "darwin": tmp_path / "Library" / "Application Support",
        "linux": tmp_path / "xdg",
    }[platform] / start.APP_NAME
    assert start.data_directory() == expected


def wait_until_ready(process, log):
    deadline = time.monotonic() + 25
    while time.monotonic() < deadline:
        text = log.read_text(encoding="utf-8")
        if "Arbeitsraum bereit:" in text:
            assert process.poll() is None, text
            return
        assert process.poll() is None, text
        time.sleep(0.1)
    pytest.fail("Server wurde nicht bereit: " + log.read_text(encoding="utf-8"))


def available_port():
    with socket.socket() as reservation:
        reservation.bind(("127.0.0.1", 0))
        return reservation.getsockname()[1]


def test_real_restart_preserves_projects_chat_settings_and_original_files(tmp_path):
    port = available_port()
    log = tmp_path / "restart.log"
    with log.open("wb") as output:
        process = launch(tmp_path, port, output)
        try:
            wait_until_ready(process, log)
            with httpx.Client(base_url=f"http://127.0.0.1:{port}", trust_env=False) as client:
                client.headers["X-CSRF-Token"] = client.get("/api/bootstrap").json()["csrf"]
                project = client.post("/api/projects", json={"name": "Neustartprüfung − 中文"})
                assert project.status_code == 200, project.text
                project_id = project.json()["id"]
                thread = client.post("/api/threads", json={
                    "project_id": project_id, "system_prompt": "Bleibt über den Neustart erhalten.", "max_tokens": 1024,
                })
                assert thread.status_code == 200, thread.text
                thread_id = thread.json()["id"]
                original = "Fiktive Quelle − bleibt unverändert. 中文".encode("utf-8")
                document = client.post("/api/documents", data={"project_id": project_id}, files={"file": ("quelle.txt", original)})
                assert document.status_code == 200, document.text
                document_id = document.json()["id"]
        finally:
            stop(process)
    with log.open("wb") as output:
        process = launch(tmp_path, port, output)
        try:
            wait_until_ready(process, log)
            with httpx.Client(base_url=f"http://127.0.0.1:{port}", trust_env=False) as client:
                boot = client.get("/api/bootstrap").json()
                assert any(p["id"] == project_id and p["name"] == "Neustartprüfung − 中文" for p in boot["projects"])
                saved = client.get("/api/threads/" + thread_id).json()["thread"]
                assert saved["system_prompt"] == "Bleibt über den Neustart erhalten."
                assert saved["parameters"]["max_tokens"] == 1024
                assert client.get("/api/documents/" + document_id + "/download").content == original
        finally:
            stop(process)


def test_second_instance_cannot_use_same_data_directory(tmp_path):
    port = available_port()
    first_log, second_log = tmp_path / "first.log", tmp_path / "second.log"
    with first_log.open("wb") as output, second_log.open("wb") as second_output:
        first = launch(tmp_path, port, output)
        try:
            wait_until_ready(first, first_log)
            second = launch(tmp_path, available_port(), second_output)
            try:
                assert second.wait(timeout=25) != 0
            finally:
                stop(second)
            text = second_log.read_text(encoding="utf-8")
            assert "bereits von einem Arbeitsraum verwendet" in text
            assert "Arbeitsraum bereit:" not in text
            assert first.poll() is None
        finally:
            stop(first)
