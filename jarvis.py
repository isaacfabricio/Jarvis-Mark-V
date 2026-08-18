"""Runner simples para o CLI Jarvis.

Este arquivo insere src/ no PYTHONPATH para facilitar execução durante
o desenvolvimento. Use assim:

  export GEMINI_API_KEY="sua_chave_aqui"
  pip install -r requirements.txt
  python jarvis.py listen

"""
from __future__ import annotations
import os
import sys

# Adiciona src/ ao PYTHONPATH para rodar o pacote localmente
ROOT = os.path.dirname(__file__)
SRC = os.path.join(ROOT, "src")
if SRC not in sys.path:
    sys.path.insert(0, SRC)

from jarvis.cli import app


if __name__ == "__main__":
    app()
