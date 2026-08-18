"""CLI do Jarvis — ponto de entrada Typer.

Comandos principais:
- listen: modo interativo (REPL) para comandos em linguagem natural
- run: executar um comando curto (string)

O LLM usado é abstraído em jarvis.llm e requer GEMINI_API_KEY na variável de ambiente.
"""
from __future__ import annotations
import os
import sys
import typer
from .nlu import interpret_command

app = typer.Typer()


@app.command()
def run(command: str):
    """Executa um único comando em linguagem natural."""
    key = os.getenv("GEMINI_API_KEY")
    if not key:
        typer.echo("Variável de ambiente GEMINI_API_KEY não encontrada. Configure-a antes de rodar.")
        raise typer.Exit(code=1)

    typer.echo(f"Interpretando comando: {command}")
    intent = interpret_command(command)
    typer.echo(f"Intent detectada: {intent}")
    # despacha a intent para os comandos implementados
    from .commands import execute_intent
    if isinstance(intent, dict):
        result = execute_intent(intent.get("intent", "unknown"), intent.get("params", {}))
    else:
        # Caso a NLU retorne string inesperada
        result = execute_intent(str(intent), {})
    typer.echo("Resultado:")
    typer.echo(result)


@app.command()
def listen():
    """Modo interativo: digite comandos em linguagem natural (REPL)."""
    key = os.getenv("GEMINI_API_KEY")
    if not key:
        typer.echo("Variável de ambiente GEMINI_API_KEY não encontrada. Configure-a antes de rodar.")
        raise typer.Exit(code=1)

    typer.echo("Jarvis (REPL) — digite 'sair' para encerrar")
    while True:
        try:
            text = typer.prompt("Você")
        except (EOFError, KeyboardInterrupt):
            typer.echo("\nEncerrando Jarvis.")
            raise typer.Exit()
        if text.strip().lower() in ("sair", "exit", "quit"):
            typer.echo("Até mais.")
            raise typer.Exit()
        intent = interpret_command(text)
        typer.echo(f"Intent: {intent}")
        from .commands import execute_intent
        if isinstance(intent, dict):
            result = execute_intent(intent.get("intent", "unknown"), intent.get("params", {}))
        else:
            result = execute_intent(str(intent), {})
        typer.echo("Resultado:")
        typer.echo(result)


if __name__ == "__main__":
    app()
