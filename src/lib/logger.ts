/**
 * Frontend logging system for NovelWriter application.
 * Provides structured logging with console output and error tracking.
 */

export enum LogLevel {
  DEBUG = 0,
  INFO = 1,
  WARN = 2,
  ERROR = 3,
}

interface LogEntry {
  timestamp: string;
  level: string;
  message: string;
  context?: Record<string, any>;
}

class Logger {
  private maxStoredErrors = 50;
  private logLevel: LogLevel = LogLevel.INFO;

  constructor() {
    // Set log level based on environment
    if (import.meta.env.DEV) {
      this.logLevel = LogLevel.DEBUG;
    }

    this.info('Logger initialized');
  }

  /**
   * Get stored errors from sessionStorage
   */
  getStoredErrors(): LogEntry[] {
    try {
      const stored = sessionStorage.getItem('novelwriter_errors');
      return stored ? JSON.parse(stored) : [];
    } catch {
      return [];
    }
  }

  /**
   * Store error in sessionStorage
   */
  private storeError(entry: LogEntry): void {
    try {
      const errors = this.getStoredErrors();
      errors.push(entry);

      // Keep only last N errors
      const trimmed = errors.slice(-this.maxStoredErrors);

      sessionStorage.setItem('novelwriter_errors', JSON.stringify(trimmed));
    } catch (e) {
      console.error('Failed to store error:', e);
    }
  }

  /**
   * Format timestamp for logs
   */
  private getTimestamp(): string {
    return new Date().toISOString();
  }

  /**
   * Format log message with context
   */
  private formatMessage(message: string, context?: Record<string, any>): string {
    if (!context || Object.keys(context).length === 0) {
      return message;
    }

    const contextStr = Object.entries(context)
      .map(([key, value]) => `${key}=${JSON.stringify(value)}`)
      .join(' | ');

    return `${message} | ${contextStr}`;
  }

  /**
   * Log debug message
   */
  debug(message: string, context?: Record<string, any>): void {
    if (this.logLevel > LogLevel.DEBUG) return;

    const timestamp = this.getTimestamp();
    const formatted = this.formatMessage(message, context);

    console.log(`[${timestamp}] [DEBUG] ${formatted}`);
  }

  /**
   * Log info message
   */
  info(message: string, context?: Record<string, any>): void {
    if (this.logLevel > LogLevel.INFO) return;

    const timestamp = this.getTimestamp();
    const formatted = this.formatMessage(message, context);

    console.log(`[${timestamp}] [INFO] ${formatted}`);
  }

  /**
   * Log warning message
   */
  warn(message: string, context?: Record<string, any>): void {
    if (this.logLevel > LogLevel.WARN) return;

    const timestamp = this.getTimestamp();
    const formatted = this.formatMessage(message, context);

    console.warn(`[${timestamp}] [WARN] ${formatted}`);
  }

  /**
   * Log error message
   */
  error(message: string, error?: Error, context?: Record<string, any>): void {
    const timestamp = this.getTimestamp();
    const errorContext = {
      ...context,
      ...(error && {
        error_name: error.name,
        error_message: error.message,
        stack: error.stack,
      }),
    };

    const formatted = this.formatMessage(message, errorContext);

    console.error(`[${timestamp}] [ERROR] ${formatted}`);

    // Store error
    const entry: LogEntry = {
      timestamp,
      level: 'ERROR',
      message,
      context: errorContext,
    };

    this.storeError(entry);
  }

  /**
   * Log API request
   */
  apiRequest(method: string, url: string, data?: any): void {
    const context: Record<string, any> = {
      method,
      url,
    };

    if (data) {
      context.data_size = JSON.stringify(data).length;
    }

    this.debug(`API Request: ${method} ${url}`, context);
  }

  /**
   * Log API response
   */
  apiResponse(
    method: string,
    url: string,
    status: number,
    duration: number,
    error?: string
  ): void {
    const context: Record<string, any> = {
      method,
      url,
      status,
      duration_ms: duration.toFixed(2),
    };

    if (error) {
      context.error = error;
      this.error(`API Response Failed: ${method} ${url}`, undefined, context);
    } else {
      this.info(`API Response: ${method} ${url}`, context);
    }
  }

  /**
   * Log API error
   */
  apiError(
    method: string,
    url: string,
    error: Error,
    context?: Record<string, any>
  ): void {
    this.error(
      `API Error: ${method} ${url}`,
      error,
      {
        method,
        url,
        ...context,
      }
    );
  }

  /**
   * Log user action
   */
  userAction(action: string, details?: Record<string, any>): void {
    this.info(`User Action: ${action}`, details);
  }

  /**
   * Log file operation
   */
  fileOperation(
    operation: string,
    path: string,
    success: boolean,
    error?: string
  ): void {
    const context = {
      operation,
      path,
      success,
      ...(error && { error }),
    };

    if (success) {
      this.debug(`File Operation: ${operation} on ${path}`, context);
    } else {
      this.error(`File Operation Failed: ${operation} on ${path}`, undefined, context);
    }
  }

  /**
   * Log agent interaction
   */
  agentInteraction(
    agentType: string,
    operation: string,
    details?: Record<string, any>
  ): void {
    this.info(`Agent Interaction: ${agentType} - ${operation}`, {
      agent_type: agentType,
      operation,
      ...details,
    });
  }

  /**
   * Clear stored errors
   */
  clearErrors(): void {
    try {
      sessionStorage.removeItem('novelwriter_errors');
      this.info('Stored errors cleared');
    } catch (e) {
      console.error('Failed to clear errors:', e);
    }
  }

  /**
   * Export logs as JSON
   */
  exportLogs(): string {
    const errors = this.getStoredErrors();
    return JSON.stringify(errors, null, 2);
  }
}

// Global logger instance
export const logger = new Logger();
