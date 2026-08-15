import { describe, expect, it } from "vitest";
import {
  buildWebSocketUrl,
  clampTelemetryMetric,
  getHandshakeDetail,
  getQuickProtocolCommand,
  getVoiceErrorMessage,
  isJarvisStatus,
  normalizeWebSocketBaseUrl,
  parseJarvisMessage,
  QUICK_PROTOCOLS,
  reduceJarvisStatus,
  serializeCommand,
  shouldSpeakJarvisReply,
} from "../shared/jarvisProtocol";

describe("JARVIS WebSocket protocol", () => {
  it("accepts only the three HUD operating states", () => {
    expect(isJarvisStatus("STANDBY")).toBe(true);
    expect(isJarvisStatus("THINKING")).toBe(true);
    expect(isJarvisStatus("SPEAKING")).toBe(true);
    expect(isJarvisStatus("ONLINE")).toBe(false);
    expect(isJarvisStatus(undefined)).toBe(false);
  });

  it("starts in STANDBY and transitions through the command lifecycle", () => {
    const initial: "STANDBY" = "STANDBY";
    const thinking = reduceJarvisStatus(initial, { type: "COMMAND_SENT" });
    const speaking = reduceJarvisStatus(thinking, { type: "SOCKET_STATUS", status: "SPEAKING" });
    const standby = reduceJarvisStatus(speaking, { type: "SPEECH_COMPLETE" });

    expect(initial).toBe("STANDBY");
    expect(thinking).toBe("THINKING");
    expect(speaking).toBe("SPEAKING");
    expect(standby).toBe("STANDBY");
    expect(reduceJarvisStatus("THINKING", { type: "RESET" })).toBe("STANDBY");
  });

  it("normalizes HTTP server addresses to WebSocket schemes", () => {
    expect(normalizeWebSocketBaseUrl("http://127.0.0.1:8000/ws/")).toBe("ws://127.0.0.1:8000/ws");
    expect(normalizeWebSocketBaseUrl("https://cerebro.example/ws")).toBe("wss://cerebro.example/ws");
  });

  it("builds a tokenized endpoint with URL encoding", () => {
    expect(buildWebSocketUrl("ws://localhost:8000/ws", "alpha token")).toBe(
      "ws://localhost:8000/ws/alpha%20token",
    );
    expect(buildWebSocketUrl("", "token")).toBe("");
    expect(buildWebSocketUrl("ws://localhost:8000/ws", "")).toBe("");
  });

  it("serializes a command payload and rejects blank commands", () => {
    expect(serializeCommand("  status report  ")).toBe(
      JSON.stringify({ tipo: "comando", comando: "status report" }),
    );
    expect(serializeCommand("   ")).toBe("");
  });

  it("parses telemetry payloads and clamps unsafe metric values", () => {
    expect(parseJarvisMessage(JSON.stringify({ tipo: "telemetria", cpu: 42, ram: 71 }))).toEqual({
      kind: "telemetry",
      cpu: 42,
      ram: 71,
    });
    expect(clampTelemetryMetric(140)).toBe(100);
    expect(clampTelemetryMetric(-5)).toBe(0);
    expect(clampTelemetryMetric("not-a-number")).toBe(0);
  });

  it("parses JARVIS speaking events and preserves the state transition", () => {
    expect(
      parseJarvisMessage(
        JSON.stringify({
          status: "SPEAKING",
          type: "jarvis",
          log: "All systems nominal, Senhor.",
          acao: "falar",
        }),
      ),
    ).toEqual({
      kind: "event",
      author: "JARVIS",
      message: "All systems nominal, Senhor.",
      status: "SPEAKING",
      shouldReturnToStandby: true,
    });
    expect(parseJarvisMessage(JSON.stringify({ status: "THINKING", type: "user", log: "Run diagnostics" }))).toEqual({
      kind: "event",
      author: "USER",
      message: "Run diagnostics",
      status: "THINKING",
      shouldReturnToStandby: false,
    });
  });

  it("returns a safe invalid result for malformed or empty signals", () => {
    expect(parseJarvisMessage("{broken").kind).toBe("invalid");
    expect(parseJarvisMessage(JSON.stringify({ tipo: "unknown" }))).toMatchObject({ kind: "invalid" });
  });

  it("reports handshake states without revealing the access token", () => {
    expect(getHandshakeDetail("idle")).toBe("TOKEN PRONTO PARA ENLACE");
    expect(getHandshakeDetail("pending")).toBe("VALIDANDO JARVIS_TOKEN");
    expect(getHandshakeDetail("pending", 4)).toBe("NOVO ENLACE EM 4S");
    expect(getHandshakeDetail("verified")).toContain("JARVIS_TOKEN ACEITO");
    expect(getHandshakeDetail("failed")).toBe("ERRO DE AUTENTICAÇÃO OU REDE");
  });

  it("speaks only JARVIS responses when voice output is enabled", () => {
    expect(shouldSpeakJarvisReply("JARVIS", true)).toBe(true);
    expect(shouldSpeakJarvisReply("JARVIS", false)).toBe(false);
    expect(shouldSpeakJarvisReply("SYSTEM", true)).toBe(false);
  });

  it("routes every quick action to its deterministic command", () => {
    expect(getQuickProtocolCommand("memory")).toBe(QUICK_PROTOCOLS.memory);
    expect(getQuickProtocolCommand("personality")).toBe(QUICK_PROTOCOLS.personality);
    expect(getQuickProtocolCommand("diagnostic")).toBe(QUICK_PROTOCOLS.diagnostic);
    expect(getQuickProtocolCommand("diagnostic")).toContain("diagnóstico");
  });

  it("maps browser microphone failures to operator-facing diagnostics", () => {
    expect(getVoiceErrorMessage("not-allowed")).toContain("Permissão do microfone negada");
    expect(getVoiceErrorMessage("no-speech")).toContain("Nenhuma fala detectada");
    expect(getVoiceErrorMessage("audio-capture")).toContain("dispositivo de entrada de microfone");
    expect(getVoiceErrorMessage("unknown-error")).toContain("Entrada de voz indisponível");
  });
});
