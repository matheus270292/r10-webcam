"""Launcher GUI: abre o servidor e o navegador, sem terminal.
Empacotado como R10Webcam.app pelo PyInstaller (console=False)."""
from __future__ import annotations

import os
import threading
import time
import webbrowser

BASE = os.path.dirname(os.path.abspath(__file__))
os.chdir(BASE)

import uvicorn  # noqa: E402


def _open_browser():
    time.sleep(1.5)
    try:
        webbrowser.open("http://127.0.0.1:8000")
    except Exception:
        pass


if __name__ == "__main__":
    threading.Thread(target=_open_browser, daemon=True).start()
    uvicorn.run("server:app", host="127.0.0.1", port=8000, log_level="warning")
