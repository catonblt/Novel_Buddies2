"""
Structured logging system for NovelWriter application.
Provides comprehensive logging with rotating file handlers and domain-specific methods.
"""

import os
import sys
import logging
import traceback
from pathlib import Path
from logging.handlers import RotatingFileHandler
from typing import Optional, Dict, Any
from datetime import datetime
import platform


class StructuredLogger:
    """
    Structured logger with rotating file handlers and domain-specific logging methods.
    """

    def __init__(self, name: str = "NovelWriter"):
        self.name = name
        self.logger = logging.getLogger(name)
        self.logger.setLevel(logging.DEBUG)

        # Prevent duplicate handlers
        if self.logger.handlers:
            return

        # Create log directory
        log_dir = self._get_log_directory()
        log_dir.mkdir(parents=True, exist_ok=True)

        # Create formatters
        detailed_formatter = logging.Formatter(
            '%(asctime)s | %(name)s | %(levelname)-8s | %(filename)s:%(lineno)d | %(funcName)s | %(message)s',
            datefmt='%Y-%m-%d %H:%M:%S'
        )

        error_formatter = logging.Formatter(
            '%(asctime)s | %(name)s | %(levelname)-8s | %(filename)s:%(lineno)d | %(funcName)s | %(message)s\n%(exc_info)s',
            datefmt='%Y-%m-%d %H:%M:%S'
        )

        # Application log (DEBUG level, 10MB, 5 backups)
        app_handler = RotatingFileHandler(
            log_dir / "application.log",
            maxBytes=10 * 1024 * 1024,  # 10MB
            backupCount=5,
            encoding='utf-8'
        )
        app_handler.setLevel(logging.DEBUG)
        app_handler.setFormatter(detailed_formatter)
        self.logger.addHandler(app_handler)

        # Error log (ERROR level only, 5MB, 3 backups)
        error_handler = RotatingFileHandler(
            log_dir / "errors.log",
            maxBytes=5 * 1024 * 1024,  # 5MB
            backupCount=3,
            encoding='utf-8'
        )
        error_handler.setLevel(logging.ERROR)
        error_handler.setFormatter(error_formatter)
        self.logger.addHandler(error_handler)

        # API log (DEBUG level, 10MB, 3 backups)
        api_handler = RotatingFileHandler(
            log_dir / "api.log",
            maxBytes=10 * 1024 * 1024,  # 10MB
            backupCount=3,
            encoding='utf-8'
        )
        api_handler.setLevel(logging.DEBUG)
        api_handler.setFormatter(detailed_formatter)
        self.logger.addHandler(api_handler)

        # Console handler for development
        console_handler = logging.StreamHandler(sys.stdout)
        console_handler.setLevel(logging.INFO)
        console_handler.setFormatter(detailed_formatter)
        self.logger.addHandler(console_handler)

        # Log initialization
        self.logger.info(f"Logger initialized. Log directory: {log_dir}")
        self.logger.info(f"Platform: {platform.system()} {platform.release()}")

    def _get_log_directory(self) -> Path:
        """
        Get the platform-specific log directory.

        Returns:
            Path to log directory
        """
        system = platform.system()

        if system == "Windows":
            # Windows: %APPDATA%\NovelWriter\logs\
            appdata = os.environ.get('APPDATA')
            if appdata:
                return Path(appdata) / "NovelWriter" / "logs"
            else:
                return Path.home() / "AppData" / "Roaming" / "NovelWriter" / "logs"

        elif system == "Darwin":
            # macOS: ~/Library/Logs/NovelWriter/
            return Path.home() / "Library" / "Logs" / "NovelWriter"

        else:
            # Linux: ~/.local/share/NovelWriter/logs/
            return Path.home() / ".local" / "share" / "NovelWriter" / "logs"

    def debug(self, message: str, **kwargs):
        """Log debug message."""
        self.logger.debug(self._format_message(message, **kwargs))

    def info(self, message: str, **kwargs):
        """Log info message."""
        self.logger.info(self._format_message(message, **kwargs))

    def warning(self, message: str, **kwargs):
        """Log warning message."""
        self.logger.warning(self._format_message(message, **kwargs))

    def error(self, message: str, **kwargs):
        """Log error message."""
        self.logger.error(self._format_message(message, **kwargs))

    def critical(self, message: str, **kwargs):
        """Log critical message."""
        self.logger.critical(self._format_message(message, **kwargs))

    def _format_message(self, message: str, **kwargs) -> str:
        """
        Format log message with additional context.

        Args:
            message: Base log message
            **kwargs: Additional context to include

        Returns:
            Formatted message string
        """
        if not kwargs:
            return message

        context_parts = [f"{k}={v}" for k, v in kwargs.items()]
        return f"{message} | {' | '.join(context_parts)}"

    def log_request(
        self,
        method: str,
        path: str,
        client_host: Optional[str] = None,
        query_params: Optional[Dict[str, Any]] = None,
        body: Optional[Dict[str, Any]] = None
    ):
        """
        Log incoming API request.

        Args:
            method: HTTP method (GET, POST, etc.)
            path: Request path
            client_host: Client IP address
            query_params: Query parameters
            body: Request body (sensitive data will be masked)
        """
        context = {
            "method": method,
            "path": path,
            "client_host": client_host or "unknown",
        }

        if query_params:
            context["query_params"] = self._sanitize_data(query_params)

        if body:
            context["body_size"] = len(str(body))
            # Don't log full body to avoid sensitive data exposure

        self.info("API Request", **context)

    def log_response(
        self,
        method: str,
        path: str,
        status_code: int,
        duration_ms: float,
        error: Optional[str] = None
    ):
        """
        Log API response.

        Args:
            method: HTTP method
            path: Request path
            status_code: HTTP status code
            duration_ms: Request duration in milliseconds
            error: Error message if request failed
        """
        context = {
            "method": method,
            "path": path,
            "status_code": status_code,
            "duration_ms": f"{duration_ms:.2f}",
        }

        if error:
            context["error"] = error
            self.error("API Response", **context)
        else:
            self.info("API Response", **context)

    def log_exception(
        self,
        error: Exception,
        context: Optional[Dict[str, Any]] = None,
        operation: Optional[str] = None
    ):
        """
        Log exception with full stack trace.

        Args:
            error: Exception object
            context: Additional context about where the error occurred
            operation: Description of the operation that failed
        """
        error_details = {
            "error_type": type(error).__name__,
            "error_message": str(error),
            "stack_trace": traceback.format_exc(),
        }

        if operation:
            error_details["operation"] = operation

        if context:
            error_details.update(self._sanitize_data(context))

        self.error("Exception occurred", **error_details)

    def log_file_operation(
        self,
        operation: str,
        file_path: str,
        success: bool,
        details: Optional[Dict[str, Any]] = None,
        error: Optional[str] = None
    ):
        """
        Log file operation.

        Args:
            operation: Operation type (read, write, delete, etc.)
            file_path: Path to file
            success: Whether operation succeeded
            details: Additional operation details
            error: Error message if operation failed
        """
        context = {
            "operation": operation,
            "file_path": file_path,
            "success": success,
        }

        if details:
            context.update(details)

        if error:
            context["error"] = error
            self.error("File operation failed", **context)
        else:
            self.info("File operation", **context)

    def log_git_operation(
        self,
        operation: str,
        repo_path: str,
        success: bool,
        details: Optional[Dict[str, Any]] = None,
        error: Optional[str] = None
    ):
        """
        Log git operation.

        Args:
            operation: Git operation (init, commit, push, etc.)
            repo_path: Path to git repository
            success: Whether operation succeeded
            details: Additional operation details
            error: Error message if operation failed
        """
        context = {
            "operation": operation,
            "repo_path": repo_path,
            "success": success,
        }

        if details:
            context.update(details)

        if error:
            context["error"] = error
            self.warning("Git operation failed", **context)
        else:
            self.info("Git operation", **context)

    def log_agent_interaction(
        self,
        agent_type: str,
        operation: str,
        prompt_length: int,
        response_length: Optional[int] = None,
        duration_ms: Optional[float] = None,
        error: Optional[str] = None
    ):
        """
        Log AI agent interaction.

        Args:
            agent_type: Type of agent (story, character, etc.)
            operation: Operation performed
            prompt_length: Length of prompt sent to agent
            response_length: Length of agent response
            duration_ms: Duration of agent interaction
            error: Error message if interaction failed
        """
        context = {
            "agent_type": agent_type,
            "operation": operation,
            "prompt_length": prompt_length,
        }

        if response_length is not None:
            context["response_length"] = response_length

        if duration_ms is not None:
            context["duration_ms"] = f"{duration_ms:.2f}"

        if error:
            context["error"] = error
            self.error("Agent interaction failed", **context)
        else:
            self.info("Agent interaction", **context)

    def log_database_operation(
        self,
        operation: str,
        table: str,
        success: bool,
        affected_rows: Optional[int] = None,
        error: Optional[str] = None
    ):
        """
        Log database operation.

        Args:
            operation: Database operation (select, insert, update, delete)
            table: Table name
            success: Whether operation succeeded
            affected_rows: Number of rows affected
            error: Error message if operation failed
        """
        context = {
            "operation": operation,
            "table": table,
            "success": success,
        }

        if affected_rows is not None:
            context["affected_rows"] = affected_rows

        if error:
            context["error"] = error
            self.error("Database operation failed", **context)
        else:
            self.debug("Database operation", **context)

    def _sanitize_data(self, data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Sanitize sensitive data before logging.

        Args:
            data: Data dictionary to sanitize

        Returns:
            Sanitized data dictionary
        """
        sensitive_keys = {
            'password', 'token', 'api_key', 'secret', 'auth',
            'authorization', 'credential', 'private_key'
        }

        sanitized = {}
        for key, value in data.items():
            if any(sensitive in key.lower() for sensitive in sensitive_keys):
                sanitized[key] = "***REDACTED***"
            elif isinstance(value, dict):
                sanitized[key] = self._sanitize_data(value)
            else:
                sanitized[key] = value

        return sanitized


# Global logger instance
logger = StructuredLogger()
