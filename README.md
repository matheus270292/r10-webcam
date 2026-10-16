# R10 Webcam — Wi-Fi CCAPI (sem USB) · macOS Apple Silicon

MVP 100% wireless para Canon EOS R10 inspirado no EOS Webcam Utility PRO.
Versão atual: `1.1.0` (ver arquivo `VERSION` + `/api/health`).

## LINK público funcional (front + back, sem câmera — modo demo)

O back é Python (FastAPI+OpenCV) e não roda no Cloudflare Pages. Para ter um link visitável:

**Render (recomendado, grátis):**
1. Acesse `dashboard.render.com` → New → Web Service → conecte este repo
2. Runtime: **Docker** (usa o `Dockerfile` + `render.yaml` já inclusos)
3. Env: `DEMO=1` (vem por padrão — gera imagem sintética sem câmera)
4. Deploy → link `https://r10-webcam.onrender.com` (front completo + `/api/status`, `/preview.mjpg`, galeria)

**Local:** `pip install -r requirements.txt && uvicorn server:app --port 8000` → `http://127.0.0.1:8000` (com `DEMO=1` funciona sem câmera; com câmera real use `DEMO=0` + IP da R10).

## Para QUEM VAI USAR (caminho fácil — compartilhar este link)

**Baixar pronto:** vá na aba **Releases** do GitHub e baixe o `R10Webcam.dmg` mais novo.

1. Abra o `.dmg`, arraste `R10Webcam.app` para Applications
2. Botão-direito → Abrir (1ª vez — app sem assinatura Apple, normal)
3. Permita **rede local** quando o macOS pedir (para achar a R10)
4. O app abre `http://127.0.0.1:8000` sozinho → digite o **IP da R10** → Conectar
5. Clique **Iniciar webcam virtual** → no Zoom/Meet/Teams selecione **OBS Virtual Camera**

**Pré-requisitos (1x):**
- Mac Apple Silicon (M1/M2/M3/M4), macOS 13+
- OBS 30+ instalado ([obsproject.com](https://obsproject.com)) — abra 1x: Start Virtual Camera → Stop → feche
- CCAPI ativado **uma única vez** na R10 (ver `static/ativacao-ccapi.html`)
- R10 e Mac na **mesma rede Wi-Fi** (ideal 5GHz perto)

**Se o Zoom não enxergar:** abra o OBS → Start Virtual Camera → Stop → feche o OBS → Iniciar pelo app de novo.
**Se der erro ao abrir:** botão-direito → Abrir → Abrir mesmo assim. Log de erro em `r10webcam.log` ao lado do app.

## Para QUEM VAI PUBLICAR (gerar o .dmg compartilhável)

**Opção A — automático (recomendado):**
1. Suba esta pasta como raiz do repo no GitHub
2. Crie a release: `git tag v1.0.0 && git push origin v1.0.0`
3. O workflow `build-dmg-macos` gera o `.dmg` e publica em **Releases** sozinho
4. Ou manual: aba **Actions → build-dmg-macos → Run workflow** → baixe o artefato

**Opção B — no próprio Mac:** `./build-mac.sh` → gera `R10Webcam.dmg` local.

**Notas:** sem assinatura + notarização Apple (Developer ID pago) o Gatekeeper sempre avisa na 1ª vez — fora do escopo do MVP. Para distribuir sem aviso seria preciso assinar.

## O que faz
- Conecta na R10 via **Wi-Fi CCAPI** (IP da câmera), sem USB, sem EDSDK, sem hack
- Preview no browser (`/preview.mjpg`), saída **webcam virtual** (OBS Virtual Camera) para Zoom/Meet/Teams
- Foto local (`captures/`), disparo remoto, controle av/tv/iso/wb, ajustes fit/fill, flip, rotate, brilho/contraste, texto overlay

## Modo dev no Mac (sem .dmg)
1. Instale Python 3.11+ (python.org) e OBS 30+ (abra 1x: Start Virtual Camera → Stop → feche).
2. Copie esta pasta `r10-webcam/` para o Mac.
3. Ative o CCAPI **uma única vez** (ver `static/ativacao-ccapi.html`).
4. No terminal: `chmod +x run.sh && ./run.sh` → abre http://127.0.0.1:8000 sozinho
5. Digite o IP da R10 → Conectar → Iniciar webcam virtual → selecione "OBS Virtual Camera" no Zoom.

## Limites do Wi-Fi (honesto)
- ~15–25fps reais, latência 0,3–0,5s — ótimo p/ reunião, não p/ gaming.
- Use bateria cheia/dummy + 5GHz próximo. Auto-reconnect com backoff até 10s.
- Fase 2 (opcional): USB/EDSDK p/ mais fps; 1080p; watermark PNG; gravação; bateria no UI; blur de fundo.

## Dev aqui (Windows, sem câmera: valida sintaxe, não o stream)
`python -m py_compile server.py canon_wifi.py pipeline.py virtualcam.py launcher.py`
