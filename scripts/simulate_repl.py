"""Script de simulação: executa interações de exemplo com a NLU/dispatcher sem LLM/Tavily.

Roda alguns comandos de exemplo e mostra a saída que o REPL exibiria.
"""
from __future__ import annotations
import os
from jarvis.nlu import interpret_command
from jarvis.commands import execute_intent

EXAMPLES = [
    "listar pedidos dos últimos 7 dias",
    "buscar na web preço do produto X",
    "buscar na web notícias sobre Shein",
    "criar uma planilha com vendas semanais",
]

def run():
    print("=== Simulação REPL Jarvis (local, sem LLM/Tavily) ===\n")
    # Forçar simulate via variável para buscas
    os.environ.setdefault("JARVIS_SIMULATE", "1")

    for cmd in EXAMPLES:
        print(f">>> Você: {cmd}")
        intent = interpret_command(cmd)
        print(f"Intent detectada: {intent}")
        if isinstance(intent, dict):
            result = execute_intent(intent.get("intent", "unknown"), intent.get("params", {}))
        else:
            result = execute_intent(str(intent), {})
        print("Resultado:")
        print(result)
        print("---\n")

if __name__ == "__main__":
    run()
