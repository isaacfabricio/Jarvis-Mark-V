#!/bin/bash

echo "======================================================"
echo "  VERIFICANDO CONFIGURACOES DO SISTEMA JARVIS..."
echo "======================================================"

if [ ! -f ".env" ]; then
    echo "[AVISO] Arquivo .env nao encontrado. Gerando padrao..."
    echo "GEMINI_API_KEY=sua_chave_aqui" > .env
    python3 -c "from cryptography.fernet import Fernet; print('VAULT_KEY=' + Fernet.generate_key().decode())" >> .env
    echo "JARVIS_TOKEN=token_padrao_seguro" >> .env
    echo "WEATHER_API_KEY=" >> .env
fi

echo ""
echo "[1/2] Ativando ambiente virtual..."
source venv/bin/activate

echo "[2/2] Iniciando o Cerebro Central e HUD (FastAPI - Porta 8000)..."
python cerebro_api.py &

echo ""
echo "======================================================"
echo "  SISTEMA J.A.R.V.I.S. DISPARADO COM SUCESSO!"
echo "======================================================"
echo " - Aceda ao HUD via aba Ports do Codespaces (Porta 8000)"
echo ""
