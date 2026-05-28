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

  it('shows federation buttons when VITE_ENABLE_FEDERATION is not false', async () => {
    const { default: LoginForm } = await import('../../../../src/components/auth/LoginForm');
    render(<LoginForm />);

    expect(screen.getByText('Sign in with Microsoft')).toBeDefined();
    expect(screen.getByText('Sign in with Okta')).toBeDefined();
    expect(screen.getByText('Sign in with Google')).toBeDefined();
  });
});
