import { useState, type FormEvent } from 'react';
import { useAuth } from '../../contexts/AuthContext';
import { federatedSignIn } from '../../services/authService';

const FEDERATION_PROVIDERS = [
  { name: 'Microsoft', key: 'Microsoft', icon: 'M' },
  { name: 'Okta', key: 'Okta', icon: 'O' },
  { name: 'Google', key: 'Google', icon: 'G' },
];

const SHOW_FEDERATION = import.meta.env.VITE_ENABLE_FEDERATION !== 'false';

export default function LoginForm() {
  const { login, error } = useAuth();
  const [username, setUsername] = useState('');
  const [password, setPassword] = useState('');
  const [loading, setLoading] = useState(false);
  const [federationError, setFederationError] = useState<string | null>(null);

  const handleSubmit = async (e: FormEvent) => {
    e.preventDefault();
    setLoading(true);
    setFederationError(null);
    try {
      await login(username, password);
    } finally {
      setLoading(false);
    }
  };

  const handleFederatedSignIn = async (provider: string) => {
    setFederationError(null);
    try {
      await federatedSignIn(provider);
    } catch (err) {
      const message = err instanceof Error ? err.message : 'Federation sign-in failed';
      setFederationError(message);
    }
  };

  return (
    <div className="flex items-center justify-center min-h-screen bg-[var(--color-background)]">
      <form onSubmit={handleSubmit} className="bg-[var(--color-surface)] rounded-xl p-8 w-full max-w-md shadow-lg border border-[var(--color-border)]">
        <h1 className="text-2xl font-bold text-center text-[var(--color-text)] mb-6">Sign in to AICA</h1>

        <label htmlFor="login-username" className="block mb-4">
          <span className="text-sm text-[var(--color-text-secondary)]">Email</span>
          <input
            id="login-username"
            type="email"
            autoComplete="username"
            value={username}
            onChange={(e) => setUsername(e.target.value)}
            required
            className="mt-1 block w-full px-3 py-2 rounded-lg bg-[var(--color-surface-hover)] text-[var(--color-text)] border border-[var(--color-border)] focus:outline-none focus:ring-2 focus:ring-[var(--color-primary)]"
          />
        </label>

        <label htmlFor="login-password" className="block mb-6">
          <span className="text-sm text-[var(--color-text-secondary)]">Password</span>
          <input
            id="login-password"
            type="password"
            autoComplete="current-password"
            value={password}
            onChange={(e) => setPassword(e.target.value)}
            required
            className="mt-1 block w-full px-3 py-2 rounded-lg bg-[var(--color-surface-hover)] text-[var(--color-text)] border border-[var(--color-border)] focus:outline-none focus:ring-2 focus:ring-[var(--color-primary)]"
          />
        </label>

        <button
          type="submit"
          disabled={loading}
          className="bg-[var(--color-primary)] hover:opacity-90 text-white w-full py-3 rounded-lg font-medium disabled:opacity-50 flex items-center justify-center gap-2"
        >
          {loading && <span className="animate-spin h-4 w-4 border-2 border-white border-t-transparent rounded-full" />}
          {loading ? 'Signing in...' : 'Sign in'}
        </button>

        {SHOW_FEDERATION && (
          <>
            <div className="flex items-center my-6">
              <div className="flex-1 border-t border-[var(--color-border)]" />
              <span className="px-3 text-xs text-[var(--color-text-secondary)]">Or sign in with</span>
              <div className="flex-1 border-t border-[var(--color-border)]" />
            </div>
            <div className="flex flex-col gap-3">
              {FEDERATION_PROVIDERS.map((provider) => (
                <button
                  key={provider.key}
                  type="button"
                  onClick={() => handleFederatedSignIn(provider.key)}
                  className="flex items-center justify-center gap-2 w-full py-2.5 rounded-lg border border-[var(--color-border)] bg-[var(--color-surface-hover)] text-[var(--color-text)] hover:opacity-80 transition-opacity font-medium text-sm"
                >
                  <span className="w-5 h-5 flex items-center justify-center text-xs font-bold rounded bg-[var(--color-primary)] text-white">
                    {provider.icon}
                  </span>
                  Sign in with {provider.name}
                </button>
              ))}
            </div>
          </>
        )}

        {error && <p className="mt-4 text-sm text-red-400 text-center">{error}</p>}
        {federationError && <p className="mt-4 text-sm text-red-400 text-center">{federationError}</p>}
      </form>
    </div>
  );
}
