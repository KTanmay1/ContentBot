"""
Configuration management for ViraLearn ContentBot.
Handles environment variables, API keys, and application settings.
"""

import os
from typing import Optional, Dict, Any
from pydantic import Field, validator
from pydantic_settings import BaseSettings, SettingsConfigDict


class DatabaseSettings(BaseSettings):
    """Database configuration settings."""
    
    model_config = SettingsConfigDict(env_prefix="DB_", extra="ignore", env_file=".env", env_file_encoding="utf-8")
    
    host: str = Field(default="localhost", description="Database host")
    port: int = Field(default=5432, description="Database port")
    name: str = Field(default="viralearn_content", description="Database name")
    user: str = Field(default="postgres", description="Database user")
    password: str = Field(default="", description="Database password")
    pool_size: int = Field(default=10, description="Connection pool size")
    max_overflow: int = Field(default=20, description="Max overflow connections")
    
    @property
    def url(self) -> str:
        """Generate database URL with fallback to SQLite."""
        # Try PostgreSQL first, fallback to SQLite if asyncpg is not available
        try:
            import asyncpg
            from urllib.parse import quote_plus
            encoded_password = quote_plus(self.password)
            return f"postgresql+asyncpg://{self.user}:{encoded_password}@{self.host}:{self.port}/{self.name}"
        except ImportError:
            # Fallback to SQLite for development/testing
            import os
            db_path = os.path.join(os.getcwd(), "contentbot.db")
            return f"sqlite+aiosqlite:///{db_path}"


class GeminiSettings(BaseSettings):
    """Gemini API configuration settings."""
    
    model_config = SettingsConfigDict(env_prefix="GEMINI_", extra="ignore", env_file=".env", env_file_encoding="utf-8")
    
    api_key: Optional[str] = Field(default=None, description="Gemini API key")
    model_name: str = Field(default="gemini-2.0-flash-exp", description="Gemini model to use")
    max_tokens: int = Field(default=8192, description="Maximum tokens per request")
    temperature: float = Field(default=0.7, description="Temperature for generation")
    top_p: float = Field(default=0.9, description="Top-p sampling parameter")
    max_retries: int = Field(default=3, description="Maximum retry attempts")
    timeout: int = Field(default=30, description="Request timeout in seconds")


class ImagenSettings(BaseSettings):
    """Imagen API configuration settings."""
    
    model_config = SettingsConfigDict(env_prefix="IMAGEN_", extra="ignore", env_file=".env", env_file_encoding="utf-8")
    
    # Uses GOOGLE_APPLICATION_CREDENTIALS for authentication
    project_id: Optional[str] = Field(default=None, description="Google Cloud project ID")
    location: str = Field(default="us-central1", description="Google Cloud location")
    model_name: str = Field(default="imagen-3.0-8b", description="Imagen model to use")
    max_retries: int = Field(default=3, description="Maximum retry attempts")
    timeout: int = Field(default=60, description="Request timeout in seconds")


class AudioSettings(BaseSettings):
    """Audio processing API configuration settings."""
    
    model_config = SettingsConfigDict(env_prefix="AUDIO_", extra="ignore", env_file=".env", env_file_encoding="utf-8")
    
    # Uses GOOGLE_APPLICATION_CREDENTIALS for authentication
    # Text-to-speech settings
    tts_voice: str = Field(default="en-US-Standard-A", description="TTS voice to use")
    
    # Speech-to-text settings
    stt_language: str = Field(default="en-US", description="STT language code")


class MistralSettings(BaseSettings):
    """Mistral AI API configuration settings."""
    
    model_config = SettingsConfigDict(env_prefix="MISTRAL_", extra="ignore", env_file=".env", env_file_encoding="utf-8")
    
    api_key: Optional[str] = Field(default=None, description="Mistral AI API key")
    model_name: str = Field(default="mistral-large-latest", description="Mistral model to use")
    max_tokens: int = Field(default=8192, description="Maximum tokens per request")
    temperature: float = Field(default=0.7, description="Temperature for generation")
    top_p: float = Field(default=0.9, description="Top-p sampling parameter")
    max_retries: int = Field(default=3, description="Maximum retry attempts")
    timeout: int = Field(default=30, description="Request timeout in seconds")


