"""Double-click desktop entry point; Tk and setup use only the standard library."""
from __future__ import annotations

import os
import queue
import subprocess
import sys
import threading
import time
from pathlib import Path

ROOT = Path(__file__).resolve().parent


def detach_from_console():
    if os.name != "nt" or Path(sys.executable).name.lower() == "pythonw.exe" or os.environ.get("WORKROOM_DESKTOP_WINDOWED") == "1":
        return False
    python = Path(sys.executable)
    windowed = python.with_name("pythonw.exe")
    env = {**os.environ, "WORKROOM_DESKTOP_WINDOWED": "1"}
    subprocess.Popen([str(windowed if windowed.is_file() else python), str(ROOT / "desktop.pyw"), *sys.argv[1:]],
                     cwd=ROOT, env=env, stdin=subprocess.DEVNULL, stdout=subprocess.DEVNULL,
                     stderr=subprocess.DEVNULL, creationflags=subprocess.CREATE_NO_WINDOW)
    return True


def main():
    if detach_from_console():
        return
    import argparse
    import tkinter as tk
    from tkinter import messagebox, ttk
    from app import __version__
    from app.desktop import DesktopService, create_shortcut, open_workspace
    from start import port_number

    parser = argparse.ArgumentParser(description="GPUStack Arbeitsraum mit grafischem Startfenster öffnen.")
    parser.add_argument("--data-dir")
    parser.add_argument("--port", type=port_number, default=8765)
    args = parser.parse_args()

    class Window:
        def __init__(self):
            self.root = tk.Tk()
            self.root.title("GPUStack Arbeitsraum")
            self.root.geometry("590x410")
            self.root.minsize(560, 410)
            style = ttk.Style(self.root)
            if "vista" in style.theme_names():
                style.theme_use("vista")
            self.service = None
            self.worker = None
            self.closing = False
            self.log_visible = False
            self.frame = ttk.Frame(self.root, padding=24)
            self.frame.pack(fill="both", expand=True)
            ttk.Label(self.frame, text="GPUStack Arbeitsraum", font=("Segoe UI", 19, "bold")).pack(anchor="w")
            ttk.Label(self.frame, text=f"Dein lokaler KI-Arbeitsraum · Version {__version__}").pack(anchor="w", pady=(3, 20))
            self.status = tk.StringVar(value="Vorbereitung …")
            ttk.Label(self.frame, textvariable=self.status, wraplength=500, font=("Segoe UI", 11)).pack(anchor="w")
            self.note = tk.StringVar(value="Die Oberfläche öffnet sich, sobald der Arbeitsraum bereit ist.")
            ttk.Label(self.frame, textvariable=self.note, wraplength=500).pack(anchor="w", pady=(8, 15))
            self.progress = ttk.Progressbar(self.frame, mode="indeterminate")
            self.progress.pack(fill="x", pady=(0, 15))
            row = ttk.Frame(self.frame)
            row.pack(fill="x")
            self.primary = ttk.Button(row, text="Startet …", state="disabled")
            self.primary.pack(side="left")
            self.shortcut = ttk.Button(row, text="Desktop-Verknüpfung", command=self.make_shortcut, state="disabled")
            if os.name == "nt":
                self.shortcut.pack(side="left", padx=8)
            self.exit = ttk.Button(row, text="Beenden", command=self.close)
            self.exit.pack(side="right")
            tools = ttk.Frame(self.frame)
            tools.pack(fill="x", pady=(14, 0))
            ttk.Button(tools, text="Details", command=self.toggle_log).pack(side="left")
            ttk.Button(tools, text="Protokoll kopieren", command=self.copy_log).pack(side="left", padx=8)
            self.log_frame = ttk.Frame(self.frame)
            self.log = tk.Text(self.log_frame, height=12, wrap="word", font=("Consolas", 9), state="disabled")
            scroll = ttk.Scrollbar(self.log_frame, orient="vertical", command=self.log.yview)
            self.log.configure(yscrollcommand=scroll.set)
            self.log.pack(side="left", fill="both", expand=True)
            scroll.pack(side="right", fill="y")
            self.root.protocol("WM_DELETE_WINDOW", self.close)
            if not self.closing:
                self.root.after(100, self.drain)
            self.begin()

        def begin(self, install=False):
            if self.worker and self.worker.is_alive():
                return
            self.service = DesktopService(port=args.port, directory=args.data_dir)
            self.primary.configure(text="Bitte warten …", state="disabled")
            self.progress.start(12)
            self.worker = threading.Thread(target=self.service.run, kwargs={"install": install}, daemon=True)
            self.worker.start()

        def add_log(self, text):
            self.log.configure(state="normal")
            self.log.insert("end", text)
            if int(self.log.index("end-1c").split(".")[0]) > 500:
                self.log.delete("1.0", "101.0")
            self.log.see("end")
            self.log.configure(state="disabled")

        def drain(self):
            if self.service:
                for _ in range(100):
                    try:
                        kind, value = self.service.events.get_nowait()
                    except queue.Empty:
                        break
                    if kind == "log":
                        self.add_log(value)
                    elif not self.closing:
                        self.event(kind, value)
            if not self.closing:
                self.root.after(100, self.drain)

        def event(self, kind, value):
            if kind == "status":
                self.status.set(value)
            elif kind == "setup_required":
                self.progress.stop()
                self.status.set(value)
                self.note.set("Die einmalige Einrichtung lädt die benötigten Python-Pakete herunter.")
                self.primary.configure(text="Einrichten und starten", state="normal", command=lambda: self.begin(True))
            elif kind in ("ready", "existing"):
                self.progress.stop()
                self.status.set("Arbeitsraum bereit")
                self.note.set("Fenster schließen oder Beenden stoppt den lokalen Dienst.")
                self.primary.configure(text="Arbeitsraum öffnen", state="normal", command=self.open)
                self.shortcut.configure(state="normal")
                self.open()
                if kind == "existing":
                    self.closing = True
                    self.root.after_idle(self.root.destroy)
            elif kind in ("error", "stopped"):
                self.progress.stop()
                self.status.set(value)
                self.note.set("Deine gespeicherten Projekte und Dateien bleiben erhalten.")
                self.primary.configure(text="Erneut versuchen", state="normal", command=self.begin)
                if kind == "error" and not self.log_visible:
                    self.toggle_log()

        def open(self):
            try:
                if not open_workspace(self.service.url):
                    messagebox.showinfo("Arbeitsraum öffnen", "Bitte im Browser öffnen:\n" + self.service.url)
            except OSError:
                messagebox.showinfo("Arbeitsraum öffnen", "Bitte im Browser öffnen:\n" + self.service.url)

        def make_shortcut(self):
            try:
                create_shortcut(self.service.python, ROOT, self.service.directory, self.service.port)
                messagebox.showinfo("Desktop-Verknüpfung", "GPUStack Arbeitsraum wurde auf dem Desktop verknüpft.\nDen Programmordner bitte an seinem jetzigen Ort behalten.")
            except (OSError, RuntimeError, subprocess.SubprocessError) as exc:
                messagebox.showerror("Desktop-Verknüpfung", str(exc))

        def toggle_log(self):
            self.log_visible = not self.log_visible
            if self.log_visible:
                self.log_frame.pack(fill="both", expand=True, pady=(14, 0))
                self.root.geometry("650x680")
            else:
                self.log_frame.pack_forget()
                self.root.geometry("590x410")

        def copy_log(self):
            self.root.clipboard_clear()
            self.root.clipboard_append(self.log.get("1.0", "end-1c"))

        def close(self):
            if self.closing:
                return
            self.closing = True
            self.status.set("Arbeitsraum wird beendet …")
            self.primary.configure(state="disabled")
            self.shortcut.configure(state="disabled")
            self.exit.configure(state="disabled")
            self.service.stop()
            self.deadline = time.monotonic() + 15
            self.wait_for_stop()

        def wait_for_stop(self):
            if not self.worker.is_alive():
                self.root.destroy()
                return
            if time.monotonic() >= self.deadline:
                self.service.stop(force=True)
            self.root.after(100, self.wait_for_stop)

    Window().root.mainloop()


if __name__ == "__main__":
    try:
        main()
    except Exception as exc:
        if os.name == "nt":
            import ctypes
            ctypes.windll.user32.MessageBoxW(None,
                "Der grafische Start konnte nicht geöffnet werden.\n"
                "Bitte das vollständige Paket und Python mit Tcl/Tk verwenden.\n\n"
                + str(exc) + "\n\nFür die Diagnose kann start-debug.cmd per Doppelklick gestartet werden.",
                "GPUStack Arbeitsraum", 0x10)
        else:
            raise
