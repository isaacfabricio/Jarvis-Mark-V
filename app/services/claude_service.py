from __future__ import annotations

"""Serviço cognitivo para execução de comandos através do modelo Claude / LLM Core."""

import asyncio
import logging
import os
from typing import Any

from app.services.llm_service import LLMService

logger = logging.getLogger(__name__)

# Fallback para LLMService interno
_llm_service = LLMService()


def executar_comando(prompt: str) -> str:
    """Executa um comando através do núcleo cognitivo do agente J.A.R.V.I.S.

    Args:
        prompt: Instrução ou pergunta enviada pelo usuário.

    Returns:
        str: Resposta textual processada pelo modelo.
    """
    if not prompt or not prompt.strip():
        return "Comando vazio recebido, Senhor."

    anthropic_api_key = os.getenv("ANTHROPIC_API_KEY")

    # Tentativa de uso via Anthropic SDK direto se configurado
    if anthropic_api_key:
        try:
            import anthropic  # type: ignore

            client = anthropic.Anthropic(api_key=anthropic_api_key)
            message = client.messages.create(
                model=os.getenv("CLAUDE_MODEL", "claude-3-7-sonnet-20250219"),
                max_tokens=1024,
                messages=[{"role": "user", "content": prompt}],
            )
            # Extrai o texto do primeiro bloco de conteúdo
            if message.content and hasattr(message.content[0], "text"):
                return message.content[0].text
        except Exception as exc:
            logger.warning("Falha ao consultar Anthropic direto, acionando fallback LLM: %s", exc)

    # Fallback transparente para o LLMService (Gemini) do J.A.R.V.I.S.
    try:
        try:
            loop = asyncio.get_event_loop()
        except RuntimeError:
            loop = asyncio.new_event_loop()
            asyncio.set_event_loop(loop)

        if loop.is_running():
            # Executado dentro de contexto já assíncrono (FastAPI worker)
            import concurrent.futures

            with concurrent.futures.ThreadPoolExecutor(max_workers=1) as pool:
                future = pool.submit(asyncio.run, _llm_service.generate_text(prompt))
                return future.result()
        else:
            return loop.run_until_complete(_llm_service.generate_text(prompt))

    except Exception as exc:
        logger.exception("Falha crítica ao executar comando cognitivo: %s", exc)
        return f"Senhor, houve uma instabilidade momentânea nos circuitos neurais: {exc}"
