export const JARVIS_STATUSES = ["STANDBY", "THINKING", "SPEAKING"] as const;

export type JarvisStatus = (typeof JARVIS_STATUSES)[number];
export type LogAuthor = "USER" | "JARVIS" | "SYSTEM";
export type HandshakeState = "idle" | "pending" | "verified" | "failed";

export const QUICK_PROTOCOLS = {
  memory: "JARVIS, liste as memórias criptografadas disponíveis no Vault.",
  personality: "JARVIS, ajuste minha personalidade para humor 25%, honestidade 100% e sarcasmo 8%.",
  diagnostic: "JARVIS, execute um diagnóstico completo do sistema e informe CPU, RAM e status do uplink.",
} as const;

export type QuickProtocolKey = keyof typeof QUICK_PROTOCOLS;

export function getQuickProtocolCommand(key: QuickProtocolKey): string {
  return QUICK_PROTOCOLS[key];
}

export function getVoiceErrorMessage(error?: string): string {
  switch (error) {
    case "not-allowed":
    case "service-not-allowed":
      return "Permissão do microfone negada pelo navegador.";
    case "no-speech":
      return "Nenhuma fala detectada. Tente novamente, Senhor.";
    case "audio-capture":
      return "Nenhum dispositivo de entrada de microfone detectado.";
    default:
      return "Entrada de voz indisponível. Verifique as permissões do navegador.";
  }
}

export type CoreEvent =
  | { type: "COMMAND_SENT" }
  | { type: "SOCKET_STATUS"; status?: JarvisStatus }
  | { type: "SPEECH_COMPLETE" }
  | { type: "RESET" };

export type ParsedJarvisMessage =
  | { kind: "telemetry"; cpu: number; ram: number }
  | { kind: "event"; author: LogAuthor; message: string; status?: JarvisStatus; shouldReturnToStandby: boolean }
  | { kind: "invalid"; message: string };

export function isJarvisStatus(value: unknown): value is JarvisStatus {
  return typeof value === "string" && (JARVIS_STATUSES as readonly string[]).includes(value);
}

export function reduceJarvisStatus(current: JarvisStatus, event: CoreEvent): JarvisStatus {
  switch (event.type) {
    case "COMMAND_SENT":
      return "THINKING";
    case "SOCKET_STATUS":
      return event.status ?? current;
    case "SPEECH_COMPLETE":
    case "RESET":
      return "STANDBY";
  }
}

export function getHandshakeDetail(state: HandshakeState, retrySeconds = 0): string {
  switch (state) {
    case "pending":
      return retrySeconds > 0 ? `NOVO ENLACE EM ${retrySeconds}S` : "VALIDANDO JARVIS_TOKEN";
    case "verified":
      return "JARVIS_TOKEN ACEITO // ENLACE ESTÁVEL";
    case "failed":
      return "ERRO DE AUTENTICAÇÃO OU REDE";
    case "idle":
      return "TOKEN PRONTO PARA ENLACE";
  }
}

export function shouldSpeakJarvisReply(author: LogAuthor, voiceEnabled: boolean): boolean {
  return voiceEnabled && author === "JARVIS";
}

export function normalizeWebSocketBaseUrl(value: string): string {
  const trimmed = value.trim().replace(/\/+$/, "");
  if (!trimmed) return "";
  return trimmed.replace(/^http:/i, "ws:").replace(/^https:/i, "wss:");
}

export function buildWebSocketUrl(baseUrl: string, token: string): string {
  const normalizedBase = normalizeWebSocketBaseUrl(baseUrl);
  const normalizedToken = encodeURIComponent(token.trim());
  if (!normalizedBase || !normalizedToken) return "";
  return `${normalizedBase}/${normalizedToken}`;
}

export function clampTelemetryMetric(value: unknown): number {
  const numeric = typeof value === "number" ? value : Number(value);
  if (!Number.isFinite(numeric)) return 0;
  return Math.max(0, Math.min(100, numeric));
}

export function parseJarvisMessage(data: string): ParsedJarvisMessage {
  try {
    const payload = JSON.parse(data) as Record<string, unknown>;
    if (payload.tipo === "telemetria") {
      return {
        kind: "telemetry",
        cpu: clampTelemetryMetric(payload.cpu),
        ram: clampTelemetryMetric(payload.ram),
      };
    }

    const message = typeof payload.log === "string" ? payload.log.trim() : "";
    if (message) {
      const author: LogAuthor = payload.type === "user" ? "USER" : payload.type === "jarvis" ? "JARVIS" : "SYSTEM";
      const status = isJarvisStatus(payload.status) ? payload.status : undefined;
      return {
        kind: "event",
        author,
        message,
        status,
        shouldReturnToStandby: payload.acao === "falar",
      };
    }

    return { kind: "invalid", message: "Sinal vazio recebido do Cérebro Central." };
  } catch {
    return { kind: "invalid", message: "Sinal ilegível recebido do Cérebro Central." };
  }
}

export function serializeCommand(command: string): string {
  const normalized = command.trim();
  if (!normalized) return "";
  return JSON.stringify({ tipo: "comando", comando: normalized });
}
