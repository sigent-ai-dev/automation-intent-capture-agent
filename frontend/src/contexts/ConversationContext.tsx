import { createContext, useCallback, useContext, useRef, useState, type ReactNode } from 'react';
import type { Message } from '../types/conversation';

interface ConversationContextValue {
  messages: Message[];
  addMessage: (role: 'user' | 'agent', text: string, isFinal: boolean) => void;
  updateInterim: (role: 'user' | 'agent', text: string) => void;
  finalizeInterim: (role: 'user' | 'agent', text: string) => void;
  clearMessages: () => void;
}

const ConversationContext = createContext<ConversationContextValue | null>(null);

export function ConversationProvider({ children }: { children: ReactNode }) {
  const [messages, setMessages] = useState<Message[]>([]);
  const interimIdRef = useRef<{ user: string | null; agent: string | null }>({ user: null, agent: null });

  const addMessage = useCallback((role: 'user' | 'agent', text: string, isFinal: boolean) => {
    const id = crypto.randomUUID();
    setMessages((prev) => [...prev, { id, role, text, timestamp: new Date(), isFinal }]);
    return id;
  }, []);

  const updateInterim = useCallback((role: 'user' | 'agent', text: string) => {
    const existingId = interimIdRef.current[role];
    if (existingId) {
      setMessages((prev) =>
        prev.map((m) => (m.id === existingId ? { ...m, text } : m)),
      );
    } else {
      const id = crypto.randomUUID();
      interimIdRef.current[role] = id;
      setMessages((prev) => [...prev, { id, role, text, timestamp: new Date(), isFinal: false }]);
    }
  }, []);

  const finalizeInterim = useCallback((role: 'user' | 'agent', text: string) => {
    const existingId = interimIdRef.current[role];
    if (existingId) {
      setMessages((prev) =>
        prev.map((m) => (m.id === existingId ? { ...m, text, isFinal: true } : m)),
      );
      interimIdRef.current[role] = null;
    } else {
      addMessage(role, text, true);
    }
  }, [addMessage]);

  const clearMessages = useCallback(() => {
    setMessages([]);
    interimIdRef.current = { user: null, agent: null };
  }, []);

  return (
    <ConversationContext.Provider value={{ messages, addMessage, updateInterim, finalizeInterim, clearMessages }}>
      {children}
    </ConversationContext.Provider>
  );
}

export function useConversation() {
  const ctx = useContext(ConversationContext);
  if (!ctx) throw new Error('useConversation must be used within ConversationProvider');
  return ctx;
}
