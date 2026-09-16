"""Conector de catálogo de e-commerce.

O repositório não inclui credenciais nem um adaptador de loja no momento.
Este módulo fornece uma resposta explícita e serializável para que o servidor
continue funcional sem inventar resultados de catálogo.
"""

from __future__ import annotations

from typing import Any


def buscar_dados_catalogo_ecommerce(
    plataforma: str = "shein", termo: str = "camiseta"
) -> dict[str, Any]:
    """Retorna o estado do conector sem simular produtos externos."""

    return {
        "status": "not_configured",
        "platform": plataforma,
        "query": termo,
        "items": [],
        "message": (
            "O conector de catálogo ainda não está configurado para esta "
            "plataforma."
        ),
    }
