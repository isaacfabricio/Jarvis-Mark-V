// Setup WebSocket connection (asks for token if not provided)
const token = window.JARVIS_TOKEN || window.localStorage.getItem('JARVIS_TOKEN') || prompt('Insira o JARVIS_TOKEN de acesso ao WebSocket:');
if (token) window.localStorage.setItem('JARVIS_TOKEN', token);
const protocol = (location.protocol === 'https:') ? 'wss' : 'ws';
const ws = new WebSocket(`${protocol}://${location.host}/ws/${token}`);

ws.onmessage = (event) => {
  const data = JSON.parse(event.data);

  if (data.type === "telemetry") {
    const cpu = Math.round(data.cpu);
    const ram = Math.round(data.ram);

    const cpuVal = document.getElementById("cpu-val");
    const ramVal = document.getElementById("ram-val");
    const cpuBar = document.getElementById("cpu-bar");
    const ramBar = document.getElementById("ram-bar");
    if (cpuVal) cpuVal.innerText = cpu + "%";
    if (ramVal) ramVal.innerText = ram + "%";
    if (cpuBar) cpuBar.style.width = cpu + "%";
    if (ramBar) ramBar.style.width = ram + "%";
  }

  if (data.log) {
    const p = document.createElement("p");
    p.style.color = data.type === "user" ? "#fff" : "#00f3ff";
    p.innerHTML = `<span style="opacity:0.5">></span> ${data.log}`;
    const log = document.getElementById("terminal-log");
    if (log) {
      log.appendChild(p);
      log.scrollTop = log.scrollHeight;
    }
  }

  if (data.status) {
    const st = document.getElementById("status-text");
    if (st) st.innerText = data.status;
    document.body.dataset.status = data.status.toLowerCase();
  }
};

ws.onopen = () => {
  const st = document.getElementById("status-text");
  if (st) st.innerText = "ONLINE";
};

ws.onclose = () => {
  const st = document.getElementById("status-text");
  if (st) st.innerText = "OFFLINE";
  document.body.dataset.status = "offline";
};

// Relógio Stark
setInterval(() => {
  const now = new Date();
  const clock = document.getElementById("clock");
  const date = document.getElementById("date");
  if (clock) clock.innerText = now.toLocaleTimeString();
  if (date) date.innerText = now.toLocaleDateString("en-GB").replace(/\//g, " ");
}, 1000);

// Função para o J.A.R.V.I.S. falar a resposta (front-end nativo)
function jarvisFalar(texto) {
    if ('speechSynthesis' in window) {
        const utterance = new SpeechSynthesisUtterance(texto);
        utterance.lang = 'pt-BR';
        utterance.pitch = 0.9; // Tom ligeiramente mais grave e metálico
        utterance.rate = 1.1;  // Resposta rápida e direta
        window.speechSynthesis.speak(utterance);
    }
}

// Captura de Comando por Voz (Speech-to-Text nativo)
function iniciarOuvidoJarvis(onResultCallback) {
    const SpeechRecognition = window.SpeechRecognition || window.webkitSpeechRecognition;
    if (!SpeechRecognition) {
        console.error("Reconhecimento de voz não suportado neste navegador.");
        return;
    }
    
    const recognition = new SpeechRecognition();
    recognition.lang = 'pt-BR';
    recognition.interimResults = false;
    
    recognition.onresult = (event) => {
        const comando = event.results[0][0].transcript;
        onResultCallback(comando);
    };
    
    recognition.onerror = (ev) => { console.error('Erro reconhecimento:', ev); };

    recognition.start();
    return recognition; // allow caller to stop if needed
}

// Conecta reconhecimento com o WebSocket: quando captar comando, envia como {comando: ...}
function habilitarComandoPorVoz() {
  iniciarOuvidoJarvis((comando) => {
    jarvisFalar('Recebido. Processando.');
    if (ws && ws.readyState === WebSocket.OPEN) {
      ws.send(JSON.stringify({comando}));
    } else {
      console.warn('WebSocket não conectado.');
    }
  });
}

// Expor funções globalmente para uso via console ou botões
window.jarvisFalar = jarvisFalar;
window.iniciarOuvidoJarvis = iniciarOuvidoJarvis;
window.habilitarComandoPorVoz = habilitarComandoPorVoz;

// Envia texto ao servidor /api/speak e reproduz o áudio retornado
async function jarvisSpeakServer(texto, voice = 'pt-BR-AntonioNeural', format = 'mp3'){
  const token = window.localStorage.getItem('JARVIS_TOKEN');
  if (!token) {
    console.error('JARVIS_TOKEN não encontrado.');
    return;
  }
  try{
    const res = await fetch('/api/speak', {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
        'Authorization': `Bearer ${token}`
      },
      body: JSON.stringify({text: texto, voice, format})
    });
    if (!res.ok) {
      const err = await res.json().catch(()=>({detail:'unknown'}));
      console.error('Erro /api/speak:', res.status, err.detail || err);
      return;
    }
    const buf = await res.arrayBuffer();
    const blob = new Blob([buf], {type: format === 'mp3' ? 'audio/mpeg' : 'audio/wav'});
    const url = URL.createObjectURL(blob);
    const audio = new Audio(url);
    audio.play();
  }catch(e){
    console.error('Falha ao chamar /api/speak', e);
  }
}

// Expor funções globalmente para uso via console ou botões
window.jarvisFalar = jarvisFalar;
window.iniciarOuvidoJarvis = iniciarOuvidoJarvis;
window.habilitarComandoPorVoz = habilitarComandoPorVoz;
window.jarvisSpeakServer = jarvisSpeakServer;
