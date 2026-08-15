"""
J.A.R.V.I.S. Core API - Mark V Secure (Com Clima e IA Integrados)
"""
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
    raise ValueError("GEMINI_API_KEY é obrigatória.")

CHAVE_VAULT = os.getenv("VAULT_KEY")
if not CHAVE_VAULT:
    raise ValueError("VAULT_KEY é obrigatória.")

TOKEN_AUTENTICACAO = os.getenv("JARVIS_TOKEN")
if not TOKEN_AUTENTICACAO:
    raise ValueError("JARVIS_TOKEN é obrigatório.")

CHAVE_API_CLIMA = os.getenv("WEATHER_API_KEY") or os.getenv("OPENWEATHER_API_KEY")

# Inicialização correta do cliente da nova biblioteca google-genai
CLIENT = genai.Client(api_key=CHAVE_API_GEMINI)

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
        response = requests.post(url, json=payload, timeout=30)
        if response.status_code == 200:
            return f"Resposta da IA Secundária: {response.json().get('response', '')}"
        return "IA secundária offline."
    except Exception as e:
        return f"Erro na IA secundária: {e}"

def consultar_clima(cidade: str) -> str:
    """Acessa os satélites meteorológicos para verificar o clima em tempo real."""
    if not CHAVE_API_CLIMA:
        return "Sensor de clima desativado. Chave API não encontrada no arquivo .env."

    url = (f"http://api.openweathermap.org/data/2.5/weather?q={cidade}"
           f"&appid={CHAVE_API_CLIMA}&units=metric&lang=pt_br")
    
    try:
        response = requests.get(url, timeout=10)
        dados = response.json()
        
        if dados.get("cod") == 200:
            temp = dados['main']['temp']
            desc = dados['weather'][0]['description']
            umidade = dados['main']['humidity']
            return (f"Senhor, em {cidade} os sensores indicam {temp}°C com {desc}. "
                    f"A umidade relativa do ar está em {umidade}%.")
        else:
            return f"Não consegui localizar a cidade de {cidade} nos meus mapas, Senhor."
            
    except Exception as e:
        return f"Houve uma falha na conexão com os satélites meteorológicos: {e}"

def instrucoes_sistema() -> str:
    return "Você é o J.A.R.V.I.S., assistente de IA avançado - Arquitetura Mark V. Chame o usuário sempre de 'Senhor'."

# Instancia o chat corretamente usando CLIENT.chats.create com as ferramentas integradas
chat = CLIENT.chats.create(
    model="gemini-1.5-flash",
    config=types.GenerateContentConfig(
        system_instruction=instrucoes_sistema(),
        temperature=0.6,
        tools=[salvar_memoria_criptografada, ajustar_personalidade, consultar_ia_secundaria_local, consultar_clima]
    )
)

app.mount("/static", StaticFiles(directory="frontend"), name="static")

@app.get("/")
async def get_interface():
    return FileResponse("frontend/index.html")

CONTROLE_BATERIA = {}

@app.websocket("/ws/{token_acesso}")
async def websocket_endpoint(websocket: WebSocket, token_acesso: str):
    ip_cliente = websocket.client.host
    tempo_atual = time.time()
    
    if ip_cliente in CONTROLE_BATERIA and tempo_atual < CONTROLE_BATERIA[ip_cliente]["desbloqueio_em"]:
        await websocket.close(code=1008)
        return

    if token_acesso != TOKEN_AUTENTICACAO:
        erros = CONTROLE_BATERIA.get(ip_cliente, {"erros": 0})["erros"] + 1
        CONTROLE_BATERIA[ip_cliente] = {"erros": erros, "desbloqueio_em": tempo_atual + (2 ** erros)}
        await websocket.close(code=1008)
        return

    if ip_cliente in CONTROLE_BATERIA:
        del CONTROLE_BATERIA[ip_cliente]
        
    await websocket.accept()
    conexoes_ativas.append(websocket)
    logger.info("Cérebro conectado de forma segura.")
    
    try:
        while True:
            data = await websocket.receive_text()
            mensagem = json.loads(data)
            
            comando = mensagem.get("comando")
            if comando:
                logger.info(f"[COMANDO]: {comando}")
                await transmitir_evento({"status": "THINKING", "log": comando, "type": "user"})
                try:
                    diretriz = f"[DIRETRIZ - Humor: {MATRIZ_PERSONALIDADE['humor']}%, Honestidade: {MATRIZ_PERSONALIDADE['honestidade']}%, Sarcasmo: {MATRIZ_PERSONALIDADE['sarcasmo']}%]\n"
                    resposta = await chat.send_message(diretriz + comando)
                    await transmitir_evento({"status": "SPEAKING", "log": resposta.text, "type": "jarvis", "acao": "falar"})
                except Exception as e:
                    logger.error(f"[ERRO AI]: {e}")
                    await transmitir_evento({"status": "STANDBY", "log": "Falha neural.", "type": "sys"})
                    
            elif mensagem.get("tipo") == "telemetria":
                await transmitir_evento(mensagem)

    except WebSocketDisconnect:
        conexoes_ativas.remove(websocket)

async def transmitir_evento(mensagem: dict):
    for ws in conexoes_ativas:
        try:
            await ws.send_json(mensagem)
        except:
            pass

if __name__ == "__main__":
    uvicorn.run(app, host="0.0.0.0", port=8000, log_level="error")
