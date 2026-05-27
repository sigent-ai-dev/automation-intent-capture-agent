import { useCallback, useEffect, useRef, useState } from 'react';
import { useSession } from '../../contexts/SessionContext';
import { useAudioCapture } from '../../hooks/useAudioCapture';
import { useAudioPlayback } from '../../hooks/useAudioPlayback';
import { wsService } from '../../services/websocketService';
import { MicButton } from './MicButton';
import { AudioMeter } from './AudioMeter';
import { TextInput } from './TextInput';

export function ControlPanel() {
  const { endSession } = useSession();
  const { feed, handleBargeIn } = useAudioPlayback();
  const [level, setLevel] = useState(0);
  const isRecordingRef = useRef(false);

  const onAudioData = useCallback((buffer: ArrayBuffer) => {
    wsService.sendBinary(buffer);
  }, []);

  const onLevelChange = useCallback((l: number) => {
    setLevel(l);
  }, []);

  const { isRecording, captureMode, error, toggleRecording } = useAudioCapture({
    onAudioData,
    onLevelChange,
  });

  isRecordingRef.current = isRecording;

  useEffect(() => {
    wsService.setHandlers({
      onBinary: (data) => {
        if (isRecordingRef.current) {
          handleBargeIn();
        } else {
          feed(data);
        }
      },
    });
  }, [feed, handleBargeIn]);

  const showTextFallback = captureMode === 'unavailable';

  return (
    <div
      className="flex items-center justify-center gap-4 p-4 border-t"
      style={{ borderColor: 'var(--color-border)', backgroundColor: 'var(--color-surface)' }}
    >
      {showTextFallback ? (
        <TextInput />
      ) : (
        <>
          <AudioMeter level={level} />
          <MicButton isRecording={isRecording} onToggle={toggleRecording} disabled={false} />
          {error && (
            <span className="text-xs" style={{ color: 'var(--color-error)' }}>{error}</span>
          )}
        </>
      )}
      <button
        className="btn btn-ghost text-xs"
        onClick={endSession}
        style={{ color: 'var(--color-error)' }}
      >
        End Session
      </button>
    </div>
  );
}
