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

import importlib

# Optional web search tool (Tavily wrapper) — dynamic import to avoid static missing-import diagnostics
buscar_na_web = None
try:
    mod = importlib.import_module("jarvis.tools.web_search")
    buscar_na_web = getattr(mod, "buscar_na_web")
except Exception:
    try:
        mod = importlib.import_module("src.jarvis.tools.web_search")
        buscar_na_web = getattr(mod, "buscar_na_web")
    except Exception:
        def buscar_na_web(*args, **kwargs):
            return {"status": "error", "message": "buscar_na_web not available in this environment"}

# Optional agent triggers — dynamic import with safe stubs if unavailable
acionar_agente_codigo = None
acionar_agente_dados_bi = None
acionar_agente_ecommerce = None
try:
    mod = importlib.import_module("agents")
    acionar_agente_codigo = getattr(mod, "acionar_agente_codigo", None)
    acionar_agente_dados_bi = getattr(mod, "acionar_agente_dados_bi", None)
    acionar_agente_ecommerce = getattr(mod, "acionar_agente_ecommerce", None)
except Exception:
    try:
        mod = importlib.import_module("jarvis.agents")
        acionar_agente_codigo = getattr(mod, "acionar_agente_codigo", None)
        acionar_agente_dados_bi = getattr(mod, "acionar_agente_dados_bi", None)
        acionar_agente_ecommerce = getattr(mod, "acionar_agente_ecommerce", None)
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
# If no REDIS_URL provided, attempt to use REDIS_HOST/REDIS_PORT, else assume local redis
if not REDIS_URL:
    REDIS_HOST = os.getenv('REDIS_HOST')
    REDIS_PORT = os.getenv('REDIS_PORT')
    if REDIS_HOST and REDIS_PORT:
        REDIS_URL = f"redis://{REDIS_HOST}:{REDIS_PORT}/0"
    else:
        # best-effort local fallback — only used when container/host exposes Redis locally
        REDIS_URL = os.getenv('REDIS_URL_FALLBACK', "redis://127.0.0.1:6379/0")

if REDIS_URL:
    try:
        import redis as _redis  # type: ignore
        # Use a short connect attempt to validate availability
        redis_client = _redis.from_url(REDIS_URL, decode_responses=False)
        # Try a ping to confirm connectivity
        try:
            redis_client.ping()
            logger.info(f"Redis rate limiter enabled via {REDIS_URL}")
        except Exception as e:
            logger.warning(f"Redis ping failed: {e}")
            redis_client = None
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


# Vault HTTP endpoints (require token)
@app.post("/api/vault/store")
async def api_vault_store(request: Request):
    _verify_token_in_request(request)
    body = await request.json()
    titulo = body.get("title") or body.get("titulo")
    conteudo = body.get("content") or body.get("conteudo")
    if not titulo or not conteudo:
        return JSONResponse(content={"status": "error", "message": "Missing title or content"}, status_code=400)
    res = salvar_memoria_criptografada(titulo, conteudo)
    return JSONResponse(content={"status": "ok", "message": res})


@app.get("/api/vault/get/{titulo}")
async def api_vault_get(titulo: str, request: Request):
    _verify_token_in_request(request)
    if cifra is None:
        return JSONResponse(content={"status": "error", "message": "Vault not configured"}, status_code=500)
    nome_arquivo = f"{titulo.replace(' ', '_').lower()}.enc"
    caminho = os.path.join(VAULT_DIR, nome_arquivo)
    if not os.path.exists(caminho):
        return JSONResponse(content={"status": "error", "message": "Not found"}, status_code=404)
    with open(caminho, "rb") as f:
        selado = f.read()
    try:
        conteudo = cifra.decrypt(selado).decode('utf-8')
    except Exception as e:
        return JSONResponse(content={"status": "error", "message": f"Decryption failed: {e}"}, status_code=500)
    return JSONResponse(content={"status": "ok", "title": titulo, "content": conteudo})

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
import hashlib

