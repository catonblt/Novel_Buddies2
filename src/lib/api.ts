import { Project, Message } from './types';
import { logger } from './logger';
import { API_BASE_URL } from './config';

/**
 * Wrapper for API calls with logging and error handling
 */
async function apiCall<T>(
  method: string,
  url: string,
  options?: RequestInit,
  body?: any
): Promise<T> {
  const fullUrl = `${API_BASE_URL}${url}`;
  const startTime = performance.now();

  // Log request
  logger.apiRequest(method, fullUrl, body);

  try {
    const response = await fetch(fullUrl, {
      method,
      headers: { 'Content-Type': 'application/json' },
      ...(body && { body: JSON.stringify(body) }),
      ...options,
    });

    const duration = performance.now() - startTime;

    if (!response.ok) {
      const errorText = await response.text();
      logger.apiResponse(method, fullUrl, response.status, duration, errorText);
      throw new Error(`API call failed: ${response.status} ${errorText}`);
    }

    logger.apiResponse(method, fullUrl, response.status, duration);

    return response.json();
  } catch (error) {
    const duration = performance.now() - startTime;

    // Enhanced error logging with more details
    if (error instanceof TypeError && error.message === 'Failed to fetch') {
      logger.error('Network error: Cannot connect to backend', error as Error, {
        url: fullUrl,
        method,
        possibleCauses: [
          'Backend server not running',
          'CORS blocked',
          'Network connectivity issue',
          'Backend URL incorrect'
        ]
      });
    } else {
      logger.apiError(method, fullUrl, error as Error, { duration });
    }

    throw error;
  }
}

export const api = {
  // Health check
  async checkHealth(): Promise<{ status: string }> {
    return apiCall<{ status: string }>('GET', '/health');
  },

  // Project operations
  async createProject(projectData: Omit<Project, 'id' | 'createdAt' | 'updatedAt'>): Promise<Project> {
    logger.userAction('create_project', { title: projectData.title });
    return apiCall<Project>('POST', '/projects', undefined, projectData);
  },

  async getProject(id: string): Promise<Project> {
    return apiCall<Project>('GET', `/projects/${id}`);
  },

  async listProjects(): Promise<Project[]> {
    return apiCall<Project[]>('GET', '/projects');
  },

  async updateProject(id: string, data: Partial<Project>): Promise<Project> {
    logger.userAction('update_project', { id, fields: Object.keys(data) });
    return apiCall<Project>('PATCH', `/projects/${id}`, undefined, data);
  },

  // Agent chat - now routes through Story Advocate
  async sendMessage(
    projectId: string,
    message: string,
    apiKey: string,
    model: string,
    autonomyLevel: number = 50
  ): Promise<ReadableStream<Uint8Array>> {
    const fullUrl = `${API_BASE_URL}/chat`;
    const startTime = performance.now();

    logger.agentInteraction('story_advocate', 'send_message', {
      project_id: projectId,
      message_length: message.length,
      model,
      autonomy_level: autonomyLevel,
    });

    logger.apiRequest('POST', fullUrl, {
      project_id: projectId,
      model,
      autonomy_level: autonomyLevel,
    });

    try {
      const response = await fetch(fullUrl, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          project_id: projectId,
          message,
          api_key: apiKey,
          model,
          autonomy_level: autonomyLevel,
        }),
      });

      const duration = performance.now() - startTime;

      if (!response.ok) {
        logger.apiResponse('POST', fullUrl, response.status, duration, 'Failed to send message');
        throw new Error('Failed to send message');
      }

      if (!response.body) {
        logger.apiResponse('POST', fullUrl, response.status, duration, 'No response body');
        throw new Error('No response body');
      }

      logger.apiResponse('POST', fullUrl, response.status, duration);
      return response.body;
    } catch (error) {
      logger.apiError('POST', fullUrl, error as Error);
      throw error;
    }
  },

  // Conversation history
  async getMessages(projectId: string): Promise<Message[]> {
    return apiCall<Message[]>('GET', `/chat/${projectId}/messages`);
  },

  // File operations
  async listFiles(projectPath: string): Promise<any> {
    logger.fileOperation('list', projectPath, true);
    return apiCall<any>('POST', '/files/list', undefined, { path: projectPath });
  },

  async readFile(filePath: string): Promise<string> {
    try {
      const data = await apiCall<{ content: string }>('POST', '/files/read', undefined, { path: filePath });
      logger.fileOperation('read', filePath, true);
      return data.content;
    } catch (error) {
      logger.fileOperation('read', filePath, false, (error as Error).message);
      throw error;
    }
  },

  async writeFile(filePath: string, content: string): Promise<void> {
    try {
      await apiCall<void>('POST', '/files/write', undefined, { path: filePath, content });
      logger.fileOperation('write', filePath, true);
    } catch (error) {
      logger.fileOperation('write', filePath, false, (error as Error).message);
      throw error;
    }
  },

  // Git operations
  async getCommitHistory(projectPath: string, maxCount: number = 20): Promise<any[]> {
    logger.debug('Getting commit history', { projectPath, maxCount });
    return apiCall<any[]>('POST', '/git/log', undefined, { repo_path: projectPath, max_count: maxCount });
  },

  async restoreFileVersion(projectPath: string, filePath: string, commitId: string): Promise<void> {
    logger.userAction('restore_file_version', { filePath, commitId });
    await apiCall<void>('POST', '/git/restore', undefined, {
      repo_path: projectPath,
      file_path: filePath,
      commit_id: commitId,
    });
  },
};
