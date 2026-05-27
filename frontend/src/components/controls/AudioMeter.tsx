interface Props {
  level: number;
}

export function AudioMeter({ level }: Props) {
  const width = Math.min(100, Math.max(0, level * 100));

  return (
    <div
      className="w-24 h-2 rounded-full overflow-hidden"
      style={{ backgroundColor: 'var(--color-border)' }}
      role="meter"
      aria-valuenow={width}
      aria-valuemin={0}
      aria-valuemax={100}
      aria-label="Audio input level"
    >
      <div
        className="h-full rounded-full transition-all duration-75"
        style={{
          width: `${width}%`,
          backgroundColor: 'var(--color-success)',
        }}
      />
    </div>
  );
}
