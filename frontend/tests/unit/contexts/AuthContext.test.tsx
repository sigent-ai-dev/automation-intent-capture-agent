import { vi, describe, it, expect } from 'vitest';
import { render, screen, waitFor } from '@testing-library/react';
import { AuthProvider, useAuth } from '../../../src/contexts/AuthContext';

vi.mock('../../../src/config/amplify', () => ({
  isAuthConfigured: true,
}));

vi.mock('../../../src/services/authService', () => ({
  login: vi.fn(),
  logout: vi.fn(),
  getToken: vi.fn(),
  isAuthenticated: vi.fn(),
  completeNewPassword: vi.fn(),
}));

vi.mock('aws-amplify/auth', () => ({
  getCurrentUser: vi.fn(),
  fetchUserAttributes: vi.fn(),
  fetchAuthSession: vi.fn(),
}));

import * as authService from '../../../src/services/authService';
import { getCurrentUser, fetchUserAttributes, fetchAuthSession } from 'aws-amplify/auth';

const mockIsAuthenticated = vi.mocked(authService.isAuthenticated);
const mockGetToken = vi.mocked(authService.getToken);
const mockGetCurrentUser = vi.mocked(getCurrentUser);
const mockFetchUserAttributes = vi.mocked(fetchUserAttributes);
const mockFetchAuthSession = vi.mocked(fetchAuthSession);

function TestConsumer() {
  const { state, user } = useAuth();
  return (
    <div>
      <span data-testid="state">{state}</span>
      <span data-testid="user">{user?.username ?? 'none'}</span>
    </div>
  );
}

describe('AuthContext', () => {
  it('transitions to unauthenticated when no session exists', async () => {
    mockIsAuthenticated.mockResolvedValue(false);

    render(
      <AuthProvider>
        <TestConsumer />
      </AuthProvider>,
    );

    await waitFor(() => {
      expect(screen.getByTestId('state').textContent).toBe('unauthenticated');
    });
  });

  it('transitions to authenticated when session exists', async () => {
    mockIsAuthenticated.mockResolvedValue(true);
    mockGetToken.mockResolvedValue('test-token');
    mockGetCurrentUser.mockResolvedValue({ username: 'user@test.com', userId: '123' } as any);
    mockFetchUserAttributes.mockResolvedValue({ email: 'user@test.com' } as any);
    mockFetchAuthSession.mockResolvedValue({ tokens: { idToken: { payload: {} } } } as any);

    render(
      <AuthProvider>
        <TestConsumer />
      </AuthProvider>,
    );

    await waitFor(() => {
      expect(screen.getByTestId('state').textContent).toBe('authenticated');
      expect(screen.getByTestId('user').textContent).toBe('user@test.com');
    });
  });
});
