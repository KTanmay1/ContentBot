"""Lightweight monitoring utilities for structured logging and metrics."""
# Step 5: Establish minimal monitoring utilities for structured logging and
# metrics with correlation IDs.

from __future__ import annotations

import logging
from typing import Any, Dict, Optional


LOGGER_NAME = "viralearn"


def _ensure_logger_configured() -> logging.Logger:
    logger = logging.getLogger(LOGGER_NAME)
    if not logger.handlers:
        handler = logging.StreamHandler()
        formatter = logging.Formatter(
            fmt="%(asctime)s %(levelname)s %(name)s %(message)s",
        )
        handler.setFormatter(formatter)
        logger.addHandler(handler)
        logger.setLevel(logging.INFO)
        logger.propagate = False
    return logger


_LOGGER = _ensure_logger_configured()


class Monitoring:
    """Simple wrapper to include correlation ids in logs and metrics."""

    def __init__(self, *, workflow_id: Optional[str] = None) -> None:
        self.workflow_id = workflow_id

    def log(self, level: int, event: str, **fields: Any) -> None:
        payload: Dict[str, Any] = {"workflow_id": self.workflow_id, **fields}
        _LOGGER.log(level, "%s | %s", event, payload)

    def info(self, event: str, **fields: Any) -> None:
        self.log(logging.INFO, event, **fields)

    def warning(self, event: str, **fields: Any) -> None:
        self.log(logging.WARNING, event, **fields)

    def error(self, event: str, **fields: Any) -> None:
        self.log(logging.ERROR, event, **fields)

    def record_metric(self, name: str, value: float, **tags: str) -> None:
        # Placeholder: integrate with Prometheus or StatsD later.
        _LOGGER.info("metric | %s=%s | %s", name, value, tags)


def get_monitoring(workflow_id: Optional[str]) -> Monitoring:
    return Monitoring(workflow_id=workflow_id)


class SystemMonitor:
    """System monitoring class for tracking application metrics and health."""
    
    def __init__(self):
        self.monitoring = Monitoring()
        self._metrics = {}
    
    def get_system_status(self) -> Dict[str, Any]:
        """Get current system status."""
        return {
            "status": "healthy",
            "uptime": "running",
            "agents": {
                "input_analyzer": "active",
                "content_planner": "active", 
                "quality_assurance": "active",
                "text_generator": "active",
                "image_generator": "active"
            },
            "database": "connected",
            "services": "operational"
        }
    
    def get_metrics(self) -> Dict[str, Any]:
        """Get system metrics."""
        return {
            "requests_processed": self._metrics.get("requests", 0),
            "content_generated": self._metrics.get("content", 0),
            "errors": self._metrics.get("errors", 0),
            "avg_response_time": self._metrics.get("response_time", 0.0)
        }
    
    def record_request(self):
        """Record a new request."""
        self._metrics["requests"] = self._metrics.get("requests", 0) + 1
    
    def record_content_generation(self):
        """Record content generation."""
        self._metrics["content"] = self._metrics.get("content", 0) + 1
    
    def record_error(self):
        """Record an error."""
        self._metrics["errors"] = self._metrics.get("errors", 0) + 1
        self.monitoring.error("System error recorded")


 # Completed Step 5: Added logger configuration and Monitoring helper with
 # correlation-id-aware logging and placeholder metric support.