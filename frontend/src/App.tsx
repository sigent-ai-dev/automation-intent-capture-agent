import { ThemeProvider } from './contexts/ThemeContext';
import { AuthProvider, useAuth } from './contexts/AuthContext';
import { SessionProvider, useSession } from './contexts/SessionContext';
import { ConversationProvider } from './contexts/ConversationContext';
import { ErrorBoundary } from './components/common/ErrorBoundary';
import { MainLayout } from './components/layout/MainLayout';
import { Header } from './components/layout/Header';
import { LandingView } from './components/session/LandingView';
import { ActiveSessionView } from './components/session/ActiveSessionView';
import { CompletionView } from './components/session/CompletionView';
import { useBeforeUnload } from './hooks/useBeforeUnload';
import LoginForm from './components/auth/LoginForm';
import NewPasswordForm from './components/auth/NewPasswordForm';
import { RoleGuard } from './components/auth/RoleGuard';
import { LoadingSpinner } from './components/common/LoadingSpinner';

function AppContent() {
  const { status } = useSession();
  useBeforeUnload(status === 'active' || status === 'completing');

  const renderContent = () => {
    switch (status) {
      case 'idle':
        return <LandingView />;
      case 'creating':
      case 'connecting':
      case 'negotiating':
        return <LandingView />;
      case 'active':
        return <ActiveSessionView />;
      case 'completing':
      case 'complete':
        return <CompletionView />;
      case 'cancelled':
        return <LandingView />;
      case 'failed':
        return <LandingView />;
      default:
        return <LandingView />;
    }
  };

  return (
    <MainLayout>
      <Header />
      <main className="flex-1 flex flex-col">
        {renderContent()}
      </main>
    </MainLayout>
  );
}

function AuthGate() {
  const { state } = useAuth();

  switch (state) {
    case 'loading':
      return (
        <div className="flex items-center justify-center min-h-screen">
          <LoadingSpinner />
        </div>
      );
    case 'unauthenticated':
      return <LoginForm />;
    case 'new-password-required':
      return <NewPasswordForm />;
    case 'authenticated':
      return (
        <SessionProvider>
          <ConversationProvider>
            <AppContent />
            <RoleGuard requiredGroups={['admin']} fallback={null}>
              <div id="admin-panel-placeholder" />
            </RoleGuard>
          </ConversationProvider>
        </SessionProvider>
      );
  }
}

export function App() {
  return (
    <ErrorBoundary>
      <ThemeProvider>
        <AuthProvider>
          <AuthGate />
        </AuthProvider>
      </ThemeProvider>
    </ErrorBoundary>
  );
}
