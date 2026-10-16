"""Launcher GUI: abre o servidor e o navegador, sem terminal.
Empacotado como R10Webcam.app pelo PyInstaller (console=False)."""
from __future__ import annotations

import os
import threading
import time
import webbrowser

BASE = os.path.dirname(os.path.abspath(__file__))
os.chdir(BASE)

LOG_FILE = os.path.join(BASE, "r10webcam.log")

VERSION = "1.0.0"
try:
    _vf = os.path.join(BASE, "VERSION")
    if os.path.exists(_vf):
        with open(_vf, encoding="utf-8") as _f:
            VERSION = _f.read().strip() or VERSION
except Exception:
    pass


def _log(msg: str) -> None:
    try:
        with open(LOG_FILE, "a", encoding="utf-8") as f:
            f.write(f"{time.strftime('%Y-%m-%d %H:%M:%S')} {msg}\n")
    except Exception:
        pass

import uvicorn  # noqa: E402


def _open_browser():
    time.sleep(1.5)
    try:
        webbrowser.open("http://127.0.0.1:8000")
    except Exception:
        pass


if __name__ == "__main__":
    import traceback
    _log(f"R10Webcam v{VERSION} iniciando...")
    threading.Thread(target=_open_browser, daemon=True).start()
    try:
        uvicorn.run("server:app", host="127.0.0.1", port=8000, log_level="warning")
    except Exception:
        _log("FALHA ao iniciar servidor:\n" + traceback.format_exc())
        raise
