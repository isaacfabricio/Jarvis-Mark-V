import { describe, expect, it } from "vitest";
import { buildReconnectPlan, extractSpeechTranscript, getSpeechSynthesisSettings } from "../shared/jarvisRuntime";

describe("JARVIS browser runtime helpers", () => {
  it("builds bounded exponential reconnect plans", () => {
    expect(buildReconnectPlan(1)).toMatchObject({ attempt: 1, shouldRetry: true, delayMs: 1000, delaySeconds: 1 });
    expect(buildReconnectPlan(3)).toMatchObject({ attempt: 3, shouldRetry: true, delayMs: 4000, detail: "NOVO ENLACE EM 4S" });
    expect(buildReconnectPlan(6)).toMatchObject({ attempt: 6, shouldRetry: false, delayMs: 30000, detail: "LIMITE DE TENTATIVAS ATINGIDO" });
  });

  it("extracts and trims browser speech recognition transcripts", () => {
    expect(extractSpeechTranscript([[{ transcript: "  abrir o vault  " }]])).toBe("abrir o vault");
    expect(extractSpeechTranscript([])).toBe("");
    expect(extractSpeechTranscript([[{ transcript: 42 }]])).toBe("");
    expect(extractSpeechTranscript(null)).toBe("");
  });

  it("keeps TTS settings deterministic for Portuguese output", () => {
    expect(getSpeechSynthesisSettings()).toEqual({ lang: "pt-BR", rate: 0.94, pitch: 0.86 });
  });
});
