#!/bin/bash
# Gera R10Webcam.dmg no Mac (rode NO Mac alvo/dev, não no Windows).
# Pré-req: Python 3.11+ e OBS 30+ instalados. Xcode CLT: xcode-select --install
set -e
cd "$(dirname "$0")"

PY=python3
$PY -m venv .build-venv
source .build-venv/bin/activate
pip install -q --upgrade pip
pip install -q -r requirements.txt pyinstaller

# Limpa builds anteriores
rm -rf build dist R10Webcam.dmg

pyinstaller r10webcam.spec

# Monta o .dmg com link para /Applications (hdiutil nativo do macOS)
STAGE="dmg-stage"
rm -rf "$STAGE" && mkdir -p "$STAGE"
cp -R "dist/R10Webcam.app" "$STAGE/"
ln -s /Applications "$STAGE/Applications"
cat > "$STAGE/LEIA-ME.txt" <<'EOF'
R10 Webcam — Canon R10 via Wi-Fi (sem USB)
1. Arraste R10Webcam.app para Applications.
2. Abra o app (botão direito > Abrir na 1ª vez — app não assinado).
3. Permita "rede local" quando o macOS pedir.
4. Abra http://127.0.0.1:8000 no navegador e digite o IP da R10.
Guia de ativação CCAPI: dentro do app em static/ativacao-ccapi.html
ou http://127.0.0.1:8000/static/ativacao-ccapi.html com o app rodando.
EOF

hdiutil create -volname "R10Webcam" -srcfolder "$STAGE" -ov -format UDZO R10Webcam.dmg
rm -rf "$STAGE"
echo "OK: $(pwd)/R10Webcam.dmg"
