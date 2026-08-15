import { describe, expect, it } from "vitest";
import { parseJarvisMessage } from "../shared/jarvisProtocol";
import { transitionHudFlow } from "../shared/jarvisHudFlow";

describe("JARVIS integrated HUD flow", () => {
  it("sends a quick-action command, logs the operator command and enters THINKING", () => {
    const flow = transitionHudFlow(
      { status: "STANDBY", voiceEnabled: true },
      { type: "COMMAND_SENT", command: "JARVIS, execute diagnóstico." },
    );

    expect(flow.state.status).toBe("THINKING");
    expect(flow.effects).toEqual([
      { type: "SEND_COMMAND", payload: JSON.stringify({ tipo: "comando", comando: "JARVIS, execute diagnóstico." }) },
      { type: "LOG", author: "USER", message: "JARVIS, execute diagnóstico." },
    ]);
  });

  it("moves a spoken JARVIS response to SPEAKING, logs it, speaks it and schedules STANDBY", () => {
    const response = parseJarvisMessage(
      JSON.stringify({ type: "jarvis", status: "SPEAKING", acao: "falar", log: "Diagnóstico concluído." }),
    );
    const speaking = transitionHudFlow({ status: "THINKING", voiceEnabled: true }, { type: "MESSAGE_RECEIVED", message: response });
    const standby = transitionHudFlow(speaking.state, { type: "SPEECH_COMPLETE" });

    expect(speaking.state.status).toBe("SPEAKING");
    expect(speaking.effects).toEqual([
      { type: "LOG", author: "JARVIS", message: "Diagnóstico concluído.", status: "SPEAKING" },
      { type: "SPEAK", text: "Diagnóstico concluído." },
      { type: "RETURN_TO_STANDBY", delayMs: 4500 },
    ]);
    expect(standby.state.status).toBe("STANDBY");
    expect(standby.effects).toEqual([]);
  });

  it("runs one complete operator-to-JARVIS sequence from command to STANDBY", () => {
    const commandFlow = transitionHudFlow(
      { status: "STANDBY", voiceEnabled: true },
      { type: "COMMAND_SENT", command: "JARVIS, execute diagnóstico." },
    );
    const userLog = commandFlow.effects.find((effect) => effect.type === "LOG");
    const response = parseJarvisMessage(
      JSON.stringify({ type: "jarvis", status: "SPEAKING", acao: "falar", log: "Diagnóstico concluído." }),
    );
    const responseFlow = transitionHudFlow(commandFlow.state, { type: "MESSAGE_RECEIVED", message: response });
    const jarvisLog = responseFlow.effects.find((effect) => effect.type === "LOG");
    const finalFlow = transitionHudFlow(responseFlow.state, { type: "SPEECH_COMPLETE" });

    expect(userLog).toEqual({ type: "LOG", author: "USER", message: "JARVIS, execute diagnóstico." });
    expect(commandFlow.state.status).toBe("THINKING");
    expect(jarvisLog).toEqual({ type: "LOG", author: "JARVIS", message: "Diagnóstico concluído.", status: "SPEAKING" });
    expect(responseFlow.state.status).toBe("SPEAKING");
    expect(responseFlow.effects).toContainEqual({ type: "SPEAK", text: "Diagnóstico concluído." });
    expect(finalFlow.state.status).toBe("STANDBY");
  });

  it("keeps the flow silent when voice is disabled while retaining the JARVIS log", () => {
    const response = parseJarvisMessage(
      JSON.stringify({ type: "jarvis", status: "SPEAKING", acao: "falar", log: "Voice disabled." }),
    );
    const flow = transitionHudFlow({ status: "THINKING", voiceEnabled: false }, { type: "MESSAGE_RECEIVED", message: response });

    expect(flow.state.status).toBe("SPEAKING");
    expect(flow.effects).toEqual([
      { type: "LOG", author: "JARVIS", message: "Voice disabled.", status: "SPEAKING" },
      { type: "RETURN_TO_STANDBY", delayMs: 4500 },
    ]);
  });
});
