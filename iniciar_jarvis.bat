@echo off
title J.A.R.V.I.S. Mark V - Central System Launcher
color 0B
cd /d C:\Users\tropa\OneDrive\Documentos\JARVIS

echo ======================================================
echo    VERIFICANDO CONFIGURACOES DO SISTEMA JARVIS...
echo ======================================================

if not exist ".env" (
    echo [AVISO] Arquivo .env nao encontrado. Gerando padrao...
    echo GEMINI_API_KEY=sua_chave_aqui > .env
    python -c "from cryptography.fernet import Fernet; print('VAULT_KEY=' + Fernet.generate_key().decode())" >> .env
    echo JARVIS_TOKEN=token_padrao_seguro >> .env
    echo WEATHER_API_KEY= >> .env
)

echo.
echo [1/3] Iniciando o Cerebro Central (FastAPI - Porta 8000)...
start "JARVIS - Cerebro Central" cmd /k "cd /d C:\Users\tropa\OneDrive\Documentos\JARVIS && call .venv\Scripts\activate.bat && python cerebro_api.py"

echo [2/3] Iniciando o Agente Windows (Microfone, TTS e Telemetria)...
start "JARVIS - Agente Windows" cmd /k "cd /d C:\Users\tropa\OneDrive\Documentos\JARVIS && call .venv\Scripts\activate.bat && python agente_windows.py"

echo [3/3] Iniciando a HUD Holografica (Node.js - Porta 3000)...
start "JARVIS - HUD Holografica" cmd /k "cd /d C:\Users\tropa\OneDrive\Documentos\JARVIS\jarvis_hologram_ui && set NODE_ENV=development && set OAUTH_SERVER_URL=https://api.manus.im && pnpm exec tsx watch server/_core/index.ts"

echo.
echo ======================================================
echo  SISTEMA J.A.R.V.I.S. DISPARADO COM SUCESSO!
echo ======================================================
echo - Cerebro: http://localhost:8000
echo - HUD Web: http://localhost:3000
echo.
pause
