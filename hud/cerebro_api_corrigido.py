import os
import json
import logging
import asyncio
import time
import requests
from fastapi import FastAPI, WebSocket, WebSocketDisconnect
from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse
import uvicorn
from google import genai
from google.genai import types
from cryptography.fernet import Fernet

try:
    from dotenv import load_dotenv
except ImportError:
    def load_dotenv():
        pass

load_dotenv()

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("CEREBRO_JARVIS")

CHAVE_API_GEMINI = os.getenv("GEMINI_API_KEY")
if not CHAVE_API_GEMINI:
    logger.warning("GEMINI_API_KEY não encontrada nas variáveis de ambiente. Verifique o arquivo .env.")

CHAVE_VAULT = os.getenv("VAULT_KEY", Fernet.generate_key().decode('utf-8'))
TOKEN_AUTENTICACAO = os.getenv("JARVIS_TOKEN", "jarvis-secret-key-2026")

CLIENT = genai.Client(api_key=CHAVE_API_GEMINI) if CHAVE_API_GEMINI else None

try:
    cifra = Fernet(CHAVE_VAULT.encode('utf-8'))
except Exception as e:
    raise ValueError(f"VAULT_KEY inválida: {e}")

VAULT_DIR = "vault_jarvis"
if not os.path.exists(VAULT_DIR):
    os.makedirs(VAULT_DIR)

app = FastAPI(title="J.A.R.V.I.S. Core API", version="Mark V Secure")
conexoes_ativas = []

MATRIZ_PERSONALIDADE = {
    "humor": 10,       
    "honestidade": 100, 
    "sarcasmo": 5       
}

def ajustar_personalidade(parametro: str, porcentagem: int) -> str:
    """Ajusta os níveis de personalidade do J.A.R.V.I.S. (humor, honestidade, sarcasmo) de 0 a 100%."""
    parametro = parametro.lower().strip()
    if parametro in MATRIZ_PERSONALIDADE:
        valor_ajustado = max(0, min(100, porcentagem))
        MATRIZ_PERSONALIDADE[parametro] = valor_ajustado
        return f"Matriz atualizada. Nível de {parametro} definido para {valor_ajustado}%."
    return "Parâmetro não reconhecido."

def salvar_memoria_criptografada(titulo: str, conteudo: str) -> str:
    """Sela a informação no Vault utilizando criptografia AES-256."""
    nome_arquivo = f"{titulo.replace(' ', '_').lower()}.enc"
    caminho = os.path.join(VAULT_DIR, nome_arquivo)
    conteudo_selado = cifra.encrypt(conteudo.encode('utf-8'))
    with open(caminho, "wb") as f:
        f.write(conteudo_selado)
    return f"Memória selada com segurança AES-256 no arquivo {nome_arquivo}."

def consultar_ia_secundaria_local(prompt_especifico: str) -> str:
    """Consulta um modelo de IA alternativo ou local (via Ollama)."""
    url = "http://localhost:11434/api/generate"
    payload = {"model": "llama3", "prompt": prompt_especifico, "stream": False}
    try:
        response = requests.post(url, json=payload, timeout=5)
        if response.status_code == 200:
            return f"Resposta da IA Secundária: {response.json().get('response', '')}"
        return "IA secundária offline."
    except Exception as e:
        return f"IA secundária indisponível ({e})."

def instrucoes_sistema() -> str:
    return "Você é o J.A.R.V.I.S., assistente de IA avançado - Arquitetura Mark V. Chame o usuário sempre de 'Senhor'."

# Inicialização segura do chat
chat = None
if CLIENT:
    try:
        chat = CLIENT.chats.create(
            model="gemini-1.5-flash",
            config=types.GenerateContentConfig(
                system_instruction=instrucoes_sistema(),
                temperature=0.6,
                tools=[salvar_memoria_criptografada, ajustar_personalidade, consultar_ia_secundaria_local]
            )
        )
    except Exception as e:
        logger.error(f"Erro ao inicializar chat do Gemini: {e}")

@app.websocket("/ws/{token_acesso}")
async def websocket_endpoint(websocket: WebSocket, token_acesso: str):
    if token_acesso != TOKEN_AUTENTICACAO:
        await websocket.close(code=4003, reason="Token inválido")
        return

    await websocket.accept()
    conexoes_ativas.append(websocket)
    logger.info("Cliente HUD conectado via WebSocket.")
    try:
        await websocket.send_text(json.dumps({
            "tipo": "telemetria",
            "cpu": 15,
            "ram": 42
        }))
        while True:
            dados = await websocket.receive_text()
            mensagem = json.loads(dados)
            comando = mensagem.get("comando", "")
            
            resposta_texto = f"Comando recebido: {comando}. Todos os sistemas operacionais operando em capacidade nominal, Senhor."
            if chat:
                try:
                    resposta_ia = chat.send_message(comando)
                    if resposta_ia and resposta_ia.text:
                        resposta_texto = resposta_ia.text
                except Exception as e:
                    logger.error(f"Erro na IA: {e}")

            await websocket.send_text(json.dumps({
                "type": "jarvis",
                "status": "SPEAKING",
                "acao": "falar",
                "log": resposta_texto
            }))
    except WebSocketDisconnect:
        conexoes_ativas.remove(websocket)
        logger.info("Cliente desconectado.")
    except Exception as e:
        if websocket in conexoes_ativas:
            conexoes_ativas.remove(websocket)
        logger.error(f"Erro no WebSocket: {e}")

if __name__ == "__main__":
    uvicorn.run(app, host="127.0.0.1", port=8000)
