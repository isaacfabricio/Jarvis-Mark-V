"""Serviço de Navegação Headless via Playwright."""
from playwright.async_api import async_playwright
import logging

logger = logging.getLogger(__name__)

async def raspar_pagina_web(url: str, seletor_css: str = None) -> dict:
    logger.info("Iniciando navegação autônoma em: %s", url)
    async with async_playwright() as p:
        try:
            browser = await p.chromium.launch(headless=True)
            page = await browser.new_page()
            await page.goto(url, timeout=15000)
            
            if seletor_css:
                conteudo = await page.locator(seletor_css).inner_text()
            else:
                conteudo = await page.evaluate("document.body.innerText")
            
            # Limpa quebras de linha excessivas para poupar tokens
            conteudo_limpo = " ".join(conteudo.split())[:5000] # Limite de segurança de 5k caracteres
            
            await browser.close()
            return {"sucesso": True, "url": url, "conteudo_extraido": conteudo_limpo}
        except Exception as e:
            logger.error("Erro ao navegar: %s", e)
            return {"sucesso": False, "erro": str(e)}
