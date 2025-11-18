/**
 * Centralized configuration for API endpoints
 * This file manages the connection URLs for both development and production builds
 */

// Backend server port
const BACKEND_PORT = 8000;

// Determine the API base URL based on environment
// In both development and production Tauri builds, we connect to localhost
// because the backend runs as a sidecar process on the same machine
const API_HOST = '127.0.0.1';

/**
 * Base URL for HTTP API calls
 */
export const API_BASE_URL = `http://${API_HOST}:${BACKEND_PORT}`;

/**
 * Base URL for WebSocket connections
 */
export const WS_BASE_URL = `ws://${API_HOST}:${BACKEND_PORT}`;

/**
 * Get the full API URL for a given endpoint
 * @param endpoint - The API endpoint path (e.g., '/health', '/projects')
 * @returns The full URL
 */
export function getApiUrl(endpoint: string): string {
  return `${API_BASE_URL}${endpoint}`;
}

/**
 * Get the WebSocket URL for a given path
 * @param path - The WebSocket path (e.g., '/ws/project-id')
 * @returns The full WebSocket URL
 */
export function getWsUrl(path: string): string {
  return `${WS_BASE_URL}${path}`;
}

/**
 * Configuration object for easy access to all config values
 */
export const config = {
  api: {
    baseUrl: API_BASE_URL,
    wsBaseUrl: WS_BASE_URL,
    port: BACKEND_PORT,
    host: API_HOST,
  },
};

export default config;
