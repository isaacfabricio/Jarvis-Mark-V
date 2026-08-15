# J.A.R.V.I.S. Mark V — Holographic Command Center

O **J.A.R.V.I.S. Mark V** é um centro de comando cognitivo com interface holográfica (HUD) inspirado na estética sci-fi das armaduras do Homem de Ferro. Projetado para operar conectado a um Cérebro Central via WebSocket, o sistema combina visual aerospacial em tons de ciano e dourado, tipografia Orbitron, telemetria em tempo real, reconhecimento de voz, síntese de fala e protocolos rápidos de operação.

---

## 🏗 Arquitetura do Sistema

A aplicação adota uma arquitetura reativa modulardividida entre a interface de cliente em React 19 / Tailwind CSS 4 e o protocolo compartilhado de comunicação [1].

| Módulo / Camada | Caminho Principal | Responsabilidade |
| :--- | :--- | :--- |
| **Protocolo WebSocket** | `shared/jarvisProtocol.ts` | Normalização de URLs, handshake seguro, parser de telemetria e eventos [1]. |
| **Runtime de Voz e Reconexão** | `shared/jarvisRuntime.ts` | Planos de backoff exponencial, transcrição de microfone e parâmetros de TTS [2]. |
| **Máquina de Estados HUD** | `shared/jarvisHudFlow.ts` | Orquestração pura de comandos, transições e efeitos de áudio/log [3]. |
| **Interface Visual (HUD)** | `client/src/pages/Home.tsx` | Núcleo central animado, painéis de diagnóstico e canal de comandos [4]. |
| **Testes Unitários** | `server/*.test.ts` | Suíte com 20 testes em Vitest cobrindo handshake, voz, telemetria e estados [5]. |

---

## 🚀 Funcionalidades Principais

1. **Núcleo Neural Central Animado:** Anéis concêntricos giratórios e pulsantes que refletem em tempo real o estado cognitivo do assistente: `STANDBY`, `THINKING` ou `SPEAKING` [4].
2. **Handshake e Segurança de Conexão:** Validação do `JARVIS_TOKEN` com indicador de status no drawer lateral. O token é armazenado exclusivamente na sessão do navegador (`sessionStorage`) para evitar exposição em logs ou persistência indesejada [1].
3. **Reconexão Exponencial:** Mecanismo automático de reconexão com backoff progressivo (de 1s até 30s) em caso de queda de rede ou reinicialização do Cérebro Central [2].
4. **Entrada e Saída de Voz Nativa:** Integração com a API de Reconhecimento de Fala (`SpeechRecognition`) para comandos por microfone em português e Síntese de Fala (`speechSynthesis`) para locução das respostas do JARVIS [2].
5. **Protocolos Rápidos (Quick Actions):** Atalhos de um toque integrados no rodapé do canal de comando para acessar o *Memory Vault*, a *Personality Matrix* e o *System Diagnostic* [4].

---

## 🛠 Comandos de Execução

Para iniciar o ambiente de desenvolvimento local ou rodar os testes unitários, utilize os comandos abaixo via terminal [6]:

```bash
# Instalar dependências
pnpm install

# Executar a suíte completa de testes unitários (Vitest)
pnpm test

# Iniciar o servidor de desenvolvimento com HMR
pnpm dev

# Gerar o build de produção otimizado
pnpm build
```

---

## 📚 Referências

[1] J.A.R.V.I.S. Protocol Specification. `shared/jarvisProtocol.ts`. Disponibilizado no repositório do projeto.  
[2] Browser Runtime and Voice Integration. `shared/jarvisRuntime.ts`. Disponibilizado no repositório do projeto.  
[3] HUD Cognitive State Machine. `shared/jarvisHudFlow.ts`. Disponibilizado no repositório do projeto.  
[4] Holographic Command Center Frontend. `client/src/pages/Home.tsx`. Disponibilizado no repositório do projeto.  
[5] Automated Test Suite. `server/jarvisHudFlow.test.ts`, `server/jarvisProtocol.test.ts`, `server/jarvisRuntime.test.ts`.  
[6] Project Package Configuration. `package.json`.
