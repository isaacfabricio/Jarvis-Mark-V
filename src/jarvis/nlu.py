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
    # Prompt em português que pede JSON estrito e exemplos. Força saída apenas em JSON.
    prompt = f"""
Você é um assistente que extrai uma única intent e parâmetros de um comando curto do usuário.
Responda EXCLUSIVAMENTE com um objeto JSON válido. Não inclua explicações.
O objeto deve ter as chaves: "intent" (snake_case) e "params" (objeto).
Campos possíveis para intent: fetch_orders, manage_products, generate_sheet, build_dashboard, web_search, unknown.
Se não conseguir determinar a intenção, retorne: {"intent": "unknown", "params": {}}.
Se a frase contém um verbo de busca como "buscar", "pesquisar", "procurar", prefira a intent "web_search" e coloque a query no params.query.
Exemplos de saída (JSON somente):
{"intent": "fetch_orders", "params": {"from":"2026-08-01","to":"2026-08-18"}}
{"intent": "web_search", "params": {"query":"preço do produto X"}}

User command: "{text}"
"""

    try:
        resp = call_llm(prompt)
    except LLMError:
        # Fallback: tentar heurística simples
        parsed = _heuristic_fallback(text)
        return parsed

    # Espera-se que resp seja JSON — tenta parse seguro
    parsed = None
    try:
        parsed = json.loads(resp)
    except Exception:
        # Se falhar, usar heurística local
        parsed = _heuristic_fallback(text)

    # Normalizar e validar o dicionário de retorno
    if not isinstance(parsed, dict):
        parsed = _heuristic_fallback(text)

    intent = parsed.get("intent") if isinstance(parsed, dict) else None
    params = parsed.get("params") if isinstance(parsed, dict) else {}

    # Se o LLM sugeriu uma intent inválida, usar fallback
    valid_intents = {"fetch_orders", "manage_products", "generate_sheet", "build_dashboard", "web_search", "unknown"}
    if intent not in valid_intents:
        parsed = _heuristic_fallback(text)
        intent = parsed.get("intent")
        params = parsed.get("params")

    # Regra adicional: se o usuário usou verbo de busca e intent não é web_search, sobrescrever
    t_lower = text.lower()
    if any(k in t_lower for k in ("buscar", "pesquisar", "pesquisa", "procurar", "pesquise")) and intent != "web_search":
        params = params or {}
        # se não houver query explícita, use o texto completo como query
        if not params.get("query"):
            params["query"] = text
        return {"intent": "web_search", "params": params}

    return {"intent": intent, "params": params}


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
    # Heurística para busca web
    if any(k in t for k in ("buscar", "pesquisar", "pesquisa", "procurar", "pesquise", "buscar na web", "pesquise na web")):
        # tenta extrair a parte após o verbo (ex.: "buscar na web preço do produto x")
        # simplificação: enviar a frase completa como query
        return {"intent": "web_search", "params": {"query": text}}
    return {"intent": "unknown", "params": {}}
