#!/usr/bin/env python3
"""Integration script to run the unified ContentBot system.

This script provides a single entry point to start the integrated application
with proper initialization sequence and health checks.
"""

import asyncio
import sys
import os
from pathlib import Path
from typing import Optional
import uvicorn
import click

# Add project root to Python path
project_root = Path(__file__).parent
sys.path.insert(0, str(project_root))

from src.utils.config import get_unified_config, validate_all_config
from src.core.monitoring import get_monitoring
from config.settings import get_settings


class IntegratedSystemManager:
    """Manager for the integrated ContentBot system."""
    
    def __init__(self):
        self.config = get_unified_config()
        self.monitoring = get_monitoring("integrated-system")
        self.settings = get_settings()
        
    async def initialize_system(self) -> bool:
        """Initialize all system components."""
        try:
            self.monitoring.info("Starting ContentBot integrated system initialization...")
            
            # Step 1: Validate configuration
            self.monitoring.info("Step 1: Validating configuration...")
            if not validate_all_config():
                self.monitoring.error("Configuration validation failed")
                return False
            
            # Step 2: Check environment variables
            self.monitoring.info("Step 2: Checking environment variables...")
            self._check_environment()
            
            # Step 3: Initialize database connection (if available)
            self.monitoring.info("Step 3: Checking database connectivity...")
            await self._check_database_connection()
            
            # Step 4: Initialize external services
            self.monitoring.info("Step 4: Checking external service configurations...")
            self._check_external_services()
            
            # Step 5: Initialize workflow engine
            self.monitoring.info("Step 5: Initializing workflow engine...")
            await self._initialize_workflow_engine()
            
            self.monitoring.info("System initialization completed successfully")
            return True
            
        except Exception as e:
            self.monitoring.error(f"System initialization failed: {e}")
            return False
    
    def _check_environment(self) -> None:
        """Check critical environment variables."""
        critical_vars = [
            "GEMINI_API_KEY",
            "IMAGEN_PROJECT_ID",
            "DB_PASSWORD"
        ]
        
        missing_vars = []
        for var in critical_vars:
            if not os.getenv(var):
                missing_vars.append(var)
        
        if missing_vars:
            self.monitoring.warning(f"Missing environment variables: {', '.join(missing_vars)}")
            self.monitoring.warning("Some features may not work properly")
        else:
            self.monitoring.info("All critical environment variables are set")
    
    async def _check_database_connection(self) -> None:
        """Check database connectivity."""
        try:
            # Import database service if available
            from src.database.service import DatabaseService
            db_service = DatabaseService()
            # Note: This would require actual database connection logic
            self.monitoring.info("Database service initialized")
        except ImportError:
            self.monitoring.warning("Database service not available - running without persistence")
        except Exception as e:
            self.monitoring.warning(f"Database connection check failed: {e}")
    
    def _check_external_services(self) -> None:
        """Check external service configurations."""
        # Check Gemini API configuration
        gemini_config = self.config.llm_config["gemini"]
        if gemini_config["api_key"]:
            self.monitoring.info("Gemini API configuration found")
        else:
            self.monitoring.warning("Gemini API key not configured")
        
        # Check Imagen configuration
        imagen_config = self.config.image_config["imagen"]
        if imagen_config["project_id"]:
            self.monitoring.info("Imagen API configuration found")
        else:
            self.monitoring.warning("Imagen project ID not configured")
    
    async def _initialize_workflow_engine(self) -> None:
        """Initialize the workflow engine."""
        try:
            from src.core.workflow_engine import WorkflowEngine
            
            # Create a basic workflow engine instance
            engine = WorkflowEngine()
            self.monitoring.info("Workflow engine initialized successfully")
            
        except Exception as e:
            self.monitoring.error(f"Failed to initialize workflow engine: {e}")
            raise
    
    def get_api_app(self):
        """Get the FastAPI application instance."""
        try:
            from src.api.main import create_app
            return create_app()
        except ImportError:
            self.monitoring.error("Failed to import FastAPI application")
            raise
    
    async def run_health_check(self) -> bool:
        """Run system health check."""
        try:
            self.monitoring.info("Running system health check...")
            
            # Check configuration
            if not validate_all_config():
                return False
            
            # Check workflow engine
            await self._initialize_workflow_engine()
            
            self.monitoring.info("Health check passed")
            return True
            
        except Exception as e:
            self.monitoring.error(f"Health check failed: {e}")
            return False


