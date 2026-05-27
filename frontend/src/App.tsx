import { ThemeProvider } from './contexts/ThemeContext';
import { SessionProvider, useSession } from './contexts/SessionContext';
import { ConversationProvider } from './contexts/ConversationContext';
import { ErrorBoundary } from './components/common/ErrorBoundary';
import { MainLayout } from './components/layout/MainLayout';
import { Header } from './components/layout/Header';
import { LandingView } from './components/session/LandingView';
import { ActiveSessionView } from './components/session/ActiveSessionView';
import { CompletionView } from './components/session/CompletionView';
import { useBeforeUnload } from './hooks/useBeforeUnload';

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

export function App() {
  return (
    <ErrorBoundary>
      <ThemeProvider>
        <SessionProvider>
          <ConversationProvider>
            <AppContent />
          </ConversationProvider>
        </SessionProvider>
      </ThemeProvider>
    </ErrorBoundary>
  );
}
