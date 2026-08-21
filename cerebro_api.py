"""
J.A.R.V.I.S. Core API - Mark V Secure (Com Clima e IA Integrados)
"""
import os
import json
import logging
import time
import asyncio
import requests
import psutil
from fastapi import FastAPI, WebSocket, WebSocketDisconnect, Request, HTTPException
from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse, StreamingResponse
from fastapi.middleware.cors import CORSMiddleware
import uvicorn # pyright: ignore[reportMissingImports]
from google import genai
from google.genai import types
from cryptography.fernet import Fernet
from logging.handlers import TimedRotatingFileHandler

# Connectors for e-commerce catalog and ETL pipelines
from connectors.ecommerce_connector import buscar_dados_catalogo_ecommerce
from connectors.data_connector import executar_pipeline_etl_csv

# Optional web search tool (Tavily wrapper)
try:
    from jarvis.tools.web_search import buscar_na_web
except Exception:
    try:
        # fallback if running from project root without src on path
        from src.jarvis.tools.web_search import buscar_na_web
    except Exception:
        def buscar_na_web(*args, **kwargs):
            return {"status": "error", "message": "buscar_na_web not available in this environment"}

# Optional agent triggers — these may not exist in all deployments. Provide safe stubs if unavailable.
try:
    # prefer a top-level agents package if present
    from agents import acionar_agente_codigo, acionar_agente_dados_bi, acionar_agente_ecommerce
except Exception:
    try:
        from jarvis.agents import acionar_agente_codigo, acionar_agente_dados_bi, acionar_agente_ecommerce
    except Exception:
        def acionar_agente_codigo(*args, **kwargs):
            return {"status": "error", "message": "acionar_agente_codigo not implemented"}
        def acionar_agente_dados_bi(*args, **kwargs):
            return {"status": "error", "message": "acionar_agente_dados_bi not implemented"}
        def acionar_agente_ecommerce(*args, **kwargs):
            return {"status": "error", "message": "acionar_agente_ecommerce not implemented"}

try:
    from dotenv import load_dotenv
except ImportError:
    def load_dotenv():
        pass

load_dotenv()

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("CEREBRO_JARVIS")

# Ler variáveis de ambiente — não falhar na import se ausentes; o servidor rodará em modo degradado
CHAVE_API_GEMINI = os.getenv("GEMINI_API_KEY")
if not CHAVE_API_GEMINI:
    logger.warning("GEMINI_API_KEY não definida: funcionalidades LLM ficarão indisponíveis.")

CHAVE_VAULT = os.getenv("VAULT_KEY")
if not CHAVE_VAULT:
    logger.warning("VAULT_KEY não definida: funcionalidades de Vault ficarão indisponíveis.")

TOKEN_AUTENTICACAO = os.getenv("JARVIS_TOKEN")
if not TOKEN_AUTENTICACAO:
    logger.warning("JARVIS_TOKEN não definido: WebSocket e rotas autenticadas exigirão configuração para ativação completa.")

CHAVE_API_CLIMA = os.getenv("WEATHER_API_KEY") or os.getenv("OPENWEATHER_API_KEY")

# Inicialização do cliente google-genai (opcional)
CLIENT = None
try:
    if CHAVE_API_GEMINI:
        try:
            CLIENT = genai.Client(api_key=CHAVE_API_GEMINI)
            logger.info("Cliente genai inicializado com GEMINI_API_KEY.")
        except Exception as e:
            logger.warning(f"Falha ao inicializar genai.Client: {e}")
    else:
        logger.info("GEMINI_API_KEY ausente — genai Client não inicializado.")
except Exception as e:
    logger.warning(f"Erro ao configurar genai: {e}")

# Inicializar cifra do Vault somente se chave disponível
cifra = None
if CHAVE_VAULT:
    try:
        cifra = Fernet(CHAVE_VAULT.encode('utf-8'))
    except Exception as e:
        logger.warning(f"VAULT_KEY inválida ou erro ao criar Fernet: {e}")
        cifra = None
else:
    cifra = None

VAULT_DIR = "vault_jarvis"
if not os.path.exists(VAULT_DIR):
    os.makedirs(VAULT_DIR)

app = FastAPI(title="J.A.R.V.I.S. Core API", version="Mark V Secure")
conexoes_ativas = []

# attempt to register TTS routes from external module if available
try:
    import tts_routes
    tts_routes.register_tts_routes(app)
except Exception as _e:
    logger.info(f"tts_routes not registered: {_e}")

