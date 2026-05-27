import { useSession } from '../../contexts/SessionContext';
import { MicButton } from './MicButton';
import { AudioMeter } from './AudioMeter';

export function ControlPanel() {
  const { endSession } = useSession();

  return (
    <div
      className="flex items-center justify-center gap-4 p-4 border-t"
      style={{ borderColor: 'var(--color-border)', backgroundColor: 'var(--color-surface)' }}
    >
      <AudioMeter level={0} />
      <MicButton />
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
