"""Input Analyzer Agent for ViraLearn ContentBot.

This agent is responsible for analyzing input content to extract themes,
perform sentiment analysis, and identify key content characteristics.
"""

import re
from typing import Dict, List, Optional, Any
from datetime import datetime

from ..models.state_models import ContentState
from ..services.llm_service import LLMService
from .base_agent import BaseAgent, AgentResult


class InputAnalyzer(BaseAgent):
    """Agent for analyzing input content and extracting key insights."""
    
    def __init__(self, llm_service: Optional[LLMService] = None):
        """Initialize the Input Analyzer agent.
        
        Args:
            llm_service: LLM service for advanced analysis
        """
        super().__init__()
        self.llm_service = llm_service or LLMService()
        self.agent_name = "InputAnalyzer"
    
    async def execute(self, state: ContentState) -> AgentResult:
        """Execute input analysis on the provided content state.
        
        Args:
            state: Current content state
            
        Returns:
            AgentResult with analysis results
        """
        try:
            # Extract input text
            input_text = state.original_input.get("text", "") if state.original_input else ""
            
            if not input_text:
                return AgentResult(
                    success=False,
                    data={},
                    error="No input text provided for analysis",
                    agent_name=self.agent_name
                )
            
            # Perform analysis
            themes = await self.extract_themes(input_text)
            sentiment = await self.analyze_sentiment(input_text)
            keywords = self.extract_keywords(input_text)
            content_type = self.identify_content_type(input_text)
            target_audience = await self.identify_target_audience(input_text)
            
            # Update state with analysis results
            analysis_data = {
                "themes": themes,
                "sentiment": sentiment,
                "keywords": keywords,
                "content_type": content_type,
                "target_audience": target_audience,
                "analyzed_at": datetime.utcnow().isoformat()
            }
            
            # Store analysis in state
            if not state.analysis_data:
                state.analysis_data = {}
            state.analysis_data.update(analysis_data)
            
            return AgentResult(
                success=True,
                data=analysis_data,
                agent_name=self.agent_name
            )
            
        except Exception as e:
            return AgentResult(
                success=False,
                data={},
                error=f"Input analysis failed: {str(e)}",
                agent_name=self.agent_name
            )
    
    async def extract_themes(self, text: str) -> List[str]:
        """Extract main themes from the input text.
        
        Args:
            text: Input text to analyze
            
        Returns:
            List of identified themes
        """
        try:
            prompt = f"""
            Analyze the following text and extract the main themes. 
            Return only the themes as a comma-separated list, no explanations.
            
            Text: {text}
            
            Themes:
            """
            
            response = await self.llm_service.generate_text(prompt)
            themes = [theme.strip() for theme in response.split(",") if theme.strip()]
            return themes[:5]  # Limit to top 5 themes
            
        except Exception:
            # Fallback to keyword-based theme extraction
            return self._extract_themes_fallback(text)
    
    async def analyze_sentiment(self, text: str) -> Dict[str, Any]:
        """Analyze sentiment of the input text.
        
        Args:
            text: Input text to analyze
            
        Returns:
            Dictionary with sentiment analysis results
        """
        try:
            prompt = f"""
            Analyze the sentiment of the following text. 
            Respond with only a JSON object containing:
            - "polarity": "positive", "negative", or "neutral"
            - "confidence": a number between 0 and 1
            - "emotion": primary emotion detected
            
            Text: {text}
            """
            
            response = await self.llm_service.generate_text(prompt)
            # Try to parse JSON response
            import json
            try:
                sentiment_data = json.loads(response)
                return sentiment_data
            except json.JSONDecodeError:
                # Fallback parsing
                return self._parse_sentiment_fallback(response)
                
        except Exception:
            # Fallback sentiment analysis
            return self._analyze_sentiment_fallback(text)
    
    def extract_keywords(self, text: str) -> List[str]:
        """Extract keywords from the input text.
        
        Args:
            text: Input text to analyze
            
        Returns:
            List of extracted keywords
        """
        # Simple keyword extraction using regex
        words = re.findall(r'\b[a-zA-Z]{3,}\b', text.lower())
        
        # Filter out common stop words
        stop_words = {
            'the', 'and', 'or', 'but', 'in', 'on', 'at', 'to', 'for', 'of', 'with',
            'by', 'from', 'up', 'about', 'into', 'through', 'during', 'before',
            'after', 'above', 'below', 'between', 'among', 'this', 'that', 'these',
            'those', 'are', 'was', 'were', 'been', 'being', 'have', 'has', 'had',
            'will', 'would', 'could', 'should', 'may', 'might', 'can', 'must'
        }
        
        keywords = [word for word in words if word not in stop_words]
        
        # Count frequency and return top keywords
        from collections import Counter
        word_counts = Counter(keywords)
        return [word for word, count in word_counts.most_common(10)]
    
    def identify_content_type(self, text: str) -> str:
        """Identify the type of content based on input text.
        
        Args:
            text: Input text to analyze
            
        Returns:
            Identified content type
        """
        text_lower = text.lower()
        
        # Check for specific content type indicators
        if any(word in text_lower for word in ['blog', 'article', 'post', 'tutorial']):
            return 'blog_post'
        elif any(word in text_lower for word in ['social', 'tweet', 'instagram', 'facebook']):
            return 'social_media'
        elif any(word in text_lower for word in ['email', 'newsletter', 'campaign']):
            return 'email_marketing'
        elif any(word in text_lower for word in ['product', 'description', 'feature']):
            return 'product_content'
        elif any(word in text_lower for word in ['news', 'announcement', 'press']):
            return 'news_content'
        else:
            return 'general_content'
    
    async def identify_target_audience(self, text: str) -> Dict[str, Any]:
        """Identify target audience characteristics.
        
        Args:
            text: Input text to analyze
            
        Returns:
            Dictionary with target audience information
        """
        try:
            prompt = f"""
            Based on the following text, identify the target audience.
            Respond with only a JSON object containing:
            - "demographics": age group, profession, interests
            - "tone_preference": formal, casual, technical, friendly
            - "expertise_level": beginner, intermediate, advanced
            
            Text: {text}
            """
            
            response = await self.llm_service.generate_text(prompt)
            import json
            try:
                audience_data = json.loads(response)
                return audience_data
            except json.JSONDecodeError:
                return self._identify_audience_fallback(text)
                
        except Exception:
            return self._identify_audience_fallback(text)
    
    def _extract_themes_fallback(self, text: str) -> List[str]:
        """Fallback theme extraction using keyword analysis."""
        keywords = self.extract_keywords(text)
        # Group related keywords as themes
        return keywords[:3]  # Return top 3 keywords as themes
    
    def _analyze_sentiment_fallback(self, text: str) -> Dict[str, Any]:
        """Fallback sentiment analysis using simple word matching."""
        positive_words = ['good', 'great', 'excellent', 'amazing', 'wonderful', 'fantastic']
        negative_words = ['bad', 'terrible', 'awful', 'horrible', 'disappointing', 'poor']
        
        text_lower = text.lower()
        positive_count = sum(1 for word in positive_words if word in text_lower)
        negative_count = sum(1 for word in negative_words if word in text_lower)
        
        if positive_count > negative_count:
            return {"polarity": "positive", "confidence": 0.6, "emotion": "optimistic"}
        elif negative_count > positive_count:
            return {"polarity": "negative", "confidence": 0.6, "emotion": "critical"}
        else:
            return {"polarity": "neutral", "confidence": 0.5, "emotion": "neutral"}
    
    def _parse_sentiment_fallback(self, response: str) -> Dict[str, Any]:
        """Parse sentiment from non-JSON response."""
        response_lower = response.lower()
        
        if 'positive' in response_lower:
            polarity = 'positive'
        elif 'negative' in response_lower:
            polarity = 'negative'
        else:
            polarity = 'neutral'
            
        return {"polarity": polarity, "confidence": 0.7, "emotion": "unknown"}
    
    def _identify_audience_fallback(self, text: str) -> Dict[str, Any]:
        """Fallback audience identification."""
        text_lower = text.lower()
        
        # Simple heuristics for audience identification
        if any(word in text_lower for word in ['technical', 'api', 'code', 'development']):
            expertise = 'advanced'
            tone = 'technical'
        elif any(word in text_lower for word in ['beginner', 'introduction', 'basics']):
            expertise = 'beginner'
            tone = 'friendly'
        else:
            expertise = 'intermediate'
            tone = 'casual'
            
        return {
            "demographics": "general audience",
            "tone_preference": tone,
            "expertise_level": expertise
        }
    
    async def validate(self, state: ContentState) -> bool:
        """Validate that input analysis can be performed.
        
        Args:
            state: Current content state
            
        Returns:
            True if validation passes
        """
        return bool(state.original_input and state.original_input.get("text"))