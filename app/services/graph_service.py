"""Serviço de Orquestração Cognitiva Integrado ao Nemotron 3 Ultra e Grafos."""
from __future__ import annotations

import logging
from typing import Any, List, TypedDict

try:
    from strands_agents import tool
except ImportError:
    # Fallback defensivo para decorators de tool caso strands_agents não esteja instalado
    def tool(func: Any) -> Any:
        return func

from app.services.memory_service import buscar_lembrancas, salvar_lembranca
from app.services.nemotron_service import NemotronUltraEngine

logger = logging.getLogger(__name__)


class JarvisState(TypedDict):
    """Estado do pipeline cognitivo de grafos."""

    user_id: str
    prompt: str
    contexto_memoria: List[Any]
    resposta_final: str
    status: str


class JarvisGraphOrchestrator:
    """Orquestrador Avançado guiado pelo Nemotron e Grafos de Estados."""

    def __init__(self, user_id: str = "isaac") -> None:
        self.user_id = user_id

    def no_recuperar_contexto(self, state: JarvisState) -> JarvisState:
        """Nó 1: Recupera histórico e contexto vetorial do Qdrant/Mem0."""
        logger.info("[GRAFO/NEMOTRON] Executando Nó: Recuperação de Contexto Vetorial")
        res = buscar_lembrancas(state["user_id"], state["prompt"])
        if res.get("sucesso"):
            state["contexto_memoria"] = res.get("resultados", [])
        else:
            state["contexto_memoria"] = []
        state["status"] = "contexto_obtido"
        return state

    def no_raciocinio_mestre(self, state: JarvisState) -> JarvisState:
        """Nó 2: Invocação do Nemotron para planejamento e tomada de decisão estratégica."""
        logger.info("[GRAFO/NEMOTRON] Executando Nó: Raciocínio de Fronteira (Nemotron Ultra)")

        sistema = (
            "Você é o J.A.R.V.I.S. Mark V, um assistente de inteligência artificial de nível corporativo e militar. "
            "Utilize o contexto fornecido para estruturar uma resposta técnica, precisa e acionável."
        )

        prompt_enriquecido = (
            f"Histórico e Contexto da Memória de Longo Prazo: {state['contexto_memoria']}\n\n"
            f"Solicitação Atual do Operador: {state['prompt']}"
        )

        resposta_nemotron = NemotronUltraEngine.raciocinar(sistema, prompt_enriquecido)
        state["resposta_final"] = resposta_nemotron
        state["status"] = "concluido"

        # Auto-aprendizagem: Grava o comando e a resposta na matriz de memória
        salvar_lembranca(state["user_id"], f"Comando: {state['prompt']} | Resposta Nemotron: {resposta_nemotron[:150]}")
        return state

    def executar(self, prompt: str) -> str:
        """Executa o pipeline completo acoplando Memória, Grafos e Nemotron."""
        state: JarvisState = {
            "user_id": self.user_id,
            "prompt": prompt,
            "contexto_memoria": [],
            "resposta_final": "",
            "status": "iniciado",
        }

        state = self.no_recuperar_contexto(state)
        state = self.no_raciocinio_mestre(state)

        return state["resposta_final"]


@tool
def executar_fluxo_grafo_nemotron(prompt: str) -> str:
    """Executa o ciclo cognitivo completo utilizando o motor de grafos encabeçado pelo Nemotron 3 Ultra.

    Args:
        prompt: A instrução ou pergunta complexa para o sistema.
    """
    grafo = JarvisGraphOrchestrator()
    return grafo.executar(prompt)
