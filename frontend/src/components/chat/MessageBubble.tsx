import { formatDistanceToNow } from 'date-fns';
import type { Message } from '../../types/conversation';

interface Props {
  message: Message;
}

export function MessageBubble({ message }: Props) {
  const isUser = message.role === 'user';

  return (
    <div className={`flex ${isUser ? 'justify-end' : 'justify-start'} animate-fade-in`}>
      <div
        className={`max-w-[75%] rounded-lg px-3 py-2 text-sm ${
          message.isFinal ? '' : 'opacity-70 italic'
        }`}
        style={{
          backgroundColor: isUser ? 'var(--color-user-bubble)' : 'var(--color-agent-bubble)',
          color: isUser ? 'white' : 'var(--color-text-primary)',
        }}
      >
        <p className="whitespace-pre-wrap break-words">{message.text}</p>
        <span
          className="block text-[10px] mt-1 opacity-60"
          style={{ color: isUser ? 'rgba(255,255,255,0.7)' : 'var(--color-text-secondary)' }}
        >
          {formatDistanceToNow(message.timestamp, { addSuffix: true })}
        </span>
      </div>
    </div>
  );
}
