#!/bin/bash
# R10 Webcam — instalador/executor 1-clique para macOS (Apple Silicon).
# Uso: duplo-clique (via Terminal) ou ./run.sh
set -e
cd "$(dirname "$0")"

echo "=== R10 Webcam v$(cat VERSION 2>/dev/null || echo '?') ==="

# 1) Checa Python 3.11+
if ! command -v python3 >/dev/null 2>&1; then
  echo "ERRO: instale Python 3.11+ em https://www.python.org/downloads/"
  echo "Depois rode ./run.sh de novo."
  exit 1
fi
PYVER=$(python3 -c 'import sys; print(f"{sys.version_info.major}.{sys.version_info.minor}")')
echo "Python $PYVER OK"

# 2) venv + deps
if [ ! -d .venv ]; then python3 -m venv .venv; fi
source .venv/bin/activate
pip install -q --upgrade pip
pip install -q -r requirements.txt

# 3) Aviso OBS (não trava se faltar — só avisa)
if [ ! -d "/Applications/OBS.app" ]; then
  echo "AVISO: OBS não encontrado em /Applications/OBS.app"
  echo "Para usar no Zoom/Meet/Teams, instale o OBS 30+ em https://obsproject.com"
  echo "Abra o OBS 1x: Start Virtual Camera -> Stop -> feche. Depois volte aqui."
fi

# 4) Abre o navegador e sobe o servidor
(sleep 1.5; open "http://127.0.0.1:8000") &
echo "Abrindo http://127.0.0.1:8000 ..."
exec uvicorn server:app --host 127.0.0.1 --port 8000
