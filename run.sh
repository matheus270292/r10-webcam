#!/bin/bash
# Uso no Mac alvo: ./run.sh  (abre http://localhost:8000)
set -e
cd "$(dirname "$0")"
if [ ! -d .venv ]; then python3 -m venv .venv; fi
source .venv/bin/activate
pip install -q -r requirements.txt
exec uvicorn server:app --host 127.0.0.1 --port 8000
