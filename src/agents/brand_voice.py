"""Brand voice agent for ensuring content compliance and consistency."""

from typing import Dict, Any, List, Optional
import json

from .base_agent import BaseAgent
from src.models.state_models import ContentState, WorkflowStatus
from src.services.llm_service import LLMService
from src.core.error_handling import AgentException, ValidationException
from src.core.monitoring import get_monitoring


class BrandVoice(BaseAgent):
    """Agent for ensuring brand voice compliance and consistency."""
    
    name = "BrandVoice"
    
    def __init__(self):
        self.llm_service = LLMService()
        self._brand_guidelines = None
        self._voice_patterns = None
    
    def before_execute(self, state: ContentState) -> None:
        """Pre-execution setup."""
        self._load_brand_guidelines(state)
    
    def execute(self, state: ContentState) -> ContentState:
        """Execute brand voice analysis and compliance checking."""
        monitoring = get_monitoring(state.workflow_id)
        monitoring.info("brand_voice_start", workflow_id=state.workflow_id)
        
        try:
            # Analyze brand compliance for text content
            if state.text_content:
                compliance_results = self._analyze_brand_compliance(state)
                state.brand_compliance = compliance_results
                
                # Apply brand voice corrections if needed
                if compliance_results.get('needs_correction', False):
                    corrected_content = self._apply_brand_corrections(state)
                    if corrected_content:
                        state.text_content = corrected_content
                        monitoring.info("brand_voice_corrections_applied")
            
            # Analyze brand compliance for image content
            if state.image_content:
                image_compliance = self._analyze_image_brand_compliance(state)
                if not hasattr(state, 'brand_compliance'):
                    state.brand_compliance = {}
                state.brand_compliance['image_compliance'] = image_compliance
            
            # Generate brand voice score
            brand_score = self._calculate_brand_score(state)
            state.quality_scores = state.quality_scores or {}
            state.quality_scores['brand_voice_score'] = brand_score
            
            state.current_agent = "BrandVoice"
            state.step_count += 1
            
            monitoring.info("brand_voice_complete", 
                          brand_score=brand_score,
                          compliance_status=state.brand_compliance.get('status', 'unknown'))
            
            return state
            
        except Exception as e:
            monitoring.error("brand_voice_error", error=str(e))
            raise AgentException(f"Brand voice analysis failed: {str(e)}")
    
    def _load_brand_guidelines(self, state: ContentState) -> None:
        """Load brand guidelines from state or default configuration."""
        # Try to get brand guidelines from state
        if hasattr(state, 'brand_guidelines') and state.brand_guidelines:
            self._brand_guidelines = state.brand_guidelines
        else:
            # Load default brand guidelines
            self._brand_guidelines = self._get_default_brand_guidelines()
        
        # Extract voice patterns for analysis
        self._voice_patterns = self._extract_voice_patterns()
    
    def _get_default_brand_guidelines(self) -> Dict[str, Any]:
        """Get default brand guidelines."""
        return {
            "tone": {
                "primary": "professional",
                "secondary": "approachable",
                "avoid": ["overly casual", "aggressive", "jargon-heavy"]
            },
            "voice_characteristics": {
                "clarity": "high",
                "formality": "medium",
                "enthusiasm": "moderate",
                "expertise": "authoritative"
            },
            "language_preferences": {
                "person": "second_person",
                "active_voice": True,
                "sentence_length": "medium",
                "technical_terms": "explain_when_used"
            },
            "content_guidelines": {
                "call_to_action": "clear_and_specific",
                "value_proposition": "benefit_focused",
                "social_proof": "include_when_relevant"
            },
            "platform_adaptations": {
                "linkedin": {"formality": "high", "length": "detailed"},
                "twitter": {"formality": "medium", "length": "concise"},
                "instagram": {"formality": "low", "length": "engaging"},
                "facebook": {"formality": "medium", "length": "conversational"}
            }
        }
    
    def _extract_voice_patterns(self) -> Dict[str, Any]:
        """Extract voice patterns for analysis."""
        return {
            "tone_keywords": self._get_tone_keywords(),
            "style_indicators": self._get_style_indicators(),
            "compliance_rules": self._get_compliance_rules()
        }
    
    def _analyze_brand_compliance(self, state: ContentState) -> Dict[str, Any]:
        """Analyze content for brand compliance."""
        try:
            compliance_results = {
                "status": "compliant",
                "score": 0.0,
                "issues": [],
                "suggestions": [],
                "needs_correction": False
            }
            
            # Analyze each piece of text content
            for content_type, content in state.text_content.items():
                if isinstance(content, str):
                    analysis = self._analyze_text_compliance(content, content_type)
                    compliance_results[f"{content_type}_analysis"] = analysis
                    
                    # Update overall compliance
                    if analysis['score'] < 0.7:
                        compliance_results['needs_correction'] = True
                        compliance_results['status'] = "needs_review"
                    
                    compliance_results['issues'].extend(analysis.get('issues', []))
                    compliance_results['suggestions'].extend(analysis.get('suggestions', []))
                
                elif isinstance(content, dict):
                    # Handle platform-specific content
                    for platform, platform_content in content.items():
                        if isinstance(platform_content, str):
                            analysis = self._analyze_platform_compliance(
                                platform_content, platform, content_type
                            )
                            compliance_results[f"{content_type}_{platform}_analysis"] = analysis
            
            # Calculate overall compliance score
            compliance_results['score'] = self._calculate_compliance_score(compliance_results)
            
            return compliance_results
            
        except Exception as e:
            raise ValidationException(f"Brand compliance analysis failed: {str(e)}")
    
    def _analyze_text_compliance(self, text: str, content_type: str) -> Dict[str, Any]:
        """Analyze individual text for brand compliance."""
        analysis = {
            "score": 1.0,
            "issues": [],
            "suggestions": [],
            "tone_match": True,
            "style_match": True
        }
        
        # Check tone compliance
        tone_score = self._check_tone_compliance(text)
        analysis['tone_score'] = tone_score
        if tone_score < 0.7:
            analysis['tone_match'] = False
            analysis['issues'].append(f"Tone doesn't match brand guidelines for {content_type}")
            analysis['suggestions'].append("Adjust tone to be more professional and approachable")
        
        # Check style compliance
        style_score = self._check_style_compliance(text)
        analysis['style_score'] = style_score
        if style_score < 0.7:
            analysis['style_match'] = False
            analysis['issues'].append(f"Writing style needs adjustment for {content_type}")
            analysis['suggestions'].append("Use more active voice and clearer language")
        
        # Calculate overall score
        analysis['score'] = (tone_score + style_score) / 2
        
        return analysis
    
    def _analyze_platform_compliance(self, text: str, platform: str, content_type: str) -> Dict[str, Any]:
        """Analyze platform-specific content compliance."""
        platform_guidelines = self._brand_guidelines.get('platform_adaptations', {}).get(platform, {})
        
        analysis = self._analyze_text_compliance(text, f"{platform}_{content_type}")
        
        # Add platform-specific checks
        if platform_guidelines:
            platform_score = self._check_platform_specific_compliance(text, platform, platform_guidelines)
            analysis['platform_score'] = platform_score
            analysis['score'] = (analysis['score'] + platform_score) / 2
            
            if platform_score < 0.7:
                analysis['issues'].append(f"Content doesn't match {platform} platform guidelines")
                analysis['suggestions'].append(f"Adapt content for {platform} audience and format")
        
        return analysis
    
    def _apply_brand_corrections(self, state: ContentState) -> Optional[Dict[str, Any]]:
        """Apply brand voice corrections to content."""
        try:
            corrected_content = {}
            
            for content_type, content in state.text_content.items():
                if isinstance(content, str):
                    corrected = self._correct_text_content(content, content_type)
                    corrected_content[content_type] = corrected
                elif isinstance(content, dict):
                    corrected_content[content_type] = {}
                    for platform, platform_content in content.items():
                        if isinstance(platform_content, str):
                            corrected = self._correct_platform_content(
                                platform_content, platform, content_type
                            )
                            corrected_content[content_type][platform] = corrected
                        else:
                            corrected_content[content_type][platform] = platform_content
                else:
                    corrected_content[content_type] = content
            
            return corrected_content
            
        except Exception as e:
            get_monitoring(state.workflow_id).error("brand_correction_error", error=str(e))
            return None
    
    def _correct_text_content(self, text: str, content_type: str) -> str:
        """Correct text content for brand compliance."""
        correction_prompt = f"""
Please revise the following {content_type} to match our brand voice guidelines:

Brand Guidelines:
- Tone: {self._brand_guidelines['tone']['primary']} and {self._brand_guidelines['tone']['secondary']}
- Voice: {', '.join(f"{k}: {v}" for k, v in self._brand_guidelines['voice_characteristics'].items())}
- Language: {', '.join(f"{k}: {v}" for k, v in self._brand_guidelines['language_preferences'].items())}

Original Content:
{text}

Revised Content:"""
        
        try:
            response = self.llm_service.generate_content(
                prompt=correction_prompt,
                max_tokens=len(text.split()) * 2,  # Allow for expansion
                temperature=0.3  # Lower temperature for consistency
            )
            return response.strip()
        except Exception:
            # Return original if correction fails
            return text
    
    def _correct_platform_content(self, text: str, platform: str, content_type: str) -> str:
        """Correct platform-specific content."""
        platform_guidelines = self._brand_guidelines.get('platform_adaptations', {}).get(platform, {})
        
        correction_prompt = f"""
Please revise the following {content_type} for {platform} to match our brand voice and platform guidelines:

Brand Guidelines:
- Tone: {self._brand_guidelines['tone']['primary']} and {self._brand_guidelines['tone']['secondary']}
- Platform-specific: {', '.join(f"{k}: {v}" for k, v in platform_guidelines.items())}

Original Content:
{text}

Revised Content:"""
        
        try:
            response = self.llm_service.generate_content(
                prompt=correction_prompt,
                max_tokens=len(text.split()) * 2,
                temperature=0.3
            )
            return response.strip()
        except Exception:
            return text
    
    def _analyze_image_brand_compliance(self, state: ContentState) -> Dict[str, Any]:
        """Analyze image content for brand compliance."""
        # This would integrate with image analysis services
        # For now, return a placeholder analysis
        return {
            "status": "compliant",
            "score": 0.85,
            "visual_consistency": True,
            "brand_elements_present": True,
            "suggestions": []
        }
    
    def _calculate_brand_score(self, state: ContentState) -> float:
        """Calculate overall brand compliance score."""
        if not hasattr(state, 'brand_compliance') or not state.brand_compliance:
            return 0.5
        
        compliance = state.brand_compliance
        
        # Weight different aspects
        text_score = compliance.get('score', 0.5)
        image_score = compliance.get('image_compliance', {}).get('score', 0.8)
        
        # Calculate weighted average
        total_score = (text_score * 0.7) + (image_score * 0.3)
        
        return round(total_score, 2)
    
    def _check_tone_compliance(self, text: str) -> float:
        """Check tone compliance using keyword analysis."""
        # Simple keyword-based tone analysis
        # In production, this would use more sophisticated NLP
        
        positive_indicators = self._voice_patterns['tone_keywords']['positive']
        negative_indicators = self._voice_patterns['tone_keywords']['negative']
        
        text_lower = text.lower()
        positive_count = sum(1 for word in positive_indicators if word in text_lower)
        negative_count = sum(1 for word in negative_indicators if word in text_lower)
        
        if len(text.split()) == 0:
            return 0.5
        
        # Calculate tone score
        word_count = len(text.split())
        positive_ratio = positive_count / word_count
        negative_ratio = negative_count / word_count
        
        score = 0.5 + (positive_ratio * 2) - (negative_ratio * 2)
        return max(0.0, min(1.0, score))
    
    def _check_style_compliance(self, text: str) -> float:
        """Check writing style compliance."""
        # Simple style analysis
        sentences = text.split('.')
        if not sentences:
            return 0.5
        
        # Check average sentence length
        avg_sentence_length = sum(len(s.split()) for s in sentences if s.strip()) / len([s for s in sentences if s.strip()])
        
        # Prefer medium-length sentences (10-20 words)
        length_score = 1.0 if 10 <= avg_sentence_length <= 20 else 0.7
        
        # Check for active voice indicators
        active_voice_score = self._check_active_voice(text)
        
        return (length_score + active_voice_score) / 2
    
    def _check_platform_specific_compliance(self, text: str, platform: str, guidelines: Dict[str, Any]) -> float:
        """Check platform-specific compliance."""
        score = 1.0
        
        # Check length appropriateness
        word_count = len(text.split())
        length_pref = guidelines.get('length', 'medium')
        
        if length_pref == 'concise' and word_count > 50:
            score -= 0.2
        elif length_pref == 'detailed' and word_count < 100:
            score -= 0.2
        
        # Check formality level
        formality = guidelines.get('formality', 'medium')
        formality_score = self._check_formality_level(text, formality)
        
        return (score + formality_score) / 2
    
    def _check_active_voice(self, text: str) -> float:
        """Check for active voice usage."""
        # Simple heuristic for active voice
        passive_indicators = ['was', 'were', 'been', 'being', 'is being', 'are being']
        text_lower = text.lower()
        
        passive_count = sum(1 for indicator in passive_indicators if indicator in text_lower)
        sentence_count = len([s for s in text.split('.') if s.strip()])
        
        if sentence_count == 0:
            return 0.5
        
        passive_ratio = passive_count / sentence_count
        return max(0.0, 1.0 - passive_ratio)
    
    def _check_formality_level(self, text: str, target_formality: str) -> float:
        """Check formality level of text."""
        # Simple formality analysis
        formal_indicators = ['therefore', 'furthermore', 'consequently', 'moreover']
        informal_indicators = ['gonna', 'wanna', 'yeah', 'cool', 'awesome']
        
        text_lower = text.lower()
        formal_count = sum(1 for word in formal_indicators if word in text_lower)
        informal_count = sum(1 for word in informal_indicators if word in text_lower)
        
        if target_formality == 'high':
            return 1.0 if formal_count > informal_count else 0.7
        elif target_formality == 'low':
            return 1.0 if informal_count > formal_count else 0.7
        else:  # medium
            return 0.9 if abs(formal_count - informal_count) <= 1 else 0.7
    
    def _calculate_compliance_score(self, compliance_results: Dict[str, Any]) -> float:
        """Calculate overall compliance score from analysis results."""
        scores = []
        
        for key, value in compliance_results.items():
            if key.endswith('_analysis') and isinstance(value, dict):
                if 'score' in value:
                    scores.append(value['score'])
        
        return sum(scores) / len(scores) if scores else 0.5
    
    def _get_tone_keywords(self) -> Dict[str, List[str]]:
        """Get tone-related keywords for analysis."""
        return {
            "positive": [
                "professional", "clear", "helpful", "effective", "reliable",
                "innovative", "quality", "excellent", "trusted", "expert"
            ],
            "negative": [
                "cheap", "basic", "simple", "easy", "quick", "fast",
                "amazing", "incredible", "unbelievable", "revolutionary"
            ]
        }
    
    def _get_style_indicators(self) -> Dict[str, List[str]]:
        """Get style-related indicators."""
        return {
            "active_voice": ["we", "you", "our", "your", "will", "can", "do"],
            "passive_voice": ["was", "were", "been", "being", "is being"]
        }
    
    def _get_compliance_rules(self) -> Dict[str, Any]:
        """Get compliance rules for validation."""
        return {
            "max_sentence_length": 25,
            "min_sentence_length": 5,
            "preferred_sentence_length": 15,
            "max_paragraph_sentences": 5
        }
    
    def after_execute(self, state: ContentState) -> None:
        """Post-execution cleanup."""
        monitoring = get_monitoring(state.workflow_id)
        brand_score = state.quality_scores.get('brand_voice_score', 0) if state.quality_scores else 0
        monitoring.info("brand_voice_complete", 
                       workflow_id=state.workflow_id,
                       brand_score=brand_score)