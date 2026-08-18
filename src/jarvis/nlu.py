"""NLU leve que usa o LLM para interpretar comandos em linguagem natural.

Função interpret_command retorna uma estrutura simples (dicionário)
com a intent e parâmetros extraídos. No começo, o módulo usa o LLM
(abstrato) para análise. Posteriormente poderá haver um cache/local NLU.
"""
from __future__ import annotations
from typing import Dict, Any
import json

from .llm import call_llm, LLMError


def interpret_command(text: str) -> Dict[str, Any]:
    """Interpreta texto em linguagem natural e retorna um dicionário com intent.

    Exemplo de retorno:
    {
        "intent": "fetch_orders",
        "params": {"from": "2026-08-01", "to": "2026-08-18"}
    }

    Observação: a função usa o LLM para produzir JSON. Em produção, vale
    validar o JSON e cair em um NLU local caso a chamada falhe.
    """
    prompt = f"""
You are an assistant that extracts a single intent and parameters from a user's short command.
Return a JSON object with keys: intent (snake_case), params (object).
If you cannot determine intent, set intent to "unknown" and return an empty params object.
User command: "{text}"
"""

    try:
        resp = call_llm(prompt)
    except LLMError as e:
        # Fallback: tentar heurística simples
        return _heuristic_fallback(text)

    # Espera-se que resp seja JSON — tenta parse seguro
    try:
        parsed = json.loads(resp)
        if isinstance(parsed, dict) and "intent" in parsed:
            return parsed
    except Exception:
        # Se falhar, usar heurística local
        return _heuristic_fallback(text)

    return _heuristic_fallback(text)


def _heuristic_fallback(text: str) -> Dict[str, Any]:
    """Heurística simples caso não haja LLM disponível."""
    t = text.lower()
    if "pedido" in t or "pedidos" in t or "order" in t:
        return {"intent": "fetch_orders", "params": {}}
    if "produto" in t or "produtos" in t:
        return {"intent": "manage_products", "params": {}}
    if "planilha" in t or "excel" in t or "power query" in t:
        return {"intent": "generate_sheet", "params": {}}
    if "dashboard" in t or "power bi" in t:
        return {"intent": "build_dashboard", "params": {}}
    return {"intent": "unknown", "params": {}}
