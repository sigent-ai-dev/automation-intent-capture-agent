interface Props {
  message: string;
  onDismiss?: () => void;
}

export function ErrorBanner({ message, onDismiss }: Props) {
  return (
    <div
      className="flex items-center justify-between px-4 py-2 text-sm animate-fade-in"
      style={{ backgroundColor: 'var(--color-error)', color: 'white' }}
    >
      <span>{message}</span>
      {onDismiss && (
        <button onClick={onDismiss} className="ml-2 opacity-80 hover:opacity-100" aria-label="Dismiss">
          ✕
        </button>
      )}
    </div>
  );
}
