declare module 'pcm-player' {
  interface PCMPlayerOptions {
    inputCodec: 'Int16' | 'Int8' | 'Float32';
    channels: number;
    sampleRate: number;
    flushTime?: number;
  }

  export default class PCMPlayer {
    constructor(options: PCMPlayerOptions);
    feed(data: Uint8Array): void;
    destroy(): void;
    pause(): void;
    continue(): void;
  }
}
