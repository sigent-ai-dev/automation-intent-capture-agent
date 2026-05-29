import { signIn, signOut, confirmSignIn, fetchAuthSession, getCurrentUser, signInWithRedirect } from 'aws-amplify/auth';

export async function login(username: string, password: string) {
  const { nextStep } = await signIn({ username, password, options: { authFlowType: 'USER_SRP_AUTH' } });
  if (nextStep.signInStep === 'DONE') return { authenticated: true, newPasswordRequired: false };
  if (nextStep.signInStep === 'CONFIRM_SIGN_IN_WITH_NEW_PASSWORD_REQUIRED') return { authenticated: false, newPasswordRequired: true };
  return { authenticated: false, newPasswordRequired: false };
}

export async function federatedSignIn(provider: string): Promise<void> {
  try {
    await signInWithRedirect({ provider: { custom: provider } });
  } catch (err) {
    const domain = import.meta.env.VITE_COGNITO_DOMAIN;
    const clientId = import.meta.env.VITE_COGNITO_CLIENT_ID;
    const redirectUri = import.meta.env.VITE_COGNITO_REDIRECT_URI || window.location.origin;

    if (domain && clientId) {
      const params = new URLSearchParams({
        identity_provider: provider,
        response_type: 'code',
        client_id: clientId,
        redirect_uri: redirectUri,
        scope: 'openid email profile',
      });
      window.location.href = `https://${domain}/oauth2/authorize?${params.toString()}`;
    } else {
      throw err;
    }
  }
}

export async function completeNewPassword(newPassword: string) {
  await confirmSignIn({ challengeResponse: newPassword });
}

export async function logout() {
  await signOut();
}

export async function getToken(): Promise<string | null> {
  try {
    const session = await fetchAuthSession();
    return session.tokens?.idToken?.toString() ?? null;
  } catch {
    return null;
  }
}

export async function isAuthenticated(): Promise<boolean> {
  try {
    await getCurrentUser();
    return true;
  } catch {
    return false;
  }
}
