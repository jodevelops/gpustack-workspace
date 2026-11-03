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
