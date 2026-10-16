"""FastAPI server: Web UI + MJPEG preview + CCAPI controls + virtualcam + demo mode."""
from __future__ import annotations

import os
import threading
import time
from datetime import datetime

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import HTMLResponse, StreamingResponse, JSONResponse, FileResponse
from fastapi.staticfiles import StaticFiles
from pydantic import BaseModel

from canon_wifi import CanonWiFi
from pipeline import Pipeline
import virtualcam

BASE = os.path.dirname(os.path.abspath(__file__))
CAP_DIR = os.path.join(BASE, "captures")
os.makedirs(CAP_DIR, exist_ok=True)

VERSION = "1.1.0"
try:
    with open(os.path.join(BASE, "VERSION"), encoding="utf-8") as _f:
        VERSION = _f.read().strip() or VERSION
except Exception:
    pass

DEMO_DEFAULT = os.getenv("DEMO", "1") == "1"  # link publico funciona sem camera
PORT = int(os.getenv("PORT", "8000"))
CLOUD = bool(os.getenv("RENDER") or os.getenv("RENDER_SERVICE_ID") or os.getenv("HF_SPACE_ID"))

# --- gravador proprio (substitui OBS p/ registrar: mp4 local, sem driver) ---
rec_state = {"recording": False, "file": "", "error": "", "started_at": ""}
_rec_stop = threading.Event()


def _rec_loop(path: str) -> None:
    import cv2
    from pipeline import FPS, H, W
    try:
        fourcc = cv2.VideoWriter_fourcc(*"mp4v")
        out = cv2.VideoWriter(path, fourcc, FPS, (W, H))
        if not out.isOpened():
            rec_state.update(recording=False, error="nao abriu VideoWriter")
            return
        while not _rec_stop.is_set():
            f = pipe.get_frame()
            if f is None:
                time.sleep(0.05)
                continue
            out.write(f)
            time.sleep(1 / FPS)
        out.release()
    except Exception as e:
        rec_state.update(recording=False, error=f"{type(e).__name__}: {e}")

pipe = Pipeline(demo=DEMO_DEFAULT)
cam = CanonWiFi(on_frame=pipe.push_jpg)

app = FastAPI(title="R10 Webcam (Wi-Fi CCAPI)")
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)
app.mount("/static", StaticFiles(directory=os.path.join(BASE, "static")), name="static")
app.mount("/captures", StaticFiles(directory=CAP_DIR), name="captures")


class ConnectReq(BaseModel):
    ip: str


class SettingReq(BaseModel):
    name: str
    value: str


class PipeReq(BaseModel):
    mode: str = "fit"
    flip_h: bool = False
    rotate: int = 0
    brightness: int = 0
    contrast: float = 1.0
    text_overlay: str = ""


@app.get("/", response_class=HTMLResponse)
def index():
    with open(os.path.join(BASE, "static", "index.html"), encoding="utf-8") as f:
        return f.read()


@app.get("/api/status")
def status():
    return {
        "version": VERSION,
        "demo": pipe.demo,
        "cloud": CLOUD,
        "camera": cam.status.__dict__,
        "virtualcam": virtualcam.status(),
        "rec": dict(rec_state),
        "pipe": {"mode": pipe.mode, "flip_h": pipe.flip_h, "rotate": pipe.rotate,
                 "brightness": pipe.brightness, "contrast": pipe.contrast,
                 "text": pipe.text_overlay},
    }


@app.get("/api/health")
def health():
    return {"ok": True, "version": VERSION, "demo": pipe.demo, "cloud": CLOUD}


class DemoReq(BaseModel):
    enabled: bool


@app.post("/api/demo")
def demo(req: DemoReq):
    pipe.demo = bool(req.enabled)
    if req.enabled:
        pipe.latest_jpg = None
    return {"ok": True, "demo": pipe.demo}


@app.get("/api/captures")
def captures():
    try:
        files = sorted(
            (f for f in os.listdir(CAP_DIR) if f.lower().endswith((".jpg", ".jpeg"))),
            reverse=True,
        )[:50]
    except Exception:
        files = []
    return {"ok": True, "files": files}


@app.get("/api/photo/{name}")
def photo(name: str):
    path = os.path.join(CAP_DIR, os.path.basename(name))
    if not os.path.isfile(path):
        return JSONResponse({"ok": False, "error": "nao encontrada"}, status_code=404)
    return FileResponse(path, media_type="image/jpeg")