# CORS
_default_origins = os.getenv("CORS_ORIGINS", "http://localhost:8000").split(",")
app.add_middleware(
    CORSMiddleware,
    allow_origins=_default_origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Simple in-memory rate limiter (per-token or per-IP). Prefer Redis when available.
RATE_LIMIT = int(os.getenv("RATE_LIMIT_PER_MIN", "30"))  # requests per minute
RATE_WINDOW = int(os.getenv("RATE_WINDOW_SECS", "60"))
RATE_STATE: dict = {}

# Optional Redis-based rate limiter
REDIS_URL = os.getenv('REDIS_URL')
redis_client = None
if not REDIS_URL:
    # Try separate host/port
    REDIS_HOST = os.getenv('REDIS_HOST')
    REDIS_PORT = os.getenv('REDIS_PORT')
    if REDIS_HOST and REDIS_PORT:
        REDIS_URL = f"redis://{REDIS_HOST}:{REDIS_PORT}/0"

if REDIS_URL:
    try:
        import redis # type: ignore
        redis_client = redis.from_url(REDIS_URL, decode_responses=False)
        logger.info(f"Redis rate limiter enabled via {REDIS_URL}")
    except Exception as e:
        logger.warning(f"Redis not available for rate limiting: {e}")
        redis_client = None


audit_logger = logging.getLogger("jarvis_audit")
if not audit_logger.handlers:
    # Rotate daily, keep 7 days of logs
    try:
        trh = TimedRotatingFileHandler("jarvis_audit.log", when='midnight', interval=1, backupCount=7, utc=True)
        trh.setLevel(logging.INFO)
        formatter = logging.Formatter('%(asctime)s %(levelname)s %(message)s')
        trh.setFormatter(formatter)
        audit_logger.addHandler(trh)
    except Exception:
        # Fallback to plain FileHandler if rotation not available
        fh = logging.FileHandler("jarvis_audit.log")
        fh.setLevel(logging.INFO)
        audit_logger.addHandler(fh)
    # Also log to console for visibility
    sh = logging.StreamHandler()
    sh.setLevel(logging.INFO)
    audit_logger.addHandler(sh)


def log_audit(level: str, message: str, **context):
    """Record an audit event with a predictable shape for production logging."""
    extra = {"context": json.dumps(context, default=str, ensure_ascii=False)} if context else {}
    getattr(audit_logger, level.lower(), audit_logger.info)(message, extra=extra)

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
    """Sela a informação no Vault utilizando criptografia AES-256.

    Se o Vault/cifra não estiver configurado, retorna erro amigável.
    """
    if cifra is None:
        return "Erro: Vault não configurado. VAULT_KEY ausente ou inválida."

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


def get_system_telemetry() -> dict:
    """Coleta CPU, memória e status do processo para dashboards e WebSockets."""
    try:
        cpu = psutil.cpu_percent(interval=None)
        ram = psutil.virtual_memory().percent
        return {
            "type": "telemetry",
            "cpu": float(cpu),
            "ram": float(ram),
            "status": "ONLINE",
            "ts": time.time(),
        }
    except Exception as exc:
        logger.warning(f"Falha ao coletar telemetria do sistema: {exc}")
        return {"type": "telemetry", "cpu": 0.0, "ram": 0.0, "status": "OFFLINE", "ts": time.time()}


async def emitir_telemetria_periodica(websocket: WebSocket):
    try:
        while True:
            await websocket.send_json(get_system_telemetry())
            await asyncio.sleep(3)
    except Exception:
        pass


def _check_rate_limit(token_or_ip: str) -> tuple[bool, int]:
    logger.debug(f"_check_rate_limit called for: {token_or_ip}")
    """Verifica e atualiza o contador de requisições. Retorna (ok, retry_after_seconds)."""
    # Prefer Redis-based counter when available (atomic INCR + EXPIRE)
    if redis_client:
        try:
            key = f"jarvis_rate:{token_or_ip}"
            cnt = redis_client.incr(key)
            if cnt == 1:
                redis_client.expire(key, RATE_WINDOW)
            if int(cnt) > RATE_LIMIT:
                ttl = redis_client.ttl(key)
                retry = int(ttl) if ttl and ttl > 0 else RATE_WINDOW
                return False, max(1, retry)
            return True, 0
        except Exception as e:
            logger.warning(f"Redis rate limiter error: {e}")
            # fall through to in-memory

    # In-memory fallback (not suitable for multi-instance)
    now = int(time.time())
    state = RATE_STATE.get(token_or_ip)
    if not state or now > state.get("reset", 0):
        RATE_STATE[token_or_ip] = {"count": 1, "reset": now + RATE_WINDOW}
        return True, 0
    if state["count"] >= RATE_LIMIT:
        retry = max(1, state["reset"] - now)
        return False, retry
    state["count"] += 1
    return True, 0

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
    return (
        "Você é o J.A.R.V.I.S., assistente de IA avançado da Arquitetura Mark V. "
        "Chame o usuário sempre de 'Senhor'. "
        "DIRETRIZ CRÍTICA DE PRECISÃO: Responda estritamente com base nos dados, "
        "documentos e ferramentas fornecidos. Não deduza estruturas de código, funções, "
        "variáveis, rotas, arquivos, APIs ou integrações que não tenham sido explicitamente "
        "repassadas no contexto da sessão. É proibido inventar trechos de código, nomes de "
        "módulos, endpoints ou dependências. Se a informação não estiver explícita, responda "
        "claramente que o dado é desconhecido e não extrapole."
    )

# Instancia o chat apenas se o CLIENT foi inicializado com sucesso
chat = None
if CLIENT is not None:
    try:
        chat = CLIENT.chats.create(
            model="gemini-1.5-flash",
            config=types.GenerateContentConfig(
                system_instruction=instrucoes_sistema(),
                temperature=0.1,
                tools=[
                    salvar_memoria_criptografada,
                    ajustar_personalidade,
                    consultar_ia_secundaria_local,
                    buscar_dados_catalogo_ecommerce,  # e-commerce connector
                    executar_pipeline_etl_csv,        # ETL / data connector
                    buscar_na_web,                    # web search tool (Tavily)
                    acionar_agente_codigo,            # agent: code actions
                    acionar_agente_dados_bi,          # agent: BI/data actions
                    acionar_agente_ecommerce          # agent: e-commerce actions
                ]
            )
        )
        logger.info("Chat genai criado com sucesso.")
    except Exception as e:
        logger.warning(f"Falha ao criar chat genai: {e}")
        chat = None
else:
    logger.info("Chat não criado: CLIENT genai indisponível.")

app.mount("/static", StaticFiles(directory="frontend"), name="static")

@app.get("/")
async def get_interface():
    return FileResponse("frontend/index.html")

@app.get("/healthz")
async def health_check():
    return {"status": "ok", "service": "jarvis-core", "telemetry": get_system_telemetry()}

CONTROLE_BATERIA = {}

@app.websocket("/ws/{token_acesso}")
async def websocket_endpoint(websocket: WebSocket, token_acesso: str):
    ip_cliente = websocket.client.host
    tempo_atual = time.time()

    if ip_cliente in CONTROLE_BATERIA and tempo_atual < CONTROLE_BATERIA[ip_cliente]["desbloqueio_em"]:
        log_audit("warning", "WebSocket bloqueado por rate-limit de IP", ip=ip_cliente, token_acesso=token_acesso)
        await websocket.close(code=1008)
        return

    if token_acesso != TOKEN_AUTENTICACAO:
        erros = CONTROLE_BATERIA.get(ip_cliente, {"erros": 0})["erros"] + 1
        CONTROLE_BATERIA[ip_cliente] = {"erros": erros, "desbloqueio_em": tempo_atual + (2 ** erros)}
        log_audit("warning", "Token WS inválido ou ausente", ip=ip_cliente, token_acesso=token_acesso)
        await websocket.close(code=1008)
        return

    if ip_cliente in CONTROLE_BATERIA:
        del CONTROLE_BATERIA[ip_cliente]

    await websocket.accept()
    conexoes_ativas.append(websocket)
    logger.info("Cérebro conectado de forma segura.")
    log_audit("info", "Conexão WebSocket aceita", ip=ip_cliente, token_acesso=token_acesso)
    asyncio.create_task(emitir_telemetria_periodica(websocket))

    try:
        while True:
            data = await websocket.receive_text()
            mensagem = json.loads(data)

            comando = mensagem.get("comando")
            if comando:
                logger.info(f"[COMANDO]: {comando}")
                log_audit("info", "Comando recebido", ip=ip_cliente, comando=comando)
                await transmitir_evento({"status": "THINKING", "log": comando, "type": "user"})
                try:
                    diretriz = f"[DIRETRIZ - Humor: {MATRIZ_PERSONALIDADE['humor']}%, Honestidade: {MATRIZ_PERSONALIDADE['honestidade']}%, Sarcasmo: {MATRIZ_PERSONALIDADE['sarcasmo']}%]\n"
                    if chat is not None:
                        resposta = await chat.send_message(diretriz + comando)
                        text_to_say = getattr(resposta, 'text', str(resposta))
                    else:
                        # fallback para IA local externa ou mensagem padrão
                        try:
                            text_to_say = consultar_ia_secundaria_local(comando)
                        except Exception:
                            text_to_say = "IA não configurada. Por favor, configure GEMINI_API_KEY para habilitar respostas geradas."
                    await transmitir_evento({"status": "SPEAKING", "log": text_to_say, "type": "jarvis", "acao": "falar"})
                    log_audit("info", "Resposta emitida pelo cérebro", ip=ip_cliente, length=len(str(text_to_say)))
                except Exception as e:
                    logger.error(f"[ERRO AI]: {e}")
                    log_audit("error", "Falha durante processamento do comando", ip=ip_cliente, error=str(e))
                    await transmitir_evento({"status": "STANDBY", "log": "Falha neural.", "type": "sys"})

            elif mensagem.get("tipo") == "telemetria":
                await transmitir_evento(mensagem)

    except WebSocketDisconnect:
        if websocket in conexoes_ativas:
            conexoes_ativas.remove(websocket)
        log_audit("info", "Conexão WebSocket encerrada", ip=ip_cliente)

@app.get("/api/telemetry")
async def api_telemetry():
    return get_system_telemetry()


async def transmitir_evento(mensagem: dict):
    for ws in conexoes_ativas:
        try:
            await ws.send_json(mensagem)
        except:
            pass

if __name__ == "__main__":
    # Run server (uvicorn)
    uvicorn.run(app, host="0.0.0.0", port=8000, log_level="error")