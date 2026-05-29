import { Amplify } from 'aws-amplify';

export const isAuthConfigured = Boolean(
  import.meta.env.VITE_COGNITO_USER_POOL_ID && import.meta.env.VITE_COGNITO_CLIENT_ID,
);

export function configureAmplify() {
  if (!isAuthConfigured) {
    console.warn('[auth] Cognito not configured: VITE_COGNITO_USER_POOL_ID or VITE_COGNITO_CLIENT_ID missing');
    return;
  }

  Amplify.configure({
    Auth: {
      Cognito: {
        userPoolId: import.meta.env.VITE_COGNITO_USER_POOL_ID,
        userPoolClientId: import.meta.env.VITE_COGNITO_CLIENT_ID,
        loginWith: { username: true },
      },
    },
  });
}
