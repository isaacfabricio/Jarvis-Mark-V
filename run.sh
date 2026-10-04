#!/bin/bash

echo "======================================================"
echo "  INICIANDO O SISTEMA J.A.R.V.I.S. MARK V..."
echo "======================================================"

if [ ! -f ".env" ]; then
    echo "[AVISO] Arquivo .env nao encontrado. Gerando padrao..."
    echo "GEMINI_API_KEY=" > .env
    echo "NEMOTRON_API_KEY=" >> .env
    echo "GROQ_API_KEY=" >> .env
fi

echo ""
echo "[1/2] Ativando ambiente virtual..."
if [ ! -d "venv" ]; then
    python3 -m venv venv
fi
source venv/bin/activate

echo "[instalando dependências essenciais...]"
pip install --quiet fastapi uvicorn requests pydantic strands-agents qdrant-client mem0ai cryptography

echo "[2/2] Iniciando o Cerebro Central e HUD Holográfica (FastAPI - Porta 8000)..."
python cerebro_api.py &

echo ""
echo "======================================================"
echo "  J.A.R.V.I.S. DISPARADO COM SUCESSO!"
echo "======================================================"
echo " - Acesse via aba Ports do Codespaces (Porta 8000)"
echo ""
