import { createContext, useCallback, useContext, useRef, useState, type ReactNode } from 'react';
import type { Session, SessionProgress, SessionResult, SessionStatus } from '../types/session';
import type { ServerMessage } from '../types/websocket';
import { sessionService } from '../services/sessionService';
import { wsService } from '../services/websocketService';

interface SessionContextValue {
  session: Session | null;
  status: SessionStatus;
  startSession: (projectName: string) => Promise<void>;
  endSession: () => Promise<void>;
  resetSession: () => void;
}

const SessionContext = createContext<SessionContextValue | null>(null);

export function SessionProvider({ children }: { children: ReactNode }) {
  const [session, setSession] = useState<Session | null>(null);
  const [status, setStatus] = useState<SessionStatus>('idle');
  const pollingRef = useRef<ReturnType<typeof setInterval> | null>(null);
  const sessionIdRef = useRef<string | null>(null);

  const updateProgress = useCallback((progress: SessionProgress) => {
    setSession((s) => (s ? { ...s, progress } : s));
  }, []);

  const handleComplete = useCallback(async (sessionId: string) => {
    setStatus('completing');
    try {
      const result = await sessionService.getResult(sessionId);
      const sessionResult: SessionResult = {
        intentMd: result.intent_md,
        state: result.state,
        auditMd: result.audit_md,
      };
      setSession((s) => (s ? { ...s, result: sessionResult } : s));
      setStatus('complete');
    } catch {
      setStatus('failed');
      setSession((s) => (s ? { ...s, error: 'Failed to fetch result' } : s));
    }
  }, []);

  const handleWsMessage = useCallback(
    (msg: ServerMessage) => {
      switch (msg.type) {
        case 'codec_ack':
          break;
        case 'session_ready':
          setStatus('active');
          break;
        case 'progress':
          updateProgress({
            sectionsCovered: msg.sections_covered,
            proposalRounds: msg.proposal_rounds,
            alignmentReached: msg.alignment_reached,
          });
          break;
        case 'session_complete':
          if (sessionIdRef.current) handleComplete(sessionIdRef.current);
          break;
        case 'error':
          setStatus('failed');
          setSession((s) => (s ? { ...s, error: msg.message } : s));
          break;
        case 'server_shutdown':
          // WebSocket service handles reconnection automatically
          break;
      }
    },
    [handleComplete, updateProgress],
  );

  const startSession = useCallback(async (projectName: string) => {
    setStatus('creating');
    try {
      const resp = await sessionService.create(projectName);
      const newSession: Session = {
        id: resp.session_id,
        projectName,
        status: 'connecting',
        joinUrl: resp.join_url,
        createdAt: resp.created_at,
        progress: { sectionsCovered: [], proposalRounds: 0, alignmentReached: false },
        result: null,
        error: null,
      };
      setSession(newSession);
      sessionIdRef.current = resp.session_id;
      setStatus('connecting');

      wsService.setHandlers({
        onMessage: handleWsMessage,
        onStatus: (wsStatus) => {
          if (wsStatus === 'connected') setStatus('negotiating');
        },
      });
      await wsService.connect(resp.session_id);
    } catch (err) {
      setStatus('failed');
      setSession((s) => (s ? { ...s, error: String(err) } : s));
    }
  }, [handleWsMessage]);

  const endSession = useCallback(async () => {
    if (!session?.id) return;
    try {
      await sessionService.cancel(session.id);
    } catch {
      // best effort
    }
    wsService.disconnect();
    setStatus('cancelled');
    if (pollingRef.current) clearInterval(pollingRef.current);
    setTimeout(() => {
      setStatus('idle');
      setSession(null);
    }, 2000);
  }, [session?.id]);

  const resetSession = useCallback(() => {
    wsService.disconnect();
    setStatus('idle');
    setSession(null);
  }, []);

  return (
    <SessionContext.Provider value={{ session, status, startSession, endSession, resetSession }}>
      {children}
    </SessionContext.Provider>
  );
}

export function useSession() {
  const ctx = useContext(SessionContext);
  if (!ctx) throw new Error('useSession must be used within SessionProvider');
  return ctx;
}
