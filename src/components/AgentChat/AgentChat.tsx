import { useState, useRef, useEffect } from 'react';
import { useStore } from '@/lib/store';
import { api } from '@/lib/api';
import { STORY_ADVOCATE, AGENT_INFO } from '@/lib/agents';
import { getApiUrl } from '@/lib/config';
import { Message, AgentStatus } from '@/lib/types';
import { ScrollArea } from '@/components/ui/scroll-area';
import { Button } from '@/components/ui/button';
import { Textarea } from '@/components/ui/textarea';
import { Send, Loader2 } from 'lucide-react';
import MessageBubble from './MessageBubble';
import FileOperationDialog, { FileOperation } from '@/components/FileOperationDialog';
import { fileSystemWS } from '@/lib/websocket';

export default function AgentChat() {
  const { currentProject, messages, addMessage, settings, triggerFileRefresh, addNotification } = useStore();
  const [input, setInput] = useState('');
  const [isStreaming, setIsStreaming] = useState(false);
  const [agentStatus, setAgentStatus] = useState<AgentStatus | null>(null);
  const scrollRef = useRef<HTMLDivElement>(null);

  // File operation state
  const [pendingOperations, setPendingOperations] = useState<FileOperation[]>([]);
  const [showFileOpDialog, setShowFileOpDialog] = useState(false);

  useEffect(() => {
    // Scroll to bottom when new messages arrive
    if (scrollRef.current) {
      scrollRef.current.scrollTop = scrollRef.current.scrollHeight;
    }
  }, [messages]);

  // Connect WebSocket when project loads
  useEffect(() => {
    if (currentProject) {
      fileSystemWS.connect(currentProject.id);
    }
    return () => {
      fileSystemWS.disconnect();
    };
  }, [currentProject]);

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
    setAgentStatus({ agent: 'story_advocate', message: 'Processing...' });

    try {
      const stream = await api.sendMessage(
        currentProject.id,
        input,
        settings.apiKey,
        settings.model,
        settings.autonomyLevel
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

              if (data.type === 'status') {
                // Update status toast
                setAgentStatus({
                  agent: data.agent || 'story_advocate',
                  message: data.message
                });
              } else if (data.type === 'content') {
                assistantContent += data.content;
              } else if (data.type === 'file_operations') {
                // Handle file operations from agent
                if (data.require_confirmation) {
                  // Show confirmation dialog
                  setPendingOperations(data.operations);
                  setShowFileOpDialog(true);
                } else {
                  // Auto-execute without confirmation
                  executeFileOperations(data.operations);
                }
              } else if (data.type === 'done') {
                const assistantMessage: Message = {
                  id: Date.now().toString(),
                  role: 'assistant',
                  content: assistantContent,
                  agentType: 'story_advocate',
                  timestamp: Math.floor(Date.now() / 1000),
                };
                addMessage(assistantMessage);
                setAgentStatus(null);
              } else if (data.type === 'error') {
                console.error('Streaming error:', data.error);
                alert(`Error: ${data.error}`);
                setAgentStatus(null);
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
      setAgentStatus(null);
    } finally {
      setIsStreaming(false);
    }
  };

  const executeFileOperations = async (operations: FileOperation[]) => {
    if (!currentProject) return;

    try {
      const response = await fetch(getApiUrl('/file-operations/batch'), {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          operations: operations,
          project_id: currentProject.id,
        }),
      });

      if (!response.ok) {
        throw new Error('Failed to execute file operations');
      }

      const result = await response.json();

      // Show notification
      addNotification({
        id: Date.now().toString(),
        type: result.successful === result.total ? 'success' : 'warning',
        message: `File operations complete: ${result.successful}/${result.total} successful`,
        timestamp: Date.now(),
      });

      // Refresh file explorer
      triggerFileRefresh();
    } catch (error) {
      console.error('Failed to execute file operations:', error);
      addNotification({
        id: Date.now().toString(),
        type: 'error',
        message: 'Failed to execute file operations',
        timestamp: Date.now(),
      });
    }
  };

  const handleFileOpConfirm = async (operations: FileOperation[]) => {
    setShowFileOpDialog(false);
    await executeFileOperations(operations);
    setPendingOperations([]);
  };

  const handleFileOpReject = () => {
    setShowFileOpDialog(false);
    setPendingOperations([]);
    addNotification({
      id: Date.now().toString(),
      type: 'info',
      message: 'File operations rejected',
      timestamp: Date.now(),
    });
  };

  const handleKeyPress = (e: React.KeyboardEvent) => {
    if (e.key === 'Enter' && !e.shiftKey) {
      e.preventDefault();
      handleSend();
    }
  };

  // Get agent display info
  const getAgentDisplay = (agentKey: string) => {
    return AGENT_INFO[agentKey] || { name: agentKey, icon: '🤖', color: '#6b7280' };
  };

  return (
    <>
      <div className="flex h-full flex-col">
        {/* Messages Area */}
        <ScrollArea className="flex-1 p-6">
          <div ref={scrollRef} className="space-y-4">
            {messages.length === 0 ? (
              <div className="flex h-full items-center justify-center text-center text-muted-foreground">
                <div>
                  <p className="text-lg font-semibold">Start a conversation</p>
                  <p className="mt-2 text-sm">
                    Tell the Story Advocate what you'd like to work on.
                  </p>
                  <p className="mt-1 text-xs text-muted-foreground">
                    The right agents will automatically contribute to your request.
                  </p>
                </div>
              </div>
            ) : (
              messages.map((message) => (
                <MessageBubble key={message.id} message={message} />
              ))
            )}
            {isStreaming && agentStatus && (
              <div className="flex items-center gap-2 text-sm text-muted-foreground">
                <Loader2 className="h-4 w-4 animate-spin" />
                <span>{agentStatus.message}</span>
              </div>
            )}
          </div>
        </ScrollArea>

        {/* Status Toast - shows which agent is working */}
        {agentStatus && (
          <div className="mx-4 mb-2">
            <div
              className="flex items-center gap-2 rounded-lg px-3 py-2 text-sm"
              style={{
                backgroundColor: getAgentDisplay(agentStatus.agent).color + '15',
                borderLeft: `3px solid ${getAgentDisplay(agentStatus.agent).color}`,
              }}
            >
              <span>{getAgentDisplay(agentStatus.agent).icon}</span>
              <span className="font-medium" style={{ color: getAgentDisplay(agentStatus.agent).color }}>
                {getAgentDisplay(agentStatus.agent).name}
              </span>
              <span className="text-muted-foreground">
                {agentStatus.message}
              </span>
            </div>
          </div>
        )}

        {/* Input Area */}
        <div className="border-t border-border p-4">
          <div className="flex gap-2">
            <Textarea
              value={input}
              onChange={(e) => setInput(e.target.value)}
              onKeyDown={handleKeyPress}
              placeholder={`Message ${STORY_ADVOCATE.name}...`}
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

      {/* File Operation Confirmation Dialog */}
      <FileOperationDialog
        operations={pendingOperations}
        isOpen={showFileOpDialog}
        onConfirm={handleFileOpConfirm}
        onReject={handleFileOpReject}
        agentType="story_advocate"
      />
    </>
  );
}
