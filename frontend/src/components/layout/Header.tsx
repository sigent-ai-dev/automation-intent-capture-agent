import { useTheme } from '../../contexts/ThemeContext';

export function Header() {
  const { effective, setMode } = useTheme();

  const toggleTheme = () => {
    setMode(effective === 'dark' ? 'light' : 'dark');
  };

  return (
    <header
      className="sticky top-0 z-10 flex items-center justify-between px-4 py-3 border-b"
      style={{
        backgroundColor: 'var(--color-surface)',
        borderColor: 'var(--color-border)',
      }}
    >
      <div className="flex items-center gap-2">
        <img src="/logo.svg" alt="" className="w-6 h-6" />
        <h1 className="text-lg font-semibold" style={{ color: 'var(--color-text-primary)' }}>
          Intent Capture
        </h1>
      </div>
      <button
        className="btn btn-ghost"
        onClick={toggleTheme}
        aria-label={`Switch to ${effective === 'dark' ? 'light' : 'dark'} mode`}
      >
        {effective === 'dark' ? '☀' : '☾'}
      </button>
    </header>
  );
}
