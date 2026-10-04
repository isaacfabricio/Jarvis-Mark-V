"""Serviço de Graph RAG em Produção com Persistência Local e Mapeamento de Entidades."""
from __future__ import annotations

import json
import logging
from pathlib import Path
from typing import Any, Dict

try:
    from strands_agents import tool
except ImportError:
    def tool(func: Any) -> Any:
        return func

from app.services.memory_service import salvar_lembranca

logger = logging.getLogger(__name__)

# Diretório para persistência do Graph RAG em disco (Codespaces ou Local)
_base_dir = (
    Path("/workspaces/Jarvis-Mark-V")
    if Path("/workspaces/Jarvis-Mark-V").exists()
    else Path(__file__).resolve().parent.parent.parent
)
GRAPH_DB_PATH = _base_dir / "data" / "graph_rag_db.json"
GRAPH_DB_PATH.parent.mkdir(parents=True, exist_ok=True)


class ProductionGraphRAG:
    """Gerenciador de Base de Conhecimento Baseada em Grafos Persistidos."""

    @staticmethod
    def _carregar_banco() -> Dict[str, Any]:
        if GRAPH_DB_PATH.exists():
            try:
                with open(GRAPH_DB_PATH, "r", encoding="utf-8") as f:
                    return json.load(f)
            except Exception:
                return {"nos": {}, "conexoes": []}
        return {"nos": {}, "conexoes": []}

    @staticmethod
    def _salvar_banco(dados: Dict[str, Any]) -> None:
        with open(GRAPH_DB_PATH, "w", encoding="utf-8") as f:
            json.dump(dados, f, ensure_ascii=False, indent=2)

    @classmethod
    def indexar_conhecimento(
        cls, entidade: str, relacao: str, detalhes: str, user_id: str = "isaac"
    ) -> dict[str, Any]:
        """Indexa uma entidade e suas conexões lógicas no banco Graph RAG."""
        db = cls._carregar_banco()

        if entidade not in db["nos"]:
            db["nos"][entidade] = []

        db["nos"][entidade].append({"relacao": relacao, "detalhes": detalhes})
        db["conexoes"].append({"de": entidade, "para": relacao, "info": detalhes})

        cls._salvar_banco(db)

        # Sincroniza também com o Qdrant/Mem0 para redundância vetorial
        payload_vetor = f"[GraphRAG Prod] Entidade: {entidade} | Relação: {relacao} | Detalhes: {detalhes}"
        salvar_lembranca(user_id, payload_vetor)

        logger.info("[GRAPH RAG] Entidade '%s' indexada com sucesso.", entidade)
        return {"sucesso": True, "total_nos": len(db["nos"]), "entidade": entidade}


@tool
def indexar_producao_graph_rag(
    entidade: str, relacao: str, detalhes: str, user_id: str = "isaac"
) -> dict[str, Any]:
    """Indexa dados complexos na matriz Graph RAG persistente do J.A.R.V.I.S.

    Args:
        entidade: O conceito principal ou componente (ex: 'Arquitetura_Codespaces', 'Regras_AVSEC').
        relacao: A conexão lógica ou dependência.
        detalhes: Contexto descritivo aprofundado.
        user_id: Identificador do operador.
    """
    return ProductionGraphRAG.indexar_conhecimento(entidade, relacao, detalhes, user_id)
