"""Cross-platform agent for content optimization and distribution."""

from typing import Dict, Any, List, Optional, Set
import json
from datetime import datetime

from .base_agent import BaseAgent
from src.models.state_models import ContentState, WorkflowStatus
from src.services.llm_service import LLMService
from src.core.error_handling import AgentException, ValidationException
from src.core.monitoring import get_monitoring


class CrossPlatform(BaseAgent):
    """Agent for cross-platform content optimization and distribution."""
    
    name = "CrossPlatform"
    
    def __init__(self):
        self.llm_service = LLMService()
        self._platform_specs = self._load_platform_specifications()
        self._supported_platforms = set(self._platform_specs.keys())
    
    def before_execute(self, state: ContentState) -> None:
        """Pre-execution setup."""
        # Validate target platforms
        target_platforms = getattr(state, 'target_platforms', [])
        if target_platforms:
            invalid_platforms = set(target_platforms) - self._supported_platforms
            if invalid_platforms:
                raise ValidationException(f"Unsupported platforms: {invalid_platforms}")
    
    def execute(self, state: ContentState) -> ContentState:
        """Execute cross-platform content optimization."""
        monitoring = get_monitoring(state.workflow_id)
        monitoring.info("cross_platform_start", workflow_id=state.workflow_id)
        
        try:
            # Get target platforms from state or use defaults
            target_platforms = getattr(state, 'target_platforms', ['twitter', 'linkedin', 'instagram'])
            
            # Optimize content for each platform
            platform_content = self._optimize_for_platforms(state, target_platforms)
            
            # Update state with platform-optimized content
            if not hasattr(state, 'platform_content'):
                state.platform_content = {}
            state.platform_content.update(platform_content)
            
            # Generate platform-specific metadata
            platform_metadata = self._generate_platform_metadata(state, target_platforms)
            state.platform_metadata = platform_metadata
            
            # Calculate cross-platform compatibility scores
            compatibility_scores = self._calculate_compatibility_scores(state, target_platforms)
            state.quality_scores = state.quality_scores or {}
            state.quality_scores['cross_platform_score'] = compatibility_scores['overall']
            state.quality_scores['platform_scores'] = compatibility_scores['individual']
            
            # Generate distribution recommendations
            distribution_plan = self._generate_distribution_plan(state, target_platforms)
            state.distribution_plan = distribution_plan
            
            state.current_agent = "CrossPlatform"
            state.step_count += 1
            
            monitoring.info("cross_platform_complete", 
                          platforms=target_platforms,
                          compatibility_score=compatibility_scores['overall'])
            
            return state
            
        except Exception as e:
            monitoring.error("cross_platform_error", error=str(e))
            raise AgentException(f"Cross-platform optimization failed: {str(e)}")
    
    def _load_platform_specifications(self) -> Dict[str, Dict[str, Any]]:
        """Load platform-specific specifications and constraints."""
        return {
            "twitter": {
                "text_limits": {
                    "max_characters": 280,
                    "max_hashtags": 2,
                    "max_mentions": 5
                },
                "image_specs": {
                    "max_images": 4,
                    "aspect_ratios": ["16:9", "1:1", "4:5"],
                    "max_size_mb": 5
                },
                "video_specs": {
                    "max_duration": 140,
                    "max_size_mb": 512
                },
                "content_style": {
                    "tone": "conversational",
                    "formality": "low",
                    "hashtag_style": "trending",
                    "call_to_action": "engagement_focused"
                },
                "best_practices": [
                    "Use engaging hooks",
                    "Include relevant hashtags",
                    "Ask questions to drive engagement",
                    "Use threads for longer content"
                ]
            },
            "linkedin": {
                "text_limits": {
                    "max_characters": 3000,
                    "optimal_length": 1300,
                    "max_hashtags": 5
                },
                "image_specs": {
                    "max_images": 9,
                    "aspect_ratios": ["1.91:1", "1:1", "4:5"],
                    "max_size_mb": 10
                },
                "video_specs": {
                    "max_duration": 600,
                    "max_size_mb": 5000
                },
                "content_style": {
                    "tone": "professional",
                    "formality": "high",
                    "hashtag_style": "industry_specific",
                    "call_to_action": "professional_networking"
                },
                "best_practices": [
                    "Share industry insights",
                    "Use professional language",
                    "Include data and statistics",
                    "Tag relevant professionals"
                ]
            },
            "instagram": {
                "text_limits": {
                    "max_characters": 2200,
                    "optimal_length": 125,
                    "max_hashtags": 30,
                    "optimal_hashtags": 11
                },
                "image_specs": {
                    "max_images": 10,
                    "aspect_ratios": ["1:1", "4:5", "9:16"],
                    "max_size_mb": 30
                },
                "video_specs": {
                    "max_duration": 60,
                    "max_size_mb": 100
                },
                "content_style": {
                    "tone": "visual_storytelling",
                    "formality": "low",
                    "hashtag_style": "discovery_focused",
                    "call_to_action": "visual_engagement"
                },
                "best_practices": [
                    "Focus on visual appeal",
                    "Use story-driven captions",
                    "Include location tags",
                    "Use mix of popular and niche hashtags"
                ]
            },
            "facebook": {
                "text_limits": {
                    "max_characters": 63206,
                    "optimal_length": 40,
                    "max_hashtags": 2
                },
                "image_specs": {
                    "max_images": 10,
                    "aspect_ratios": ["16:9", "1:1", "4:5"],
                    "max_size_mb": 10
                },
                "video_specs": {
                    "max_duration": 240,
                    "max_size_mb": 10000
                },
                "content_style": {
                    "tone": "community_focused",
                    "formality": "medium",
                    "hashtag_style": "minimal",
                    "call_to_action": "community_building"
                },
                "best_practices": [
                    "Encourage comments and shares",
                    "Use native video when possible",
                    "Post when audience is most active",
                    "Create shareable content"
                ]
            },
            "youtube": {
                "text_limits": {
                    "title_max": 100,
                    "description_max": 5000,
                    "max_hashtags": 15
                },
                "video_specs": {
                    "min_duration": 60,
                    "max_duration": 43200,
                    "max_size_gb": 256
                },
                "content_style": {
                    "tone": "educational_entertaining",
                    "formality": "medium",
                    "hashtag_style": "searchable",
                    "call_to_action": "subscribe_focused"
                },
                "best_practices": [
                    "Create compelling thumbnails",
                    "Use SEO-optimized titles",
                    "Include clear call-to-actions",
                    "Add timestamps for longer videos"
                ]
            }
        }
    
    def _optimize_for_platforms(self, state: ContentState, target_platforms: List[str]) -> Dict[str, Dict[str, Any]]:
        """Optimize content for specific platforms."""
        platform_content = {}
        
        for platform in target_platforms:
            if platform not in self._platform_specs:
                continue
            
            platform_spec = self._platform_specs[platform]
            optimized_content = self._optimize_single_platform(state, platform, platform_spec)
            platform_content[platform] = optimized_content
        
        return platform_content
    
    def _optimize_single_platform(self, state: ContentState, platform: str, spec: Dict[str, Any]) -> Dict[str, Any]:
        """Optimize content for a single platform."""
        optimized = {
            "text_content": {},
            "image_content": {},
            "video_content": {},
            "metadata": {}
        }
        
        # Optimize text content
        if state.text_content:
            optimized["text_content"] = self._optimize_text_for_platform(
                state.text_content, platform, spec
            )
        
        # Optimize image content
        if state.image_content:
            optimized["image_content"] = self._optimize_images_for_platform(
                state.image_content, platform, spec
            )
        
        # Optimize video content
        if hasattr(state, 'video_content') and state.video_content:
            optimized["video_content"] = self._optimize_videos_for_platform(
                state.video_content, platform, spec
            )
        
        # Generate platform-specific metadata
        optimized["metadata"] = self._generate_platform_specific_metadata(state, platform, spec)
        
        return optimized
    
    def _optimize_text_for_platform(self, text_content: Dict[str, Any], platform: str, spec: Dict[str, Any]) -> Dict[str, Any]:
        """Optimize text content for platform constraints."""
        optimized_text = {}
        text_limits = spec.get('text_limits', {})
        content_style = spec.get('content_style', {})
        
        for content_type, content in text_content.items():
            if isinstance(content, str):
                optimized_text[content_type] = self._adapt_text_to_platform(
                    content, platform, text_limits, content_style
                )
            elif isinstance(content, dict) and platform in content:
                # Use existing platform-specific content if available
                optimized_text[content_type] = content[platform]
            elif isinstance(content, dict):
                # Adapt from general content
                general_content = content.get('general', '') or next(iter(content.values()), '')
                optimized_text[content_type] = self._adapt_text_to_platform(
                    general_content, platform, text_limits, content_style
                )
            else:
                optimized_text[content_type] = content
        
        return optimized_text
    
    def _adapt_text_to_platform(self, text: str, platform: str, limits: Dict[str, Any], style: Dict[str, Any]) -> str:
        """Adapt text content to platform-specific requirements."""
        try:
            adaptation_prompt = f"""
Adapt the following content for {platform}:

Platform Requirements:
- Character limit: {limits.get('max_characters', 'unlimited')}
- Optimal length: {limits.get('optimal_length', 'flexible')}
- Tone: {style.get('tone', 'neutral')}
- Formality: {style.get('formality', 'medium')}
- Hashtag limit: {limits.get('max_hashtags', 'unlimited')}

Original Content:
{text}

Adapted Content:"""
            
            response = self.llm_service.generate_content(
                prompt=adaptation_prompt,
                max_tokens=min(limits.get('max_characters', 1000) // 4, 500),
                temperature=0.4
            )
            
            adapted_text = response.strip()
            
            # Ensure character limit compliance
            max_chars = limits.get('max_characters')
            if max_chars and len(adapted_text) > max_chars:
                adapted_text = adapted_text[:max_chars-3] + "..."
            
            return adapted_text
            
        except Exception as e:
            get_monitoring().error("text_adaptation_error", platform=platform, error=str(e))
            # Fallback: truncate original text
            max_chars = limits.get('max_characters', len(text))
            return text[:max_chars-3] + "..." if len(text) > max_chars else text
    
    def _optimize_images_for_platform(self, image_content: Dict[str, Any], platform: str, spec: Dict[str, Any]) -> Dict[str, Any]:
        """Optimize image content for platform specifications."""
        optimized_images = {}
        image_specs = spec.get('image_specs', {})
        
        for image_type, images in image_content.items():
            if isinstance(images, list):
                # Limit number of images
                max_images = image_specs.get('max_images', len(images))
                optimized_images[image_type] = images[:max_images]
                
                # Add platform-specific image metadata
                for i, image in enumerate(optimized_images[image_type]):
                    if isinstance(image, dict):
                        image['platform_specs'] = {
                            'target_platform': platform,
                            'recommended_aspect_ratios': image_specs.get('aspect_ratios', []),
                            'max_size_mb': image_specs.get('max_size_mb', 10)
                        }
            else:
                optimized_images[image_type] = images
        
        return optimized_images
    
    def _optimize_videos_for_platform(self, video_content: Dict[str, Any], platform: str, spec: Dict[str, Any]) -> Dict[str, Any]:
        """Optimize video content for platform specifications."""
        optimized_videos = {}
        video_specs = spec.get('video_specs', {})
        
        for video_type, videos in video_content.items():
            if isinstance(videos, list):
                optimized_videos[video_type] = []
                for video in videos:
                    if isinstance(video, dict):
                        optimized_video = video.copy()
                        optimized_video['platform_specs'] = {
                            'target_platform': platform,
                            'max_duration': video_specs.get('max_duration', 600),
                            'max_size_mb': video_specs.get('max_size_mb', 100)
                        }
                        optimized_videos[video_type].append(optimized_video)
                    else:
                        optimized_videos[video_type].append(videos)
            else:
                optimized_videos[video_type] = videos
        
        return optimized_videos
    
    def _generate_platform_specific_metadata(self, state: ContentState, platform: str, spec: Dict[str, Any]) -> Dict[str, Any]:
        """Generate platform-specific metadata."""
        metadata = {
            "platform": platform,
            "optimization_timestamp": datetime.now().isoformat(),
            "content_style": spec.get('content_style', {}),
            "best_practices": spec.get('best_practices', []),
            "constraints": {
                "text_limits": spec.get('text_limits', {}),
                "image_specs": spec.get('image_specs', {}),
                "video_specs": spec.get('video_specs', {})
            }
        }
        
        # Add suggested hashtags
        if hasattr(state, 'keywords') and state.keywords:
            metadata['suggested_hashtags'] = self._generate_platform_hashtags(
                state.keywords, platform, spec
            )
        
        # Add posting recommendations
        metadata['posting_recommendations'] = self._get_posting_recommendations(platform)
        
        return metadata
    
    def _generate_platform_metadata(self, state: ContentState, target_platforms: List[str]) -> Dict[str, Any]:
        """Generate overall platform metadata."""
        return {
            "target_platforms": target_platforms,
            "optimization_timestamp": datetime.now().isoformat(),
            "total_platforms": len(target_platforms),
            "supported_platforms": list(self._supported_platforms),
            "cross_platform_features": {
                "unified_branding": True,
                "consistent_messaging": True,
                "platform_specific_optimization": True
            }
        }
    
    def _calculate_compatibility_scores(self, state: ContentState, target_platforms: List[str]) -> Dict[str, Any]:
        """Calculate cross-platform compatibility scores."""
        individual_scores = {}
        
        for platform in target_platforms:
            score = self._calculate_platform_score(state, platform)
            individual_scores[platform] = score
        
        overall_score = sum(individual_scores.values()) / len(individual_scores) if individual_scores else 0.0
        
        return {
            "overall": round(overall_score, 2),
            "individual": individual_scores
        }
    
    def _calculate_platform_score(self, state: ContentState, platform: str) -> float:
        """Calculate compatibility score for a specific platform."""
        if platform not in self._platform_specs:
            return 0.0
        
        spec = self._platform_specs[platform]
        score = 1.0
        
        # Check text content compliance
        if state.text_content:
            text_score = self._score_text_compliance(state.text_content, spec)
            score = (score + text_score) / 2
        
        # Check image content compliance
        if state.image_content:
            image_score = self._score_image_compliance(state.image_content, spec)
            score = (score + image_score) / 2
        
        return round(score, 2)
    
    def _score_text_compliance(self, text_content: Dict[str, Any], spec: Dict[str, Any]) -> float:
        """Score text content compliance with platform specs."""
        text_limits = spec.get('text_limits', {})
        max_chars = text_limits.get('max_characters')
        
        if not max_chars:
            return 1.0
        
        total_score = 0.0
        content_count = 0
        
        for content_type, content in text_content.items():
            if isinstance(content, str):
                content_count += 1
                if len(content) <= max_chars:
                    total_score += 1.0
                else:
                    # Partial score based on how much over the limit
                    overage = len(content) - max_chars
                    penalty = min(overage / max_chars, 0.5)  # Max 50% penalty
                    total_score += max(0.5, 1.0 - penalty)
        
        return total_score / content_count if content_count > 0 else 1.0
    
    def _score_image_compliance(self, image_content: Dict[str, Any], spec: Dict[str, Any]) -> float:
        """Score image content compliance with platform specs."""
        image_specs = spec.get('image_specs', {})
        max_images = image_specs.get('max_images')
        
        if not max_images:
            return 1.0
        
        total_score = 0.0
        content_count = 0
        
        for image_type, images in image_content.items():
            if isinstance(images, list):
                content_count += 1
                if len(images) <= max_images:
                    total_score += 1.0
                else:
                    # Partial score for exceeding image limit
                    excess = len(images) - max_images
                    penalty = min(excess / max_images, 0.3)  # Max 30% penalty
                    total_score += max(0.7, 1.0 - penalty)
        
        return total_score / content_count if content_count > 0 else 1.0
    
    def _generate_platform_hashtags(self, keywords: List[str], platform: str, spec: Dict[str, Any]) -> List[str]:
        """Generate platform-appropriate hashtags."""
        text_limits = spec.get('text_limits', {})
        max_hashtags = text_limits.get('max_hashtags', 5)
        hashtag_style = spec.get('content_style', {}).get('hashtag_style', 'general')
        
        # Select appropriate keywords based on platform style
        if hashtag_style == 'trending':
            # For platforms like Twitter, focus on trending/popular hashtags
            selected_keywords = keywords[:max_hashtags]
        elif hashtag_style == 'industry_specific':
            # For platforms like LinkedIn, focus on professional/industry hashtags
            selected_keywords = [kw for kw in keywords if len(kw) > 4][:max_hashtags]
        elif hashtag_style == 'discovery_focused':
            # For platforms like Instagram, mix popular and niche hashtags
            selected_keywords = keywords[:max_hashtags]
        else:
            selected_keywords = keywords[:max_hashtags]
        
        # Format as hashtags
        hashtags = [f"#{kw.replace(' ', '').lower()}" for kw in selected_keywords]
        
        return hashtags[:max_hashtags]
    
    def _get_posting_recommendations(self, platform: str) -> Dict[str, Any]:
        """Get posting recommendations for the platform."""
        recommendations = {
            "twitter": {
                "best_times": ["9-10 AM", "12-1 PM", "5-6 PM"],
                "frequency": "3-5 times per day",
                "engagement_tips": ["Use polls", "Ask questions", "Retweet with comments"]
            },
            "linkedin": {
                "best_times": ["8-9 AM", "12-1 PM", "5-6 PM"],
                "frequency": "1-2 times per day",
                "engagement_tips": ["Share industry insights", "Tag colleagues", "Use professional tone"]
            },
            "instagram": {
                "best_times": ["11 AM-1 PM", "7-9 PM"],
                "frequency": "1-2 times per day",
                "engagement_tips": ["Use Stories", "Post high-quality visuals", "Engage with comments"]
            },
            "facebook": {
                "best_times": ["1-3 PM", "7-9 PM"],
                "frequency": "1-2 times per day",
                "engagement_tips": ["Encourage shares", "Use native video", "Create events"]
            },
            "youtube": {
                "best_times": ["2-4 PM", "8-11 PM"],
                "frequency": "2-3 times per week",
                "engagement_tips": ["Create playlists", "Use end screens", "Respond to comments"]
            }
        }
        
        return recommendations.get(platform, {
            "best_times": ["9 AM-5 PM"],
            "frequency": "1-2 times per day",
            "engagement_tips": ["Post consistently", "Engage with audience"]
        })
    
    def _generate_distribution_plan(self, state: ContentState, target_platforms: List[str]) -> Dict[str, Any]:
        """Generate a distribution plan for cross-platform content."""
        return {
            "platforms": target_platforms,
            "distribution_strategy": "simultaneous",  # or "staggered"
            "priority_order": self._get_platform_priority_order(target_platforms),
            "timing_recommendations": {
                platform: self._get_posting_recommendations(platform)["best_times"]
                for platform in target_platforms
            },
            "content_variations": {
                platform: f"Optimized for {platform} audience and format"
                for platform in target_platforms
            },
            "cross_promotion_opportunities": self._identify_cross_promotion_opportunities(target_platforms)
        }
    
    def _get_platform_priority_order(self, platforms: List[str]) -> List[str]:
        """Get recommended priority order for platform distribution."""
        # Priority based on typical engagement and reach
        priority_map = {
            "linkedin": 1,  # Professional content often performs best here first
            "twitter": 2,   # Good for real-time engagement
            "instagram": 3, # Visual content performs well
            "facebook": 4,  # Broader reach but lower engagement
            "youtube": 5    # Longer-form content, different timing
        }
        
        return sorted(platforms, key=lambda p: priority_map.get(p, 999))
    
    def _identify_cross_promotion_opportunities(self, platforms: List[str]) -> List[Dict[str, Any]]:
        """Identify opportunities for cross-platform promotion."""
        opportunities = []
        
        if "youtube" in platforms and "twitter" in platforms:
            opportunities.append({
                "type": "video_teaser",
                "description": "Share video teasers on Twitter to drive YouTube views",
                "platforms": ["twitter", "youtube"]
            })
        
        if "instagram" in platforms and "facebook" in platforms:
            opportunities.append({
                "type": "cross_post",
                "description": "Cross-post visual content between Instagram and Facebook",
                "platforms": ["instagram", "facebook"]
            })
        
        if "linkedin" in platforms and "twitter" in platforms:
            opportunities.append({
                "type": "professional_discussion",
                "description": "Start professional discussions on LinkedIn, continue on Twitter",
                "platforms": ["linkedin", "twitter"]
            })
        
        return opportunities
    
    def after_execute(self, state: ContentState) -> None:
        """Post-execution cleanup."""
        monitoring = get_monitoring(state.workflow_id)
        platform_count = len(getattr(state, 'target_platforms', []))
        cross_platform_score = state.quality_scores.get('cross_platform_score', 0) if state.quality_scores else 0
        
        monitoring.info("cross_platform_complete", 
                       workflow_id=state.workflow_id,
                       platform_count=platform_count,
                       cross_platform_score=cross_platform_score)