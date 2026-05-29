import type { ReactNode } from 'react';
import { useAuth } from '../../contexts/AuthContext';

interface RoleGuardProps {
  requiredGroups: string[];
  children: ReactNode;
  fallback?: ReactNode;
}

export function RoleGuard({ requiredGroups, children, fallback }: RoleGuardProps) {
  const { state, user } = useAuth();

  if (state !== 'authenticated' || !user) return null;

  if (requiredGroups.length === 0) return <>{children}</>;

  const hasAccess = user.groups.some((g) => requiredGroups.includes(g));

  if (hasAccess) return <>{children}</>;

  return (
    <>
      {fallback ?? (
        <div className="flex items-center justify-center min-h-[200px]">
          <p className="text-[var(--color-text-secondary)] text-lg">Access Denied</p>
        </div>
      )}
    </>
  );
}
