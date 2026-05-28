import { vi, describe, it, expect } from 'vitest';
import { render, screen } from '@testing-library/react';
import { RoleGuard } from '../../../../src/components/auth/RoleGuard';

vi.mock('../../../../src/contexts/AuthContext', () => ({
  useAuth: vi.fn(),
}));

import { useAuth } from '../../../../src/contexts/AuthContext';
const mockUseAuth = vi.mocked(useAuth);

describe('RoleGuard', () => {
  it('renders children when user has required group', () => {
    mockUseAuth.mockReturnValue({
      state: 'authenticated',
      user: { username: 'admin@test.com', token: 'tok', groups: ['admin'] },
      error: null,
      login: vi.fn(),
      logout: vi.fn(),
      completeNewPassword: vi.fn(),
    });

    render(
      <RoleGuard requiredGroups={['admin']}>
        <span>Protected Content</span>
      </RoleGuard>,
    );

    expect(screen.getByText('Protected Content')).toBeDefined();
  });

  it('renders fallback when user lacks required group', () => {
    mockUseAuth.mockReturnValue({
      state: 'authenticated',
      user: { username: 'user@test.com', token: 'tok', groups: ['user'] },
      error: null,
      login: vi.fn(),
      logout: vi.fn(),
      completeNewPassword: vi.fn(),
    });

    render(
      <RoleGuard requiredGroups={['admin']}>
        <span>Protected Content</span>
      </RoleGuard>,
    );

    expect(screen.getByText('Access Denied')).toBeDefined();
    expect(screen.queryByText('Protected Content')).toBeNull();
  });

  it('renders children when requiredGroups is empty', () => {
    mockUseAuth.mockReturnValue({
      state: 'authenticated',
      user: { username: 'user@test.com', token: 'tok', groups: [] },
      error: null,
      login: vi.fn(),
      logout: vi.fn(),
      completeNewPassword: vi.fn(),
    });

    render(
      <RoleGuard requiredGroups={[]}>
        <span>Open Content</span>
      </RoleGuard>,
    );

    expect(screen.getByText('Open Content')).toBeDefined();
  });

  it('renders nothing when not authenticated', () => {
    mockUseAuth.mockReturnValue({
      state: 'unauthenticated',
      user: null,
      error: null,
      login: vi.fn(),
      logout: vi.fn(),
      completeNewPassword: vi.fn(),
    });

    const { container } = render(
      <RoleGuard requiredGroups={['admin']}>
        <span>Protected Content</span>
      </RoleGuard>,
    );

    expect(container.innerHTML).toBe('');
  });
});
