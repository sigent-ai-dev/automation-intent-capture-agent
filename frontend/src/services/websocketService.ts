import { CONFIG } from '../config/constants';
import type { ClientMessage, ServerMessage } from '../types/websocket';
import { getToken } from './authService';

export type MessageHandler = (msg: ServerMessage) => void;
export type BinaryHandler = (data: ArrayBuffer) => void;
export type StatusHandler = (status: 'connected' | 'disconnected' | 'connecting' | 'reconnecting') => void;

export class WebSocketService {
  private ws: WebSocket | null = null;
  private heartbeatTimer: ReturnType<typeof setInterval> | null = null;
  private reconnectAttempt = 0;
  private reconnectTimer: ReturnType<typeof setTimeout> | null = null;
  private sessionId: string | null = null;
  private intentionallyClosed = false;

  private onMessage: MessageHandler | null = null;
  private onBinary: BinaryHandler | null = null;
  private onStatus: StatusHandler | null = null;

  setHandlers(handlers: { onMessage?: MessageHandler; onBinary?: BinaryHandler; onStatus?: StatusHandler }) {
    if (handlers.onMessage) this.onMessage = handlers.onMessage;
    if (handlers.onBinary) this.onBinary = handlers.onBinary;
    if (handlers.onStatus) this.onStatus = handlers.onStatus;
  }

  async connect(sessionId: string): Promise<void> {
    this.sessionId = sessionId;
    this.intentionallyClosed = false;
    this.reconnectAttempt = 0;
    await this.doConnect();
  }

  private async doConnect(): Promise<void> {
    this.onStatus?.('connecting');
    const url = `${CONFIG.WEBSOCKET_URL}?session_id=${this.sessionId}`;
    const token = await getToken();
    const protocols = token ? ['v1.audio.intent', token] : ['v1.audio.intent'];
    this.ws = new WebSocket(url, protocols);
    this.ws.binaryType = 'arraybuffer';

    this.ws.onopen = () => {
      this.reconnectAttempt = 0;
      this.onStatus?.('connected');
      this.startHeartbeat();
      this.sendCodecNegotiate();
    };

    this.ws.onmessage = (event) => {
      if (event.data instanceof ArrayBuffer) {
        this.onBinary?.(event.data);
      } else {
        try {
          const msg = JSON.parse(event.data) as ServerMessage;
          this.onMessage?.(msg);
        } catch {
          // ignore unparseable messages
        }
      }
    };

    this.ws.onclose = () => {
      this.stopHeartbeat();
      if (!this.intentionallyClosed) {
        this.attemptReconnect();
      } else {
        this.onStatus?.('disconnected');
      }
    };

    this.ws.onerror = () => {
      // onclose will fire after onerror
    };
  }

  private sendCodecNegotiate(): void {
    this.sendJSON({
      type: 'codec_negotiate',
      codec: 'pcm',
      sample_rate: CONFIG.INPUT_SAMPLE_RATE,
      bit_depth: 16,
      channels: 1,
    });
  }

  sendJSON(msg: ClientMessage): void {
    if (this.ws?.readyState === WebSocket.OPEN) {
      this.ws.send(JSON.stringify(msg));
    }
  }

  sendBinary(data: ArrayBuffer): void {
    if (this.ws?.readyState === WebSocket.OPEN) {
      this.ws.send(data);
    }
  }

  private startHeartbeat(): void {
    this.heartbeatTimer = setInterval(() => {
      this.sendJSON({ type: 'ping' });
    }, CONFIG.HEARTBEAT_INTERVAL_MS);
  }

  private stopHeartbeat(): void {
    if (this.heartbeatTimer) {
      clearInterval(this.heartbeatTimer);
      this.heartbeatTimer = null;
    }
  }

  private attemptReconnect(): void {
    if (this.reconnectAttempt >= CONFIG.MAX_RECONNECT_ATTEMPTS) {
      this.onStatus?.('disconnected');
      return;
    }
    this.onStatus?.('reconnecting');
    const delay = Math.pow(2, this.reconnectAttempt) * 1000;
    this.reconnectAttempt++;
    this.reconnectTimer = setTimeout(() => { this.doConnect(); }, delay);
  }

  disconnect(): void {
    this.intentionallyClosed = true;
    if (this.reconnectTimer) {
      clearTimeout(this.reconnectTimer);
      this.reconnectTimer = null;
    }
    this.stopHeartbeat();
    if (this.ws) {
      this.ws.close(1000);
      this.ws = null;
    }
    this.onStatus?.('disconnected');
  }

  get isConnected(): boolean {
    return this.ws?.readyState === WebSocket.OPEN;
  }
}

export const wsService = new WebSocketService();
