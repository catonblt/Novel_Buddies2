import { create } from 'zustand';
import { Project, Message, Agent, AppSettings, FileNode } from './types';

export interface Notification {
  id: string;
  type: 'info' | 'success' | 'warning' | 'error';
  message: string;
  timestamp: number;
}

interface AppState {
  // Project state
  currentProject: Project | null;
  setCurrentProject: (project: Project | null) => void;

  // Chat state
  messages: Message[];
  addMessage: (message: Message) => void;
  clearMessages: () => void;

  // Active agents
  activeAgents: Agent[];
  setActiveAgents: (agents: Agent[]) => void;

  // File explorer
  selectedFile: FileNode | null;
  setSelectedFile: (file: FileNode | null) => void;

  // File refresh trigger
  fileRefreshCounter: number;
  triggerFileRefresh: () => void;

  // Notifications
  notifications: Notification[];
  addNotification: (notification: Notification) => void;
  removeNotification: (id: string) => void;
  clearNotifications: () => void;

  // Settings
  settings: AppSettings;
  updateSettings: (settings: Partial<AppSettings>) => void;

  // UI state
  isLoading: boolean;
  setIsLoading: (loading: boolean) => void;
}

const defaultSettings: AppSettings = {
  apiKey: '',
  model: 'claude-sonnet-4-5-20250929',
  autoSave: true,
  autoCommit: true,
  autonomyLevel: 50,
};

export const useStore = create<AppState>((set) => ({
  currentProject: null,
  setCurrentProject: (project) => set({ currentProject: project }),

  messages: [],
  addMessage: (message) =>
    set((state) => ({ messages: [...state.messages, message] })),
  clearMessages: () => set({ messages: [] }),

  activeAgents: [],
  setActiveAgents: (agents) => set({ activeAgents: agents }),

  selectedFile: null,
  setSelectedFile: (file) => set({ selectedFile: file }),

  // File refresh trigger - increment counter to trigger useEffect in FileExplorer
  fileRefreshCounter: 0,
  triggerFileRefresh: () =>
    set((state) => ({ fileRefreshCounter: state.fileRefreshCounter + 1 })),

  // Notifications
  notifications: [],
  addNotification: (notification) =>
    set((state) => ({
      notifications: [...state.notifications, notification].slice(-10), // Keep last 10
    })),
  removeNotification: (id) =>
    set((state) => ({
      notifications: state.notifications.filter((n) => n.id !== id),
    })),
  clearNotifications: () => set({ notifications: [] }),

  settings: defaultSettings,
  updateSettings: (newSettings) =>
    set((state) => ({ settings: { ...state.settings, ...newSettings } })),

  isLoading: false,
  setIsLoading: (loading) => set({ isLoading: loading }),
}));
