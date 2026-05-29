import { useTheme } from '../../contexts/ThemeContext';
import { useAuth } from '../../contexts/AuthContext';

export function Header() {
  const { effective, setMode } = useTheme();
  const { user, logout } = useAuth();

  const toggleTheme = () => {
    setMode(effective === 'dark' ? 'light' : 'dark');
  };

  return (
    <header
      className="sticky top-0 z-10 flex items-center justify-between px-5 py-3 border-b backdrop-blur-md"
      style={{
        backgroundColor: 'rgba(var(--color-surface-rgb, 26, 26, 26), 0.7)',
        borderColor: 'var(--color-border)',
        borderImage: 'linear-gradient(to right, var(--color-primary), transparent) 1',
      }}
    >
      <div className="flex items-center gap-2.5">
        <img src="/logo.svg" alt="" className="w-7 h-7" />
        <h1 className="text-lg font-bold tracking-wide" style={{ color: 'var(--color-primary)' }}>
          AICA
        </h1>
      </div>
      <div className="flex items-center gap-3">
        {user && (
          <>
            <span className="text-sm" style={{ color: 'var(--color-text-secondary)' }}>
              {user.username}
            </span>
            <button
              className="btn btn-ghost text-sm"
              onClick={logout}
              aria-label="Sign out"
            >
              Sign out
            </button>
          </>
        )}
        <button
          className="btn btn-ghost"
          onClick={toggleTheme}
          aria-label={`Switch to ${effective === 'dark' ? 'light' : 'dark'} mode`}
        >
          {effective === 'dark' ? '☀' : '☾'}
        </button>
      </div>
    </header>
  );
}