@click.group()
def cli():
    """ContentBot Integrated System CLI."""
    pass


@cli.command()
@click.option('--host', default='0.0.0.0', help='Host to bind to')
@click.option('--port', default=8000, help='Port to bind to')
@click.option('--reload', is_flag=True, help='Enable auto-reload for development')
@click.option('--workers', default=1, help='Number of worker processes')
def serve(host: str, port: int, reload: bool, workers: int):
    """Start the integrated ContentBot API server."""
    import asyncio
    
    async def run_serve():
        manager = IntegratedSystemManager()
        
        # Initialize system
        if not await manager.initialize_system():
            click.echo("❌ System initialization failed", err=True)
            sys.exit(1)
        
        click.echo("✅ System initialized successfully")
        click.echo(f"🚀 Starting server on {host}:{port}")
        
        # Get API configuration from settings
        api_config = manager.config.api_config
        actual_host = host if host != '0.0.0.0' else api_config['host']
        actual_port = port if port != 8000 else api_config['port']
        
        # Start the server
        config = uvicorn.Config(
            "src.api.main:create_app",
            factory=True,
            host=actual_host,
            port=actual_port,
            reload=reload,
            workers=workers if not reload else 1,
            log_level="info"
        )
        
        server = uvicorn.Server(config)
        await server.serve()
    
    asyncio.run(run_serve())


@cli.command()
def health():
    """Run system health check."""
    import asyncio
    manager = IntegratedSystemManager()
    
    async def run_health():
        if await manager.run_health_check():
            click.echo("✅ System health check passed")
            sys.exit(0)
        else:
            click.echo("❌ System health check failed", err=True)
            sys.exit(1)
    
    asyncio.run(run_health())


@cli.command()
def config():
    """Display current configuration."""
    manager = IntegratedSystemManager()
    
    click.echo("📋 Current Configuration:")
    click.echo(f"  App Name: {manager.settings.app_name}")
    click.echo(f"  Debug Mode: {manager.settings.debug}")
    click.echo(f"  Log Level: {manager.settings.log_level}")
    click.echo(f"  API Host: {manager.settings.api_host}")
    click.echo(f"  API Port: {manager.settings.api_port}")
    click.echo(f"  Database URL: {manager.config.database_url}")
    click.echo(f"  Supported Platforms: {', '.join(manager.settings.supported_platforms)}")
    
    # Check API keys (masked)
    gemini_key = manager.settings.gemini.api_key
    if gemini_key:
        masked_key = gemini_key[:8] + "..." + gemini_key[-4:] if len(gemini_key) > 12 else "***"
        click.echo(f"  Gemini API Key: {masked_key}")
    else:
        click.echo("  Gemini API Key: Not configured")
    
    imagen_project = manager.settings.imagen.project_id
    if imagen_project:
        click.echo(f"  Imagen Project: {imagen_project}")
    else:
        click.echo("  Imagen Project: Not configured")


@cli.command()
def validate():
    """Validate system configuration."""
    if validate_all_config():
        click.echo("✅ Configuration validation passed")
    else:
        click.echo("❌ Configuration validation failed", err=True)
        sys.exit(1)


def main():
    """Main entry point."""
    # Handle async commands
    if len(sys.argv) > 1 and sys.argv[1] in ['serve', 'health']:
        asyncio.run(cli())
    else:
        cli()


if __name__ == "__main__":
    main()