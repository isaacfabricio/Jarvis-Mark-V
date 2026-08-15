const ws = new WebSocket("ws://127.0.0.1:8000/ws");
const ws = new WebSocket(`ws://127.0.0.1clear:8000/ws/${JARVIS_TOKEN}`);

ws.onmessage = (event) => {
  const data = JSON.parse(event.data);

  if (data.type === "telemetry") {
    const cpu = Math.round(data.cpu);
    const ram = Math.round(data.ram);

    document.getElementById("cpu-val").innerText = cpu + "%";
    document.getElementById("ram-val").innerText = ram + "%";
    document.getElementById("cpu-bar").style.width = cpu + "%";
    document.getElementById("ram-bar").style.width = ram + "%";
  }

  if (data.log) {
    const p = document.createElement("p");
    p.style.color = data.type === "user" ? "#fff" : "#00f3ff";
    p.innerHTML = `<span style="opacity:0.5">></span> ${data.log.toUpperCase()}`;
    const log = document.getElementById("terminal-log");
    log.appendChild(p);
    log.scrollTop = log.scrollHeight;
  }

  if (data.status) {
    document.getElementById("status-text").innerText = data.status;
    document.body.dataset.status = data.status.toLowerCase();
  }
};

ws.onopen = () => {
  document.getElementById("status-text").innerText = "ONLINE";
};

ws.onclose = () => {
  document.getElementById("status-text").innerText = "OFFLINE";
  document.body.dataset.status = "offline";
};

// Relógio Stark
setInterval(() => {
  const now = new Date();
  document.getElementById("clock").innerText = now.toLocaleTimeString();
  document.getElementById("date").innerText = now
    .toLocaleDateString("en-GB")
    .replace(/\//g, " ");
}, 1000);
