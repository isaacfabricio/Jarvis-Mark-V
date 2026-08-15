import { useCallback, useEffect, useMemo, useRef, useState } from "react";
import {
  Activity,
  Bot,
  ChevronDown,
  Clock3,
  Cpu,
  Globe2,
  KeyRound,
  Link2,
  MemoryStick,
  Mic2,
  Radio,
  RotateCw,
  Send,
  Settings2,
  ShieldCheck,
  Terminal,
  Volume2,
  VolumeX,
  Wifi,
  WifiOff,
  X,
  Zap,
} from "lucide-react";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { Textarea } from "@/components/ui/textarea";
import {
  buildWebSocketUrl,
  clampTelemetryMetric,
  getHandshakeDetail,
  getQuickProtocolCommand,
  getVoiceErrorMessage,
  parseJarvisMessage,
  reduceJarvisStatus,
  type HandshakeState,
  type JarvisStatus,
  type LogAuthor,
} from "@shared/jarvisProtocol";
import { transitionHudFlow } from "@shared/jarvisHudFlow";
import { buildReconnectPlan, extractSpeechTranscript, getSpeechSynthesisSettings } from "@shared/jarvisRuntime";

const DEFAULT_WS_BASE = "ws://127.0.0.1:8000/ws";
const MAX_TELEMETRY_POINTS = 26;

type ConnectionState = "disconnected" | "connecting" | "connected";
interface BrowserSpeechResult {
  0?: { transcript?: string };
}

interface BrowserSpeechRecognition {
  lang: string;
  continuous: boolean;
  interimResults: boolean;
  start(): void;
  stop(): void;
  onstart: (() => void) | null;
  onresult: ((event: { results?: BrowserSpeechResult[] }) => void) | null;
  onerror: ((event: { error?: string }) => void) | null;
  onend: (() => void) | null;
}

type BrowserSpeechRecognitionConstructor = new () => BrowserSpeechRecognition;
type LogEntry = {
  id: number;
  author: LogAuthor;
  message: string;
  timestamp: string;
  status?: JarvisStatus;
};

type TelemetryPoint = {
  cpu: number;
  ram: number;
  timestamp: number;
};

const initialLogs: LogEntry[] = [
  {
    id: 1,
    author: "SYSTEM",
    message: "Interface cognitiva inicializada. Configure um enlace WebSocket seguro para começar.",
    timestamp: new Date().toISOString(),
  },
  {
    id: 2,
    author: "SYSTEM",
    message: "Matriz da HUD online // aguardando handshake do Cérebro Central.",
    timestamp: new Date().toISOString(),
  },
];

const initialTelemetry = Array.from({ length: 26 }, (_, index) => ({
  cpu: 0,
  ram: 0,
  timestamp: Date.now() - (25 - index) * 1800,
}));

function formatTime(timestamp: string | number) {
  return new Intl.DateTimeFormat("en-GB", {
    hour: "2-digit",
    minute: "2-digit",
    second: "2-digit",
  }).format(new Date(timestamp));
}

function appendLog(
  setLogs: React.Dispatch<React.SetStateAction<LogEntry[]>>,
  author: LogAuthor,
  message: string,
  status?: JarvisStatus,
) {
  if (!message.trim()) return;
  setLogs((current) => [
    ...current,
    {
      id: Date.now() + Math.random(),
      author,
      message: message.trim(),
      timestamp: new Date().toISOString(),
      status,
    },
  ]);
}

function StatusPill({ state }: { state: ConnectionState }) {
  const config = {
    connected: { label: "CONEXÃO ESTÁVEL", className: "is-connected", icon: Wifi },
    connecting: { label: "CONECTANDO...", className: "is-connecting", icon: RotateCw },
    disconnected: { label: "DESCONECTADO", className: "is-disconnected", icon: WifiOff },
  }[state];
  const Icon = config.icon;

  return (
    <div className={`status-pill ${config.className}`} aria-live="polite">
      <Icon size={13} className={state === "connecting" ? "spin-slow" : ""} />
      <span>{config.label}</span>
      <span className="status-dot" aria-hidden="true" />
    </div>
  );
}

