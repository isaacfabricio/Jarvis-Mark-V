# Guia Operacional Passo a Passo — J.A.R.V.I.S. Mark V

Este documento apresenta o procedimento completo e sequencial, incluindo todas as linhas de comando e blocos de código necessários para instalar, configurar, testar e colocar em operação a interface holográfica **J.A.R.V.I.S. Mark V** integrada ao Cérebro Central [1].

---

## Passo 1: Preparação do Ambiente e Instalação de Dependências

Abra o terminal no sistema onde o projeto está localizado e navegue até a raiz da HUD JARVIS [2]:

```bash
cd /home/ubuntu/jarvis_hologram_ui
```

Certifique-se de que o gerenciador de pacotes `pnpm` e o Node.js estão disponíveis. Instale as dependências do projeto executando [2]:

```bash
pnpm install
```

---

## Passo 2: Execução da Suíte de Testes Automatizados

Antes de subir o servidor, valide se todos os contratos de protocolo, runtime de voz, reconexão e máquina de estados estão íntegros executando os testes unitários (Vitest) [3]:

```bash
pnpm test
```

*Resultado esperado:* Todos os 20 testes da suíte (`jarvisProtocol.test.ts`, `jarvisRuntime.test.ts`, `jarvisHudFlow.test.ts`, etc.) devem retornar com sucesso (*tests passed*) [3].

---

## Passo 3: Inicialização do Servidor de Desenvolvimento (HMR)

Para iniciar a interface web em modo de desenvolvimento com recarregamento a quente, execute [2]:

```bash
pnpm dev
```

O terminal exibirá a URL local e a porta ativa (por exemplo, `http://localhost:3000/`) [2]. Acesse essa URL em um navegador moderno (como Google Chrome ou Microsoft Edge) para visualizar a HUD [4].

---

## Passo 4: Configuração do Enlace WebSocket e Handshake de Segurança

Assim que a HUD estiver aberta no navegador, realize a conexão com o seu Cérebro Central:

1. Clique no botão de **Configurações (Ícone de Engrenagem)** localizado no cabeçalho superior direito da HUD [4].
2. Preencha os campos do modal de conexão:
   - **WebSocket URL:** Insira o endereço do seu backend Python ou Cérebro Central (ex: `ws://127.0.0.1:8000/ws`) [4].
   - **JARVIS Token:** Insira o token de segurança secreto compartilhado (ex: `jarvis-secret-key-2026`) [4].
3. Clique no botão **CONNECT UPLINK** [4].

A HUD validará o handshake e alterará o status de *OFFLINE* para *ONLINE (CONNECTED)*. O token é mantido com segurança na sessão do navegador (`sessionStorage`) [4].

---

## Passo 5: Testando os Protocolos Rápidos e os Canais de Voz

Com a HUD conectada:
- **Comandos de Texto:** Digite um comando no **Command Channel** na parte inferior e pressione `Enter` ou clique em `SEND` [4]. O núcleo mudará para o estado `THINKING` e depois para `SPEAKING` ao receber a resposta [4].
- **Protocolos Rápidos:** Clique nos botões de um toque na barra inferior (*Memory Vault*, *Personality Matrix* ou *System Diagnostic*) para injetar comandos predefinidos instantaneamente [4].
- **Reconhecimento e Síntese de Voz:** Clique no ícone de **Microfone** para ditar comandos por voz ou ative o ícone de **Alto-falante** no cabeçalho para que o JARVIS leia as respostas em voz alta usando a síntese nativa em português (`pt-BR`) [4].

---

## Passo 6: Compilação e Execução em Produção

Quando desejar executar a aplicação em modo de produção otimizado, utilize os comandos de build e start [2]:

```bash
# Compilar frontend e backend empacotados
pnpm build

# Iniciar o servidor em modo de produção
pnpm start
```

---

## Referências

[1] J.A.R.V.I.S. Protocol Specification. `shared/jarvisProtocol.ts`. Disponibilizado no repositório do projeto.  
[2] Project Package Configuration and Scripts. `package.json`.  
[3] Automated Test Suite. `server/jarvisProtocol.test.ts`, `server/jarvisRuntime.test.ts`, `server/jarvisHudFlow.test.ts`.  
[4] Holographic Command Center Frontend. `client/src/pages/Home.tsx`.
