import { useState, type FormEvent } from 'react';
import { useAuth } from '../../contexts/AuthContext';

export default function NewPasswordForm() {
  const { completeNewPassword, error } = useAuth();
  const [newPassword, setNewPassword] = useState('');
  const [loading, setLoading] = useState(false);

  const handleSubmit = async (e: FormEvent) => {
    e.preventDefault();
    setLoading(true);
    try {
      await completeNewPassword(newPassword);
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="flex items-center justify-center min-h-screen bg-[var(--color-background)]">
      <form onSubmit={handleSubmit} className="bg-[var(--color-surface)] rounded-xl p-8 w-full max-w-md shadow-lg border border-[var(--color-border)]">
        <h1 className="text-2xl font-bold text-center text-[var(--color-text)] mb-2">Set New Password</h1>
        <p className="text-sm text-center text-[var(--color-text-secondary)] mb-6">
          Your account requires a new password before you can continue.
        </p>

        <label htmlFor="new-password" className="block mb-6">
          <span className="text-sm text-[var(--color-text-secondary)]">New Password</span>
          <input
            id="new-password"
            type="password"
            autoComplete="new-password"
            value={newPassword}
            onChange={(e) => setNewPassword(e.target.value)}
            required
            minLength={8}
            className="mt-1 block w-full px-3 py-2 rounded-lg bg-[var(--color-surface-hover)] text-[var(--color-text)] border border-[var(--color-border)] focus:outline-none focus:ring-2 focus:ring-[var(--color-primary)]"
          />
          <span className="text-xs text-[var(--color-text-secondary)] mt-1 block">
            Minimum 8 characters, including uppercase, lowercase, and a number
          </span>
        </label>

        <button
          type="submit"
          disabled={loading}
          className="bg-[var(--color-primary)] hover:opacity-90 text-white w-full py-3 rounded-lg font-medium disabled:opacity-50 flex items-center justify-center gap-2"
        >
          {loading && <span className="animate-spin h-4 w-4 border-2 border-white border-t-transparent rounded-full" />}
          {loading ? 'Setting password...' : 'Set Password & Continue'}
        </button>

        {error && <p className="mt-4 text-sm text-red-400 text-center">{error}</p>}
      </form>
    </div>
  );
}
