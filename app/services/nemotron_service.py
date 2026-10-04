"""Serviço de Integração com o NVIDIA Nemotron (Raciocínio de Fronteira)."""
from __future__ import annotations

import logging
import os
from typing import Any
import requests

try:
    from strands_agents import tool
except ImportError:
    # Fallback defensivo para decorators de tool caso strands_agents não esteja instalado
    def tool(func: Any) -> Any:
        return func

logger = logging.getLogger(__name__)

# Configuração da API do Nemotron (suporta NVIDIA NIM oficial ou OpenRouter)
NEMOTRON_API_KEY = os.getenv("NEMOTRON_API_KEY", "").strip()

# Se a chave for nvapi-..., o endpoint padrão é o NVIDIA NIM oficial
_default_url = (
    "https://integrate.api.nvidia.com/v1/chat/completions"
    if NEMOTRON_API_KEY.startswith("nvapi-")
    else "https://openrouter.ai/api/v1/chat/completions"
)
NEMOTRON_API_URL = os.getenv("NEMOTRON_API_URL", _default_url)

_default_model = (
    "nvidia/llama-3.1-nemotron-70b-instruct"
    if NEMOTRON_API_KEY.startswith("nvapi-")
    else "nvidia/nemotron-3-ultra-550b-a55b:free"
)
NEMOTRON_MODEL = os.getenv("NEMOTRON_MODEL", _default_model)


class NemotronUltraEngine:
    """Motor Cognitivo de Alta Precisão baseado no NVIDIA Nemotron."""

    @staticmethod
    def raciocinar(prompt_sistema: str, prompt_usuario: str) -> str:
        """Envia uma solicitação de raciocínio complexo para o Nemotron."""
        api_key = os.getenv("NEMOTRON_API_KEY", "").strip() or NEMOTRON_API_KEY
        if not api_key:
            logger.warning("[NEMOTRON] NEMOTRON_API_KEY não configurada. Usando fallback de simulação local.")
            return f"[Nemotron 3 Ultra - Modo Simulação Avançada]: Processado com sucesso para -> '{prompt_usuario[:60]}...'"

        headers = {
            "Authorization": f"Bearer {api_key}",
            "Content-Type": "application/json",
            "HTTP-Referer": "https://github.com/isaacfabricio/Jarvis-Mark-V",
            "X-Title": "J.A.R.V.I.S. Mark V",
        }

        payload = {
            "model": NEMOTRON_MODEL,
            "messages": [
                {"role": "system", "content": prompt_sistema},
                {"role": "user", "content": prompt_usuario},
            ],
            "temperature": 0.2,
            "max_tokens": 2048,
        }

        try:
            response = requests.post(NEMOTRON_API_URL, json=payload, headers=headers, timeout=45)
            response.raise_for_status()
            data = response.json()
            return data["choices"][0]["message"]["content"]
        except Exception as exc:
            logger.exception("Erro ao comunicar com a API do Nemotron.")
            return f"Erro crítico na inferência do Nemotron Ultra: {exc}"


@tool
def executar_raciocinio_nemotron(prompt_complexo: str) -> str:
    """Executa um planejamento estratégico ou análise profunda usando o Nemotron 3 Ultra.

    Args:
        prompt_complexo: A tarefa de alta complexidade, auditoria ou código a ser analisada.
    """
    sistema_prompt = (
        "Você é o núcleo de raciocínio estratégico supremo do J.A.R.V.I.S. Mark V. "
        "Sua função é realizar análises profundas, planejamento de longo prazo e validações de segurança "
        "com precisão cirúrgica."
    )
    return NemotronUltraEngine.raciocinar(sistema_prompt, prompt_complexo)
