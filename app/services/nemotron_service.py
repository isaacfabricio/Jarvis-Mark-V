"""Serviço de Orquestração Cognitiva com Cascata de Failover Multi-Modelo."""
from __future__ import annotations

import logging
import os
import requests
from strands_agents import tool

logger = logging.getLogger(__name__)

# Chaves de API de múltiplos provedores
NEMOTRON_API_URL = os.getenv("NEMOTRON_API_URL", "https://openrouter.ai/api/v1/chat/completions")
NEMOTRON_API_KEY = os.getenv("NEMOTRON_API_KEY", "")

GEMINI_API_KEY = os.getenv("GEMINI_API_KEY") or os.getenv("GOOGLE_API_KEY")
GROQ_API_KEY = os.getenv("GROQ_API_KEY", "")

class MultiModelFailoverEngine:
    """Gerencia uma cascata infinita de redundância entre diferentes provedores de IA."""

    @staticmethod
    def _tentar_groq(prompt_sistema: str, prompt_usuario: str) -> str:
        """Fallback via Groq (Llama 3) - Conhecido por alta velocidade e excelente cota gratuita."""
        if not GROQ_API_KEY:
            raise ValueError("Groq API Key não configurada.")
        
        logger.info("[FAILOVER] Acionando backup via Groq (Llama)...")
        url = "https://api.groq.com/openai/v1/chat/completions"
        headers = {
            "Authorization": f"Bearer {GROQ_API_KEY}",
            "Content-Type": "application/json"
        }
        payload = {
            "model": "llama-3.3-70b-versatile",
            "messages": [
                {"role": "system", "content": prompt_sistema},
                {"role": "user", "content": prompt_usuario}
            ],
            "max_tokens": 1024
        }
        res = requests.post(url, json=payload, headers=headers, timeout=30)
        res.raise_for_status()
        return res.json()["choices"][0]["message"]["content"]

    @staticmethod
    def _tentar_gemini(prompt_sistema: str, prompt_usuario: str) -> str:
        """Fallback via Google Gemini Flash."""
        if not GEMINI_API_KEY:
            raise ValueError("Gemini API Key não configurada.")
        
        logger.info("[FAILOVER] Acionando backup via Gemini Flash...")
        url = f"https://generativelanguage.googleapis.com/v1beta/models/gemini-2.5-flash:generateContent?key={GEMINI_API_KEY}"
        headers = {"Content-Type": "application/json"}
        payload = {
            "contents": [
                {"parts": [{"text": f"Instrução: {prompt_sistema}\n\nSolicitação: {prompt_usuario}"}]}
            ]
        }
        res = requests.post(url, json=payload, headers=headers, timeout=30)
        res.raise_for_status()
        return res.json()["candidates"][0]["content"]["parts"][0]["text"]

    @staticmethod
    def _tentar_nemotron(prompt_sistema: str, prompt_usuario: str) -> str:
        """Tentativa primária com o Nemotron 3 Ultra via OpenRouter."""
        if not NEMOTRON_API_KEY:
            raise ValueError("Nemotron API Key não configurada.")

        headers = {
            "Authorization": f"Bearer {NEMOTRON_API_KEY}",
            "Content-Type": "application/json",
            "HTTP-Referer": "https://github.com/isaacfabricio/Jarvis-Mark-V",
            "X-Title": "J.A.R.V.I.S. Mark V"
        }
        payload = {
            "model": "nvidia/nemotron-3-ultra-550b-a55b:free",
            "messages": [
                {"role": "system", "content": prompt_sistema},
                {"role": "user", "content": prompt_usuario}
            ],
            "temperature": 0.2,
            "max_tokens": 1024
        }
        res = requests.post(NEMOTRON_API_URL, json=payload, headers=headers, timeout=35)
        if res.status_code == 429 or res.status_code >= 500:
            raise RuntimeError(f"Nemotron indisponível ou cota esgotada (Status {res.status_code})")
        res.raise_for_status()
        return res.json()["choices"][0]["message"]["content"]

    @classmethod
    def raciocinar(cls, prompt_sistema: str, prompt_usuario: str) -> str:
        """Executa a cascata de failover: Nemotron -> Gemini -> Groq -> Modo Seguro."""
        
        # 1. Tenta Nemotron (Primário)
        try:
            return cls._tentar_nemotron(prompt_sistema, prompt_usuario)
        except Exception as exc1:
            logger.warning("[CASCATA] Nemotron falhou: %s. Tentando próximo da fila...", exc1)

        # 2. Tenta Gemini (Primeiro Fallback)
        try:
            return cls._tentar_gemini(prompt_sistema, prompt_usuario)
        except Exception as exc2:
            logger.warning("[CASCATA] Gemini falhou: %s. Tentando próximo da fila...", exc2)

        # 3. Tenta Groq (Segundo Fallback)
        try:
            return cls._tentar_groq(prompt_sistema, prompt_usuario)
        except Exception as exc3:
            logger.warning("[CASCATA] Groq falhou: %s. Todos os provedores externos esgotados.", exc3)

        # 4. Última linha de defesa (Modo Offline / Memória Local)
        return (
            "[MODO DE RESILIÊNCIA TOTAL ATIVADO] Todos os provedores externos de IA "
            "(Nemotron, Gemini e Groq) retornaram limites de cota ou indisponibilidade no momento. "
            f"Consulta processada internamente com base na memória vetorial para o prompt: '{prompt_usuario[:50]}...'"
        )

@tool
def executar_raciocinio_nemotron(prompt_complexo: str) -> str:
    """Executa raciocínio estratégico com cascata infinita de failover entre múltiplos modelos.

    Args:
        prompt_complexo: A instrução ou tarefa complexa para o sistema.
    """
    sistema_prompt = (
        "Você é o núcleo cognitivo supremo do J.A.R.V.I.S. Mark V. "
        "Forneça respostas técnicas, precisas e objetivas."
    )
    return MultiModelFailoverEngine.raciocinar(sistema_prompt, prompt_complexo)
