"""Shared exception types and helpers for agents and API."""
# Step 4: Implement central error types and helpers for consistent handling and
# machine-readable error codes across agents and API layers.

from __future__ import annotations

import asyncio
import logging
import traceback
from enum import Enum
from typing import Any, Dict, Optional, Callable, List
from datetime import datetime


class ErrorCode(str, Enum):
    VALIDATION_ERROR = "validation_error"
    AGENT_EXECUTION_ERROR = "agent_execution_error"
    EXTERNAL_SERVICE_ERROR = "external_service_error"
    WORKFLOW_ERROR = "workflow_error"
    DATABASE_ERROR = "database_error"
    AUTHENTICATION_ERROR = "authentication_error"
    AUTHORIZATION_ERROR = "authorization_error"
    RATE_LIMIT_ERROR = "rate_limit_error"
    TIMEOUT_ERROR = "timeout_error"
    CONFIGURATION_ERROR = "configuration_error"
    RESOURCE_NOT_FOUND = "resource_not_found"
    RESOURCE_CONFLICT = "resource_conflict"
    UNKNOWN_ERROR = "unknown_error"


class AgentException(Exception):
    def __init__(self, message: str, *, error_code: ErrorCode = ErrorCode.AGENT_EXECUTION_ERROR, details: Optional[Dict[str, Any]] = None):
        super().__init__(message)
        self.error_code = error_code
        self.details = details or {}


class ValidationException(AgentException):
    def __init__(self, message: str, *, details: Optional[Dict[str, Any]] = None):
        super().__init__(message, error_code=ErrorCode.VALIDATION_ERROR, details=details)


class ExternalServiceException(AgentException):
    def __init__(self, message: str, *, details: Optional[Dict[str, Any]] = None):
        super().__init__(message, error_code=ErrorCode.EXTERNAL_SERVICE_ERROR, details=details)


class WorkflowException(AgentException):
    def __init__(self, message: str, *, details: Optional[Dict[str, Any]] = None):
        super().__init__(message, error_code=ErrorCode.WORKFLOW_ERROR, details=details)


class DatabaseException(AgentException):
    def __init__(self, message: str, *, details: Optional[Dict[str, Any]] = None):
        super().__init__(message, error_code=ErrorCode.DATABASE_ERROR, details=details)


class AuthenticationException(AgentException):
    def __init__(self, message: str, *, details: Optional[Dict[str, Any]] = None):
        super().__init__(message, error_code=ErrorCode.AUTHENTICATION_ERROR, details=details)


class AuthorizationException(AgentException):
    def __init__(self, message: str, *, details: Optional[Dict[str, Any]] = None):
        super().__init__(message, error_code=ErrorCode.AUTHORIZATION_ERROR, details=details)


class RateLimitException(AgentException):
    def __init__(self, message: str, *, details: Optional[Dict[str, Any]] = None):
        super().__init__(message, error_code=ErrorCode.RATE_LIMIT_ERROR, details=details)


class TimeoutException(AgentException):
    def __init__(self, message: str, *, details: Optional[Dict[str, Any]] = None):
        super().__init__(message, error_code=ErrorCode.TIMEOUT_ERROR, details=details)


class ConfigurationException(AgentException):
    def __init__(self, message: str, *, details: Optional[Dict[str, Any]] = None):
        super().__init__(message, error_code=ErrorCode.CONFIGURATION_ERROR, details=details)


class ResourceNotFoundException(AgentException):
    def __init__(self, message: str, *, details: Optional[Dict[str, Any]] = None):
        super().__init__(message, error_code=ErrorCode.RESOURCE_NOT_FOUND, details=details)


class ResourceConflictException(AgentException):
    def __init__(self, message: str, *, details: Optional[Dict[str, Any]] = None):
        super().__init__(message, error_code=ErrorCode.RESOURCE_CONFLICT, details=details)