# Model selection and token limits configurable via env for cost control
GEMINI_MODEL = os.getenv("GEMINI_MODEL", "gemini-1.5-flash")
GEMINI_MAX_TOKENS = int(os.getenv("GEMINI_MAX_TOKENS", "256"))
CACHE_TTL = int(os.getenv("CACHE_TTL_SECS", "3600"))  # seconds

# Simple in-memory cache as fallback
_RESPONSE_CACHE: dict = {}

def _cache_get(key: str):
    # Redis-backed cache preferred
    try:
        if redis_client:
            val = redis_client.get(key)
            if val is None:
                return None
            # redis stores bytes; decode
            if isinstance(val, bytes):
                return val.decode('utf-8')
            return val
    except Exception:
        pass
    # in-memory fallback with expiry
    entry = _RESPONSE_CACHE.get(key)
    if not entry:
        return None
    value, expiry = entry
    if time.time() > expiry:
        del _RESPONSE_CACHE[key]
        return None
    return value


def _cache_set(key: str, value: str, ttl: int = CACHE_TTL):
    try:
        if redis_client:
            redis_client.setex(key, ttl, value)
            return
    except Exception:
        pass
    _RESPONSE_CACHE[key] = (value, time.time() + ttl)


async def _cached_chat_response(prompt: str) -> str:
    """Cache chat responses to avoid repeated expensive LLM calls."""
    key = "chat:" + hashlib.sha256(prompt.encode('utf-8')).hexdigest()
    cached = _cache_get(key)
    if cached is not None:
        logger.debug("cache hit for chat prompt")
        return cached

    if chat is None:
        # fallback to secondary/local IA
        try:
            return consultar_ia_secundaria_local(prompt)
        except Exception as e:
            return f"IA não configurada: {e}"

    try:
        # Use configured model and token limit when creating/generating content
        resposta = await chat.send_message(prompt)
        text_to_say = getattr(resposta, 'text', str(resposta))
        _cache_set(key, text_to_say)
        return text_to_say
    except Exception as e:
        logger.warning(f"LLM call failed: {e}")
        # fallback to local IA
        try:
            return consultar_ia_secundaria_local(prompt)
        except Exception:
            return f"Erro na chamada LLM: {e}"


def _cached_tool_call(func, *args, **kwargs):
    key_base = func.__name__ + ":" + ":".join(map(str, args)) + ":" + ":".join(f"{k}={v}" for k, v in kwargs.items())
    key = "tool:" + hashlib.sha256(key_base.encode('utf-8')).hexdigest()
    cached = _cache_get(key)
    if cached is not None:
        try:
            return json.loads(cached)
        except Exception:
            return cached

    try:
        res = func(*args, **kwargs)
        # store as JSON when possible
        try:
            to_store = json.dumps(res, ensure_ascii=False)
        except Exception:
            to_store = str(res)
        _cache_set(key, to_store)
        try:
            return json.loads(to_store)
        except Exception:
            return to_store
    except Exception as e:
        raise


