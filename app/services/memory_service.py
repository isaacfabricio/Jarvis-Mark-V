"""Serviço de Memória de Longo Prazo com Mem0."""
from mem0 import Memory
import logging
import os

logger = logging.getLogger(__name__)

# Configuração local para armazenamento vetorial
# Ajuste o caminho conforme necessário para persistência no Replit
MEM_PATH = os.getenv('MEM0_DIR', './ops/memoria_vetorial')

config = {
    "vector_store": {
        "provider": "qdrant",
        "config": {"path": MEM_PATH}
    }
}

try:
    if not os.path.exists(MEM_PATH):
        os.makedirs(MEM_PATH, exist_ok=True)
    memoria_jarvis = Memory.from_config(config)
    logger.info("Sistema de memória Mem0 inicializado.")
except Exception as e:
    logger.error(f"Erro ao inicializar Mem0: {e}")
    memoria_jarvis = None

def salvar_lembranca(usuario_id: str, fato: str) -> dict:
    if not memoria_jarvis:
        return {"sucesso": False, "erro": "Sistema de memória não inicializado."}
    try:
        memoria_jarvis.add(fato, user_id=usuario_id)
        logger.info("Nova lembrança salva para %s", usuario_id)
        return {"sucesso": True, "mensagem": "Fato armazenado na memória de longo prazo."}
    except Exception as e:
        logger.error(f"Erro ao salvar lembrança: {e}")
        return {"sucesso": False, "erro": str(e)}

def buscar_lembrancas(usuario_id: str, contexto: str) -> str:
    if not memoria_jarvis:
        return "Nenhuma lembrança encontrada (sistema offline)."
    try:
        resultados = memoria_jarvis.search(contexto, user_id=usuario_id)
        fatos = [r["memory"] for r in resultados]
        return "Lembranças relevantes: " + " | ".join(fatos) if fatos else "Nenhuma lembrança encontrada."
    except Exception as e:
        logger.error(f"Erro ao buscar lembranças: {e}")
        return f"Erro ao buscar lembranças: {e}"