function TelemetryChart({
  points,
  metric,
  color,
}: {
  points: TelemetryPoint[];
  metric: "cpu" | "ram";
  color: "cyan" | "gold";
}) {
  return (
    <div className={`telemetry-bars telemetry-bars-${color}`} aria-label={`${metric} telemetry chart`}>
      {points.map((point, index) => {
        const value = clampTelemetryMetric(point[metric]);
        return (
          <span
            key={`${point.timestamp}-${index}`}
            className="telemetry-bar"
            style={{ height: `${Math.max(value, 3)}%` }}
            title={`${value.toFixed(0)}% at ${formatTime(point.timestamp)}`}
          />
        );
      })}
    </div>
  );
}

function CoreStatus({ status }: { status: JarvisStatus }) {
  return (
    <section className={`core-panel core-${status.toLowerCase()}`} aria-label={`Status do JARVIS: ${status}`}>
      <div className="core-topline">
        <span>NÚCLEO NEURAL // MK-V</span>
        <span className="core-serial">JV-07.84</span>
      </div>
      <div className="core-stage">
        <div className="core-orbit orbit-outer" />
        <div className="core-orbit orbit-middle" />
        <div className="core-orbit orbit-inner" />
        <div className="core-crosshair crosshair-horizontal" />
        <div className="core-crosshair crosshair-vertical" />
        <div className="core-scanline" />
        <div className="core-energy-ring" />
        <div className="core-spark spark-one" />
        <div className="core-spark spark-two" />
        <div className="core-spark spark-three" />
        <div className="core-spark spark-four" />
        <div className="core-center">
          <Bot size={24} strokeWidth={1.4} />
          <span>J</span>
        </div>
        <div className="core-radial-label label-top">ENLACE SINÁPTICO</div>
        <div className="core-radial-label label-bottom">ENERGIA 98,4%</div>
        <div className="core-radial-label label-left">A-17</div>
        <div className="core-radial-label label-right">NÚCLEO IA</div>
      </div>
      <div className="core-status-block">
        <div className="eyebrow">ESTADO OPERACIONAL ATUAL</div>
        <div className="core-status-text">{status}</div>
        <p>
          {status === "STANDBY"
            ? "Todos os sistemas nominais. Aguardando seu comando."
            : status === "THINKING"
              ? "Caminhos cognitivos ativos. Processando comando."
              : "Síntese de voz ativa. Canal de resposta aberto."}
        </p>
      </div>
      <div className="core-microstats">
        <span><i /> LATÊNCIA 28MS</span>
        <span><i /> VOZ PRONTA</span>
        <span><i /> COFRE SELADO</span>
      </div>
    </section>
  );
}

function LogRow({ entry }: { entry: LogEntry }) {
  const authorLabel = entry.author === "USER" ? "VOCÊ" : entry.author === "SYSTEM" ? "SISTEMA" : "JARVIS";
  return (
    <article className={`log-row log-${entry.author.toLowerCase()}`}>
      <div className="log-marker" aria-hidden="true" />
      <div className="log-row-content">
        <div className="log-row-meta">
          <span className="log-author">{authorLabel}</span>
          {entry.status && <span className="log-state">{entry.status}</span>}
          <time dateTime={entry.timestamp}>{formatTime(entry.timestamp)}</time>
        </div>
        <p>{entry.message}</p>
      </div>
    </article>
  );
}