chat = None
if CLIENT is not None:
    try:
        # Configure chat with model selection and token limits set via env vars.
        chat = CLIENT.chats.create(
            model=GEMINI_MODEL,
            config=types.GenerateContentConfig(
                system_instruction=instrucoes_sistema(),
                temperature=float(os.getenv("GEMINI_TEMPERATURE", "0.1")),
                max_output_tokens=GEMINI_MAX_TOKENS,
                tools=[
                    salvar_memoria_criptografada,
                    ajustar_personalidade,
                    consultar_ia_secundaria_local,
                    buscar_dados_catalogo_ecommerce,
                    executar_pipeline_etl_csv,
                    buscar_na_web,
                    acionar_agente_codigo,
                    acionar_agente_dados_bi,
                    acionar_agente_ecommerce,
                ],
            ),
        )
        logger.info(f"Chat genai criado com sucesso com o modelo {GEMINI_MODEL}.")
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

            # Tool invocation via WebSocket: {"tool": "ecommerce", "plataforma":"shein", "termo":"camiseta"}
            if mensagem.get("tool") == "ecommerce":
                plataforma = mensagem.get("plataforma", "shein")
                termo = mensagem.get("termo", "camiseta")
                try:
                    resultado = _cached_tool_call(buscar_dados_catalogo_ecommerce, plataforma, termo)
                    payload = resultado
                    await websocket.send_json({"type": "tool_result", "tool": "ecommerce", "result": payload})
                except Exception as e:
                    await websocket.send_json({"type": "tool_result", "tool": "ecommerce", "error": str(e)})
                continue

            if mensagem.get("tool") == "etl":
                caminho = mensagem.get("path")
                if not caminho:
                    await websocket.send_json({"type": "tool_result", "tool": "etl", "error": "missing 'path'"})
                    continue
                try:
                    resultado = executar_pipeline_etl_csv(caminho)
                    await websocket.send_json({"type": "tool_result", "tool": "etl", "result": resultado})
                except Exception as e:
                    await websocket.send_json({"type": "tool_result", "tool": "etl", "error": str(e)})
                continue

            comando = mensagem.get("comando")
            if comando:
                logger.info(f"[COMANDO]: {comando}")
                log_audit("info", "Comando recebido", ip=ip_cliente, comando=comando)
                await transmitir_evento({"status": "THINKING", "log": comando, "type": "user"})
                try:
                    diretriz = f"[DIRETRIZ - Humor: {MATRIZ_PERSONALIDADE['humor']}%, Honestidade: {MATRIZ_PERSONALIDADE['honestidade']}%, Sarcasmo: {MATRIZ_PERSONALIDADE['sarcasmo']}%]\n"
                    if chat is not None:
                        # Use cached chat response to reduce LLM calls
                        text_to_say = await _cached_chat_response(diretriz + comando)
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


from fastapi.responses import JSONResponse

# HTTP endpoint to trigger e-commerce catalog fetch
@app.get("/api/ecommerce/catalog")
async def api_ecommerce_catalog(plataforma: str = "shein", termo: str = "camiseta"):
    try:
        resultado = buscar_dados_catalogo_ecommerce(plataforma, termo)
        try:
            payload = json.loads(resultado)
        except Exception:
            payload = {"raw": resultado}
        return JSONResponse(content={"status": "ok", "data": payload})
    except Exception as e:
        return JSONResponse(content={"status": "error", "message": str(e)}, status_code=500)


# Simple token verification for critical routes
from uuid import uuid4

def _verify_token_in_request(request: Request):
    auth = request.headers.get("Authorization") or request.headers.get("X-JARVIS-TOKEN")
    if not auth:
        raise HTTPException(status_code=401, detail="Missing authorization token")
    # Support 'Bearer <token>' and raw token
    if auth.startswith("Bearer "):
        token = auth.split(" ", 1)[1]
    else:
        token = auth
    if TOKEN_AUTENTICACAO and token != TOKEN_AUTENTICACAO:
        raise HTTPException(status_code=403, detail="Invalid token")


# Background ETL job processing with optional Redis-backed status storage
ETL_RESULTS_DIR = "./data/etl_results"
os.makedirs(ETL_RESULTS_DIR, exist_ok=True)

