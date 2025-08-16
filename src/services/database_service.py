"""
Database Service for ViraLearn ContentBot.
Handles database operations, state persistence, and data management.
"""

import asyncio
import logging
from typing import Dict, List, Optional, Any, Union
from datetime import datetime, timedelta
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, update, delete, and_, or_, func, text
from sqlalchemy.orm import selectinload
import json

from config.database import get_db_session
from config.settings import get_settings

logger = logging.getLogger(__name__)


class DatabaseServiceError(Exception):
    """Custom exception for database service errors."""
    pass


class DatabaseService:
    """Service for database operations and state management."""
    
    def __init__(self):
        self.settings = get_settings()
        self._session = None
    
    async def get_session(self) -> AsyncSession:
        """Get database session."""
        async for session in get_db_session():
            return session
    
    async def close_session(self) -> None:
        """Close database session."""
        # Session is managed by the context manager, no need to close manually
        pass
    
    async def create_workflow(self, workflow_data: Dict[str, Any]) -> str:
        """Create a new workflow and return its ID."""
        try:
            async for session in get_db_session():
                # Create workflow record
                workflow = {
                    "id": workflow_data.get("id"),
                    "user_id": workflow_data.get("user_id"),
                    "status": workflow_data.get("status", "created"),
                    "content_type": workflow_data.get("content_type"),
                    "platform": workflow_data.get("platform"),
                    "input_data": json.dumps(workflow_data.get("input_data", {})),
                    "created_at": datetime.utcnow(),
                    "updated_at": datetime.utcnow(),
                }
                
                # Insert workflow
                result = await session.execute(
                    text("INSERT INTO workflows (id, user_id, status, content_type, platform, input_data, created_at, updated_at) VALUES (:id, :user_id, :status, :content_type, :platform, :input_data, :created_at, :updated_at) RETURNING id"),
                    workflow
                )
                
                workflow_id = result.scalar()
                await session.commit()
                
                logger.info(f"Created workflow: {workflow_id}")
                return workflow_id
            
        except Exception as e:
            logger.error(f"Failed to create workflow: {e}")
            raise DatabaseServiceError(f"Failed to create workflow: {e}")
    
    async def update_workflow_status(self, workflow_id: str, status: str, metadata: Optional[Dict[str, Any]] = None) -> bool:
        """Update workflow status and metadata."""
        try:
            session = await self.get_session()
            
            update_data = {
                "status": status,
                "updated_at": datetime.utcnow(),
            }
            
            if metadata:
                update_data["metadata"] = json.dumps(metadata)
            
            result = await session.execute(
                "UPDATE workflows SET status = :status, updated_at = :updated_at, metadata = COALESCE(:metadata, metadata) WHERE id = :workflow_id",
                {**update_data, "workflow_id": workflow_id}
            )
            
            await session.commit()
            
            if result.rowcount > 0:
                logger.info(f"Updated workflow {workflow_id} status to {status}")
                return True
            else:
                logger.warning(f"Workflow {workflow_id} not found for status update")
                return False
                
        except Exception as e:
            await session.rollback()
            logger.error(f"Failed to update workflow status: {e}")
            raise DatabaseServiceError(f"Failed to update workflow status: {e}")
    
    async def save_content(self, workflow_id: str, content_data: Dict[str, Any]) -> str:
        """Save generated content to database."""
        try:
            session = await self.get_session()
            
            content = {
                "id": content_data.get("id"),
                "workflow_id": workflow_id,
                "content_type": content_data.get("content_type"),
                "platform": content_data.get("platform"),
                "title": content_data.get("title"),
                "body": content_data.get("body"),
                "metadata": json.dumps(content_data.get("metadata", {})),
                "created_at": datetime.utcnow(),
            }
            
            # Insert content
            result = await session.execute(
                "INSERT INTO content (id, workflow_id, content_type, platform, title, body, metadata, created_at) VALUES (:id, :workflow_id, :content_type, :platform, :title, :body, :metadata, :created_at) RETURNING id",
                content
            )
            
            content_id = result.scalar()
            await session.commit()
            
            logger.info(f"Saved content: {content_id} for workflow: {workflow_id}")
            return content_id
            
        except Exception as e:
            await session.rollback()
            logger.error(f"Failed to save content: {e}")
            raise DatabaseServiceError(f"Failed to save content: {e}")
    
    async def save_media(self, content_id: str, media_data: Dict[str, Any]) -> str:
        """Save media files (images, audio) to database."""
        try:
            session = await self.get_session()
            
            media = {
                "id": media_data.get("id"),
                "content_id": content_id,
                "media_type": media_data.get("media_type"),  # image, audio, video
                "file_path": media_data.get("file_path"),
                "file_size": media_data.get("file_size"),
                "mime_type": media_data.get("mime_type"),
                "metadata": json.dumps(media_data.get("metadata", {})),
                "created_at": datetime.utcnow(),
            }
            
            # Insert media
            result = await session.execute(
                "INSERT INTO media (id, content_id, media_type, file_path, file_size, mime_type, metadata, created_at) VALUES (:id, :content_id, :media_type, :file_path, :file_size, :mime_type, :metadata, :created_at) RETURNING id",
                media
            )
            
            media_id = result.scalar()
            await session.commit()
            
            logger.info(f"Saved media: {media_id} for content: {content_id}")
            return media_id
            
        except Exception as e:
            await session.rollback()
            logger.error(f"Failed to save media: {e}")
            raise DatabaseServiceError(f"Failed to save media: {e}")
    
    async def get_workflow(self, workflow_id: str) -> Optional[Dict[str, Any]]:
        """Get workflow by ID."""
        try:
            session = await self.get_session()
            
            result = await session.execute(
                text("SELECT * FROM workflows WHERE id = :workflow_id"),
                {"workflow_id": workflow_id}
            )
            
            row = result.fetchone()
            if row:
                workflow = dict(row._mapping)
                workflow["input_data"] = json.loads(workflow["input_data"]) if workflow["input_data"] else {}
                workflow["metadata"] = json.loads(workflow["metadata"]) if workflow["metadata"] else {}
                return workflow
            return None
            
        except Exception as e:
            logger.error(f"Failed to get workflow: {e}")
            raise DatabaseServiceError(f"Failed to get workflow: {e}")
    
    async def get_workflow_content(self, workflow_id: str) -> List[Dict[str, Any]]:
        """Get all content for a workflow."""
        try:
            session = await self.get_session()
            
            result = await session.execute(
                """
                SELECT c.*, m.id as media_id, m.media_type, m.file_path, m.mime_type
                FROM content c
                LEFT JOIN media m ON c.id = m.content_id
                WHERE c.workflow_id = :workflow_id
                ORDER BY c.created_at
                """,
                {"workflow_id": workflow_id}
            )
            
            content_items = []
            for row in result.fetchall():
                content = dict(row._mapping)
                content["metadata"] = json.loads(content["metadata"]) if content["metadata"] else {}
                
                # Group media by content
                if content["id"] not in [item["id"] for item in content_items]:
                    content["media"] = []
                    content_items.append(content)
                
                if content["media_id"]:
                    media = {
                        "id": content["media_id"],
                        "media_type": content["media_type"],
                        "file_path": content["file_path"],
                        "mime_type": content["mime_type"],
                    }
                    content_items[-1]["media"].append(media)
                
                # Remove media fields from content dict
                for key in ["media_id", "media_type", "file_path", "mime_type"]:
                    content.pop(key, None)
            
            return content_items
            
        except Exception as e:
            logger.error(f"Failed to get workflow content: {e}")
            raise DatabaseServiceError(f"Failed to get workflow content: {e}")
    
    async def get_user_workflows(self, user_id: str, limit: int = 50, offset: int = 0) -> List[Dict[str, Any]]:
        """Get workflows for a user with pagination."""
        try:
            session = await self.get_session()
            
            result = await session.execute(
                text("""
                SELECT * FROM workflows 
                WHERE user_id = :user_id 
                ORDER BY created_at DESC 
                LIMIT :limit OFFSET :offset
                """),
                {"user_id": user_id, "limit": limit, "offset": offset}
            )
            
            workflows = []
            for row in result.fetchall():
                workflow = dict(row._mapping)
                workflow["input_data"] = json.loads(workflow["input_data"]) if workflow["input_data"] else {}
                workflow["metadata"] = json.loads(workflow["metadata"]) if workflow["metadata"] else {}
                workflows.append(workflow)
            
            return workflows
            
        except Exception as e:
            logger.error(f"Failed to get user workflows: {e}")
            raise DatabaseServiceError(f"Failed to get user workflows: {e}")
    
    async def delete_workflow(self, workflow_id: str) -> bool:
        """Delete a workflow and all associated content."""
        try:
            session = await self.get_session()
            
            # Delete media first (due to foreign key constraints)
            await session.execute(
                "DELETE FROM media WHERE content_id IN (SELECT id FROM content WHERE workflow_id = :workflow_id)",
                {"workflow_id": workflow_id}
            )
            
            # Delete content
            await session.execute(
                "DELETE FROM content WHERE workflow_id = :workflow_id",
                {"workflow_id": workflow_id}
            )
            
            # Delete workflow
            result = await session.execute(
                "DELETE FROM workflows WHERE id = :workflow_id",
                {"workflow_id": workflow_id}
            )
            
            await session.commit()
            
            if result.rowcount > 0:
                logger.info(f"Deleted workflow: {workflow_id}")
                return True
            else:
                logger.warning(f"Workflow {workflow_id} not found for deletion")
                return False
                
        except Exception as e:
            await session.rollback()
            logger.error(f"Failed to delete workflow: {e}")
            raise DatabaseServiceError(f"Failed to delete workflow: {e}")
    
    async def save_quality_metrics(self, content_id: str, metrics: Dict[str, Any]) -> str:
        """Save quality metrics for content."""
        try:
            session = await self.get_session()
            
            quality_data = {
                "id": metrics.get("id"),
                "content_id": content_id,
                "readability_score": metrics.get("readability_score"),
                "sentiment_score": metrics.get("sentiment_score"),
                "seo_score": metrics.get("seo_score"),
                "engagement_score": metrics.get("engagement_score"),
                "overall_score": metrics.get("overall_score"),
                "feedback": json.dumps(metrics.get("feedback", {})),
                "created_at": datetime.utcnow(),
            }
            
            result = await session.execute(
                """
                INSERT INTO quality_metrics (id, content_id, readability_score, sentiment_score, seo_score, engagement_score, overall_score, feedback, created_at) 
                VALUES (:id, :content_id, :readability_score, :sentiment_score, :seo_score, :engagement_score, :overall_score, :feedback, :created_at) 
                RETURNING id
                """,
                quality_data
            )
            
            metric_id = result.scalar()
            await session.commit()
            
            logger.info(f"Saved quality metrics: {metric_id} for content: {content_id}")
            return metric_id
            
        except Exception as e:
            await session.rollback()
            logger.error(f"Failed to save quality metrics: {e}")
            raise DatabaseServiceError(f"Failed to save quality metrics: {e}")
    
    async def get_content_analytics(self, user_id: str, days: int = 30) -> Dict[str, Any]:
        """Get content analytics for a user."""
        try:
            session = await self.get_session()
            
            start_date = datetime.utcnow() - timedelta(days=days)
            
            # Get workflow statistics
            workflow_stats = await session.execute(
                """
                SELECT 
                    COUNT(*) as total_workflows,
                    COUNT(CASE WHEN status = 'completed' THEN 1 END) as completed_workflows,
                    COUNT(CASE WHEN status = 'failed' THEN 1 END) as failed_workflows,
                    AVG(EXTRACT(EPOCH FROM (updated_at - created_at))) as avg_processing_time
                FROM workflows 
                WHERE user_id = :user_id AND created_at >= :start_date
                """,
                {"user_id": user_id, "start_date": start_date}
            )
            
            # Get content statistics
            content_stats = await session.execute(
                """
                SELECT 
                    COUNT(*) as total_content,
                    COUNT(CASE WHEN content_type = 'blog' THEN 1 END) as blog_posts,
                    COUNT(CASE WHEN content_type = 'social' THEN 1 END) as social_posts,
                    COUNT(CASE WHEN content_type = 'video' THEN 1 END) as video_content
                FROM content c
                JOIN workflows w ON c.workflow_id = w.id
                WHERE w.user_id = :user_id AND c.created_at >= :start_date
                """,
                {"user_id": user_id, "start_date": start_date}
            )
            
            # Get quality metrics
            quality_stats = await session.execute(
                """
                SELECT 
                    AVG(overall_score) as avg_quality_score,
                    AVG(readability_score) as avg_readability,
                    AVG(sentiment_score) as avg_sentiment,
                    AVG(seo_score) as avg_seo_score
                FROM quality_metrics qm
                JOIN content c ON qm.content_id = c.id
                JOIN workflows w ON c.workflow_id = w.id
                WHERE w.user_id = :user_id AND qm.created_at >= :start_date
                """,
                {"user_id": user_id, "start_date": start_date}
            )
            
            workflow_row = workflow_stats.fetchone()
            content_row = content_stats.fetchone()
            quality_row = quality_stats.fetchone()
            
            return {
                "period_days": days,
                "workflows": {
                    "total": workflow_row.total_workflows if workflow_row else 0,
                    "completed": workflow_row.completed_workflows if workflow_row else 0,
                    "failed": workflow_row.failed_workflows if workflow_row else 0,
                    "avg_processing_time_seconds": workflow_row.avg_processing_time if workflow_row else 0,
                },
                "content": {
                    "total": content_row.total_content if content_row else 0,
                    "blog_posts": content_row.blog_posts if content_row else 0,
                    "social_posts": content_row.social_posts if content_row else 0,
                    "video_content": content_row.video_content if content_row else 0,
                },
                "quality": {
                    "avg_overall_score": quality_row.avg_quality_score if quality_row else 0,
                    "avg_readability": quality_row.avg_readability if quality_row else 0,
                    "avg_sentiment": quality_row.avg_sentiment if quality_row else 0,
                    "avg_seo_score": quality_row.avg_seo_score if quality_row else 0,
                }
            }
            
        except Exception as e:
            logger.error(f"Failed to get content analytics: {e}")
            raise DatabaseServiceError(f"Failed to get content analytics: {e}")
    
    async def cleanup_old_data(self, days: int = 90) -> Dict[str, int]:
        """Clean up old data to maintain database performance."""
        try:
            session = await self.get_session()
            cutoff_date = datetime.utcnow() - timedelta(days=days)
            
            # Delete old workflows and related data
            media_deleted = await session.execute(
                """
                DELETE FROM media 
                WHERE content_id IN (
                    SELECT c.id FROM content c 
                    JOIN workflows w ON c.workflow_id = w.id 
                    WHERE w.created_at < :cutoff_date
                )
                """,
                {"cutoff_date": cutoff_date}
            )
            
            content_deleted = await session.execute(
                """
                DELETE FROM content 
                WHERE workflow_id IN (
                    SELECT id FROM workflows WHERE created_at < :cutoff_date
                )
                """,
                {"cutoff_date": cutoff_date}
            )
            
            workflows_deleted = await session.execute(
                "DELETE FROM workflows WHERE created_at < :cutoff_date",
                {"cutoff_date": cutoff_date}
            )
            
            await session.commit()
            
            cleanup_stats = {
                "workflows_deleted": workflows_deleted.rowcount,
                "content_deleted": content_deleted.rowcount,
                "media_deleted": media_deleted.rowcount,
            }
            
            logger.info(f"Cleanup completed: {cleanup_stats}")
            return cleanup_stats
            
        except Exception as e:
            await session.rollback()
            logger.error(f"Failed to cleanup old data: {e}")
            raise DatabaseServiceError(f"Failed to cleanup old data: {e}")
    
    async def health_check(self) -> Dict[str, Any]:
        """Check database health and performance."""
        try:
            session = await self.get_session()
            
            # Test basic connectivity
            result = await session.execute(text("SELECT 1"))
            connectivity_ok = result.scalar() == 1
            
            # Get database statistics
            stats = await session.execute(
                text("""
                SELECT 
                    (SELECT COUNT(*) FROM workflows) as workflow_count,
                    (SELECT COUNT(*) FROM content) as content_count,
                    (SELECT COUNT(*) FROM media) as media_count,
                    (SELECT COUNT(*) FROM quality_metrics) as metrics_count
                """)
            )
            
            db_stats = stats.fetchone()
            
            return {
                "status": "healthy" if connectivity_ok else "unhealthy",
                "connectivity": connectivity_ok,
                "statistics": {
                    "workflows": db_stats.workflow_count if db_stats else 0,
                    "content": db_stats.content_count if db_stats else 0,
                    "media": db_stats.media_count if db_stats else 0,
                    "quality_metrics": db_stats.metrics_count if db_stats else 0,
                }
            }
            
        except Exception as e:
            return {"status": "unhealthy", "error": str(e)}


# Global database service instance
db_service = DatabaseService()


async def get_db_service() -> DatabaseService:
    """Get the global database service instance."""
    return db_service