class HuggingFaceSettings(BaseSettings):
    """Hugging Face API configuration settings."""
    
    model_config = SettingsConfigDict(env_prefix="HUGGINGFACE_", extra="ignore", env_file=".env", env_file_encoding="utf-8")
    
    api_token: Optional[str] = Field(default=None, description="Hugging Face API token (optional for public models)")
    timeout: int = Field(default=60, description="Request timeout in seconds")
    max_retries: int = Field(default=3, description="Maximum retry attempts")


class RedisSettings(BaseSettings):
    """Redis configuration settings."""
    
    model_config = SettingsConfigDict(env_prefix="REDIS_", extra="ignore", env_file=".env", env_file_encoding="utf-8")
    
    host: str = Field(default="localhost", description="Redis host")
    port: int = Field(default=6379, description="Redis port")
    password: Optional[str] = Field(default=None, description="Redis password")
    db: int = Field(default=0, description="Redis database number")
    
    @property
    def url(self) -> str:
        """Generate Redis URL."""
        if self.password:
            return f"redis://:{self.password}@{self.host}:{self.port}/{self.db}"
        return f"redis://{self.host}:{self.port}/{self.db}"


class AppSettings(BaseSettings):
    """Main application settings."""
    
    model_config = SettingsConfigDict(env_file=".env", env_file_encoding="utf-8", extra="ignore")
    
    # Application settings
    app_name: str = Field(default="ViraLearn ContentBot", description="Application name")
    debug: bool = Field(default=False, description="Debug mode")
    log_level: str = Field(default="INFO", description="Logging level")
    
    # API settings
    api_host: str = Field(default="0.0.0.0", description="API host")
    api_port: int = Field(default=8000, description="API port")
    api_prefix: str = Field(default="/api/v1", description="API prefix")
    
    # Security settings
    secret_key: str = Field(default="dev-secret-key-change-in-production", description="Secret key for JWT tokens")
    algorithm: str = Field(default="HS256", description="JWT algorithm")
    access_token_expire_minutes: int = Field(default=30, description="Access token expiry")
    
    # Content settings
    max_content_length: int = Field(default=10000, description="Maximum content length")
    supported_platforms: list = Field(default=["twitter", "linkedin", "instagram", "facebook"], 
                                     description="Supported social platforms")
    
    # Database settings
    database: DatabaseSettings = Field(default_factory=DatabaseSettings)
    
    # AI Service Settings
    gemini: GeminiSettings = Field(default_factory=GeminiSettings)
    mistral: MistralSettings = Field(default_factory=MistralSettings)
    imagen: ImagenSettings = Field(default_factory=ImagenSettings)
    audio: AudioSettings = Field(default_factory=AudioSettings)
    huggingface: HuggingFaceSettings = Field(default_factory=HuggingFaceSettings)
    
    # Cache configuration
    redis: RedisSettings = Field(default_factory=RedisSettings)
    
    @validator("log_level")
    def validate_log_level(cls, v):
        """Validate log level."""
        valid_levels = ["DEBUG", "INFO", "WARNING", "ERROR", "CRITICAL"]
        if v.upper() not in valid_levels:
            raise ValueError(f"Log level must be one of {valid_levels}")
        return v.upper()
    
    @validator("supported_platforms")
    def validate_platforms(cls, v):
        """Validate supported platforms."""
        valid_platforms = ["twitter", "linkedin", "instagram", "facebook", "tiktok", "youtube"]
        for platform in v:
            if platform.lower() not in valid_platforms:
                raise ValueError(f"Unsupported platform: {platform}")
        return [p.lower() for p in v]


# Global settings instance (lazy-loaded)
_settings = None


def get_settings() -> AppSettings:
    """Get application settings."""
    global _settings
    if _settings is None:
        _settings = AppSettings()
    return _settings


def reload_settings() -> None:
    """Reload settings from environment."""
    global _settings
    _settings = None