async def _process_etl_job(job_id: str, path: str):
    key = f"etl:job:{job_id}"
    # update status
    if redis_client:
        try:
            redis_client.hset(key, mapping={"status": "running"})
        except Exception:
            pass
    else:
        with open(os.path.join(ETL_RESULTS_DIR, f"{job_id}.json"), "w", encoding="utf-8") as f:
            json.dump({"status": "running"}, f, ensure_ascii=False)
    try:
        resultado = executar_pipeline_etl_csv(path)
        # store result
        entry = {"status": "done", "result": resultado}
        if redis_client:
            try:
                redis_client.hset(key, mapping={"status": "done", "result": json.dumps(resultado, ensure_ascii=False)})
            except Exception:
                pass
        else:
            with open(os.path.join(ETL_RESULTS_DIR, f"{job_id}.json"), "w", encoding="utf-8") as f:
                json.dump(entry, f, ensure_ascii=False)
    except Exception as e:
        entry = {"status": "error", "error": str(e)}
        if redis_client:
            try:
                redis_client.hset(key, mapping={"status": "error", "error": str(e)})
            except Exception:
                pass
        else:
            with open(os.path.join(ETL_RESULTS_DIR, f"{job_id}.json"), "w", encoding="utf-8") as f:
                json.dump(entry, f, ensure_ascii=False)


@app.post("/api/etl/run")
async def api_etl_run(request: Request):
    # token verification
    _verify_token_in_request(request)
    body = await request.json()
    caminho = body.get("path")
    if not caminho:
        return JSONResponse(content={"status": "error", "message": "Missing 'path' in JSON body"}, status_code=400)

    job_id = uuid4().hex
    key = f"etl:job:{job_id}"
    # enqueue (or mark queued)
    if redis_client:
        try:
            redis_client.hset(key, mapping={"status": "queued", "path": caminho})
            redis_client.lpush("etl:queue", job_id)
        except Exception as e:
            logger.warning(f"Redis enqueue failed: {e}")
            # fallback to file
            with open(os.path.join(ETL_RESULTS_DIR, f"{job_id}.json"), "w", encoding="utf-8") as f:
                json.dump({"status": "queued", "path": caminho}, f, ensure_ascii=False)
    else:
        with open(os.path.join(ETL_RESULTS_DIR, f"{job_id}.json"), "w", encoding="utf-8") as f:
            json.dump({"status": "queued", "path": caminho}, f, ensure_ascii=False)

    # start background processing task in this process (acts as worker)
    asyncio.create_task(_process_etl_job(job_id, caminho))

    return JSONResponse(content={"status": "ok", "job_id": job_id})


@app.get("/api/etl/status/{job_id}")
async def api_etl_status(job_id: str, request: Request):
    _verify_token_in_request(request)
    key = f"etl:job:{job_id}"
    if redis_client:
        try:
            data = redis_client.hgetall(key)
            if not data:
                raise HTTPException(status_code=404, detail="Job not found")
            # decode bytes if necessary
            decoded = {k.decode() if isinstance(k, bytes) else k: (v.decode() if isinstance(v, bytes) else v) for k, v in data.items()}
            return JSONResponse(content={"status": "ok", "job": decoded})
        except HTTPException:
            raise
        except Exception as e:
            logger.warning(f"Redis read error: {e}")
    # fallback to file
    path = os.path.join(ETL_RESULTS_DIR, f"{job_id}.json")
    if os.path.exists(path):
        with open(path, "r", encoding="utf-8") as f:
            j = json.load(f)
        return JSONResponse(content={"status": "ok", "job": j})
    raise HTTPException(status_code=404, detail="Job not found")


@app.get("/api/etl/result/{job_id}")
async def api_etl_result(job_id: str, request: Request):
    # alias to status for now
    return await api_etl_status(job_id, request)


