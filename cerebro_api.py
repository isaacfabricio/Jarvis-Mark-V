"""Servidor Central do J.A.R.V.I.S. (FastAPI Backend + HUD Host)."""
from __future__ import annotations

import logging
import os
from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from pydantic import BaseModel

from app.services.claude_service import executar_comando
from app.services.memory_service import salvar_lembranca, buscar_lembrancas

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("JARVIS-Cerebro")

app = FastAPI(title="J.A.R.V.I.S. Mark V - Cerebro Central", version="5.0")

# Configuração de CORS para aceitar requisições da HUD
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


class ComandoRequest(BaseModel):
    prompt: str
    user_id: str = "isaac"


class MemoriaRequest(BaseModel):
    user_id: str = "isaac"
    texto: str


@app.get("/api/health")
def health_check():
    return {"status": "online", "sistema": "J.A.R.V.I.S. Mark V Core Ativo"}


@app.post("/api/comando")
def processar_comando(req: ComandoRequest):
    """Executa um comando através do núcleo cognitivo do agente."""
    try:
        resposta = executar_comando(req.prompt)
        return {"sucesso": True, "resposta": resposta}
    except Exception as exc:
        logger.exception("Erro ao processar comando via API.")
        raise HTTPException(status_code=500, detail=str(exc)) from exc


@app.post("/api/memoria/salvar")
def api_salvar_memoria(req: MemoriaRequest):
    """Adiciona um fato à memória de longo prazo."""
    resultado = salvar_lembranca(req.user_id, req.texto)
    if not resultado.get("sucesso"):
        raise HTTPException(status_code=400, detail=resultado.get("erro"))
    return resultado


@app.get("/api/memoria/buscar")
def api_buscar_memoria(user_id: str, q: str):
    """Consulta memórias persistidas do usuário."""
    resultado = buscar_lembrancas(user_id, q)
    if not resultado.get("sucesso"):
        raise HTTPException(status_code=400, detail=resultado.get("erro"))
    return resultado


# Monta os arquivos estáticos da HUD (caso a pasta frontend exista)
if os.path.exists("frontend"):
    app.mount("/", StaticFiles(directory="frontend", html=True), name="frontend")

if __name__ == "__main__":
    import uvicorn

    uvicorn.run("cerebro_api:app", host="0.0.0.0", port=8000, reload=True)