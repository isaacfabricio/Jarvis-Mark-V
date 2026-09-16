"""
Ponto de entrada principal do J.A.R.V.I.S. Mark V.
Inicializa o ecossistema, aplica o hardening de segurança e abre a interface de terminal.
"""
import sys
import logging

# Configuração de logs para manter o console limpo e profissional
logging.basicConfig(level=logging.INFO, format="[%(levelname)s] %(message)s")
logger = logging.getLogger(__name__)

# Importa a validação de segurança
from ops.hardening import aplicar_hardening_sistema
# Importa o motor do agente refatorado
from app.services.claude_service import executar_comando

def main():
    print("==================================================")
    print("  J.A.R.V.I.S. Mark V (Strands Protocol) Online   ")
    print("==================================================\n")
    
    # 1. Validação de Segurança (Fail-Fast)
    aplicar_hardening_sistema()
    
    print("\n[STATUS] Sistemas vitais operacionais e blindados.")
    print("Aguardando comandos. (Digite 'sair' para encerrar)\n")
    
    # 2. Loop de Interação Contínua no Terminal
    while True:
        try:
            comando = input("\nSenhor > ")
            
            if comando.lower() in ['sair', 'exit', 'quit']:
                print("\n[STATUS] Desligando motores cognitivos. Até logo.")
                break
            
            if not comando.strip():
                continue
                
            # Aciona o Strands Agents para resolver o problema
            resposta = executar_comando(comando)
            
            print(f"\nJ.A.R.V.I.S. > {resposta}")
            
        except KeyboardInterrupt:
            print("\n\n[AVISO] Desligamento forçado (CTRL+C). Encerrando processos.")
            sys.exit(0)
        except Exception as exc:
            logger.error("Falha crítica durante a execução do loop agentico: %s", exc)

if __name__ == "__main__":
    main()
