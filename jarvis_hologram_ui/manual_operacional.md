# Manual Operacional — J.A.R.V.I.S. Mark V

Este manual reúne todos os comandos necessários para instalar, configurar, testar e colocar em funcionamento normal a interface holográfica **J.A.R.V.I.S. Mark V** e sua integração com o Cérebro Central via WebSocket [1].

---

## 1. Instalação e Configuração Inicial

Antes de iniciar os servidores, certifique-se de que possui o **Node.js** (versão 22 ou superior) e o gerenciador de pacotes **pnpm** instalados no ambiente [2].

```bash
# Entrar no diretório raiz do projeto JARVIS HUD
cd /home/ubuntu/jarvis_hologram_ui

# Instalar todas as dependências do projeto
pnpm install
```

---

## 2. Comandos de Execução e Desenvolvimento

O projeto oferece scripts utilitários definidos no `package.json` para cobrir desde o desenvolvimento local até o build de produção [2].

| Ação Operacional | Comando no Terminal | Descrição |
| :--- | :--- | :--- |
| **Desenvolvimento Local** | `pnpm dev` | Inicia o servidor com recarregamento a quente (HMR) e watcher [2]. |
| **Execução de Testes** | `pnpm test` | Executa a suíte de testes unitários (Vitest) para validar protocolo, voz e HUD [3]. |
| **Validação TypeScript** | `pnpm check` | Verifica a integridade dos tipos e reporta erros estáticos [2]. |
| **Build de Produção** | `pnpm build` | Compila o frontend e o backend empacotados para distribuição [2]. |
| **Execução em Produção** | `pnpm start` | Inicia o servidor otimizado em ambiente de produção (`dist/index.js`) [2]. |

---

## 3. Conectando a HUD ao Cérebro Central

Para estabelecer o enlace seguro entre a HUD e o backend do Cérebro Central (ou o agente Python), siga os passos abaixo:

1. Inicie a HUD executando `pnpm dev` ou `pnpm start` e abra a URL fornecida no navegador.
2. Clique no ícone de **Configurações (Engrenagem)** no canto superior direito para abrir o painel de Enlace WebSocket.
3. Insira a URL do servidor WebSocket (por exemplo: `ws://127.0.0.1:8000/ws`) [4].
4. Insira o token de segurança (`JARVIS_TOKEN`) fornecido pelo seu Cérebro Central [4].
5. Clique em **CONNECT UPLINK**. O indicador de status mudará para verde (*ONLINE / CONNECTED*) assim que o handshake for aceito [4].

> **Nota de Segurança:** O token de acesso é mantido exclusivamente na sessão do navegador (`sessionStorage`) e nunca é gravado permanentemente em arquivos ou logs de eventos.

---

## 4. Referências

[1] J.A.R.V.I.S. Protocol Specification. `shared/jarvisProtocol.ts`. Disponibilizado no repositório do projeto.  
[2] Project Package Configuration and Scripts. `package.json`.  
[3] Automated Test Suite. `server/jarvisProtocol.test.ts`, `server/jarvisRuntime.test.ts`, `server/jarvisHudFlow.test.ts`.  
[4] Holographic Command Center Frontend. `client/src/pages/Home.tsx`.
