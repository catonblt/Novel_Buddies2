import { useState, useRef, useEffect } from 'react';
import { useStore } from '@/lib/store';
import { api } from '@/lib/api';
import { AGENTS } from '@/lib/agents';
import { AgentType, Message } from '@/lib/types';
import { ScrollArea } from '@/components/ui/scroll-area';
import { Button } from '@/components/ui/button';
import { Textarea } from '@/components/ui/textarea';
import { Send, Loader2 } from 'lucide-react';
import MessageBubble from './MessageBubble';
import AgentSelector from './AgentSelector';

export default function AgentChat() {
  const { currentProject, messages, addMessage, settings } = useStore();
  const [input, setInput] = useState('');
  const [isStreaming, setIsStreaming] = useState(false);
  const [selectedAgent, setSelectedAgent] = useState<AgentType>('story-architect');
  const scrollRef = useRef<HTMLDivElement>(null);

  useEffect(() => {
    // Scroll to bottom when new messages arrive
    if (scrollRef.current) {
      scrollRef.current.scrollTop = scrollRef.current.scrollHeight;
    }
  }, [messages]);

  useEffect(() => {
    // Load existing messages for the project
    if (currentProject) {
      const loadMessages = async () => {
        try {
          const msgs = await api.getMessages(currentProject.id);
          // Load messages into store
          msgs.forEach((msg) => addMessage(msg));
        } catch (error) {
          console.error('Failed to load messages:', error);
        }
      };
      loadMessages();
    }
  }, [currentProject, addMessage]);

  const handleSend = async () => {
    if (!input.trim() || !currentProject || !settings.apiKey) {
      if (!settings.apiKey) {
        alert('Please set your Anthropic API key in settings');
      }
      return;
    }

    const userMessage: Message = {
      id: Date.now().toString(),
      role: 'user',
      content: input,
      timestamp: Math.floor(Date.now() / 1000),
    };

    addMessage(userMessage);
    setInput('');
    setIsStreaming(true);

    try {
      const stream = await api.sendMessage(
        currentProject.id,
        input,
        selectedAgent,
        settings.apiKey
      );

      const reader = stream.getReader();
      const decoder = new TextDecoder();
      let assistantContent = '';

      while (true) {
        const { done, value } = await reader.read();
        if (done) break;

        const chunk = decoder.decode(value);
        const lines = chunk.split('\n');

        for (const line of lines) {
          if (line.startsWith('data: ')) {
            try {
              const data = JSON.parse(line.slice(6));

              if (data.type === 'content') {
                assistantContent += data.content;
              } else if (data.type === 'done') {
                const assistantMessage: Message = {
                  id: Date.now().toString(),
                  role: 'assistant',
                  content: assistantContent,
                  agentType: selectedAgent,
                  timestamp: Math.floor(Date.now() / 1000),
                };
                addMessage(assistantMessage);
              } else if (data.type === 'error') {
                console.error('Streaming error:', data.error);
                alert(`Error: ${data.error}`);
              }
            } catch (e) {
              // Ignore parsing errors for incomplete chunks
            }
          }
        }
      }
    } catch (error) {
      console.error('Failed to send message:', error);
      alert('Failed to send message. Please check your connection.');
    } finally {
      setIsStreaming(false);
    }
  };

  const handleKeyPress = (e: React.KeyboardEvent) => {
    if (e.key === 'Enter' && !e.shiftKey) {
      e.preventDefault();
      handleSend();
    }
  };

  return (
    <div className="flex h-full flex-col">
      {/* Messages Area */}
      <ScrollArea className="flex-1 p-6">
        <div ref={scrollRef} className="space-y-4">
          {messages.length === 0 ? (
            <div className="flex h-full items-center justify-center text-center text-muted-foreground">
              <div>
                <p className="text-lg font-semibold">Start a conversation</p>
                <p className="mt-2 text-sm">
                  Select an agent below and describe what you'd like to work on.
                </p>
              </div>
            </div>
          ) : (
            messages.map((message) => (
              <MessageBubble key={message.id} message={message} />
            ))
          )}
          {isStreaming && (
            <div className="flex items-center gap-2 text-sm text-muted-foreground">
              <Loader2 className="h-4 w-4 animate-spin" />
              <span>{AGENTS[selectedAgent].name} is thinking...</span>
            </div>
          )}
        </div>
      </ScrollArea>

      {/* Input Area */}
      <div className="border-t border-border p-4">
        <AgentSelector selected={selectedAgent} onSelect={setSelectedAgent} />

        <div className="mt-3 flex gap-2">
          <Textarea
            value={input}
            onChange={(e) => setInput(e.target.value)}
            onKeyDown={handleKeyPress}
            placeholder={`Message ${AGENTS[selectedAgent].name}...`}
            className="min-h-[80px] resize-none"
            disabled={isStreaming}
          />
          <Button
            onClick={handleSend}
            disabled={!input.trim() || isStreaming}
            size="icon"
            className="h-[80px] w-12"
          >
            <Send className="h-5 w-5" />
          </Button>
        </div>
      </div>
    </div>
  );
}
