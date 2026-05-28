# Contract: AuthContext

**Type**: React Context API | **Consumer**: All authenticated components

## Provider Interface

```typescript
interface AuthContextValue {
  state: 'loading' | 'unauthenticated' | 'new-password-required' | 'authenticated';
  user: AuthUser | null;
  error: string | null;
  login(username: string, password: string): Promise<void>;
  logout(): Promise<void>;
  completeNewPassword(newPassword: string): Promise<void>;
}

interface AuthUser {
  username: string;
  token: string;
  groups: string[];
}
```

## Behavior Contract

| Method             | Precondition              | Postcondition                         | Error Behavior                    |
| ------------------ | ------------------------- | ------------------------------------- | --------------------------------- |
| login              | state = unauthenticated   | state = authenticated OR new-password-required | error set, state unchanged |
| logout             | state = authenticated     | state = unauthenticated, user = null  | state = unauthenticated           |
| completeNewPassword | state = new-password-required | state = authenticated             | error set, state unchanged        |

## Session Persistence

- On mount: checks for existing Cognito session → state = authenticated if valid
- On token expiry: Amplify auto-refreshes; if refresh fails → state = unauthenticated
- On page refresh: session restored from Amplify's localStorage tokens