export default function Home() {
  const [status, setStatus] = useState<JarvisStatus>("STANDBY");
  const [connectionState, setConnectionState] = useState<ConnectionState>("disconnected");
  const [serverUrl, setServerUrl] = useState(DEFAULT_WS_BASE);
  const [token, setToken] = useState("");
  const [command, setCommand] = useState("");
  const [logs, setLogs] = useState<LogEntry[]>(initialLogs);
  const [telemetry, setTelemetry] = useState<TelemetryPoint[]>(initialTelemetry);
  const [showConnection, setShowConnection] = useState(false);
  const [handshakeState, setHandshakeState] = useState<HandshakeState>("idle");
  const [handshakeDetail, setHandshakeDetail] = useState(() => getHandshakeDetail("idle"));
  const [isListening, setIsListening] = useState(false);
  const [voiceEnabled, setVoiceEnabled] = useState(true);
  const [isSpeaking, setIsSpeaking] = useState(false);
  const socketRef = useRef<WebSocket | null>(null);
  const reconnectTimerRef = useRef<number | null>(null);
  const reconnectAttemptRef = useRef(0);
  const manualCloseRef = useRef(false);
  const connectRef = useRef<() => void>(() => undefined);
  const speechRef = useRef<BrowserSpeechRecognition | null>(null);
  const commandRef = useRef<HTMLTextAreaElement>(null);

  useEffect(() => {
    const savedServerUrl = window.localStorage.getItem("jarvis.serverUrl");
    const savedToken = window.sessionStorage.getItem("jarvis.token");
    if (savedServerUrl) setServerUrl(savedServerUrl);
    if (savedToken) setToken(savedToken);
  }, []);

  useEffect(() => {
    window.localStorage.setItem("jarvis.serverUrl", serverUrl);
    window.sessionStorage.setItem("jarvis.token", token);
    window.localStorage.removeItem("jarvis.token");
  }, [serverUrl, token]);

  useEffect(() => {
    const speechWindow = window as Window & {
      SpeechRecognition?: BrowserSpeechRecognitionConstructor;
      webkitSpeechRecognition?: BrowserSpeechRecognitionConstructor;
    };
    const Recognition = speechWindow.SpeechRecognition ?? speechWindow.webkitSpeechRecognition;
    if (!Recognition) return;

    const recognition = new Recognition();
    recognition.lang = "pt-BR";
    recognition.continuous = false;
    recognition.interimResults = false;
    recognition.onstart = () => setIsListening(true);
    recognition.onresult = (event) => {
      const transcript = extractSpeechTranscript(event.results);
      if (transcript) setCommand((current) => current ? `${current} ${transcript}` : transcript);
    };
    recognition.onerror = (event) => {
      setIsListening(false);
      appendLog(setLogs, `SYSTEM`, getVoiceErrorMessage(event.error));
    };
    recognition.onend = () => setIsListening(false);
    speechRef.current = recognition;

    return () => {
      recognition.stop();
      speechRef.current = null;
    };
  }, []);

  useEffect(() => {
    const handleShortcut = (event: KeyboardEvent) => {
      if ((event.metaKey || event.ctrlKey) && event.key.toLowerCase() === "k") {
        event.preventDefault();
        commandRef.current?.focus();
      }
    };
    window.addEventListener("keydown", handleShortcut);
    return () => window.removeEventListener("keydown", handleShortcut);
  }, []);

  const speakText = useCallback((text: string) => {
    if (!voiceEnabled || !("speechSynthesis" in window) || !text.trim()) return;
    window.speechSynthesis.cancel();
    const utterance = new SpeechSynthesisUtterance(text);
    const speechSettings = getSpeechSynthesisSettings();
    utterance.lang = speechSettings.lang;
    utterance.rate = speechSettings.rate;
    utterance.pitch = speechSettings.pitch;
    utterance.onstart = () => setIsSpeaking(true);
    utterance.onend = () => setIsSpeaking(false);
    utterance.onerror = () => setIsSpeaking(false);
    window.speechSynthesis.speak(utterance);
  }, [voiceEnabled]);

  useEffect(() => {
    if (!voiceEnabled && "speechSynthesis" in window) {
      window.speechSynthesis.cancel();
      setIsSpeaking(false);
    }
  }, [voiceEnabled]);

  const disconnect = useCallback((writeLog = true) => {
    manualCloseRef.current = true;
    if (reconnectTimerRef.current) {
      window.clearTimeout(reconnectTimerRef.current);
      reconnectTimerRef.current = null;
    }
    const socket = socketRef.current;
    socketRef.current = null;
    if (socket && (socket.readyState === WebSocket.OPEN || socket.readyState === WebSocket.CONNECTING)) {
      socket.close(1000, "Manual disconnect");
    }
    setConnectionState("disconnected");
    setHandshakeState("idle");
    setHandshakeDetail(getHandshakeDetail("idle"));
    setStatus((current) => reduceJarvisStatus(current, { type: "RESET" }));
    if (writeLog) appendLog(setLogs, "SYSTEM", "Enlace WebSocket encerrado pelo operador.");
  }, []);

  const connect = useCallback(() => {
    manualCloseRef.current = false;
    reconnectAttemptRef.current = 0;
    if (reconnectTimerRef.current) {
      window.clearTimeout(reconnectTimerRef.current);
      reconnectTimerRef.current = null;
    }
    const websocketUrl = buildWebSocketUrl(serverUrl, token);
    if (!websocketUrl) {
      setConnectionState("disconnected");
      setHandshakeState("failed");
      setHandshakeDetail(getHandshakeDetail("failed"));
      appendLog(setLogs, "SYSTEM", "Conexão bloqueada: a URL do servidor e o token são obrigatórios.");
      setShowConnection(true);
      return;
    }

    const previousSocket = socketRef.current;
    if (previousSocket && (previousSocket.readyState === WebSocket.OPEN || previousSocket.readyState === WebSocket.CONNECTING)) {
      previousSocket.close(1000, "Replacing uplink");
    }
    setConnectionState("connecting");
    setHandshakeState("pending");
    setHandshakeDetail(getHandshakeDetail("pending"));
    appendLog(setLogs, "SYSTEM", `Abrindo enlace seguro para ${websocketUrl.replace(token, "••••••")}.`);

    let socket: WebSocket;
    try {
      socket = new WebSocket(websocketUrl);
    } catch {
      setConnectionState("disconnected");
      setHandshakeState("failed");
      setHandshakeDetail(getHandshakeDetail("failed"));
      appendLog(setLogs, "SYSTEM", "Não foi possível criar a conexão WebSocket.");
      return;
    }

    socketRef.current = socket;
    socket.onopen = () => {
      reconnectAttemptRef.current = 0;
      setConnectionState("connected");
      setHandshakeState("verified");
      setHandshakeDetail(getHandshakeDetail("verified"));
      setStatus((current) => reduceJarvisStatus(current, { type: "RESET" }));
      appendLog(setLogs, "SYSTEM", "Handshake do Cérebro Central aceito. JARVIS_TOKEN verificado.");
    };
    socket.onmessage = (event) => {
      const parsed = parseJarvisMessage(event.data);
      if (parsed.kind === "telemetry") {
        setTelemetry((current) => [
          ...current.slice(-(MAX_TELEMETRY_POINTS - 1)),
          { cpu: parsed.cpu, ram: parsed.ram, timestamp: Date.now() },
        ]);
        return;
      }
      if (parsed.kind === "event") {
        const flow = transitionHudFlow({ status: parsed.status ?? "STANDBY", voiceEnabled }, { type: "MESSAGE_RECEIVED", message: parsed });
        setStatus((current) => transitionHudFlow({ status: current, voiceEnabled }, { type: "MESSAGE_RECEIVED", message: parsed }).state.status);
        flow.effects.forEach((effect) => {
          if (effect.type === "LOG") appendLog(setLogs, effect.author, effect.message, effect.status);
          if (effect.type === "SPEAK") speakText(effect.text);
          if (effect.type === "RETURN_TO_STANDBY") {
            window.setTimeout(() => setStatus((current) => transitionHudFlow({ status: current, voiceEnabled }, { type: "SPEECH_COMPLETE" }).state.status), effect.delayMs);
          }
        });
        return;
      }
      appendLog(setLogs, "SYSTEM", parsed.message);
    };
    socket.onerror = () => {
      setHandshakeState("failed");
      setHandshakeDetail(getHandshakeDetail("failed"));
      appendLog(setLogs, "SYSTEM", "Erro no enlace WebSocket. Verifique o servidor e o JARVIS_TOKEN.");
    };
    socket.onclose = (event) => {
      if (socketRef.current !== socket) return;
      socketRef.current = null;
      setConnectionState("disconnected");
      setStatus((current) => reduceJarvisStatus(current, { type: "RESET" }));
      if (manualCloseRef.current || event.code === 1000) return;

      const attempt = reconnectAttemptRef.current + 1;
      reconnectAttemptRef.current = attempt;
      const reconnectPlan = buildReconnectPlan(attempt);
      setHandshakeState(reconnectPlan.shouldRetry ? "pending" : "failed");
      setHandshakeDetail(reconnectPlan.detail);
      if (reconnectPlan.shouldRetry) {
        reconnectTimerRef.current = window.setTimeout(() => connectRef.current(), reconnectPlan.delayMs);
      }
    };
  }, [serverUrl, token, speakText, voiceEnabled]);

  connectRef.current = connect;
  useEffect(() => () => disconnect(false), [disconnect]);

  const transmitCommand = useCallback((rawCommand: string, clearInput = false) => {
    const message = rawCommand.trim();
    const socket = socketRef.current;
    if (!message) return;
    if (!socket || socket.readyState !== WebSocket.OPEN) {
      appendLog(setLogs, "SYSTEM", "Comando não enviado: estabeleça o enlace primeiro.");
      setShowConnection(true);
      return;
    }
    const commandFlow = transitionHudFlow({ status: "STANDBY", voiceEnabled }, { type: "COMMAND_SENT", command: message });
    const sendEffect = commandFlow.effects.find((effect) => effect.type === "SEND_COMMAND");
    if (sendEffect?.type !== "SEND_COMMAND") return;
    socket.send(sendEffect.payload);
    if (clearInput) setCommand("");
    setStatus((current) => transitionHudFlow({ status: current, voiceEnabled }, { type: "COMMAND_SENT", command: message }).state.status);
    commandFlow.effects.forEach((effect) => {
      if (effect.type === "LOG") appendLog(setLogs, effect.author, effect.message, effect.status);
    });
  }, [voiceEnabled]);

  const sendCommand = useCallback(() => {
    transmitCommand(command, true);
  }, [command, transmitCommand]);

  const toggleListening = useCallback(() => {
    const recognition = speechRef.current;
    if (!recognition) {
      appendLog(setLogs, "SYSTEM", "A interface do microfone não está disponível neste navegador.");
      return;
    }
    if (isListening) {
      recognition.stop();
      setIsListening(false);
      return;
    }
    try {
      recognition.start();
    } catch {
      appendLog(setLogs, "SYSTEM", "O microfone já está calibrando ou aguarda permissão.");
    }
  }, [isListening]);

  const latestTelemetry = telemetry[telemetry.length - 1] ?? { cpu: 0, ram: 0 };
  const timelineLabel = useMemo(() => {
    if (connectionState === "connected") return "TELEMETRIA AO VIVO // CICLO DE 1,8s";
    if (connectionState === "connecting") return "CALIBRANDO MATRIZ DE SENSORES";
    return "BUFFER DE TELEMETRIA // SEM ENLACE";
  }, [connectionState]);

  return (
    <main className="hud-app">
      <div className="hud-grid" aria-hidden="true" />
      <div className="hud-scanlines" aria-hidden="true" />
      <div className="hud-vignette" aria-hidden="true" />

      <header className="hud-header">
        <div className="brand-lockup">
          <div className="brand-mark"><span>J</span></div>
          <div>
            <div className="brand-name">JARVIS</div>
            <div className="brand-subtitle">SISTEMA COGNITIVO PESSOAL // MARK V</div>
          </div>
        </div>
        <div className="header-center-readout">
          <span className="header-rule" />
          <span>INTERFACE DE COMANDO</span>
          <span className="header-rule header-rule-right" />
        </div>
        <div className="header-actions">
          <StatusPill state={connectionState} />
          <Button
            variant="ghost"
            size="icon"
            className={`hud-icon-button voice-toggle ${voiceEnabled ? "is-active" : ""} ${isSpeaking ? "is-speaking" : ""}`}
            onClick={() => setVoiceEnabled((current) => !current)}
            aria-label={voiceEnabled ? "Desativar voz do JARVIS" : "Ativar voz do JARVIS"}
            title={voiceEnabled ? "Saída de voz ativada" : "Saída de voz desativada"}
          >
            {voiceEnabled ? <Volume2 size={17} /> : <VolumeX size={17} />}
          </Button>
          <Button
            variant="ghost"
            size="icon"
            className="hud-icon-button"
            onClick={() => setShowConnection((current) => !current)}
            aria-label="Abrir configurações de conexão"
          >
            <Settings2 size={18} />
          </Button>
        </div>
      </header>

      <div className="hud-content">
        <aside className="hud-rail hud-rail-left">
          <div className="rail-title"><span /> DIAGNÓSTICO DO NÚCLEO</div>
          <div className="side-stat-card">
            <div className="side-stat-label"><Cpu size={14} /> CARGA DO PROCESSADOR</div>
            <div className="side-stat-value">{latestTelemetry.cpu.toFixed(0)}<small>%</small></div>
            <div className="mini-meter"><span style={{ width: `${latestTelemetry.cpu}%` }} /></div>
            <div className="side-stat-foot"><span>MATRIZ DE THREADS</span><span>IDEAL</span></div>
          </div>
          <div className="side-stat-card">
            <div className="side-stat-label"><MemoryStick size={14} /> ALOCAÇÃO DE MEMÓRIA</div>
            <div className="side-stat-value">{latestTelemetry.ram.toFixed(0)}<small>%</small></div>
            <div className="mini-meter meter-gold"><span style={{ width: `${latestTelemetry.ram}%` }} /></div>
            <div className="side-stat-foot"><span>CACHE DO COFRE</span><span>SELADO</span></div>
          </div>
          <div className="diagnostic-list">
            <div><span className="diagnostic-dot is-good" /> CAMINHOS NEURAIS <b>PRONTO</b></div>
            <div><span className="diagnostic-dot is-good" /> SÍNTESE DE VOZ <b>PRONTO</b></div>
            <div><span className="diagnostic-dot is-gold" /> MODELO LOCAL <b>STANDBY</b></div>
            <div><span className="diagnostic-dot is-good" /> CRIPTOGRAFIA <b>AES-256</b></div>
          </div>
          <div className="rail-footnote"><ShieldCheck size={14} /> TODOS OS SISTEMAS MONITORADOS</div>
        </aside>

        <section className="hud-main-column">
          <div className="main-intro">
            <div>
              <div className="eyebrow"><span className="eyebrow-line" /> TELEMETRIA COGNITIVA AO VIVO</div>
              <h1>Bem-vindo de volta, <em>Operador.</em></h1>
            </div>
            <div className="command-hint"><span>CTRL</span><span>+</span><span>K</span> FOCO NO COMANDO</div>
          </div>

          <CoreStatus status={status} />

          <section className="command-deck">
            <div className="deck-rivet rivet-one" />
            <div className="deck-rivet rivet-two" />
            <div className="deck-headline"><span><Terminal size={14} /> CANAL DE COMANDO</span><span className="deck-lock"><LockGlyph /> CRIPTOGRAFADO</span></div>
            <div className="command-input-wrap">
              <Textarea
                ref={commandRef}
                value={command}
                onChange={(event) => setCommand(event.target.value)}
                onKeyDown={(event) => {
                  if (event.key === "Enter" && !event.shiftKey) {
                    event.preventDefault();
                    sendCommand();
                  }
                }}
                placeholder="Transmita um comando para o JARVIS..."
                className="command-input"
                rows={1}
                aria-label="Comando para o JARVIS"
              />
              <Button
                variant="ghost"
                size="icon"
                className={`mic-button ${isListening ? "is-listening" : ""}`}
                onClick={toggleListening}
                aria-label={isListening ? "Parar microfone" : "Iniciar microfone"}
                title={isListening ? "Parar microfone" : "Iniciar microfone"}
              >
                <Mic2 size={18} />
              </Button>
              <Button className="send-button" onClick={sendCommand} disabled={connectionState !== "connected" || !command.trim()}>
                <Send size={16} /> ENVIAR
              </Button>
            </div>
            <div className="command-footer"><span>PRESSIONE ENTER PARA ENVIAR</span><span>SHIFT + ENTER PARA NOVA LINHA</span></div>
          </section>
          <section className="quick-actions" aria-label="Protocolos rápidos do JARVIS">
            <div className="quick-actions-head"><span><Zap size={13} /> PROTOCOLOS RÁPIDOS</span><span>COMANDOS DE UM TOQUE</span></div>
            <div className="quick-action-grid">
              <Button variant="ghost" className="quick-action-button" onClick={() => transmitCommand(getQuickProtocolCommand("memory"))}>
                <span className="quick-action-index">01</span><span><strong>COFRE DE MEMÓRIAS</strong><small>Listar memórias seladas</small></span>
              </Button>
              <Button variant="ghost" className="quick-action-button quick-action-gold" onClick={() => transmitCommand(getQuickProtocolCommand("personality"))}>
                <span className="quick-action-index">02</span><span><strong>MATRIZ DE PERSONALIDADE</strong><small>Ajustar perfil de interação</small></span>
              </Button>
              <Button variant="ghost" className="quick-action-button" onClick={() => transmitCommand(getQuickProtocolCommand("diagnostic"))}>
                <span className="quick-action-index">03</span><span><strong>DIAGNÓSTICO DO SISTEMA</strong><small>Executar varredura completa</small></span>
              </Button>
            </div>
          </section>
        </section>

        <aside className="hud-rail hud-rail-right">
          <div className="telemetry-header">
            <div className="rail-title"><span /> FLUXO DE TELEMETRIA</div>
            <span className="live-indicator"><i /> AO VIVO</span>
          </div>
          <div className="telemetry-card">
            <div className="telemetry-card-header"><span><Cpu size={14} /> USO DE CPU</span><strong>{latestTelemetry.cpu.toFixed(1)}<small>%</small></strong></div>
            <TelemetryChart points={telemetry} metric="cpu" color="cyan" />
            <div className="chart-scale"><span>−30S</span><span>AGORA</span></div>
          </div>
          <div className="telemetry-card telemetry-card-gold">
            <div className="telemetry-card-header"><span><MemoryStick size={14} /> USO DE RAM</span><strong>{latestTelemetry.ram.toFixed(1)}<small>%</small></strong></div>
            <TelemetryChart points={telemetry} metric="ram" color="gold" />
            <div className="chart-scale"><span>−30S</span><span>AGORA</span></div>
          </div>
          <div className="telemetry-status"><Activity size={14} /><span>{timelineLabel}</span></div>
          <div className="right-quote"><span>“</span><p>Às vezes é preciso correr antes de aprender a andar.</p><small>— ARQUIVO DO SISTEMA // 11.04</small></div>
        </aside>
      </div>

      <section className="event-console">
        <div className="event-console-head">
          <div className="rail-title"><span /> LOG DE EVENTOS // HISTÓRICO COMPLETO DA SESSÃO</div>
          <div className="event-console-meta"><Clock3 size={13} /> {logs.length.toString().padStart(2, "0")} EVENTOS <span className="console-divider">/</span> <span className="console-live"><i /> TRANSMITINDO</span></div>
        </div>
        <div className="event-log" aria-live="polite">
          {logs.map((entry) => <LogRow key={entry.id} entry={entry} />)}
        </div>
      </section>

      <footer className="hud-footer">
        <div><Zap size={14} /> SISTEMAS CENTRAIS DO JARVIS <span>v5.0.7</span></div>
        <div className="footer-center"><span className="footer-ring" /> INTERFACE COGNITIVA SEGURA <span className="footer-ring" /></div>
        <div><Globe2 size={14} /> NÓ LOCAL <span>127.0.0.1</span></div>
      </footer>

      <div className={`connection-drawer ${showConnection ? "is-open" : ""}`} aria-hidden={!showConnection}>
        <div className="drawer-inner">
          <div className="drawer-head"><div><div className="eyebrow"><Link2 size={13} /> MATRIZ DE CONEXÃO</div><h2>Enlace WebSocket</h2></div><Button variant="ghost" size="icon" className="hud-icon-button" onClick={() => setShowConnection(false)} aria-label="Fechar configurações de conexão"><X size={18} /></Button></div>
          <p className="drawer-copy">Point the HUD at the Cérebro Central endpoint. Your token stays in this browser session and is never rendered into the event log.</p>
          <div className={`handshake-status handshake-${handshakeState}`}><span /> {handshakeDetail}</div>
          <label className="hud-field"><span><Globe2 size={13} /> URL DO SERVIDOR</span><Input value={serverUrl} onChange={(event) => setServerUrl(event.target.value)} placeholder={DEFAULT_WS_BASE} /></label>
          <label className="hud-field"><span><KeyRound size={13} /> TOKEN DE ACESSO</span><Input type="password" value={token} onChange={(event) => setToken(event.target.value)} placeholder="JARVIS_TOKEN" /></label>
          <div className="drawer-actions"><Button className="connect-button" onClick={() => { connect(); setShowConnection(false); }}><Radio size={15} /> CONECTAR ENLACE</Button><Button variant="outline" className="disconnect-button" onClick={() => disconnect()}>DESCONECTAR</Button></div>
          <div className="drawer-note"><ShieldCheck size={14} /> Expected route: <code>/ws/{"{token}"}</code></div>
        </div>
      </div>
    </main>
  );
}

function LockGlyph() {
  return <span className="lock-glyph" aria-hidden="true" />;
}
