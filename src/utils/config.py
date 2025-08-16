"""Unified configuration system for the integrated ContentBot application.

This module provides a single entry point for all configuration settings,
bridging the main application settings with any additional configuration needs.
"""

import os
from typing import Optional, Dict, Any
from functools import lru_cache

from config.settings import get_settings, AppSettings
from src.core.monitoring import get_monitoring


class UnifiedConfig:
    """Unified configuration manager for the integrated application."""
    
    def __init__(self):
        self._settings: Optional[AppSettings] = None
        self._monitoring = get_monitoring("config-system")
        
    @property
    def settings(self) -> AppSettings:
        """Get the main application settings."""
        if self._settings is None:
            self._settings = get_settings()
        return self._settings
    
    @property
    def database_url(self) -> str:
        """Get the database connection URL."""
        return self.settings.database.url
    
    @property
    def redis_url(self) -> str:
        """Get the Redis connection URL."""
        return self.settings.redis.url
    
    @property
    def api_config(self) -> Dict[str, Any]:
        """Get API configuration settings."""
        return {
            "host": self.settings.api_host,
            "port": self.settings.api_port,
            "prefix": self.settings.api_prefix,
            "debug": self.settings.debug
        }
    
    @property
    def llm_config(self) -> Dict[str, Any]:
        """Get LLM service configuration."""
        return {
            "gemini": {
                "api_key": self.settings.gemini.api_key,
                "model_name": self.settings.gemini.model_name,
                "max_tokens": self.settings.gemini.max_tokens,
                "temperature": self.settings.gemini.temperature,
                "max_retries": self.settings.gemini.max_retries,
                "timeout": self.settings.gemini.timeout
            }
        }
    
    @property
    def image_config(self) -> Dict[str, Any]:
        """Get image generation configuration."""
        return {
            "imagen": {
                "project_id": self.settings.imagen.project_id,
                "location": self.settings.imagen.location,
                "model_name": self.settings.imagen.model_name,
                "max_retries": self.settings.imagen.max_retries,
                "timeout": self.settings.imagen.timeout
            }
        }
    
    @property
    def audio_config(self) -> Dict[str, Any]:
        """Get audio processing configuration."""
        return {
            "tts_voice": self.settings.audio.tts_voice,
            "stt_language": self.settings.audio.stt_language
        }
    
    @property
    def workflow_config(self) -> Dict[str, Any]:
        """Get workflow engine configuration."""
        return {
            "max_content_length": self.settings.max_content_length,
            "supported_platforms": self.settings.supported_platforms,
            "max_retries": 3,  # Default workflow retry limit
            "timeout_seconds": 300,  # Default workflow timeout
            "enable_checkpointing": True,  # Enable state persistence
            "enable_monitoring": True  # Enable workflow monitoring
        }
    
    @property
    def security_config(self) -> Dict[str, Any]:
        """Get security configuration."""
        return {
            "secret_key": self.settings.secret_key,
            "algorithm": self.settings.algorithm,
            "access_token_expire_minutes": self.settings.access_token_expire_minutes
        }
    
    def get_environment_variable(self, key: str, default: Optional[str] = None) -> Optional[str]:
        """Get environment variable with optional default."""
        value = os.getenv(key, default)
        if value is None:
            self._monitoring.warning(f"Environment variable {key} not found")
        return value
    
    def validate_configuration(self) -> bool:
        """Validate that all required configuration is present."""
        try:
            # Check critical settings
            if not self.settings.secret_key or self.settings.secret_key == "dev-secret-key-change-in-production":
                self._monitoring.warning("Using default secret key - change for production")
            
            # Check external service configurations
            if not self.settings.gemini.api_key:
                self._monitoring.warning("Gemini API key not configured")
            
            if not self.settings.imagen.project_id:
                self._monitoring.warning("Imagen project ID not configured")
            
            # Log configuration status
            self._monitoring.info("Configuration validation completed")
            return True
            
        except Exception as e:
            self._monitoring.error(f"Configuration validation failed: {e}")
            return False
    
    def reload(self) -> None:
        """Reload configuration settings."""
        self._settings = None
        from config.settings import reload_settings
        reload_settings()
        self._monitoring.info("Configuration reloaded")


@lru_cache(maxsize=1)
def get_unified_config() -> UnifiedConfig:
    """Get the unified configuration instance (singleton)."""
    return UnifiedConfig()


# Convenience functions for common configuration access
def get_database_url() -> str:
    """Get database URL."""
    return get_unified_config().database_url


def get_api_config() -> Dict[str, Any]:
    """Get API configuration."""
    return get_unified_config().api_config


def get_llm_config() -> Dict[str, Any]:
    """Get LLM configuration."""
    return get_unified_config().llm_config


def get_workflow_config() -> Dict[str, Any]:
    """Get workflow configuration."""
    return get_unified_config().workflow_config


def validate_all_config() -> bool:
    """Validate all configuration settings."""
    return get_unified_config().validate_configuration()