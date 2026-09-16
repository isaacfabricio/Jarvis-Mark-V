"""Serviço Principal do Agente utilizando Strands Agents SDK."""
import os
import logging
import asyncio
from strands import Agent, tool
from strands.models.gemini import GeminiModel

# Importação dos serviços MCP
from app.services import db_service, browser_service, memory_service

logger = logging.getLogger(__name__)

# 1. Diretriz Rigorosa do Agente (Zero-Yapping)
ZERO_YAPPING_PROMPT = """
Você é o J.A.R.V.I.S. Mark V, um agente de operações de alta performance.

DIRETRIZES DE OTIMIZAÇÃO (ZERO-YAPPING):
1. EXECUÇÃO SILENCIOSA: É TERMINANTEMENTE PROIBIDO gerar textos explicativos ou introduções.
2. SAÍDA RESTRITA: Guarde seu processamento lógico no seu contexto interno.
3. ECONOMIA: Utilize as ferramentas à sua disposição imediatamente e devolva apenas o resultado final tangível.
"""

# 2. Definição das Ferramentas usando o Decorator nativo do Strands
@tool
def salvar_lembranca(fato: str) -> dict:
    """Salva uma informação no banco vetorial de longo prazo (Mem0).
    Args:
        fato: A informação importante a ser lembrada pelo sistema.
    """
    return memory_service.salvar_lembranca("isaac", fato)

@tool
def navegar_web(url: str, seletor_css: str = None) -> dict:
    """Abre um navegador headless para extrair e raspar conteúdo de uma URL.
    Args:
        url: A URL a ser visitada.
        seletor_css: Opcional. Seletor CSS específico para focar a extração.
    """
    return asyncio.run(browser_service.raspar_pagina_web(url, seletor_css))

@tool
def consultar_firebase(colecao: str, campo_filtro: str = None, valor_filtro: str = None) -> dict:
    """Consulta dados nativos do sistema no Firebase Firestore.
    Args:
        colecao: Nome da coleção do Firebase (ex: 'usuarios').
        campo_filtro: Opcional. Campo para realizar o filtro.
        valor_filtro: Opcional. Valor do filtro.
    """
    return db_service.consultar_banco_dados(colecao, campo_filtro, valor_filtro)

# 3. Orquestração do Agente Strands
def iniciar_agente():
    """Constrói o objeto do agente conectando o modelo, o prompt e as ferramentas."""
    api_key = os.getenv("GEMINI_API_KEY")
    model = (
        GeminiModel(
            client_args={"api_key": api_key},
            model_id=os.getenv("GEMINI_MODEL", "gemini-3.6-flash"),
        )
        if api_key
        else None
    )
    return Agent(
        model=model,
        name="JARVIS-Mark-V",
        system_prompt=ZERO_YAPPING_PROMPT,
        tools=[
            salvar_lembranca,
            navegar_web,
            consultar_firebase
        ]
    )

def executar_comando(prompt_usuario: str) -> str:
    """Ponto de entrada para conversar com o J.A.R.V.I.S."""
    jarvis = iniciar_agente()
    logger.info("Processando comando via Strands Agents...")
    
    resposta = jarvis(prompt_usuario)
    mensagem = getattr(resposta, "message", None)
    if isinstance(mensagem, dict):
        conteudo = mensagem.get("content", "")
        if isinstance(conteudo, list):
            textos = [
                bloco.get("text", "")
                for bloco in conteudo
                if isinstance(bloco, dict) and bloco.get("text")
            ]
            return "\n".join(textos)
        if isinstance(conteudo, str):
            return conteudo
    return str(resposta)
