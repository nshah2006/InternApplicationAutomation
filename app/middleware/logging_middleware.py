"""
Logging middleware for FastAPI.

Captures request/response information and logs API calls.
"""

import time
import logging
from typing import Callable
from fastapi import Request, Response
from starlette.middleware.base import BaseHTTPMiddleware
from app.core.logging_config import get_logger

logger = get_logger(__name__)


class LoggingMiddleware(BaseHTTPMiddleware):
    """
    Middleware to log HTTP requests and responses.
    
    Logs request method, path, status code, duration, and errors.
    """
    
    async def dispatch(self, request: Request, call_next: Callable) -> Response:
        """Process request and log information."""
        start_time = time.time()
        
        # Extract request information
        method = request.method
        path = request.url.path
        client_ip = request.client.host if request.client else None
        user_agent = request.headers.get('user-agent', '')
        
        # Log request
        logger.info(
            "Request received",
            extra={
                'event_type': 'http_request',
                'method': method,
                'path': path,
                'client_ip': client_ip,
                'user_agent': user_agent,
                'query_params': dict(request.query_params) if request.query_params else None
            }
        )
        
        # Process request
        try:
            response = await call_next(request)
            
            # Calculate duration
            duration = time.time() - start_time
            
            # Extract response information
            status_code = response.status_code
            
            # Log response
            log_level = logging.ERROR if status_code >= 500 else logging.WARNING if status_code >= 400 else logging.INFO
            
            logger.log(
                log_level,
                "Request completed",
                extra={
                    'event_type': 'http_response',
                    'method': method,
                    'path': path,
                    'status_code': status_code,
                    'duration_ms': round(duration * 1000, 2),
                    'client_ip': client_ip
                }
            )
            
            return response
            
        except Exception as e:
            # Calculate duration
            duration = time.time() - start_time
            
            # Log error
            logger.error(
                "Request failed",
                extra={
                    'event_type': 'http_error',
                    'method': method,
                    'path': path,
                    'error_type': type(e).__name__,
                    'error_message': str(e),
                    'duration_ms': round(duration * 1000, 2),
                    'client_ip': client_ip
                },
                exc_info=True
            )
            
            raise

