export interface Project {
  id: string;
  title: string;
  author: string;
  genre: string;
  targetWordCount: number;
  createdAt: number;
  updatedAt: number;
  path: string;
  premise?: string;
  themes?: string;
  setting?: string;
  keyCharacters?: string;
}

export interface Message {
  id: string;
  role: 'user' | 'assistant';
  content: string;
  agentType?: string;
  timestamp: number;
  fileChanges?: FileChange[];
}

export interface FileChange {
  type: 'created' | 'modified' | 'deleted';
  path: string;
  wordsChanged?: number;
}

export interface Agent {
  name: string;
  icon: string;
  color: string;
  description: string;
}

export interface FileNode {
  name: string;
  path: string;
  isDirectory: boolean;
  size?: number;
  children?: FileNode[];
  wordCount?: number;
}

export interface CommitInfo {
  id: string;
  message: string;
  author: string;
  timestamp: number;
}

export interface AppSettings {
  apiKey: string;
  model: string;
  autoSave: boolean;
  autoCommit: boolean;
  autonomyLevel: number; // 0-100
}

export interface AgentStatus {
  agent: string;
  message: string;
}
