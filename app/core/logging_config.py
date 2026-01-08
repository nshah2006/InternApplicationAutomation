"""
Logging configuration for structured logging.

Provides JSON-formatted structured logs with sensitive data sanitization.
"""

import logging
import json
import sys
from datetime import datetime
from typing import Any, Dict, Optional
from pythonjsonlogger import jsonlogger
import os


class SensitiveDataFilter(logging.Filter):
    """
    Filter to sanitize sensitive data from log records.
    
    Removes or masks sensitive fields like passwords, tokens, emails, etc.
    """
    
    # Fields that should be completely removed
    SENSITIVE_FIELDS = {
        'password', 'passwd', 'pwd', 'secret', 'token', 'access_token',
        'refresh_token', 'api_key', 'apikey', 'auth_token', 'authorization',
        'credit_card', 'ssn', 'social_security', 'phone_number', 'phone'
    }
    
    # Fields that should be masked (show partial value)
    MASK_FIELDS = {
        'email', 'username', 'user_id'
    }
    
    def filter(self, record: logging.LogRecord) -> bool:
        """Filter and sanitize log record."""
        # Sanitize extra fields
        if hasattr(record, '__dict__'):
            for key in list(record.__dict__.keys()):
                key_lower = key.lower()
                
                # Remove sensitive fields
                if any(sensitive in key_lower for sensitive in self.SENSITIVE_FIELDS):
                    setattr(record, key, '[REDACTED]')
                
                # Mask partial fields
                elif any(mask in key_lower for mask in self.MASK_FIELDS):
                    value = getattr(record, key, None)
                    if isinstance(value, str) and len(value) > 4:
                        setattr(record, key, f"{value[:2]}***{value[-2:]}")
        
        # Sanitize message
        if hasattr(record, 'msg') and isinstance(record.msg, str):
            record.msg = self._sanitize_string(record.msg)
        
        # Sanitize args
        if hasattr(record, 'args') and record.args:
            sanitized_args = []
            for arg in record.args:
                if isinstance(arg, str):
                    sanitized_args.append(self._sanitize_string(arg))
                elif isinstance(arg, dict):
                    sanitized_args.append(self._sanitize_dict(arg))
                else:
                    sanitized_args.append(arg)
            record.args = tuple(sanitized_args)
        
        return True
    
    def _sanitize_string(self, text: str) -> str:
        """Sanitize sensitive data in string."""
        if not isinstance(text, str):
            return text
        
        # Remove common patterns
        import re
        
        # Remove tokens (long alphanumeric strings)
        text = re.sub(r'\b[A-Za-z0-9]{32,}\b', '[TOKEN_REDACTED]', text)
        
        # Remove email addresses (keep domain)
        text = re.sub(r'\b[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Z|a-z]{2,}\b', '[EMAIL_REDACTED]', text)
        
        # Remove phone numbers
        text = re.sub(r'\b\d{3}[-.]?\d{3}[-.]?\d{4}\b', '[PHONE_REDACTED]', text)
        
        return text
    
    def _sanitize_dict(self, data: Dict[str, Any]) -> Dict[str, Any]:
        """Sanitize sensitive data in dictionary."""
        sanitized = {}
        for key, value in data.items():
            key_lower = key.lower()
            
            # Remove sensitive fields
            if any(sensitive in key_lower for sensitive in self.SENSITIVE_FIELDS):
                sanitized[key] = '[REDACTED]'
            # Mask partial fields
            elif any(mask in key_lower for mask in self.MASK_FIELDS):
                if isinstance(value, str) and len(value) > 4:
                    sanitized[key] = f"{value[:2]}***{value[-2:]}"
                else:
                    sanitized[key] = value
            # Recursively sanitize nested dicts
            elif isinstance(value, dict):
                sanitized[key] = self._sanitize_dict(value)
            elif isinstance(value, str):
                sanitized[key] = self._sanitize_string(value)
            else:
                sanitized[key] = value
        
        return sanitized


class StructuredJsonFormatter(jsonlogger.JsonFormatter):
    """
    Custom JSON formatter for structured logging.
    
    Formats log records as JSON with additional metadata.
    """
    
    def add_fields(self, log_record: Dict[str, Any], record: logging.LogRecord, message_dict: Dict[str, Any]) -> None:
        """Add custom fields to log record."""
        super().add_fields(log_record, record, message_dict)
        
        # Add timestamp
        log_record['timestamp'] = datetime.utcnow().isoformat()
        
        # Add log level
        log_record['level'] = record.levelname
        
        # Add logger name
        log_record['logger'] = record.name
        
        # Add module and function
        log_record['module'] = record.module
        log_record['function'] = record.funcName
        log_record['line'] = record.lineno
        
        # Add process/thread info
        log_record['process_id'] = record.process
        log_record['thread_id'] = record.thread
        
        # Format message
        if message_dict:
            log_record['message'] = message_dict
        else:
            log_record['message'] = record.getMessage()


def setup_logging(
    log_level: str = None,
    log_file: Optional[str] = None,
    enable_console: bool = True
) -> None:
    """
    Set up structured logging configuration.
    
    Args:
        log_level: Logging level (DEBUG, INFO, WARNING, ERROR, CRITICAL)
        log_file: Optional file path for file logging
        enable_console: Whether to enable console logging
    """
    # Get log level from environment or use default
    if log_level is None:
        log_level = os.getenv('LOG_LEVEL', 'INFO').upper()
    
    level = getattr(logging, log_level, logging.INFO)
    
    # Create root logger
    root_logger = logging.getLogger()
    root_logger.setLevel(level)
    
    # Remove existing handlers
    root_logger.handlers.clear()
    
    # Create formatter
    formatter = StructuredJsonFormatter(
        '%(timestamp)s %(level)s %(name)s %(message)s'
    )
    
    # Add sensitive data filter
    sensitive_filter = SensitiveDataFilter()
    
    # Console handler
    if enable_console:
        console_handler = logging.StreamHandler(sys.stdout)
        console_handler.setLevel(level)
        console_handler.setFormatter(formatter)
        console_handler.addFilter(sensitive_filter)
        root_logger.addHandler(console_handler)
    
    # File handler (if specified)
    if log_file:
        file_handler = logging.FileHandler(log_file)
        file_handler.setLevel(level)
        file_handler.setFormatter(formatter)
        file_handler.addFilter(sensitive_filter)
        root_logger.addHandler(file_handler)
    
    # Set levels for third-party loggers
    logging.getLogger('uvicorn').setLevel(logging.WARNING)
    logging.getLogger('uvicorn.access').setLevel(logging.WARNING)
    logging.getLogger('sqlalchemy.engine').setLevel(logging.WARNING)
    logging.getLogger('playwright').setLevel(logging.WARNING)


def get_logger(name: str) -> logging.Logger:
    """
    Get a logger instance with the given name.
    
    Args:
        name: Logger name (typically __name__)
        
    Returns:
        Logger instance
    """
    return logging.getLogger(name)

