import { createContext, useContext, useState, useEffect, useCallback, type ReactNode } from 'react';
import { AuthState, AuthUser } from '../types/auth';
import * as authService from '../services/authService';
import { getCurrentUser, fetchUserAttributes, fetchAuthSession } from 'aws-amplify/auth';
import { isAuthConfigured } from '../config/amplify';

async function getDisplayName(): Promise<string> {
  const attrs = await fetchUserAttributes();
  return attrs.email ?? attrs.preferred_username ?? (await getCurrentUser()).username;
}

async function getGroups(): Promise<string[]> {
  try {
    const session = await fetchAuthSession();
    const groups = session.tokens?.idToken?.payload?.['cognito:groups'];
    if (Array.isArray(groups)) return groups as string[];
    if (typeof groups === 'string') return [groups];
    return [];
  } catch {
    return [];
  }
}

interface AuthContextValue {
  state: AuthState;
  user: AuthUser | null;
  error: string | null;
  login: (username: string, password: string) => Promise<void>;
  logout: () => Promise<void>;
  completeNewPassword: (newPassword: string) => Promise<void>;
}

const AuthContext = createContext<AuthContextValue | null>(null);

export function AuthProvider({ children }: { children: ReactNode }) {
  const [state, setState] = useState<AuthState>('loading');
  const [user, setUser] = useState<AuthUser | null>(null);
  const [error, setError] = useState<string | null>(null);

  const loadUser = async () => {
    const token = (await authService.getToken()) ?? '';
    const username = await getDisplayName();
    const groups = await getGroups();
    setUser({ username, token, groups });
  };

  useEffect(() => {
    (async () => {
      if (!isAuthConfigured) {
        setState('authenticated');
        setUser({ username: 'anonymous', token: '', groups: [] });
        return;
      }
      try {
        const authed = await authService.isAuthenticated();
        if (authed) {
          await loadUser();
          setState('authenticated');
        } else {
          setState('unauthenticated');
        }
      } catch {
        setState('unauthenticated');
      }
    })();
  }, []);

  const login = useCallback(async (username: string, password: string) => {
    setError(null);
    try {
      const result = await authService.login(username, password);
      if (result.newPasswordRequired) {
        setState('new-password-required');
      } else if (result.authenticated) {
        await loadUser();
        setState('authenticated');
      }
    } catch (e) {
      setError(e instanceof Error ? e.message : 'Login failed');
    }
  }, []);

  const logout = useCallback(async () => {
    await authService.logout();
    setUser(null);
    setState('unauthenticated');
  }, []);

  const completeNewPassword = useCallback(async (newPassword: string) => {
    setError(null);
    try {
      await authService.completeNewPassword(newPassword);
      await loadUser();
      setState('authenticated');
    } catch (e) {
      setError(e instanceof Error ? e.message : 'Password change failed');
    }
  }, []);

  return (
    <AuthContext.Provider value={{ state, user, error, login, logout, completeNewPassword }}>
      {children}
    </AuthContext.Provider>
  );
}

export function useAuth() {
  const ctx = useContext(AuthContext);
  if (!ctx) throw new Error('useAuth must be used within AuthProvider');
  return ctx;
}
