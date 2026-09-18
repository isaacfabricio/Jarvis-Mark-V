import os
import logging
from google import genai
from app.services import data_agent_service

logger = logging.getLogger(__name__)

ZERO_YAPPING_PROMPT = """
Você é o J.A.R.V.I.S. Mark V, um agente de operações de alta performance.
DIRETRIZ: Seja direto, técnico e objetivo. Sem textos desnecessários.
"""

def executar_comando(prompt_usuario: str) -> str:
    # Utiliza a chave da API do Google Gemini
    api_key = os.getenv("GEMINI_API_KEY") or os.getenv("GOOGLE_API_KEY")
    if not api_key:
        return "Erro crítico: GEMINI_API_KEY ou GOOGLE_API_KEY não encontrada no ambiente."
    
    try:
        client = genai.Client(api_key=api_key)
        
        # Combinando o prompt do sistema com a instrução do usuário
        prompt_completo = f"{ZERO_YAPPING_PROMPT}\n\nUsuário: {prompt_usuario}"
        
        response = client.models.generate_content(
            model='gemini-2.5-flash',
            contents=prompt_completo,
        )
        
        return response.text
        
    except Exception as e:
        return f"Falha no núcleo cognitivo do Gemini: {str(e)}"
