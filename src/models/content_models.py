"""Content object schemas for text-based artifacts."""
# Step 2: Define content data models (BlogPost, SocialPost) used by generators
# and planners for structured content exchange across agents.

from __future__ import annotations

from typing import Dict, List, Optional

try:
    from pydantic import BaseModel, Field
except ImportError:  # pragma: no cover - fallback for static analyzers
    class BaseModel:  # type: ignore
        pass

    def Field(*_args, **kwargs):  # type: ignore
        return kwargs.get("default", None)


class BlogPost(BaseModel):
    title: str
    summary: Optional[str] = None
    sections: List[Dict[str, str]] = Field(
        default_factory=list,
        description="Ordered sections with keys like 'heading' and 'body'",
    )
    keywords: List[str] = Field(default_factory=list)
    seo_meta_description: Optional[str] = None


class SocialPost(BaseModel):
    platform: str
    content: str
    hashtags: List[str] = Field(default_factory=list)
    mentions: List[str] = Field(default_factory=list)
    call_to_action: Optional[str] = None

# Completed Step 2: Added BlogPost and SocialPost schemas for downstream
# generator/optimizer agents.