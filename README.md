Jarvis — Assistente CLI (scaffold inicial)
=======================================

Objetivo
--------
Este repositório contém um scaffold inicial para o Jarvis CLI em Python.
O objetivo é construir um assistente que interprete comandos em linguagem natural
(usando um LLM) e execute tarefas como gestão de loja (Shein), geração de
planilhas com Power Query e criação de dashboards Power BI.

Como executar (desenvolvimento)
--------------------------------
1. Instale dependências (recomenda-se um virtualenv):

   python -m pip install -r requirements.txt

2. Configure a variável de ambiente com sua chave Gemini (conforme você informou):

   export GEMINI_API_KEY="SUA_CHAVE_GEMINI"

3. Rode o modo interativo (REPL):

   python jarvis.py listen

4. Ou execute um comando único:

   python jarvis.py run "listar pedidos dos últimos 7 dias"

Observações importantes
----------------------
- O módulo jarvis.llm.call_llm atualmente é um stub que exige implementação do
  adaptador para o provedor Gemini/Google GenAI. Há comentários no arquivo
  jarvis/llm.py com instruções de onde implementar o wrapper.

- Para desenvolvimento offline ou como fallback, o sistema já tem uma heurística
  simples em jarvis/nlu.py que identifica intents básicas (pedidos, produtos,
  planilhas, dashboards).

Próximos passos sugeridos
-------------------------
- Implementar o adaptador Gemini (usar google-genai ou outro cliente compatível).
- Implementar os handlers em jarvis/commands.py: conector Shein, gerador de
  Power Query M, gerador de templates Power BI (.pbit/.pbix) ou instruções para
  importação.
- Adicionar testes unitários e integração contínua.

Se desejar, posso:
- Implementar agora o adaptador Gemini (se você confirmar que pode fornecer a
  chave via GEMINI_API_KEY e confirmar o método de autenticação que prefere),
- Criar handlers iniciais que gerem um template Power Query M a partir de um
  CSV de exemplo,
- Ou construir o NLU mais robusto para interpretar frases em português.

Sou um assistente de IA usando Copilot CLI runtime em VS Code — diga qual
próxima tarefa prefere que execute e começo a implementá-la.
