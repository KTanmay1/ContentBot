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


 # Completed Step 5: Added logger configuration and Monitoring helper with
 # correlation-id-aware logging and placeholder metric support.