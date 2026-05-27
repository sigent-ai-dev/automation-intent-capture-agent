import { useCallback, useRef } from 'react';
import PCMPlayer from 'pcm-player';
import { CONFIG } from '../config/constants';

export function useAudioPlayback() {
  const playerRef = useRef<InstanceType<typeof PCMPlayer> | null>(null);

  const getPlayer = useCallback(() => {
    if (!playerRef.current) {
      playerRef.current = new PCMPlayer({
        inputCodec: 'Int16',
        channels: 1,
        sampleRate: CONFIG.OUTPUT_SAMPLE_RATE,
        flushTime: 100,
      } as any); // eslint-disable-line @typescript-eslint/no-explicit-any
    }
    return playerRef.current;
  }, []);

  const feed = useCallback((data: ArrayBuffer) => {
    (getPlayer() as any).feed(data); // eslint-disable-line @typescript-eslint/no-explicit-any
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
