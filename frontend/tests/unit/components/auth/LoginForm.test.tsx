import { vi, describe, it, expect } from 'vitest';
import { render, screen } from '@testing-library/react';

vi.mock('../../../../src/contexts/AuthContext', () => ({
  useAuth: vi.fn(() => ({
    login: vi.fn(),
    error: null,
  })),
}));

vi.mock('../../../../src/services/authService', () => ({
  federatedSignIn: vi.fn(),
}));

describe('LoginForm', () => {
  it('renders login form with email and password fields', async () => {
    const { default: LoginForm } = await import('../../../../src/components/auth/LoginForm');
    render(<LoginForm />);

    expect(screen.getByLabelText('Email')).toBeDefined();
    expect(screen.getByLabelText('Password')).toBeDefined();
    expect(screen.getByRole('button', { name: 'Sign in' })).toBeDefined();
  });

  it('renders federation buttons based on VITE_ENABLE_FEDERATION env var', async () => {
    const { default: LoginForm } = await import('../../../../src/components/auth/LoginForm');
    render(<LoginForm />);

    const federationEnabled = import.meta.env.VITE_ENABLE_FEDERATION !== 'false';

    if (federationEnabled) {
      expect(screen.getByText('Sign in with Microsoft')).toBeDefined();
      expect(screen.getByText('Sign in with Okta')).toBeDefined();
      expect(screen.getByText('Sign in with Google')).toBeDefined();
    } else {
      expect(screen.queryByText('Sign in with Microsoft')).toBeNull();
    }
  });
});
