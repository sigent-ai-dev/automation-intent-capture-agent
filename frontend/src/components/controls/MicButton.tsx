import { useState } from 'react';

export function MicButton() {
  const [isRecording, setIsRecording] = useState(false);

  const toggle = () => {
    setIsRecording((r) => !r);
    // TODO: Wire to useAudioCapture hook
  };

  return (
    <button
      className="relative w-14 h-14 rounded-full flex items-center justify-center transition-colors"
      style={{
        backgroundColor: isRecording ? 'var(--color-mic-active)' : 'var(--color-mic-inactive)',
      }}
      onClick={toggle}
      aria-label={isRecording ? 'Stop recording' : 'Start recording'}
    >
      {isRecording && (
        <span
          className="absolute inset-0 rounded-full animate-ping"
          style={{ backgroundColor: 'var(--color-mic-active)', opacity: 0.3 }}
        />
      )}
      <svg className="w-6 h-6 text-white" fill="currentColor" viewBox="0 0 24 24">
        {isRecording ? (
          <rect x="6" y="6" width="12" height="12" rx="2" />
        ) : (
          <path d="M12 1a4 4 0 0 1 4 4v7a4 4 0 0 1-8 0V5a4 4 0 0 1 4-4zm-1 18.93A8.001 8.001 0 0 1 4 12h2a6 6 0 0 0 12 0h2a8.001 8.001 0 0 1-7 7.93V22h-2v-2.07z" />
        )}
      </svg>
    </button>
  );
}
