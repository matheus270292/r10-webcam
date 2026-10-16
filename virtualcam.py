"""Virtual camera output via pyvirtualcam (OBS backend, Win + Mac)."""
from __future__ import annotations

import threading
import time

from pipeline import FPS, H, W

_state = {"running": False, "device": "", "error": "", "backend": "obs"}


def status() -> dict:
    return dict(_state)


def start(pipeline, backend: str = "obs") -> None:
    import pyvirtualcam

    def _run():
        try:
            with pyvirtualcam.Camera(width=W, height=H, fps=FPS,
                                     fmt=pyvirtualcam.PixelFormat.BGR,
                                     backend=backend if backend != "auto" else None) as cam:
                _state.update(running=True, device=str(cam.device), backend=backend, error="")
                while _state["running"]:
                    frame = pipeline.get_frame()
                    if frame is None:
                        time.sleep(0.05)
                        continue
                    cam.send(frame)
                    cam.sleep_until_next_frame()
        except Exception as e:
            _state.update(running=False, error=f"{type(e).__name__}: {e}")

    _state.update(running=True, error="")
    threading.Thread(target=_run, daemon=True, name="virtualcam").start()


def stop() -> None:
    _state["running"] = False
