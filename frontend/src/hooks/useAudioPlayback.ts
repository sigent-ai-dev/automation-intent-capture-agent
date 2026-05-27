import { useCallback, useRef } from 'react';
import PCMPlayer from 'pcm-player';
import { CONFIG } from '../config/constants';

export function useAudioPlayback() {
  const playerRef = useRef<PCMPlayer | null>(null);

  const getPlayer = useCallback(() => {
    if (!playerRef.current) {
      playerRef.current = new PCMPlayer({
        inputCodec: 'Int16',
        channels: 1,
        sampleRate: CONFIG.OUTPUT_SAMPLE_RATE,
        flushTime: 100,
      });
    }
    return playerRef.current;
  }, []);

  const feed = useCallback((data: ArrayBuffer) => {
    getPlayer().feed(new Uint8Array(data));
  }, [getPlayer]);

  const stop = useCallback(() => {
    if (playerRef.current) {
      playerRef.current.destroy();
      playerRef.current = null;
    }
  }, []);

  const handleBargeIn = useCallback(() => {
    stop();
  }, [stop]);

  return { feed, stop, handleBargeIn };
}
