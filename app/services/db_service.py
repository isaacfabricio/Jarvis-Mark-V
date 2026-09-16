"""Serviço de Interação Direta com Firebase Firestore."""
import firebase_admin
from firebase_admin import credentials, firestore
import logging
import os

logger = logging.getLogger(__name__)

# Caminho para a chave do Firebase (ajuste se necessário)
FIREBASE_KEY_PATH = os.getenv('FIREBASE_SERVICE_ACCOUNT_PATH', '/workspaces/Jarvis-Mark-V/ops/firebase-adminsdk.json')

# Inicializa com a chave de serviço do seu Firebase
if not firebase_admin._apps:
    if os.path.exists(FIREBASE_KEY_PATH):
        try:
            cred = credentials.Certificate(FIREBASE_KEY_PATH)
            firebase_admin.initialize_app(cred)
            logger.info("Firebase inicializado com sucesso.")
        except Exception as e:
            logger.error(f"Erro ao inicializar Firebase: {e}")
    else:
        logger.warning(f"Chave do Firebase não encontrada em {FIREBASE_KEY_PATH}. Consultas falharão.")

db = firestore.client() if firebase_admin._apps else None

def consultar_banco_dados(colecao: str, campo_filtro: str = None, valor_filtro: str = None) -> dict:
    if not db:
        return {"sucesso": False, "erro": "Firebase não inicializado."}
    try:
        ref = db.collection(colecao)
        if campo_filtro and valor_filtro:
            ref = ref.where(campo_filtro, "==", valor_filtro)
        
        docs = ref.stream()
        resultados = {doc.id: doc.to_dict() for doc in docs}
        
        logger.info("Consulta realizada em %s. %d registros encontrados.", colecao, len(resultados))
        return {"sucesso": True, "dados": resultados}
    except Exception as e:
        logger.error(f"Erro na consulta Firebase: {e}")
        return {"sucesso": False, "erro": str(e)}
