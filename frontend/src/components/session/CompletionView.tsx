import { useSession } from '../../contexts/SessionContext';
import { LoadingSpinner } from '../common/LoadingSpinner';

export function CompletionView() {
  const { session, status, resetSession } = useSession();

  if (status === 'completing') {
    return (
      <div className="flex-1 flex flex-col items-center justify-center gap-4 p-8">
        <LoadingSpinner size={32} />
        <p style={{ color: 'var(--color-text-secondary)' }}>Finalizing intent...</p>
      </div>
    );
  }

  const result = session?.result;
  if (!result) {
    return (
      <div className="flex-1 flex items-center justify-center p-8">
        <p style={{ color: 'var(--color-error)' }}>No result available.</p>
      </div>
    );
  }

  const handleDownload = () => {
    const blob = new Blob([result.intentMd], { type: 'text/markdown' });
    const url = URL.createObjectURL(blob);
    const a = document.createElement('a');
    a.href = url;
    a.download = 'intent.md';
    a.click();
    URL.revokeObjectURL(url);
  };

  return (
    <div className="flex-1 overflow-y-auto p-6 max-w-3xl mx-auto w-full">
      <div className="animate-fade-in">
        <h2 className="text-xl font-semibold mb-4" style={{ color: 'var(--color-text-primary)' }}>
          Intent Captured
        </h2>

        <div
          className="rounded-lg p-6 mb-4 prose prose-sm max-w-none"
          style={{ backgroundColor: 'var(--color-surface)', border: `1px solid var(--color-border)` }}
        >
          <pre className="whitespace-pre-wrap text-sm font-mono" style={{ color: 'var(--color-text-primary)' }}>
            {result.intentMd}
          </pre>
        </div>

        <details className="mb-6">
          <summary className="cursor-pointer text-sm font-medium" style={{ color: 'var(--color-text-secondary)' }}>
            Audit Trail
          </summary>
          <pre className="mt-2 text-xs whitespace-pre-wrap p-4 rounded" style={{ backgroundColor: 'var(--color-surface)', color: 'var(--color-text-secondary)' }}>
            {result.auditMd}
          </pre>
        </details>

        <div className="flex gap-3">
          <button className="btn btn-primary" onClick={handleDownload}>
            Download intent.md
          </button>
          <button className="btn btn-ghost" onClick={resetSession}>
            Start New Session
          </button>
        </div>
      </div>
    </div>
  );
}
