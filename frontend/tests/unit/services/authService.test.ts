import { vi, describe, it, expect, afterEach } from 'vitest';
import { login, logout, getToken, isAuthenticated, completeNewPassword, federatedSignIn } from '../../../src/services/authService';

vi.mock('aws-amplify/auth', () => ({
  signIn: vi.fn(),
  signOut: vi.fn(),
  confirmSignIn: vi.fn(),
  fetchAuthSession: vi.fn(),
  getCurrentUser: vi.fn(),
  signInWithRedirect: vi.fn(),
}));

import { signIn, signOut, confirmSignIn, fetchAuthSession, getCurrentUser, signInWithRedirect } from 'aws-amplify/auth';

const mockSignIn = vi.mocked(signIn);
const mockSignOut = vi.mocked(signOut);
const mockConfirmSignIn = vi.mocked(confirmSignIn);
const mockFetchAuthSession = vi.mocked(fetchAuthSession);
const mockGetCurrentUser = vi.mocked(getCurrentUser);
const mockSignInWithRedirect = vi.mocked(signInWithRedirect);

describe('authService', () => {
  afterEach(() => vi.restoreAllMocks());

  describe('login', () => {
    it('returns authenticated when signIn step is DONE', async () => {
      mockSignIn.mockResolvedValue({ nextStep: { signInStep: 'DONE' }, isSignedIn: true } as any);
      const result = await login('user@test.com', 'pass');
      expect(result).toEqual({ authenticated: true, newPasswordRequired: false });
    });

    it('returns newPasswordRequired when step is CONFIRM_SIGN_IN_WITH_NEW_PASSWORD_REQUIRED', async () => {
      mockSignIn.mockResolvedValue({
        nextStep: { signInStep: 'CONFIRM_SIGN_IN_WITH_NEW_PASSWORD_REQUIRED' },
        isSignedIn: false,
      } as any);
      const result = await login('user@test.com', 'pass');
      expect(result).toEqual({ authenticated: false, newPasswordRequired: true });
    });

    it('returns not authenticated for other steps', async () => {
      mockSignIn.mockResolvedValue({
        nextStep: { signInStep: 'CONFIRM_SIGN_UP' },
        isSignedIn: false,
      } as any);
      const result = await login('user@test.com', 'pass');
      expect(result).toEqual({ authenticated: false, newPasswordRequired: false });
    });
  });

  describe('getToken', () => {
    it('returns token string from fetchAuthSession', async () => {
      mockFetchAuthSession.mockResolvedValue({
        tokens: { idToken: { toString: () => 'test-token' } },
      } as any);
      expect(await getToken()).toBe('test-token');
    });

    it('returns null on error', async () => {
      mockFetchAuthSession.mockRejectedValue(new Error('fail'));
      expect(await getToken()).toBeNull();
    });
  });

  describe('isAuthenticated', () => {
    it('returns true when getCurrentUser succeeds', async () => {
      mockGetCurrentUser.mockResolvedValue({} as any);
      expect(await isAuthenticated()).toBe(true);
    });

    it('returns false when getCurrentUser throws', async () => {
      mockGetCurrentUser.mockRejectedValue(new Error('not signed in'));
      expect(await isAuthenticated()).toBe(false);
    });
  });

  describe('logout', () => {
    it('calls signOut', async () => {
      mockSignOut.mockResolvedValue(undefined as any);
      await logout();
      expect(mockSignOut).toHaveBeenCalled();
    });
  });

  describe('completeNewPassword', () => {
    it('calls confirmSignIn with challengeResponse', async () => {
      mockConfirmSignIn.mockResolvedValue({} as any);
      await completeNewPassword('newPass123!');
      expect(mockConfirmSignIn).toHaveBeenCalledWith({ challengeResponse: 'newPass123!' });
    });
  });

  describe('federatedSignIn', () => {
    it('calls signInWithRedirect with provider', async () => {
      mockSignInWithRedirect.mockResolvedValue(undefined as any);
      await federatedSignIn('Microsoft');
      expect(mockSignInWithRedirect).toHaveBeenCalledWith({ provider: { custom: 'Microsoft' } });
    });

    it('throws when signInWithRedirect fails and no domain configured', async () => {
      mockSignInWithRedirect.mockRejectedValue(new Error('redirect failed'));
      await expect(federatedSignIn('Microsoft')).rejects.toThrow('redirect failed');
    });
  });
});
