# -*- mode: python ; coding: utf-8 -*-
"""PyInstaller spec — gera R10Webcam.app (arm64/x64 universal via runner).
Uso: executado por build-mac.sh ou GitHub Actions. Não rode no Windows.
"""
import os

BASE = os.path.abspath(SPECDIR)

a = Analysis(
    ["launcher.py"],
    pathex=[BASE],
    binaries=[],
    datas=[
        ("static", "static"),
        ("requirements.txt", "."),
        ("VERSION", "."),
        ("README.md", "."),
    ],
    hiddenimports=[
        "uvicorn",
        "uvicorn.logging",
        "uvicorn.loops.auto",
        "uvicorn.protocols.http.auto",
        "uvicorn.lifespan.on",
        "fastapi",
        "starlette",
        "pydantic",
        "httpx",
        "cv2",
        "numpy",
        "pyvirtualcam",
    ],
    hookspath=[],
    hooksconfig={},
    runtime_hooks=[],
    excludes=["tkinter", "matplotlib", "PIL"],
    noarchive=False,
)
pyz = PYZ(a.pure)
exe = EXE(
    pyz,
    a.scripts,
    exclude_binaries=True,
    name="R10Webcam",
    debug=False,
    strip=False,
    upx=False,
    console=False,  # app de janela (sem terminal)
)
coll = COLLECT(
    exe,
    a.binaries,
    a.datas,
    strip=False,
    upx=False,
    name="R10Webcam",
)
app = BUNDLE(
    coll,
    name="R10Webcam.app",
    icon=None,
    bundle_identifier="com.r10webcam.app",
    info_plist={
        "NSPrincipalClass": "NSApplication",
        "NSHighResolutionCapable": "True",
        "LSMinimumSystemVersion": "13.0",
        "NSLocalNetworkUsageDescription": (
            "O R10 Webcam precisa da rede local para falar com a Canon R10 via Wi-Fi (CCAPI)."
        ),
        "NSCameraUsageDescription": (
            "O R10 Webcam cria uma câmera virtual (via OBS) para Zoom/Meet/Teams."
        ),
    },
)
