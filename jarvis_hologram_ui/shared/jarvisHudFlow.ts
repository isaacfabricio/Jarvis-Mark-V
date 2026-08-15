import {
  serializeCommand,
  shouldSpeakJarvisReply,
  type JarvisStatus,
  type LogAuthor,
  type ParsedJarvisMessage,
} from "./jarvisProtocol";

export type HudFlowState = {
  status: JarvisStatus;
  voiceEnabled: boolean;
};

export type HudFlowEvent =
  | { type: "COMMAND_SENT"; command: string }
  | { type: "MESSAGE_RECEIVED"; message: ParsedJarvisMessage }
  | { type: "SPEECH_COMPLETE" };

export type HudFlowEffect =
  | { type: "SEND_COMMAND"; payload: string }
  | { type: "SPEAK"; text: string }
  | { type: "LOG"; author: LogAuthor; message: string; status?: JarvisStatus }
  | { type: "RETURN_TO_STANDBY"; delayMs: number };

export function transitionHudFlow(state: HudFlowState, event: HudFlowEvent): { state: HudFlowState; effects: HudFlowEffect[] } {
  if (event.type === "COMMAND_SENT") {
    const payload = serializeCommand(event.command);
    const normalizedCommand = event.command.trim();
    return {
      state: { ...state, status: "THINKING" },
      effects: payload
        ? [
            { type: "SEND_COMMAND", payload },
            { type: "LOG", author: "USER", message: normalizedCommand },
          ]
        : [],
    };
  }

  if (event.type === "SPEECH_COMPLETE") {
    return { state: { ...state, status: "STANDBY" }, effects: [] };
  }

  if (event.message.kind === "event") {
    const effects: HudFlowEffect[] = [
      { type: "LOG", author: event.message.author, message: event.message.message, status: event.message.status },
    ];
    if (shouldSpeakJarvisReply(event.message.author, state.voiceEnabled)) {
      effects.push({ type: "SPEAK", text: event.message.message });
    }
    if (event.message.shouldReturnToStandby) {
      effects.push({ type: "RETURN_TO_STANDBY", delayMs: 4500 });
    }
    return {
      state: { ...state, status: event.message.status ?? state.status },
      effects,
    };
  }

  return { state, effects: [] };
}
