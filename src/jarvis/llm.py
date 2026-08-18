"""Abstração mínima para chamadas ao LLM (Gemini/Outro).

Este módulo fornece uma função call_llm(prompt) que, por enquanto,
é um stub que precisa da implementação concreta do provedor Gemini.
A razão de abstract é permitir trocar o provedor sem alterar o resto do código.

Como usar:
- Configure a variável de ambiente GEMINI_API_KEY
- Implementar a função _call_gemini_api com a forma de autenticação correta
  (o formato depende do método de acesso que você tem ao Gemini)
"""
from __future__ import annotations
import os
from typing import Any, Dict


class LLMError(RuntimeError):
    pass


def call_llm(prompt: str, *, model: str = "gemini") -> str:
    """Chama o LLM configurado e retorna a resposta em texto.

    Atualmente esta função verifica a existência da chave GEMINI_API_KEY
    e delega para a implementação do provedor. Se desejar usar outro provedor,
    adapte este módulo.
    """
    api_key = os.getenv("GEMINI_API_KEY")
    if not api_key:
        raise LLMError("GEMINI_API_KEY não encontrada no ambiente")

    # Implementação mínima usando a REST API do Google Generative Language
    # A função tenta usar o endpoint v1beta2 `:generateText` com a chave de API
    # passada em GEMINI_API_KEY. Se desejar usar outro adaptador (biblioteca
    # oficial), substitua `_call_gemini_api` abaixo.
    try:
        return _call_gemini_api(prompt, api_key, model=model)
    except Exception as e:
        raise LLMError(f"Erro ao chamar LLM: {e}")


def _call_gemini_api(prompt: str, api_key: str, model: str = "gemini") -> str:
    """Chama o endpoint REST da Google Generative Language usando requests.

    Observações:
    - Usa `models/text-bison-001` por padrão, mapeado do alias 'gemini'.
    - A API aceita o parâmetro `key` na query string quando se tem uma API key.
    - A resposta esperada contém `candidates` com `content` ou `output`.

    Substitua ou estenda esta função caso seu acesso ao Gemini use outro
    endpoint ou método de autenticação (p.ex. OAuth/service account).
    """
    import requests

    # Mapeamento simples de alias para nome do modelo na API
    model_map = {
        "gemini": "models/text-bison-001",
        "text-bison": "models/text-bison-001",
    }
    model_name = model_map.get(model, model)

    endpoint = f"https://generativelanguage.googleapis.com/v1beta2/{model_name}:generateText"
    params = {"key": api_key}
    payload = {"prompt": {"text": prompt}}

    resp = requests.post(endpoint, params=params, json=payload, timeout=30)
    try:
        resp.raise_for_status()
    except Exception:
        # For debug: include response text (trunc) in the exception
        text = resp.text[:1000]
        raise RuntimeError(f"LLM request failed: {resp.status_code} {text}")

    j = resp.json()
    # Tentar extrair o texto de forma robusta
    if "candidates" in j and isinstance(j["candidates"], list) and j["candidates"]:
        return j["candidates"][0].get("content", "")
    # Alguns endpoints retornam `output_text` ou `result` — tentar alternativas
    if "output" in j and isinstance(j["output"], dict):
        return j["output"].get("text", "")
    # Fallback: stringify completo
    return j.get("completion", j.get("response", str(j)))



# Exemplo de assinatura para um adaptador (não implementado):
# def _call_gemini_api(prompt: str, api_key: str) -> str:
#     headers = {"Authorization": f"Bearer {api_key}"}
#     payload = {"prompt": prompt, "max_tokens": 512}
#     resp = requests.post("https://api-gemini.example/v1/complete", json=payload, headers=headers)
#     resp.raise_for_status()
#     return resp.json()["text"]
