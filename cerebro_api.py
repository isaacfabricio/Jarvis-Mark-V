"""Servidor Central do J.A.R.V.I.S. Mark V (Versão Suprema + Multi-Team Security)."""
from __future__ import annotations

import logging
import os
from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from pydantic import BaseModel

from app.services.graph_service import JarvisGraphOrchestrator
from app.services.graph_rag_service import ProductionGraphRAG
from app.services.self_healing_service import diagnosticar_e_corrigir_codigo
from app.services.voice_service import VoiceEngine
from app.services.cyber_security_service import executar_auditoria_ciberseguranca
from app.services.strix_pentest_service import executar_pentest_strix
from app.services.multi_team_security_service import executar_analise_multiteam

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("JARVIS-Cerebro")

app = FastAPI(title="J.A.R.V.I.S. Mark V - Supremos + Multi-Team Ativo", version="10.0")

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

class ProductionGraphRagRequest(BaseModel):
    user_id: str = "isaac"
    entidade: str
    relacao: str
    detalhes: str

class HealingRequest(BaseModel):
    arquivo: str

class SecurityAuditRequest(BaseModel):
    dominio: str
    contexto: str

class StrixPentestRequest(BaseModel):
    alvo: str
    escopo: str = "OWASP Top 10"

class MultiTeamRequest(BaseModel):
    time: str
    contexto: str

@app.get("/api/health")
def health_check():
    return {"status": "online", "sistema": "J.A.R.V.I.S. Mark V com Matriz Multi-Team Ativa"}

@app.post("/api/comando")
def processar_comando(req: ComandoRequest):
    try:
        grafo = JarvisGraphOrchestrator(user_id=req.user_id)
        resposta = grafo.executar(req.prompt)
        return {"sucesso": True, "resposta": resposta}
    except Exception as exc:
        logger.exception("Erro crítico no processamento.")
        raise HTTPException(status_code=500, detail=str(exc)) from exc

@app.post("/api/security/multiteam")
def api_multiteam(req: MultiTeamRequest):
    try:
        return executar_analise_multiteam(req.time, req.contexto)
    except Exception as exc:
        raise HTTPException(status_code=500, detail=str(exc)) from exc

@app.post("/api/security/strix-pentest")
def api_strix_pentest(req: StrixPentestRequest):
    return executar_pentest_strix(req.alvo, req.escopo)

@app.post("/api/security/audit")
def api_security_audit(req: SecurityAuditRequest):
    return executar_auditoria_ciberseguranca(req.dominio, req.contexto)

@app.post("/api/graph-rag-prod")
def api_graph_rag_prod(req: ProductionGraphRagRequest):
    return ProductionGraphRAG.indexar_conhecimento(req.entidade, req.relacao, req.detalhes, req.user_id)

@app.post("/api/self-healing")
def api_self_healing(req: HealingRequest):
    return diagnosticar_e_corrigir_codigo(req.arquivo)

if os.path.exists("frontend"):
    app.mount("/", StaticFiles(directory="frontend", html=True), name="frontend")

if __name__ == "__main__":
    import uvicorn
    uvicorn.run("cerebro_api:app", host="0.0.0.0", port=8000, reload=True)
