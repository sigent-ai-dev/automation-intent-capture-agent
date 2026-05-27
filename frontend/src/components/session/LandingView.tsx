import { useState } from 'react';
import { LoadingSpinner } from '../common/LoadingSpinner';

export function LandingView() {
  const [projectName, setProjectName] = useState('');
  const [isCreating, setIsCreating] = useState(false);

  const handleStart = async () => {
    setIsCreating(true);
    // TODO: Wire to SessionContext.startSession()
    setTimeout(() => setIsCreating(false), 2000);
  };

  return (
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
        className="w-full px-4 py-2 rounded-lg border text-sm"
        style={{
          backgroundColor: 'var(--color-surface)',
          borderColor: 'var(--color-border)',
          color: 'var(--color-text-primary)',
        }}
      />

      <button
        className="btn btn-primary btn-lg w-full"
        onClick={handleStart}
        disabled={isCreating}
      >
        {isCreating ? (
          <>
            <LoadingSpinner size={18} />
            Creating session...
          </>
        ) : (
          'Start Capture'
        )}
      </button>
    </div>
  );
}
