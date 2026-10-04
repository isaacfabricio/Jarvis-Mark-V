"""Serviço de Auto-Cura e Diagnóstico de Código (Self-Healing) para o J.A.R.V.I.S."""
from __future__ import annotations

import ast
import logging
from pathlib import Path
from typing import Any

from app.services.nemotron_service import NemotronUltraEngine

logger = logging.getLogger(__name__)


def diagnosticar_e_corrigir_codigo(caminho_arquivo: str) -> dict[str, Any]:
    """Realiza auto-diagnóstico estático e análise de integridade em arquivos Python do sistema.

    Args:
        caminho_arquivo: Caminho relativo ou absoluto do arquivo a ser inspecionado.

    Returns:
        dict[str, Any]: Diagnóstico do estado do arquivo e correções propostas.
    """
    logger.info("[SELF-HEALING] Iniciando auditoria de código no arquivo: %s", caminho_arquivo)
    alvo = Path(caminho_arquivo)

    if not alvo.exists():
        logger.warning("[SELF-HEALING] Arquivo '%s' não encontrado.", caminho_arquivo)
        return {
            "status": "erro",
            "arquivo": caminho_arquivo,
            "mensagem": f"Arquivo '{caminho_arquivo}' não localizado na árvore do projeto.",
        }

    try:
        conteudo = alvo.read_text(encoding="utf-8")
        # Análise sintática AST (Abstract Syntax Tree)
        ast.parse(conteudo, filename=str(alvo))
        logger.info("[SELF-HEALING] Código de '%s' validado sem erros de sintaxe.", caminho_arquivo)
        return {
            "status": "integro",
            "arquivo": caminho_arquivo,
            "mensagem": "Sintaxe Python íntegra e aprovada nos testes de AST.",
        }
    except SyntaxError as err:
        logger.error("[SELF-HEALING] Falha de sintaxe em '%s': %s", caminho_arquivo, err)
        prompt_cura = (
            f"O arquivo {caminho_arquivo} apresentou a seguinte falha de sintaxe:\n"
            f"Linha {err.lineno}: {err.msg}\n"
            f"Texto: {err.text}\n"
            "Proponha a correção técnica imediata."
        )
        diagnostico_ia = NemotronUltraEngine.raciocinar(
            "Você é o especialista de Self-Healing e correção de código do J.A.R.V.I.S.",
            prompt_cura,
        )
        return {
            "status": "corrigindo",
            "arquivo": caminho_arquivo,
            "erro_detectado": str(err),
            "diagnostico_ia": diagnostico_ia,
            "mensagem": f"Erro de sintaxe detectado na linha {err.lineno}. Plano de cura elaborado.",
        }
    except Exception as exc:
        logger.exception("[SELF-HEALING] Erro inesperado durante diagnóstico de '%s'", caminho_arquivo)
        return {
            "status": "erro",
            "arquivo": caminho_arquivo,
            "mensagem": f"Falha na leitura ou auditoria do arquivo: {exc}",
        }
