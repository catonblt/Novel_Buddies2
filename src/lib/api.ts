import { Project, Message, AgentType } from './types';

const API_BASE_URL = 'http://localhost:8000';

export const api = {
  // Project operations
  async createProject(projectData: Omit<Project, 'id' | 'createdAt' | 'updatedAt'>): Promise<Project> {
    const response = await fetch(`${API_BASE_URL}/projects`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify(projectData),
    });
    if (!response.ok) throw new Error('Failed to create project');
    return response.json();
  },

  async getProject(id: string): Promise<Project> {
    const response = await fetch(`${API_BASE_URL}/projects/${id}`);
    if (!response.ok) throw new Error('Failed to get project');
    return response.json();
  },

  async listProjects(): Promise<Project[]> {
    const response = await fetch(`${API_BASE_URL}/projects`);
    if (!response.ok) throw new Error('Failed to list projects');
    return response.json();
  },

  async updateProject(id: string, data: Partial<Project>): Promise<Project> {
    const response = await fetch(`${API_BASE_URL}/projects/${id}`, {
      method: 'PATCH',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify(data),
    });
    if (!response.ok) throw new Error('Failed to update project');
    return response.json();
  },

  // Agent chat
  async sendMessage(
    projectId: string,
    message: string,
    agentType: AgentType,
    apiKey: string
  ): Promise<ReadableStream<Uint8Array>> {
    const response = await fetch(`${API_BASE_URL}/chat`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({
        project_id: projectId,
        message,
        agent_type: agentType,
        api_key: apiKey,
      }),
    });
    if (!response.ok) throw new Error('Failed to send message');
    if (!response.body) throw new Error('No response body');
    return response.body;
  },

  // Conversation history
  async getMessages(projectId: string): Promise<Message[]> {
    const response = await fetch(`${API_BASE_URL}/projects/${projectId}/messages`);
    if (!response.ok) throw new Error('Failed to get messages');
    return response.json();
  },

  // File operations
  async listFiles(projectPath: string): Promise<any> {
    const response = await fetch(`${API_BASE_URL}/files/list`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ path: projectPath }),
    });
    if (!response.ok) throw new Error('Failed to list files');
    return response.json();
  },

  async readFile(filePath: string): Promise<string> {
    const response = await fetch(`${API_BASE_URL}/files/read`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ path: filePath }),
    });
    if (!response.ok) throw new Error('Failed to read file');
    const data = await response.json();
    return data.content;
  },

  async writeFile(filePath: string, content: string): Promise<void> {
    const response = await fetch(`${API_BASE_URL}/files/write`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ path: filePath, content }),
    });
    if (!response.ok) throw new Error('Failed to write file');
  },

  // Git operations
  async getCommitHistory(projectPath: string, maxCount: number = 20): Promise<any[]> {
    const response = await fetch(`${API_BASE_URL}/git/log`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ repo_path: projectPath, max_count: maxCount }),
    });
    if (!response.ok) throw new Error('Failed to get commit history');
    return response.json();
  },

  async restoreFileVersion(projectPath: string, filePath: string, commitId: string): Promise<void> {
    const response = await fetch(`${API_BASE_URL}/git/restore`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ repo_path: projectPath, file_path: filePath, commit_id: commitId }),
    });
    if (!response.ok) throw new Error('Failed to restore file version');
  },
};