@app.post("/api/connect")
def connect(req: ConnectReq):
    try:
        info = cam.probe(req.ip)
        cam.start()
        return {"ok": True, "info": info}
    except Exception as e:
        cam.status.last_error = f"{type(e).__name__}: {e}"
        return JSONResponse({"ok": False, "error": str(e)}, status_code=400)


@app.post("/api/disconnect")
def disconnect():
    cam.stop()
    cam.status.connected = False
    return {"ok": True}


@app.post("/api/shutter")
def shutter():
    try:
        return {"ok": True, "res": cam.shutter()}
    except Exception as e:
        return JSONResponse({"ok": False, "error": str(e)}, status_code=400)


@app.post("/api/setting")
def setting(req: SettingReq):
    try:
        return {"ok": True, "res": cam.set_setting(req.name, req.value)}
    except Exception as e:
        return JSONResponse({"ok": False, "error": str(e)}, status_code=400)


@app.post("/api/pipe")
def pipe_update(req: PipeReq):
    pipe.mode = req.mode if req.mode in ("fit", "fill") else "fit"
    pipe.flip_h = req.flip_h
    pipe.rotate = req.rotate if req.rotate in (0, 90, 180, 270) else 0
    pipe.brightness = max(-100, min(100, req.brightness))
    pipe.contrast = max(0.5, min(2.0, req.contrast))
    pipe.text_overlay = req.text_overlay[:120]
    return {"ok": True}


@app.post("/api/snapshot")
def snapshot():
    jpg = pipe.get_jpeg(quality=92)
    if not jpg:
        return JSONResponse({"ok": False, "error": "sem frame"}, status_code=400)
    fn = f"r10_{datetime.now().strftime('%Y%m%d_%H%M%S')}.jpg"
    with open(os.path.join(CAP_DIR, fn), "wb") as f:
        f.write(jpg)
    return {"ok": True, "file": fn}


@app.post("/api/virtualcam/start")
def vcam_start(backend: str = "obs"):
    if CLOUD:
        msg = "Webcam virtual indisponivel na nuvem — use o app local (Mac/Windows + OBS) ou o Modo Apresentar (/present) com Compartilhar tela no Meet/Zoom."
        virtualcam._state.update(running=False, error=msg)
        return JSONResponse({"ok": False, "error": msg}, status_code=400)
    virtualcam.start(pipe, backend=backend)
    time.sleep(1.5)
    st = virtualcam.status()
    if st["error"]:
        hint = st["error"] + " Dica: instale o OBS 30+, abra 1x Start Virtual Camera -> Stop, ou use /present + Compartilhar tela."
        return JSONResponse({"ok": False, "error": hint, **st}, status_code=400)
    return {"ok": True, **st}


@app.post("/api/virtualcam/stop")
def vcam_stop():
    virtualcam.stop()
    return {"ok": True}


@app.post("/api/rec/start")
def rec_start():
    if rec_state["recording"]:
        return {"ok": True, **rec_state}
    fn = f"r10_{datetime.now().strftime('%Y%m%d_%H%M%S')}.mp4"
    path = os.path.join(CAP_DIR, fn)
    _rec_stop.clear()
    rec_state.update(recording=True, file=fn, error="", started_at=datetime.now().isoformat())
    threading.Thread(target=_rec_loop, args=(path,), daemon=True, name="rec").start()
    return {"ok": True, **rec_state}


@app.post("/api/rec/stop")
def rec_stop():
    _rec_stop.set()
    rec_state["recording"] = False
    return {"ok": True, **rec_state}


@app.get("/api/rec/status")
def rec_status():
    return {"ok": True, **rec_state}


@app.get("/api/videos")
def videos():
    try:
        files = sorted(
            (f for f in os.listdir(CAP_DIR) if f.lower().endswith((".mp4", ".avi"))),
            reverse=True,
        )[:50]
    except Exception:
        files = []
    return {"ok": True, "files": files}


@app.get("/present", response_class=HTMLResponse)
def present():
    with open(os.path.join(BASE, "static", "present.html"), encoding="utf-8") as f:
        return f.read()


@app.get("/preview.mjpg")
def preview():
    def gen():
        while True:
            jpg = pipe.get_jpeg()
            if jpg:
                yield (b"--frame\r\nContent-Type: image/jpeg\r\n\r\n" + jpg + b"\r\n")
            time.sleep(1 / 30)
    return StreamingResponse(gen(), media_type="multipart/x-mixed-replace; boundary=frame")
