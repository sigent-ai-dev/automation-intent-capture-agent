import { ThemeProvider } from './contexts/ThemeContext';
import { ErrorBoundary } from './components/common/ErrorBoundary';
import { MainLayout } from './components/layout/MainLayout';
import { Header } from './components/layout/Header';
import { LandingView } from './components/session/LandingView';

export function App() {
  return (
    <ErrorBoundary>
      <ThemeProvider>
        <MainLayout>
          <Header />
          <main className="flex-1 flex flex-col items-center justify-center p-4">
            <LandingView />
          </main>
        </MainLayout>
      </ThemeProvider>
    </ErrorBoundary>
  );
}
