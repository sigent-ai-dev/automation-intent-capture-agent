import { useCallback, useState } from 'react';
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

  // Wire WebSocket transcript messages to conversation
  // This would ideally be in a higher-level orchestrator, but for now
  // we set up the binary handler here
  wsService.setHandlers({
    onBinary: (data) => {
      if (isRecording) {
        handleBargeIn();
      } else {
        feed(data);
      }
    },
  });

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
