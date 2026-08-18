"""Integração com Tavily para buscas web em tempo real.

Função pública: buscar_na_web(pergunta) -> dict
Retorna um dicionário com status e resultados.
"""
from __future__ import annotations
import os
from typing import Any, Dict, List


def buscar_na_web(pergunta: str, *, simulate: bool = False) -> Dict[str, Any]:
    """Realiza uma busca usando a biblioteca tavily-python.

    Requer a variável de ambiente TAVILY_API_KEY definida, a menos que simulate=True.
    Retorna um dicionário: {status: 'ok'|'error', results: [...]}.
    """
    if simulate:
        # Resposta simulada para testes locais
        sample = {
            "results": [
                {"url": "https://example.com/article-1", "content": f"Resumo simulado da pesquisa sobre: {pergunta}. Texto de exemplo 1."},
                {"url": "https://example.com/article-2", "content": f"Outro resultado simulado referente a: {pergunta}. Texto de exemplo 2."},
            ]
        }
        return {"status": "ok", "results": sample["results"]}

    try:
        from tavily import TavilyClient
    except Exception as e:
        return {"status": "error", "message": f"biblioteca tavily não instalada: {e}"}

    api_key = os.getenv("TAVILY_API_KEY")
    if not api_key:
        return {"status": "error", "message": "TAVILY_API_KEY não definida no ambiente"}

    client = TavilyClient(api_key)
    try:
        resp = client.search(query=pergunta, search_depth="advanced")
    except Exception as e:
        return {"status": "error", "message": str(e)}

    # Normalizar resposta: esperamos um dict com 'results' sendo lista
    if isinstance(resp, dict) and "results" in resp and isinstance(resp["results"], list):
        results = []
        for r in resp["results"]:
            url = r.get("url") if isinstance(r, dict) else None
            content = r.get("content") if isinstance(r, dict) else str(r)
            results.append({"url": url, "content": content})
        return {"status": "ok", "results": results}

    # Fallback: tentar serializar a resposta bruta
    return {"status": "ok", "raw": resp}
