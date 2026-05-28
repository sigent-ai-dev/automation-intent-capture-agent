declare global {
  interface Window {
    APP_CONFIG?: {
      WEBSOCKET_URL?: string;
      API_URL?: string;
    };
  }
}

const env = import.meta.env;
const runtime = window.APP_CONFIG ?? {};

export const CONFIG = {
  WEBSOCKET_URL: runtime.WEBSOCKET_URL || env.VITE_WEBSOCKET_URL || 'ws://localhost:8080/ws/audio',
  API_URL: runtime.API_URL || env.VITE_API_URL || 'http://localhost:8080',
  INPUT_SAMPLE_RATE: Number(env.VITE_INPUT_SAMPLE_RATE) || 16000,
  OUTPUT_SAMPLE_RATE: Number(env.VITE_OUTPUT_SAMPLE_RATE) || 24000,
  AUDIO_CHUNK_SIZE: Number(env.VITE_AUDIO_CHUNK_SIZE) || 1600,
  HEARTBEAT_INTERVAL_MS: 30000,
  MAX_RECONNECT_ATTEMPTS: 5,
  TOTAL_SECTIONS: ['Context', 'Problem Statement', 'Constraints', 'Success Criteria', 'Stakeholders', 'Timeline'],
} as const;
