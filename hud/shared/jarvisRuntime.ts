export type ReconnectPlan = {
  attempt: number;
  shouldRetry: boolean;
  delayMs: number;
  delaySeconds: number;
  detail: string;
};

export function buildReconnectPlan(attempt: number): ReconnectPlan {
  const normalizedAttempt = Math.max(1, Math.floor(attempt));
  const shouldRetry = normalizedAttempt <= 5;
  const delayMs = Math.min(30000, 1000 * 2 ** Math.min(normalizedAttempt - 1, 5));
  return {
    attempt: normalizedAttempt,
    shouldRetry,
    delayMs,
    delaySeconds: Math.ceil(delayMs / 1000),
    detail: shouldRetry ? `NOVO ENLACE EM ${Math.ceil(delayMs / 1000)}S` : "LIMITE DE TENTATIVAS ATINGIDO",
  };
}

export function extractSpeechTranscript(results: unknown): string {
  if (!Array.isArray(results)) return "";
  const firstResult = results[0] as { 0?: { transcript?: unknown } } | undefined;
  const transcript = firstResult?.[0]?.transcript;
  return typeof transcript === "string" ? transcript.trim() : "";
}

export function getSpeechSynthesisSettings() {
  return {
    lang: "pt-BR",
    rate: 0.94,
    pitch: 0.86,
  } as const;
}
