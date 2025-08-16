"""Shared exception types and helpers for agents and API."""
# Step 4: Implement central error types and helpers for consistent handling and
# machine-readable error codes across agents and API layers.

from __future__ import annotations

from enum import Enum
from typing import Any, Dict, Optional


class ErrorCode(str, Enum):
    VALIDATION_ERROR = "validation_error"
    AGENT_EXECUTION_ERROR = "agent_execution_error"
    EXTERNAL_SERVICE_ERROR = "external_service_error"
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


def exception_to_payload(exc: Exception) -> Dict[str, Any]:
    """Serialize an exception to a safe payload for logs or API responses."""
    if isinstance(exc, AgentException):
        return {"error_code": exc.error_code, "message": str(exc), "details": getattr(exc, "details", {})}
    return {"error_code": ErrorCode.UNKNOWN_ERROR, "message": str(exc), "details": {}}

# Completed Step 4: Added AgentException hierarchy, ErrorCode enum, and
# exception_to_payload() serializer for logs/API responses.


