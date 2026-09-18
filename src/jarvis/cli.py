import typer
import logging
from app.services.claude_service import executar_comando

logging.basicConfig(level=logging.INFO, format="[%(levelname)s] %(message)s")
logger = logging.getLogger(__name__)

app = typer.Typer(help="J.A.R.V.I.S. Mark V - Interface de Comando Operacional")

@app.command()
def listen():
    """Modo interativo: digite comandos em linguagem natural (REPL)."""
    print("==================================================")
    print("  J.A.R.V.I.S. Mark V (Modo Interativo) Online    ")
    print("==================================================\n")
    print("[STATUS] Sistemas vitais operacionais. Digite 'sair' para encerrar.\n")

    while True:
        try:
            comando = input("\nSenhor > ")
            if comando.lower() in ['sair', 'exit', 'quit']:
                print("\n[STATUS] Desligando motores cognitivos. Até logo.")
                break
            if not comando.strip():
                continue

            resposta = executar_comando(comando)
            print(f"\nJ.A.R.V.I.S. > {resposta}")

        except KeyboardInterrupt:
            print("\n\n[AVISO] Desligamento forçado.")
            break

@app.command()
def run(prompt: str):
    """Executa um único comando em linguagem natural repassado por argumento."""
    print(f"[PROCESSANDO] Executando instrução: {prompt}")
    resposta = executar_comando(prompt)
    print(f"\nJ.A.R.V.I.S. > {resposta}")

@app.command()
def web_search(
    query: str,
    simulate: bool = typer.Option(
        False,
        "--simulate",
        help="Executa em modo simulado sem Tavily.",
    ),
):
    """Executa uma busca web usando a integração disponível."""
    from .commands import web_search as _web_search

    result = _web_search({"query": query, "simulate": simulate})
    print("Resultado:")
    print(result)

if __name__ == "__main__":
    app()
