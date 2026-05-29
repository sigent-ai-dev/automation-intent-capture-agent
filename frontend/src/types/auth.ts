export type AuthState =
  | 'loading'
  | 'unauthenticated'
  | 'new-password-required'
  | 'authenticated';

export interface AuthUser {
  username: string;
  token: string;
  groups: string[];
}
