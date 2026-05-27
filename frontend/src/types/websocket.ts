export interface CodecNegotiateMessage {
  type: 'codec_negotiate';
  codec: string;
  sample_rate: number;
  bit_depth: number;
  channels: number;
}

export interface CodecAckMessage {
  type: 'codec_ack';
  session_id: string;
  codec: string;
  sample_rate: number;
  bit_depth: number;
  channels: number;
}

export interface SessionReadyMessage {
  type: 'session_ready';
  session_id: string;
  user_id: string;
  timestamp: number;
}

export interface TranscriptMessage {
  type: 'transcript';
  role: 'user' | 'agent';
  text: string;
  final: boolean;
}

export interface ProgressMessage {
  type: 'progress';
  sections_covered: string[];
  proposal_rounds: number;
  alignment_reached: boolean;
}

export interface IntentPreviewMessage {
  type: 'intent_preview';
  markdown: string;
}

export interface SessionCompleteMessage {
  type: 'session_complete';
}

export interface ErrorMessage {
  type: 'error';
  message: string;
  code: string;
}

export interface ServerShutdownMessage {
  type: 'server_shutdown';
  drain_seconds: number;
  message: string;
}

export interface PingMessage {
  type: 'ping';
}

export interface PongMessage {
  type: 'pong';
  timestamp: number;
}

export interface TextInputMessage {
  type: 'text_input';
  text: string;
}

export type ServerMessage =
  | CodecAckMessage
  | SessionReadyMessage
  | TranscriptMessage
  | ProgressMessage
  | IntentPreviewMessage
  | SessionCompleteMessage
  | ErrorMessage
  | ServerShutdownMessage
  | PongMessage;

export type ClientMessage = CodecNegotiateMessage | PingMessage | TextInputMessage;
