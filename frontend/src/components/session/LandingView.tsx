import { useState } from 'react';
import { useSession } from '../../contexts/SessionContext';
import { LoadingSpinner } from '../common/LoadingSpinner';
import { ConnectionStatus } from '../connection/ConnectionStatus';

export function LandingView() {
  const { status, startSession, session } = useSession();
  const [projectName, setProjectName] = useState('');

  const isLoading = status === 'creating' || status === 'connecting' || status === 'negotiating';

  const handleStart = () => {
    startSession(projectName);
  };

  const statusLabel = () => {
    switch (status) {
      case 'creating': return 'Creating session...';
      case 'connecting': return 'Connecting to voice server...';
      case 'negotiating': return 'Negotiating audio...';
      case 'failed': return session?.error || 'Something went wrong';
      case 'cancelled': return 'Session ended';
      default: return null;
    }
  };

  return (
    <div className="flex-1 flex items-center justify-center p-4">
      <div className="animate-fade-in flex flex-col items-center gap-6 max-w-md w-full">
        <div className="text-center">
          <h2 className="text-2xl font-semibold mb-2" style={{ color: 'var(--color-text-primary)' }}>
            Capture Your Intent
          </h2>
          <p className="text-sm" style={{ color: 'var(--color-text-secondary)' }}>
            Start a voice conversation to capture your project intent
          </p>
        </div>

        <input
          type="text"
          placeholder="Project name (optional)"
          value={projectName}
          onChange={(e) => setProjectName(e.target.value)}
          disabled={isLoading}
          className="w-full px-4 py-2 rounded-lg border text-sm"
          style={{
            backgroundColor: 'var(--color-surface)',
            borderColor: 'var(--color-border)',
            color: 'var(--color-text-primary)',
          }}
          onKeyDown={(e) => { if (e.key === 'Enter' && !isLoading) handleStart(); }}
        />

        <button
          className="btn btn-primary btn-lg w-full"
          onClick={handleStart}
          disabled={isLoading}
        >
          {isLoading ? (
            <>
              <LoadingSpinner size={18} />
              {statusLabel()}
            </>
          ) : (
            'Start Capture'
          )}
        </button>

        {status === 'failed' && (
          <p className="text-sm" style={{ color: 'var(--color-error)' }}>
            {session?.error || 'Connection failed. Please try again.'}
          </p>
        )}

        {isLoading && <ConnectionStatus status="connecting" />}
      </div>
    </div>
  );
}
