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

    # Placeholder: implementar wrapper real para Gemini ou outro provedor.
    # Exemplo:
    # if model == "gemini":
    #     return _call_gemini_api(prompt, api_key)
    # elif model == "openai":
    #     return _call_openai_api(prompt, api_key)

    # Por ora, falhar com mensagem clara para que o usuário implemente o adaptador.
    raise LLMError(
        "Cliente LLM não implementado: adicione um adaptador para Gemini no arquivo jarvis/llm.py"
    )


# Exemplo de assinatura para um adaptador (não implementado):
# def _call_gemini_api(prompt: str, api_key: str) -> str:
#     headers = {"Authorization": f"Bearer {api_key}"}
#     payload = {"prompt": prompt, "max_tokens": 512}
#     resp = requests.post("https://api-gemini.example/v1/complete", json=payload, headers=headers)
#     resp.raise_for_status()
#     return resp.json()["text"]
