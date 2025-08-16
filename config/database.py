"""
Database connection setup and configuration for ViraLearn ContentBot.
Handles async SQLAlchemy setup, connection pooling, and session management.
"""

import asyncio
from typing import AsyncGenerator, Optional
from sqlalchemy.ext.asyncio import (
    AsyncSession, 
    create_async_engine, 
    async_sessionmaker,
    AsyncEngine
)
from sqlalchemy.pool import NullPool
from sqlalchemy import event
from sqlalchemy.engine import Engine

from config.settings import get_settings


class DatabaseManager:
    """Database connection manager for async operations."""
    
    def __init__(self):
        self.settings = None
        self.engine: Optional[AsyncEngine] = None
        self.session_factory: Optional[async_sessionmaker[AsyncSession]] = None
        self._initialized = False
    
    def _get_settings(self):
        """Lazy load settings."""
        if self.settings is None:
            self.settings = get_settings()
        return self.settings
    
    async def initialize(self) -> None:
        """Initialize database engine and session factory."""
        if self._initialized:
            return
        
        settings = self._get_settings()
        
        try:
            # Try to create async engine with connection pooling
            database_url = settings.database.url
            
            # Handle PostgreSQL connection args only if using PostgreSQL
            connect_args = {}
            if "postgresql" in database_url:
                connect_args = {
                    "server_settings": {
                        "application_name": "viralearn_contentbot",
                    }
                }
            
            self.engine = create_async_engine(
                database_url,
                echo=settings.debug,
                pool_size=settings.database.pool_size,
                max_overflow=settings.database.max_overflow,
                pool_pre_ping=True,  # Verify connections before use
                pool_recycle=3600,   # Recycle connections every hour
                connect_args=connect_args
            )
            
            # Create session factory
            self.session_factory = async_sessionmaker(
                bind=self.engine,
                class_=AsyncSession,
                expire_on_commit=False,
                autoflush=False,
                autocommit=False,
            )
            
            self._initialized = True
            
            # Test connection
            await self.test_connection()
            
        except Exception as e:
            print(f"Database initialization failed: {e}")
            print("Falling back to SQLite...")
            
            # Force fallback to SQLite
            import os
            db_path = os.path.join(os.getcwd(), "contentbot_fallback.db")
            sqlite_url = f"sqlite+aiosqlite:///{db_path}"
            
            self.engine = create_async_engine(
                sqlite_url,
                echo=settings.debug,
                pool_pre_ping=True
            )
            
            self.session_factory = async_sessionmaker(
                bind=self.engine,
                class_=AsyncSession,
                expire_on_commit=False,
                autoflush=False,
                autocommit=False,
            )
            
            self._initialized = True
            print(f"Successfully initialized SQLite fallback database at: {db_path}")
    
    async def test_connection(self) -> bool:
        """Test database connection."""
        if not self.engine:
            print("Database engine not initialized")
            return False
        
        try:
            from sqlalchemy import text
            async with self.engine.begin() as conn:
                await conn.execute(text("SELECT 1"))
            print("Database connection test successful")
            return True
        except Exception as e:
            print(f"Database connection test failed: {e}")
            return False
    
    async def get_session(self) -> AsyncGenerator[AsyncSession, None]:
        """Get database session."""
        if not self.session_factory:
            raise RuntimeError("Session factory not initialized")
        
        async with self.session_factory() as session:
            try:
                yield session
            except Exception:
                await session.rollback()
                raise
            finally:
                await session.close()
    
    async def close(self) -> None:
        """Close database connections."""
        if self.engine:
            await self.engine.dispose()
            self._initialized = False


# Global database manager instance (lazy-loaded)
_db_manager = None


def get_db_manager() -> DatabaseManager:
    """Get the global database manager instance."""
    global _db_manager
    if _db_manager is None:
        _db_manager = DatabaseManager()
    return _db_manager


async def get_db_session() -> AsyncGenerator[AsyncSession, None]:
    """Dependency function to get database session."""
    db_manager = get_db_manager()
    async for session in db_manager.get_session():
        yield session


async def init_database() -> None:
    """Initialize database connection."""
    db_manager = get_db_manager()
    await db_manager.initialize()


async def close_database() -> None:
    """Close database connection."""
    db_manager = get_db_manager()
    await db_manager.close()


# Database event listeners for better connection management
@event.listens_for(Engine, "connect")
def set_sqlite_pragma(dbapi_connection, connection_record):
    """Set SQLite pragmas for better performance (if using SQLite)."""
    if "sqlite" in str(dbapi_connection):
        cursor = dbapi_connection.cursor()
        cursor.execute("PRAGMA journal_mode=WAL")
        cursor.execute("PRAGMA synchronous=NORMAL")
        cursor.execute("PRAGMA cache_size=10000")
        cursor.execute("PRAGMA temp_store=MEMORY")
        cursor.close()


# Health check function
async def check_database_health() -> dict:
    """Check database health status."""
    try:
        db_manager = get_db_manager()
        if not db_manager._initialized:
            return {"status": "not_initialized", "error": "Database not initialized"}
        
        is_healthy = await db_manager.test_connection()
        return {
            "status": "healthy" if is_healthy else "unhealthy",
            "connection_pool": {
                "size": db_manager._get_settings().database.pool_size,
                "overflow": db_manager._get_settings().database.max_overflow,
            }
        }
    except Exception as e:
        return {"status": "error", "error": str(e)}
