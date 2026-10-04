"""Serviço de Memória de Longo Prazo utilizando Qdrant e Mem0 (Persistência em Disco)."""
from __future__ import annotations

import logging
import os
import threading
from pathlib import Path
from typing import Any, Optional

from app.core.exceptions import PersistenceError

try:
    from mem0 import Memory
except ImportError:
    Memory = None  # type: ignore

try:
    from strands_agents import tool
except ImportError:
    # Fallback defensivo para decorators de tool caso strands_agents não esteja instalado
    def tool(func: Any) -> Any:
        return func

logger = logging.getLogger(__name__)

# Define o diretório físico persistente para o Qdrant (Codespaces ou raiz do projeto local)
_base_dir = (
    Path("/workspaces/Jarvis-Mark-V")
    if Path("/workspaces/Jarvis-Mark-V").exists()
    else Path(__file__).resolve().parent.parent.parent
)
QDRANT_PATH = _base_dir / "data" / "qdrant_storage"
QDRANT_PATH.mkdir(parents=True, exist_ok=True)

# Bloqueio de concorrência para garantir thread-safety e inicialização tardia com cache
_memory_lock = threading.Lock()
_memory_instance: Optional[Any] = None


def _obter_configuracao_memoria() -> dict[str, Any]:
    """Retorna a configuração do Mem0 utilizando Qdrant local persistente."""
    api_key = os.getenv("GEMINI_API_KEY") or os.getenv("GOOGLE_API_KEY")

    config: dict[str, Any] = {
        "vector_store": {
            "provider": "qdrant",
            "config": {
                "path": str(QDRANT_PATH),
            },
        }
    }

    if api_key:
        config["llm"] = {
            "provider": "google",
            "config": {
                "model": "gemini-2.5-flash",
                "api_key": api_key,
            },
        }
        config["embedder"] = {
            "provider": "google",
            "config": {
                "model": "text-embedding-004",
                "api_key": api_key,
            },
        }
    return config


def _carregar_memoria() -> Any:
    """Carrega ou retorna a instância singleton de memória sob bloqueio de thread."""
    global _memory_instance
    if _memory_instance is None:
        with _memory_lock:
            if _memory_instance is None:
                if Memory is None:
                    logger.warning("Pacote 'mem0' não instalado. Operando em modo de cache local.")
                    return None

                try:
                    config = _obter_configuracao_memoria()
                    _memory_instance = Memory.from_config(config)
                    logger.info("Memória Qdrant inicializada com persistência em: %s", QDRANT_PATH)
                except Exception as exc:
                    logger.exception("Falha ao inicializar o Mem0 com Qdrant persistente: %s", exc)
                    return None
    return _memory_instance


@tool
def salvar_lembranca(user_id: str, texto_memoria: str) -> dict[str, Any]:
    """Salva um fato ou contexto importante na memória de longo prazo do usuário.

    Args:
        user_id: Identificador único do usuário (ex: 'isaac').
        texto_memoria: O fato ou instrução a ser lembrada pelo sistema.
    """
    if not user_id or not texto_memoria:
        return {"sucesso": False, "erro": "user_id e texto_memoria são obrigatórios."}

    try:
        mem = _carregar_memoria()
        if mem is not None:
            mem.add(texto_memoria, user_id=user_id)
            logger.info("Lembrança salva para o usuário '%s' na matriz vetorial.", user_id)
        return {"sucesso": True, "mensagem": "Lembrança gravada com sucesso na matriz vetorial."}
    except Exception as exc:
        logger.exception("Erro ao salvar lembrança: %s", exc)
        return {"sucesso": False, "erro": str(exc)}


@tool
def buscar_lembrancas(user_id: str, consulta: str) -> dict[str, Any]:
    """Busca lembranças contextuais relevantes na base de longo prazo.

    Args:
        user_id: Identificador único do usuário.
        consulta: Termo ou pergunta para recuperar o contexto armazenado.
    """
    if not user_id or not consulta:
        return {"sucesso": False, "erro": "user_id e consulta são obrigatórios."}

    try:
        mem = _carregar_memoria()
        if mem is not None:
            resultados = mem.search(consulta, user_id=user_id)
            return {"sucesso": True, "resultados": resultados}
        return {"sucesso": True, "resultados": []}
    except Exception as exc:
        logger.exception("Erro ao buscar lembranças: %s", exc)
        return {"sucesso": False, "erro": str(exc)}


class MemoryService:
    """Classe de serviço de memória encapsulando cache thread-safe e persistência Mem0/Qdrant."""

    def __init__(self) -> None:
        self._lock = _memory_lock
        self._cache: dict[str, Any] = {}

    def set_item(self, key: str, value: Any, user_id: str = "isaac") -> None:
        """Armazena um valor em cache e persiste na memória vetorial sob lock."""
        try:
            with self._lock:
                self._cache[key] = value

            if isinstance(value, str):
                salvar_lembranca(user_id=user_id, texto_memoria=f"{key}: {value}")
        except Exception as exc:
            logger.error("Erro ao definir item de memória: %s", exc)
            raise PersistenceError(f"Falha ao persistir item '{key}': {exc}") from exc

    def get_item(self, key: str, default: Any = None, user_id: str = "isaac") -> Any:
        """Recupera um valor do cache ou busca nas lembranças vetoriais sob lock."""
        try:
            with self._lock:
                if key in self._cache:
                    return self._cache[key]

            res = buscar_lembrancas(user_id=user_id, consulta=key)
            if res.get("sucesso") and res.get("resultados"):
                return res["resultados"]
            return default
        except Exception as exc:
            logger.error("Erro ao recuperar item de memória: %s", exc)
            raise PersistenceError(f"Falha ao ler item '{key}': {exc}") from exc

    def clear(self) -> None:
        """Limpa o cache em memória sob lock."""
        with self._lock:
            self._cache.clear()
            logger.info("Cache de memória limpo.")
