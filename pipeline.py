"""Frame pipeline: JPEG bytes -> BGR frame 1280x720, filters, overlays."""
from __future__ import annotations

import threading
import time

import cv2
import numpy as np

W, H, FPS = 1280, 720, 30


class Pipeline:
    def __init__(self):
        self.lock = threading.Lock()
        self.latest_jpg: bytes | None = None
        self.latest_frame: np.ndarray | None = None
        self.last_jpg_ts = 0.0
        # settings (from Web UI)
        self.mode = "fit"          # fit | fill
        self.flip_h = False
        self.rotate = 0            # 0|90|180|270
        self.brightness = 0        # -100..100
        self.contrast = 1.0        # 0.5..2.0
        self.text_overlay = ""
        self.running = True
        self._t = threading.Thread(target=self._decode_loop, daemon=True)
        self._t.start()

    def push_jpg(self, data: bytes) -> None:
        with self.lock:
            self.latest_jpg = data
            self.last_jpg_ts = time.time()

    def _decode_loop(self):
        while self.running:
            jpg = None
            with self.lock:
                jpg = self.latest_jpg
            if jpg:
                arr = np.frombuffer(jpg, dtype=np.uint8)
                img = cv2.imdecode(arr, cv2.IMREAD_COLOR)
                if img is not None:
                    img = self._process(img)
                    with self.lock:
                        self.latest_frame = img
            else:
                # placeholder slate when no signal
                img = np.zeros((H, W, 3), np.uint8)
                cv2.putText(img, "SEM SINAL — conecte a R10 via Wi-Fi (CCAPI)",
                            (90, H // 2), cv2.FONT_HERSHEY_SIMPLEX, 0.8, (255, 255, 255), 2)
                with self.lock:
                    self.latest_frame = img
            time.sleep(1 / FPS)

    def _process(self, img: np.ndarray) -> np.ndarray:
        h, w = img.shape[:2]
        scale = min(W / w, H / h) if self.mode == "fit" else max(W / w, H / h)
        img = cv2.resize(img, (int(w * scale), int(h * scale)))
        # center-crop / letterbox to 1280x720
        canvas = np.zeros((H, W, 3), np.uint8)
        y0 = max(0, (H - img.shape[0]) // 2)
        x0 = max(0, (W - img.shape[1]) // 2)
        sy0, sx0 = max(0, (img.shape[0] - H) // 2), max(0, (img.shape[1] - W) // 2)
        dh, dw = min(H, img.shape[0]), min(W, img.shape[1])
        canvas[y0:y0 + dh, x0:x0 + dw] = img[sy0:sy0 + dh, sx0:sx0 + dw]
        img = canvas
        if self.rotate in (90, 180, 270):
            codes = {90: cv2.ROTATE_90_CLOCKWISE, 180: cv2.ROTATE_180, 270: cv2.ROTATE_90_COUNTERCLOCKWISE}
            img = cv2.rotate(img, codes[self.rotate])
            img = cv2.resize(img, (W, H))
        if self.flip_h:
            img = cv2.flip(img, 1)
        if self.brightness != 0 or self.contrast != 1.0:
            img = cv2.convertScaleAbs(img, alpha=self.contrast, beta=self.brightness)
        if self.text_overlay:
            cv2.putText(img, self.text_overlay, (24, H - 28),
                        cv2.FONT_HERSHEY_SIMPLEX, 0.9, (255, 255, 255), 2, cv2.LINE_AA)
        return img

    def get_frame(self) -> np.ndarray | None:
        with self.lock:
            return None if self.latest_frame is None else self.latest_frame.copy()

    def get_jpeg(self, quality: int = 80) -> bytes | None:
        f = self.get_frame()
        if f is None:
            return None
        ok, buf = cv2.imencode(".jpg", f, [int(cv2.IMWRITE_JPEG_QUALITY), quality])
        return bytes(buf) if ok else None
