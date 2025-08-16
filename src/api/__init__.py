"""API module exports (Developer A)."""
# Step 16: Add API module exports for clean imports.
# Why: Enables clean imports like 'from src.api import create_app' and
# completes the API module structure for Phase 3.

from src.api.main import app, create_app

__all__ = ["app", "create_app"]
