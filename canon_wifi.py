"""Canon CCAPI (Wi-Fi) client for EOS R10 — 100% wireless, no USB/EDSDK.

Docs: https://developercommunity.usa.canon.com (CCAPI 1.4.x)
R10 requires: firmware >= 1.5.0 (1.8.0 recommended) + CCAPI activation (one-time,
free, via Canon Developer Community).

Typical endpoints (ver100):
  GET  http://<cam-ip>:8080/ccapi/ver100/deviceinformation
  POST http://<cam-ip>:8080/ccapi/ver100/shooting/liveview/flip  (enable LV stream)
  GET  http://<cam-ip>:8080/ccapi/ver100/shooting/liveview/flip  (stream MJPEG-ish)
  POST .../shooting/control/shutterbutton {"af": true, "shoot": true}
  GET/PUT .../shooting/settings/av, tv, iso, wb, exposure, battery, etc.
Different firmware revisions vary slightly — this client probes and adapts.
"""
from __future__ import annotations

import threading
import time
from dataclasses import dataclass
from typing import Callable, Optional

import httpx

BASE_TEMPLATE = "http://{ip}:8080/ccapi"


@dataclass
class CameraStatus:
    connected: bool = False
    ip: str = ""
    camera_name: str = ""
    battery: str = ""
    last_error: str = ""
    fps: float = 0.0
    last_frame_ts: float = 0.0


class CanonWiFi:
    """Threaded CCAPI liveview client with auto-reconnect."""

    def __init__(self, ip: str = "", on_frame: Optional[Callable[[bytes], None]] = None):
        self.ip = ip.strip()
        self.on_frame = on_frame
        self.status = CameraStatus(ip=self.ip)
        self._stop = threading.Event()
        self._thread: Optional[threading.Thread] = None
        self._client = httpx.Client(timeout=8.0)
        self._frame_count = 0
        self._fps_t0 = time.time()

    # ---------- connection ----------
    @property
    def base(self) -> str:
        return BASE_TEMPLATE.format(ip=self.ip)

    def set_ip(self, ip: str) -> None:
        self.ip = ip.strip()
        self.status.ip = self.ip

    def probe(self, ip: str = "") -> dict:
        """Test connectivity: GET deviceinformation. Raises on failure."""
        target = ip.strip() or self.ip
        if not target:
            raise ValueError("Informe o IP da câmera (ex: 192.168.1.20)")
        url = BASE_TEMPLATE.format(ip=target) + "/ver100/deviceinformation"
        r = self._client.get(url)
        r.raise_for_status()
        data = r.json()
        self.ip = target
        self.status.ip = target
        self.status.connected = True
        self.status.camera_name = data.get("model", data.get("productname", "Canon"))
        self.status.last_error = ""
        return data

    def get(self, path: str) -> dict:
        r = self._client.get(self.base + path)
        r.raise_for_status()
        try:
            return r.json()
        except Exception:
            return {"raw": r.text}

    def post(self, path: str, payload: dict | None = None) -> dict:
        r = self._client.post(self.base + (path), json=payload or {})
        r.raise_for_status()
        try:
            return r.json()
        except Exception:
            return {"ok": True}

    def put(self, path: str, payload: dict) -> dict:
        r = self._client.put(self.base + path, json=payload)
        r.raise_for_status()
        try:
            return r.json()
        except Exception:
            return {"ok": True}

    # ---------- actions ----------
    def shutter(self, af: bool = True) -> dict:
        return self.post("/ver100/shooting/control/shutterbutton", {"af": af, "shoot": True})

    def set_setting(self, name: str, value: str) -> dict:
        # e.g. name="av" value="f2.8" -> PUT /shooting/settings/av {"value": "f2.8"}
        return self.put(f"/ver100/shooting/settings/{name}", {"value": value})

    def get_battery(self) -> str:
        try:
            d = self.get("/ver100/deviceinformation/battery")
            # shapes vary: {"value": ...} | {"level": ...} | {"name":...}
            for k in ("value", "level", "capacity", "name"):
                if k in d:
                    return str(d[k])
            return str(d)
        except Exception as e:
            return f"n/d ({e})"

    # ---------- liveview loop ----------
    def start(self) -> None:
        if self._thread and self._thread.is_alive():
            return
        self._stop.clear()
        self._thread = threading.Thread(target=self._loop, daemon=True, name="ccapi-lv")
        self._thread.start()

    def stop(self) -> None:
        self._stop.set()

    def _loop(self) -> None:
        backoff = 1.0
        while not self._stop.is_set():
            try:
                self._stream_liveview()
                backoff = 1.0  # reset after clean exit
            except Exception as e:
                self.status.connected = False
                self.status.last_error = f"{type(e).__name__}: {e}"
                time.sleep(backoff)
                backoff = min(backoff * 1.5, 10.0)

    def _stream_liveview(self) -> None:
        # 1) ensure flip/liveview enabled (best-effort; ignore errors)
        for path in ("/ver100/shooting/liveview/flip", "/ver100/shooting/liveview"):
            try:
                self.post(path, {"liveview": "on", "flip": "on"} if "flip" in path else {"liveview": "on"})
                break
            except Exception:
                continue
        # 2) stream: CCAPI liveview returns multipart JPEG; poll sequentially
        url = self.base + "/ver100/shooting/liveview/flip"
        self.status.connected = True
        self.status.last_error = ""
        with self._client.stream("GET", url, timeout=30.0) as resp:
            resp.raise_for_status()
            buf = b""
            for chunk in resp.iter_bytes(chunk_size=65536):
                if self._stop.is_set():
                    return
                buf += chunk
                # extract JPEG frames (FFD8 ... FFD9)
                while True:
                    start = buf.find(b"\xff\xd8")
                    end = buf.find(b"\xff\xd9")
                    if start == -1 or end == -1 or end <= start:
                        # keep buffer bounded
                        if len(buf) > 8_000_000:
                            buf = buf[-4_000_000:]
                        break
                    jpg = buf[start:end + 2]
                    buf = buf[end + 2:]
                    self._emit(jpg)

    def _emit(self, jpg: bytes) -> None:
        self._frame_count += 1
        now = time.time()
        self.status.last_frame_ts = now
        if now - self._fps_t0 >= 2.0:
            self.status.fps = self._frame_count / (now - self._fps_t0)
            self._frame_count = 0
            self._fps_t0 = now
        # refresh battery occasionally
        if int(now) % 20 == 0:
            try:
                self.status.battery = self.get_battery()
            except Exception:
                pass
        if self.on_frame:
            try:
                self.on_frame(jpg)
            except Exception:
                pass
