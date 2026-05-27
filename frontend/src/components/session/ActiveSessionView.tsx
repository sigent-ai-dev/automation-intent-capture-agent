import { useConversation } from '../../contexts/ConversationContext';
import { MessageList } from '../chat/MessageList';
import { ControlPanel } from '../controls/ControlPanel';

export function ActiveSessionView() {
  const { messages } = useConversation();

  return (
    <div className="flex-1 flex flex-col h-full">
      <div className="flex-1 overflow-hidden">
        <MessageList messages={messages} />
      </div>
      <ControlPanel />
    </div>
  );
}
