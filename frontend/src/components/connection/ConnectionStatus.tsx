interface Props {
  status: 'connected' | 'disconnected' | 'connecting' | 'reconnecting';
}

const statusConfig = {
  connected: { color: 'var(--color-success)', label: 'Connected' },
  disconnected: { color: 'var(--color-error)', label: 'Disconnected' },
  connecting: { color: 'var(--color-warning)', label: 'Connecting...' },
  reconnecting: { color: 'var(--color-warning)', label: 'Reconnecting...' },
};

export function ConnectionStatus({ status }: Props) {
  const config = statusConfig[status];

  return (
    <div className="flex items-center gap-1.5 text-xs" style={{ color: 'var(--color-text-secondary)' }}>
      <div
        className="w-2 h-2 rounded-full"
        style={{ backgroundColor: config.color }}
        aria-label={config.label}
      />
      <span>{config.label}</span>
    </div>
  );
}
