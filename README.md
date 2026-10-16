# R10 Webcam — Wi-Fi CCAPI (sem USB) · Win + Mac

MVP 100% wireless para Canon EOS R10 inspirado no EOS Webcam Utility PRO.

## O que faz
- Conecta na R10 via **Wi-Fi CCAPI** (IP da câmera), sem USB, sem EDSDK, sem hack
- Preview no browser (`/preview.mjpg`), saída **webcam virtual** (OBS Virtual Camera) para Zoom/Meet/Teams
- Foto local (`captures/`), disparo remoto, controle av/tv/iso/wb, ajustes fit/fill, flip, rotate, brilho/contraste, texto overlay

## Distribuição em .dmg (macOS)

**Opção A — automático (recomendado, sem Mac em mãos):**
1. Suba o conteúdo desta pasta como raiz de um repo no GitHub (junto da pasta `.github/` que está um nível acima).
2. Aba **Actions → build-dmg-macos → Run workflow** → baixe o artefato `R10Webcam-macOS-arm64` (o `.dmg`).
3. No Mac: abra o `.dmg`, arraste para Applications, botão-direito → Abrir (1ª vez, app sem assinatura Apple).

**Opção B — no próprio Mac:** `./build-mac.sh` (usa `hdiutil` nativo) → gera `R10Webcam.dmg` local.

**Notas:** o app abre `http://127.0.0.1:8000` sozinho e pede permissão de *rede local* (para achar a R10). Para distribuir sem o aviso do Gatekeeper seria preciso assinatura + notarização Apple (Developer ID pago) — fora do escopo do MVP.

## No Mac alvo (modo dev, sem .dmg)
1. Instale Python 3.11+ (python.org) e OBS 30+ (abra 1x: Start Virtual Camera → Stop → feche).
2. Copie esta pasta `r10-webcam/` para o Mac.
3. Ative o CCAPI **uma única vez** (ver `static/ativacao-ccapi.html`).
4. No terminal: `chmod +x run.sh && ./run.sh` → abra http://localhost:8000
5. Digite o IP da R10 → Conectar → Iniciar webcam virtual → selecione "OBS Virtual Camera" no Zoom.

## Limites do Wi-Fi (honesto)
- ~15–25fps reais, latência 0,3–0,5s — ótimo p/ reunião, não p/ gaming.
- Use bateria cheia/dummy + 5GHz próximo. Auto-reconnect com backoff até 10s.
- Fase 2 (opcional): USB/EDSDK p/ mais fps; 1080p; watermark PNG; gravação; bateria no UI; blur de fundo.

## Dev aqui (Windows, sem câmera: valida sintaxe, não o stream)
`py -m py_compile server.py canon_wifi.py pipeline.py virtualcam.py`
