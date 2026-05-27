import { useEffect, useRef } from 'react';
import type { Message } from '../../types/conversation';
import { MessageBubble } from './MessageBubble';

interface Props {
  messages: Message[];
}

export function MessageList({ messages }: Props) {
  const endRef = useRef<HTMLDivElement>(null);

  useEffect(() => {
    endRef.current?.scrollIntoView({ behavior: 'smooth' });
  }, [messages.length]);

  if (messages.length === 0) {
    return (
      <div className="flex-1 flex items-center justify-center h-full p-4">
        <p className="text-sm" style={{ color: 'var(--color-text-secondary)' }}>
          Start speaking to begin the conversation...
        </p>
      </div>
    );
  }

  return (
    <div className="h-full overflow-y-auto p-4 space-y-3">
      {messages.map((msg) => (
        <MessageBubble key={msg.id} message={msg} />
      ))}
      <div ref={endRef} />
    </div>
  );
}
