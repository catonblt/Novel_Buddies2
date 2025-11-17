import { Message } from '@/lib/types';
import { AGENTS } from '@/lib/agents';
import { formatDate } from '@/lib/utils';
import { cn } from '@/lib/utils';

interface MessageBubbleProps {
  message: Message;
}

export default function MessageBubble({ message }: MessageBubbleProps) {
  const isUser = message.role === 'user';
  const agent = message.agentType ? AGENTS[message.agentType] : null;

  return (
    <div className={cn('flex gap-3', isUser && 'flex-row-reverse')}>
      {/* Avatar */}
      <div
        className={cn(
          'flex h-10 w-10 shrink-0 items-center justify-center rounded-full text-lg',
          isUser ? 'bg-primary' : 'bg-secondary'
        )}
        style={agent ? { backgroundColor: agent.color + '20' } : undefined}
      >
        {isUser ? '👤' : agent?.icon || '🤖'}
      </div>

      {/* Message Content */}
      <div className={cn('flex-1 space-y-1', isUser && 'text-right')}>
        <div className="flex items-baseline gap-2">
          <span className="text-sm font-semibold">
            {isUser ? 'You' : agent?.name || 'Assistant'}
          </span>
          <span className="text-xs text-muted-foreground">
            {formatDate(message.timestamp)}
          </span>
        </div>

        <div
          className={cn(
            'inline-block rounded-lg px-4 py-2',
            isUser
              ? 'bg-primary text-primary-foreground'
              : 'bg-secondary text-secondary-foreground'
          )}
        >
          <div className="whitespace-pre-wrap text-sm">{message.content}</div>
        </div>

        {message.fileChanges && message.fileChanges.length > 0 && (
          <div className="mt-2 space-y-1">
            {message.fileChanges.map((change, idx) => (
              <div
                key={idx}
                className="inline-flex items-center gap-2 rounded bg-accent px-2 py-1 text-xs"
              >
                <span
                  className={cn(
                    change.type === 'created' && 'text-green-500',
                    change.type === 'modified' && 'text-yellow-500',
                    change.type === 'deleted' && 'text-red-500'
                  )}
                >
                  {change.type === 'created' && '✓ Created'}
                  {change.type === 'modified' && '± Modified'}
                  {change.type === 'deleted' && '✗ Deleted'}
                </span>
                <span className="font-mono">{change.path}</span>
                {change.wordsChanged && (
                  <span className="text-muted-foreground">
                    ({change.wordsChanged} words)
                  </span>
                )}
              </div>
            ))}
          </div>
        )}
      </div>
    </div>
  );
}
