# Guia de Execução Windows — J.A.R.V.I.S. Mark V

Como o seu projeto está localizado na pasta **`C:\Users\tropa\OneDrive\Documentos\JARVIS`**, este guia fornece o passo a passo exato utilizando o **PowerShell** ou o **Prompt de Comando (CMD)** do Windows [1].

---

## Passo 1: Abrir o PowerShell no Diretório do Projeto

Pressione as teclas `Windows + X` no seu teclado e selecione **PowerShell** (ou abra o Terminal do Windows). Navegue até a pasta do seu projeto digitando [1]:

```powershell
cd "C:\Users\tropa\OneDrive\Documentos\JARVIS"
```

*(Nota: Se o seu projeto HUD estiver dentro de uma subpasta específica, como `jarvis_hologram_ui` ou o backend Python, entre nessa respectiva pasta com `cd nome_da_pasta`)*.

---

## Passo 2: Executar o Cérebro Central (Backend Python)

Se o seu Cérebro Central estiver em Python (por exemplo, `cerebro_api.py` ou `agente_windows.py`), abra um **novo terminal do PowerShell**, navegue até a pasta do projeto e ative o ambiente virtual antes de iniciar a API [2]:

```powershell
cd "C:\Users\tropa\OneDrive\Documentos\JARVIS"

# Ativar o ambiente virtual (caso esteja usando .venv)
.\.venv\Scripts\Activate.ps1

# Instalar dependências Python (se necessário)
pip install -r requirements.txt

# Iniciar o Cérebro Central
python cerebro_api.py
```

---

## Passo 3: Instalar e Iniciar a HUD Holográfica (Frontend Node.js)

Se a interface HUD estiver na pasta do projeto Node, abra mais um **terminal do PowerShell**, navegue até a pasta e execute os comandos de instalação e inicialização [3]:

```powershell
cd "C:\Users\tropa\OneDrive\Documentos\JARVIS"

# Instalar dependências Node.js
pnpm install

# Iniciar o servidor de desenvolvimento com HMR
pnpm dev
```

O terminal exibirá a URL local (geralmente `http://localhost:3000`). Abra essa URL no seu navegador para interagir com a HUD do JARVIS [3].

---

## Passo 4: Conectar a HUD ao WebSocket

1. Abra a HUD no navegador.
2. Clique no ícone de **Configurações (Engrenagem)** no topo direito.
3. Insira o endereço WebSocket do seu backend (ex: `ws://127.0.0.1:8000/ws`) [4].
4. Insira o seu **JARVIS_TOKEN** de acesso [4].
5. Clique em **CONNECT UPLINK** [4].

---

## Referências

[1] Windows Directory Structure for JARVIS Project. `C:\Users\tropa\OneDrive\Documentos\JARVIS`.  
[2] Python Backend Execution. `cerebro_api.py`, `requirements.txt`.  
[3] Node.js Frontend Configuration. `package.json`.  
[4] Holographic Command Center Frontend. `client/src/pages/Home.tsx`.
