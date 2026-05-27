import { useSession } from '../../contexts/SessionContext';
import { CONFIG } from '../../config/constants';

export function ProgressPanel() {
  const { session } = useSession();
  const progress = session?.progress;

  if (!progress) return null;

  const totalSections = CONFIG.TOTAL_SECTIONS.length;
  const coveredCount = progress.sectionsCovered.length;
  const percentage = Math.round((coveredCount / totalSections) * 100);

  const statusLabel = progress.alignmentReached
    ? 'Complete'
    : progress.proposalRounds > 0
      ? 'Proposing'
      : coveredCount > 0
        ? 'Eliciting'
        : 'Starting';

  const statusColor = progress.alignmentReached ? 'var(--color-success)' : 'var(--color-primary)';

  return (
    <aside
      className="w-64 border-l p-4 overflow-y-auto hidden lg:block"
      style={{ borderColor: 'var(--color-border)', backgroundColor: 'var(--color-surface)' }}
    >
      <h3 className="text-sm font-semibold mb-3" style={{ color: 'var(--color-text-primary)' }}>
        Session Progress
      </h3>

      <div className="mb-4">
        <span
          className="inline-block px-2 py-0.5 rounded text-xs font-medium"
          style={{ backgroundColor: statusColor, color: 'white' }}
        >
          {statusLabel}
        </span>
      </div>

      <div className="mb-4">
        <div className="flex justify-between text-xs mb-1" style={{ color: 'var(--color-text-secondary)' }}>
          <span>Sections</span>
          <span>{coveredCount}/{totalSections}</span>
        </div>
        <div className="w-full h-2 rounded-full" style={{ backgroundColor: 'var(--color-border)' }}>
          <div
            className="h-full rounded-full transition-all duration-300"
            style={{ width: `${percentage}%`, backgroundColor: statusColor }}
          />
        </div>
      </div>

      <ul className="space-y-1.5 mb-4">
        {CONFIG.TOTAL_SECTIONS.map((section) => {
          const covered = progress.sectionsCovered.includes(section);
          return (
            <li key={section} className="flex items-center gap-2 text-xs">
              <span style={{ color: covered ? 'var(--color-success)' : 'var(--color-text-secondary)' }}>
                {covered ? '✓' : '○'}
              </span>
              <span style={{ color: covered ? 'var(--color-text-primary)' : 'var(--color-text-secondary)' }}>
                {section}
              </span>
            </li>
          );
        })}
      </ul>

      {progress.proposalRounds > 0 && (
        <div className="text-xs" style={{ color: 'var(--color-text-secondary)' }}>
          Proposal round: {progress.proposalRounds}
        </div>
      )}
    </aside>
  );
}
