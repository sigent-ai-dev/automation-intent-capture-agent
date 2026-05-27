import { useState } from 'react';
import { wsService } from '../../services/websocketService';

export function TextInput() {
  const [text, setText] = useState('');

  const handleSubmit = (e: React.FormEvent) => {
    e.preventDefault();
    if (!text.trim()) return;
    wsService.sendJSON({ type: 'text_input', text: text.trim() });
    setText('');
  };

  return (
    <form onSubmit={handleSubmit} className="flex gap-2 w-full">
      <input
        type="text"
        value={text}
        onChange={(e) => setText(e.target.value)}
        placeholder="Type your response (mic unavailable)..."
        className="flex-1 px-3 py-2 rounded-lg border text-sm"
        style={{
          backgroundColor: 'var(--color-background)',
          borderColor: 'var(--color-border)',
          color: 'var(--color-text-primary)',
        }}
      />
      <button
        type="submit"
        disabled={!text.trim()}
        className="btn btn-primary"
      >
        Send
      </button>
    </form>
  );
}