# Fetch a public dataset (CSV) by URL and run ETL on it. Background job with token auth.
@app.post("/api/datasets/fetch")
async def api_datasets_fetch(request: Request):
    _verify_token_in_request(request)
    body = await request.json()
    url = body.get("url")
    if not url:
        return JSONResponse(content={"status": "error", "message": "Missing 'url' in JSON body"}, status_code=400)

    # create job id and paths
    job_id = uuid4().hex
    datasets_dir = os.path.join("data", "datasets")
    os.makedirs(datasets_dir, exist_ok=True)

    # derive filename safely
    try:
        fname = os.path.basename(url.split('?')[0]) or f"dataset_{job_id}.csv"
        # limit filename length
        if len(fname) > 200:
            fname = fname[-200:]
        dest_path = os.path.join(datasets_dir, f"{job_id}_" + fname)
    except Exception:
        dest_path = os.path.join(datasets_dir, f"{job_id}_dataset.csv")

    # register as queued job (reuse etl job keys)
    key = f"etl:job:{job_id}"
    if redis_client:
        try:
            redis_client.hset(key, mapping={"status": "queued", "source_url": url})
            redis_client.lpush("etl:queue", job_id)
        except Exception as e:
            logger.warning(f"Redis enqueue failed for dataset fetch: {e}")
            with open(os.path.join(ETL_RESULTS_DIR, f"{job_id}.json"), "w", encoding="utf-8") as f:
                json.dump({"status": "queued", "source_url": url}, f, ensure_ascii=False)
    else:
        with open(os.path.join(ETL_RESULTS_DIR, f"{job_id}.json"), "w", encoding="utf-8") as f:
            json.dump({"status": "queued", "source_url": url}, f, ensure_ascii=False)

    async def _download_and_process(job_id_inner: str, source_url: str, dest: str):
        key_inner = f"etl:job:{job_id_inner}"
        # update status
        if redis_client:
            try:
                redis_client.hset(key_inner, mapping={"status": "downloading"})
            except Exception:
                pass
        else:
            with open(os.path.join(ETL_RESULTS_DIR, f"{job_id_inner}.json"), "w", encoding="utf-8") as f:
                json.dump({"status": "downloading", "source_url": source_url}, f, ensure_ascii=False)

        try:
            # stream download
            with requests.get(source_url, stream=True, timeout=30) as r:
                r.raise_for_status()
                with open(dest, "wb") as f:
                    for chunk in r.iter_content(chunk_size=8192):
                        if chunk:
                            f.write(chunk)

            # after download, run the ETL job pipeline
            if redis_client:
                try:
                    redis_client.hset(key_inner, mapping={"status": "processing", "path": dest})
                except Exception:
                    pass
            else:
                with open(os.path.join(ETL_RESULTS_DIR, f"{job_id_inner}.json"), "w", encoding="utf-8") as f:
                    json.dump({"status": "processing", "path": dest}, f, ensure_ascii=False)

            # call ETL (synchronous) and store result
            resultado = executar_pipeline_etl_csv(dest)
            entry = {"status": "done", "result": resultado, "path": dest}
            if redis_client:
                try:
                    redis_client.hset(key_inner, mapping={"status": "done", "result": json.dumps(resultado, ensure_ascii=False)})
                except Exception:
                    pass
            else:
                with open(os.path.join(ETL_RESULTS_DIR, f"{job_id_inner}.json"), "w", encoding="utf-8") as f:
                    json.dump(entry, f, ensure_ascii=False)
        except Exception as e:
            entry = {"status": "error", "error": str(e)}
            if redis_client:
                try:
                    redis_client.hset(key_inner, mapping={"status": "error", "error": str(e)})
                except Exception:
                    pass
            else:
                with open(os.path.join(ETL_RESULTS_DIR, f"{job_id_inner}.json"), "w", encoding="utf-8") as f:
                    json.dump(entry, f, ensure_ascii=False)

    # schedule background downloader + ETL
    asyncio.create_task(_download_and_process(job_id, url, dest_path))

    return JSONResponse(content={"status": "ok", "job_id": job_id, "path": dest_path})


async def transmitir_evento(mensagem: dict):
    for ws in conexoes_ativas:
        try:
            await ws.send_json(mensagem)
        except:
            pass

if __name__ == "__main__":
    # Run server (uvicorn)
    uvicorn.run(app, host="0.0.0.0", port=8000, log_level="error")