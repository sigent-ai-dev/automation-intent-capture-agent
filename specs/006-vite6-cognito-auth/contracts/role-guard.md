# Contract: RoleGuard Component

**Type**: React component | **Consumer**: Route-level access control

## Interface

```typescript
interface RoleGuardProps {
  requiredGroups: string[];
  children: ReactNode;
  fallback?: ReactNode; // defaults to "Access Denied" message
}
```

## Behavior

| User Groups       | Required Groups | Result            |
| ----------------- | --------------- | ----------------- |
| ["admin"]         | ["admin"]       | Render children   |
| ["admin", "user"] | ["admin"]       | Render children   |
| ["user"]          | ["admin"]       | Render fallback   |
| []                | ["admin"]       | Render fallback   |
| ["admin"]         | []              | Render children   |

**Match logic**: User must have at least one group in common with `requiredGroups` (OR semantics).

## Dependencies

- Reads from `AuthContext.user.groups`
- If `AuthContext.state !== 'authenticated'`, renders nothing (auth check happens upstream)
