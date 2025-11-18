import { useStore } from './store';

interface FileChangeEvent {
  type: 'file_change';
  path: string;
  operation: string;
  agent_type?: string;
  timestamp: string;
}

interface FileOperationsCompleteEvent {
  type: 'file_operations_complete';
  results: Array<{
    success: boolean;
    path: string;
    message: string;
    operation: string;
  }>;
  timestamp: string;
}

type WebSocketMessage = FileChangeEvent | FileOperationsCompleteEvent | { type: 'ping' };

class FileSystemWebSocket {
  private ws: WebSocket | null = null;
  private reconnectInterval: ReturnType<typeof setInterval> | null = null;
  private reconnectAttempts = 0;
  private maxReconnectAttempts = 5;
  private projectId: string | null = null;
  private isConnecting = false;

  connect(projectId: string) {
    // Don't reconnect if already connected to same project
    if (this.projectId === projectId && this.ws?.readyState === WebSocket.OPEN) {
      return;
    }

    // Close existing connection
    if (this.ws) {
      this.ws.close();
      this.ws = null;
    }

    this.projectId = projectId;
    this.isConnecting = true;
    this.reconnectAttempts = 0;

    this.createConnection();
  }

  private createConnection() {
    if (!this.projectId) return;

    try {
      this.ws = new WebSocket(`ws://localhost:8000/ws/${this.projectId}`);

      this.ws.onopen = () => {
        console.log(`WebSocket connected for project: ${this.projectId}`);
        this.isConnecting = false;
        this.reconnectAttempts = 0;
        this.clearReconnect();
      };

      this.ws.onmessage = (event) => {
        try {
          const data: WebSocketMessage = JSON.parse(event.data);
          this.handleMessage(data);
        } catch (e) {
          // Handle pong response
          if (event.data === 'pong') {
            return;
          }
          console.error('Failed to parse WebSocket message:', e);
        }
      };

      this.ws.onerror = (error) => {
        console.error('WebSocket error:', error);
        this.isConnecting = false;
      };

      this.ws.onclose = (event) => {
        console.log(`WebSocket disconnected: ${event.code} ${event.reason}`);
        this.isConnecting = false;

        // Only reconnect if we still have a project and haven't exceeded attempts
        if (this.projectId && this.reconnectAttempts < this.maxReconnectAttempts) {
          this.scheduleReconnect();
        }
      };
    } catch (error) {
      console.error('Failed to create WebSocket connection:', error);
      this.isConnecting = false;
    }
  }

  private handleMessage(data: WebSocketMessage) {
    const store = useStore.getState();

    switch (data.type) {
      case 'file_change':
        // Trigger file explorer refresh
        if (store.triggerFileRefresh) {
          store.triggerFileRefresh();
        }

        // Add notification
        store.addNotification({
          id: Date.now().toString(),
          type: 'info',
          message: `File ${data.operation}: ${data.path}`,
          timestamp: Date.now(),
        });
        break;

      case 'file_operations_complete':
        // Trigger file explorer refresh
        if (store.triggerFileRefresh) {
          store.triggerFileRefresh();
        }

        // Show completion notification
        const successCount = data.results.filter(r => r.success).length;
        const totalCount = data.results.length;

        store.addNotification({
          id: Date.now().toString(),
          type: successCount === totalCount ? 'success' : 'warning',
          message: `File operations complete: ${successCount}/${totalCount} successful`,
          timestamp: Date.now(),
        });
        break;

      case 'ping':
        // Respond to server ping
        if (this.ws?.readyState === WebSocket.OPEN) {
          this.ws.send('pong');
        }
        break;
    }
  }

  private scheduleReconnect() {
    if (this.reconnectInterval) return;

    this.reconnectAttempts++;
    const delay = Math.min(1000 * Math.pow(2, this.reconnectAttempts), 30000);

    console.log(`Scheduling WebSocket reconnect in ${delay}ms (attempt ${this.reconnectAttempts})`);

    this.reconnectInterval = setTimeout(() => {
      this.reconnectInterval = null;
      if (this.projectId) {
        this.createConnection();
      }
    }, delay);
  }

  private clearReconnect() {
    if (this.reconnectInterval) {
      clearTimeout(this.reconnectInterval);
      this.reconnectInterval = null;
    }
  }

  disconnect() {
    this.clearReconnect();
    this.projectId = null;
    this.reconnectAttempts = 0;

    if (this.ws) {
      this.ws.close();
      this.ws = null;
    }
  }

  isConnected(): boolean {
    return this.ws?.readyState === WebSocket.OPEN;
  }

  getProjectId(): string | null {
    return this.projectId;
  }
}

// Export singleton instance
export const fileSystemWS = new FileSystemWebSocket();
