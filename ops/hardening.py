"""Script de segurança e validação de chaves de ambiente."""
import os
import sys
import logging

logger = logging.getLogger(__name__)

def aplicar_hardening_sistema():
    """Verifica se as chaves críticas de API estão configuradas nos Secrets."""
    logger.info("Iniciando varredura de segurança do ambiente...")
    
    chaves_criticas = ['ANTHROPIC_API_KEY', 'GEMINI_API_KEY']
    chaves_ausentes = [chave for chave in chaves_criticas if not os.getenv(chave)]
    
    if chaves_ausentes:
        logger.error("FALHA DE SEGURANÇA: Chaves de API ausentes: %s", ", ".join(chaves_ausentes))
        logger.error("Configure-as na aba 'Secrets' do Replit antes de ligar o sistema.")
        sys.exit(1)
        
    logger.info("Hardening concluído. Credenciais verificadas.")
