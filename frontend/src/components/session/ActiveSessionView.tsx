import { useConversation } from '../../contexts/ConversationContext';
import { MessageList } from '../chat/MessageList';
import { ControlPanel } from '../controls/ControlPanel';
import { ProgressPanel } from './ProgressPanel';

export function ActiveSessionView() {
  const { messages } = useConversation();

  return (
    <div className="flex-1 flex h-full overflow-hidden">
      <div className="flex-1 flex flex-col">
        <div className="flex-1 overflow-hidden">
          <MessageList messages={messages} />
        </div>
        <ControlPanel />
      </div>
      <ProgressPanel />
    </div>
  );
}