class ErrorRecoveryStrategy:
    """Base class for error recovery strategies."""
    
    def __init__(self, max_retries: int = 3, backoff_factor: float = 1.0):
        self.max_retries = max_retries
        self.backoff_factor = backoff_factor
    
    async def execute_with_retry(self, func: Callable, *args, **kwargs) -> Any:
        """Execute a function with retry logic."""
        last_exception = None
        
        for attempt in range(self.max_retries + 1):
            try:
                if asyncio.iscoroutinefunction(func):
                    return await func(*args, **kwargs)
                else:
                    return func(*args, **kwargs)
            except Exception as e:
                last_exception = e
                
                if attempt < self.max_retries:
                    if self.should_retry(e):
                        wait_time = self.calculate_backoff(attempt)
                        await asyncio.sleep(wait_time)
                        continue
                    else:
                        break
                else:
                    break
        
        # If we get here, all retries failed
        raise last_exception
    
    def should_retry(self, exception: Exception) -> bool:
        """Determine if an exception should trigger a retry."""
        # Retry on external service errors and timeouts
        if isinstance(exception, (ExternalServiceException, TimeoutException)):
            return True
        
        # Don't retry on validation or authentication errors
        if isinstance(exception, (ValidationException, AuthenticationException, AuthorizationException)):
            return False
        
        # Default: retry on unknown errors
        return True
    
    def calculate_backoff(self, attempt: int) -> float:
        """Calculate backoff time for retry attempt."""
        return self.backoff_factor * (2 ** attempt)


class ErrorHandler:
    """Central error handler for the application."""
    
    def __init__(self):
        self.logger = logging.getLogger(__name__)
        self.error_callbacks: List[Callable] = []
        self.recovery_strategy = ErrorRecoveryStrategy()
    
    def add_error_callback(self, callback: Callable):
        """Add a callback to be called when errors occur."""
        self.error_callbacks.append(callback)
    
    async def handle_error(self, error: Exception, context: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
        """Handle an error with logging and callbacks."""
        error_data = self.create_error_data(error, context)
        
        # Log the error
        self.logger.error(
            f"Error occurred: {error_data['error_code']} - {error_data['message']}",
            extra={
                "error_data": error_data,
                "context": context or {},
                "traceback": traceback.format_exc()
            }
        )
        
        # Call error callbacks
        for callback in self.error_callbacks:
            try:
                if asyncio.iscoroutinefunction(callback):
                    await callback(error_data, context)
                else:
                    callback(error_data, context)
            except Exception as callback_error:
                self.logger.error(f"Error in error callback: {callback_error}")
        
        return error_data
    
    def create_error_data(self, error: Exception, context: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
        """Create standardized error data."""
        error_data = exception_to_payload(error)
        error_data["timestamp"] = datetime.utcnow().isoformat()
        error_data["context"] = context or {}
        
        # Add stack trace for debugging (only in development)
        if context and context.get("include_traceback", False):
            error_data["traceback"] = traceback.format_exc()
        
        return error_data
    
    async def execute_with_error_handling(self, func: Callable, *args, **kwargs) -> Any:
        """Execute a function with comprehensive error handling."""
        try:
            return await self.recovery_strategy.execute_with_retry(func, *args, **kwargs)
        except Exception as e:
            await self.handle_error(e, {"function": func.__name__, "args": str(args)[:100]})
            raise


def exception_to_payload(exc: Exception) -> Dict[str, Any]:
    """Serialize an exception to a safe payload for logs or API responses."""
    if isinstance(exc, AgentException):
        return {
            "error_code": exc.error_code,
            "message": str(exc),
            "details": getattr(exc, "details", {})
        }
    return {
        "error_code": ErrorCode.UNKNOWN_ERROR,
        "message": str(exc),
        "details": {"exception_type": type(exc).__name__}
    }


def create_error_response(error: Exception, include_details: bool = False) -> Dict[str, Any]:
    """Create a standardized error response for API endpoints."""
    error_data = exception_to_payload(error)
    
    response = {
        "success": False,
        "error": {
            "code": error_data["error_code"],
            "message": error_data["message"]
        }
    }
    
    if include_details and error_data.get("details"):
        response["error"]["details"] = error_data["details"]
    
    return response


# Global error handler instance
error_handler = ErrorHandler()

# Completed Step 4: Enhanced error handling with comprehensive exception types,
# retry strategies, error recovery mechanisms, and centralized error handling.