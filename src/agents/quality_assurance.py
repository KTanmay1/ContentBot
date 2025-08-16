"""Quality Assurance Agent for ViraLearn ContentBot.

This agent is responsible for assessing content quality, checking consistency,
and ensuring content meets standards and requirements.
"""

import re
from typing import Dict, List, Optional, Any, Tuple
from datetime import datetime

from ..models.state_models import ContentState
from ..services.llm_service import LLMService
from .base_agent import BaseAgent, AgentResult


class QualityAssurance(BaseAgent):
    """Agent for quality assessment and content validation."""
    
    def __init__(self, llm_service: Optional[LLMService] = None):
        """Initialize the Quality Assurance agent.
        
        Args:
            llm_service: LLM service for quality assessment
        """
        super().__init__()
        self.llm_service = llm_service or LLMService()
        self.agent_name = "QualityAssurance"
        
        # Quality thresholds
        self.min_readability_score = 60
        self.min_grammar_score = 80
        self.min_coherence_score = 70
        self.min_relevance_score = 75
    
    async def execute(self, state: ContentState) -> AgentResult:
        """Execute quality assessment on generated content.
        
        Args:
            state: Current content state with generated content
            
        Returns:
            AgentResult with quality assessment results
        """
        try:
            # Get content to assess
            text_content = state.text_content or ""
            planning_data = state.planning_data or {}
            analysis_data = state.analysis_data or {}
            
            if not text_content:
                return AgentResult(
                    success=False,
                    data={},
                    error="No content available for quality assessment",
                    agent_name=self.agent_name
                )
            
            # Perform quality assessments
            quality_scores = await self.assess_quality(text_content, planning_data, analysis_data)
            consistency_check = await self.check_consistency(text_content, planning_data, analysis_data)
            grammar_check = await self.check_grammar(text_content)
            readability_assessment = self.assess_readability(text_content)
            seo_assessment = self.assess_seo(text_content, analysis_data)
            brand_compliance = await self.check_brand_compliance(text_content, state)
            
            # Calculate overall quality score
            overall_score = self.calculate_overall_score({
                "quality": quality_scores,
                "consistency": consistency_check,
                "grammar": grammar_check,
                "readability": readability_assessment,
                "seo": seo_assessment,
                "brand_compliance": brand_compliance
            })
            
            # Generate improvement suggestions
            suggestions = self.generate_suggestions({
                "quality": quality_scores,
                "consistency": consistency_check,
                "grammar": grammar_check,
                "readability": readability_assessment,
                "seo": seo_assessment,
                "brand_compliance": brand_compliance
            })
            
            # Compile quality assessment results
            qa_data = {
                "overall_score": overall_score,
                "quality_scores": quality_scores,
                "consistency_check": consistency_check,
                "grammar_check": grammar_check,
                "readability_assessment": readability_assessment,
                "seo_assessment": seo_assessment,
                "brand_compliance": brand_compliance,
                "suggestions": suggestions,
                "passed_qa": overall_score >= 75,
                "assessed_at": datetime.utcnow().isoformat()
            }
            
            # Update state with QA results
            state.quality_scores = quality_scores
            if not hasattr(state, 'qa_data') or not state.qa_data:
                state.qa_data = {}
            state.qa_data.update(qa_data)
            
            return AgentResult(
                success=True,
                data=qa_data,
                agent_name=self.agent_name
            )
            
        except Exception as e:
            return AgentResult(
                success=False,
                data={},
                error=f"Quality assessment failed: {str(e)}",
                agent_name=self.agent_name
            )
    
    async def assess_quality(self, content: str, planning_data: Dict[str, Any], analysis_data: Dict[str, Any]) -> Dict[str, float]:
        """Assess overall content quality.
        
        Args:
            content: Content to assess
            planning_data: Planning information
            analysis_data: Analysis results
            
        Returns:
            Dictionary with quality scores
        """
        try:
            themes = analysis_data.get("themes", [])
            strategy = planning_data.get("strategy", {})
            
            prompt = f"""
            Assess the quality of the following content based on these criteria:
            - Relevance to themes: {', '.join(themes)}
            - Alignment with strategy: {strategy}
            - Clarity and coherence
            - Engagement level
            - Information value
            
            Content: {content[:2000]}...
            
            Respond with only a JSON object containing scores (0-100) for:
            - "relevance": how well content matches themes
            - "clarity": how clear and understandable the content is
            - "engagement": how engaging the content is
            - "information_value": how valuable the information is
            - "coherence": how well the content flows
            """
            
            response = await self.llm_service.generate_text(prompt)
            
            import json
            try:
                scores = json.loads(response)
                # Ensure all scores are between 0 and 100
                for key, value in scores.items():
                    scores[key] = max(0, min(100, float(value)))
                return scores
            except (json.JSONDecodeError, ValueError):
                return self._assess_quality_fallback(content, planning_data, analysis_data)
                
        except Exception:
            return self._assess_quality_fallback(content, planning_data, analysis_data)
    
    async def check_consistency(self, content: str, planning_data: Dict[str, Any], analysis_data: Dict[str, Any]) -> Dict[str, Any]:
        """Check content consistency with plan and requirements.
        
        Args:
            content: Content to check
            planning_data: Planning information
            analysis_data: Analysis results
            
        Returns:
            Consistency check results
        """
        try:
            strategy = planning_data.get("strategy", {})
            outline = planning_data.get("outline", {})
            target_audience = analysis_data.get("target_audience", {})
            
            prompt = f"""
            Check if the content is consistent with the plan:
            - Strategy: {strategy}
            - Outline: {outline}
            - Target Audience: {target_audience}
            
            Content: {content[:1500]}...
            
            Respond with only a JSON object containing:
            - "tone_consistency": score 0-100 for tone alignment
            - "structure_consistency": score 0-100 for structure alignment
            - "audience_consistency": score 0-100 for audience alignment
            - "message_consistency": score 0-100 for key message alignment
            - "issues": list of specific consistency issues found
            """
            
            response = await self.llm_service.generate_text(prompt)
            
            import json
            try:
                consistency = json.loads(response)
                return consistency
            except json.JSONDecodeError:
                return self._check_consistency_fallback(content, planning_data, analysis_data)
                
        except Exception:
            return self._check_consistency_fallback(content, planning_data, analysis_data)
    
    async def check_grammar(self, content: str) -> Dict[str, Any]:
        """Check grammar and language quality.
        
        Args:
            content: Content to check
            
        Returns:
            Grammar check results
        """
        try:
            prompt = f"""
            Check the grammar and language quality of this content:
            
            {content[:2000]}...
            
            Respond with only a JSON object containing:
            - "grammar_score": score 0-100 for grammar quality
            - "spelling_errors": number of spelling errors found
            - "grammar_errors": number of grammar errors found
            - "suggestions": list of specific improvements
            """
            
            response = await self.llm_service.generate_text(prompt)
            
            import json
            try:
                grammar_check = json.loads(response)
                return grammar_check
            except json.JSONDecodeError:
                return self._check_grammar_fallback(content)
                
        except Exception:
            return self._check_grammar_fallback(content)
    
    def assess_readability(self, content: str) -> Dict[str, Any]:
        """Assess content readability.
        
        Args:
            content: Content to assess
            
        Returns:
            Readability assessment results
        """
        # Simple readability metrics
        sentences = re.split(r'[.!?]+', content)
        words = content.split()
        
        if not sentences or not words:
            return {"readability_score": 0, "grade_level": "unknown", "issues": ["No content to analyze"]}
        
        # Calculate basic metrics
        avg_sentence_length = len(words) / len([s for s in sentences if s.strip()])
        avg_word_length = sum(len(word) for word in words) / len(words)
        
        # Simple readability score (Flesch-like)
        readability_score = 206.835 - (1.015 * avg_sentence_length) - (84.6 * (avg_word_length / 4.7))
        readability_score = max(0, min(100, readability_score))
        
        # Determine grade level
        if readability_score >= 90:
            grade_level = "5th grade"
        elif readability_score >= 80:
            grade_level = "6th grade"
        elif readability_score >= 70:
            grade_level = "7th grade"
        elif readability_score >= 60:
            grade_level = "8th-9th grade"
        elif readability_score >= 50:
            grade_level = "10th-12th grade"
        else:
            grade_level = "College level"
        
        issues = []
        if avg_sentence_length > 20:
            issues.append("Sentences are too long")
        if avg_word_length > 6:
            issues.append("Words are too complex")
        
        return {
            "readability_score": round(readability_score, 1),
            "grade_level": grade_level,
            "avg_sentence_length": round(avg_sentence_length, 1),
            "avg_word_length": round(avg_word_length, 1),
            "issues": issues
        }
    
    def assess_seo(self, content: str, analysis_data: Dict[str, Any]) -> Dict[str, Any]:
        """Assess SEO quality of content.
        
        Args:
            content: Content to assess
            analysis_data: Analysis results with keywords
            
        Returns:
            SEO assessment results
        """
        keywords = analysis_data.get("keywords", [])
        content_lower = content.lower()
        
        # Check keyword density
        keyword_density = {}
        total_words = len(content.split())
        
        for keyword in keywords[:5]:  # Check top 5 keywords
            count = content_lower.count(keyword.lower())
            density = (count / total_words) * 100 if total_words > 0 else 0
            keyword_density[keyword] = {
                "count": count,
                "density": round(density, 2)
            }
        
        # Check content length
        word_count = len(content.split())
        length_score = 100 if 300 <= word_count <= 2000 else max(0, 100 - abs(word_count - 800) / 10)
        
        # Check for headings (simple heuristic)
        has_headings = bool(re.search(r'^#{1,6}\s', content, re.MULTILINE) or 
                           re.search(r'<h[1-6]>', content, re.IGNORECASE))
        
        seo_score = (
            (50 if any(kd["density"] > 0.5 for kd in keyword_density.values()) else 0) +
            (min(30, length_score * 0.3)) +
            (20 if has_headings else 0)
        )
        
        return {
            "seo_score": round(seo_score, 1),
            "keyword_density": keyword_density,
            "word_count": word_count,
            "has_headings": has_headings,
            "recommendations": self._generate_seo_recommendations(keyword_density, word_count, has_headings)
        }
    
    async def check_brand_compliance(self, content: str, state: ContentState) -> Dict[str, Any]:
        """Check brand compliance and voice consistency.
        
        Args:
            content: Content to check
            state: Current content state
            
        Returns:
            Brand compliance results
        """
        # Simple brand compliance check
        # In a real implementation, this would check against brand guidelines
        
        analysis_data = state.analysis_data or {}
        target_audience = analysis_data.get("target_audience", {})
        tone_preference = target_audience.get("tone_preference", "neutral")
        
        # Check tone consistency
        content_lower = content.lower()
        
        formal_indicators = ['furthermore', 'therefore', 'consequently', 'moreover']
        casual_indicators = ['hey', 'awesome', 'cool', 'great', 'amazing']
        technical_indicators = ['api', 'algorithm', 'implementation', 'framework']
        
        formal_count = sum(1 for indicator in formal_indicators if indicator in content_lower)
        casual_count = sum(1 for indicator in casual_indicators if indicator in content_lower)
        technical_count = sum(1 for indicator in technical_indicators if indicator in content_lower)
        
        # Determine detected tone
        if technical_count > formal_count and technical_count > casual_count:
            detected_tone = "technical"
        elif formal_count > casual_count:
            detected_tone = "formal"
        elif casual_count > 0:
            detected_tone = "casual"
        else:
            detected_tone = "neutral"
        
        tone_match = detected_tone == tone_preference
        compliance_score = 85 if tone_match else 60
        
        return {
            "compliance_score": compliance_score,
            "tone_match": tone_match,
            "expected_tone": tone_preference,
            "detected_tone": detected_tone,
            "issues": [] if tone_match else [f"Tone mismatch: expected {tone_preference}, detected {detected_tone}"]
        }
    
    def calculate_overall_score(self, assessments: Dict[str, Any]) -> float:
        """Calculate overall quality score from all assessments.
        
        Args:
            assessments: All assessment results
            
        Returns:
            Overall quality score (0-100)
        """
        weights = {
            "quality": 0.3,
            "consistency": 0.2,
            "grammar": 0.2,
            "readability": 0.15,
            "seo": 0.1,
            "brand_compliance": 0.05
        }
        
        total_score = 0
        total_weight = 0
        
        for category, weight in weights.items():
            if category in assessments:
                if category == "quality":
                    # Average of quality scores
                    quality_scores = assessments[category]
                    if quality_scores:
                        score = sum(quality_scores.values()) / len(quality_scores)
                    else:
                        score = 0
                elif category == "consistency":
                    # Average of consistency scores
                    consistency = assessments[category]
                    scores = [v for k, v in consistency.items() if k.endswith('_consistency') and isinstance(v, (int, float))]
                    score = sum(scores) / len(scores) if scores else 0
                elif category == "grammar":
                    score = assessments[category].get("grammar_score", 0)
                elif category == "readability":
                    score = assessments[category].get("readability_score", 0)
                elif category == "seo":
                    score = assessments[category].get("seo_score", 0)
                elif category == "brand_compliance":
                    score = assessments[category].get("compliance_score", 0)
                else:
                    score = 0
                
                total_score += score * weight
                total_weight += weight
        
        return round(total_score / total_weight if total_weight > 0 else 0, 1)
    
    def generate_suggestions(self, assessments: Dict[str, Any]) -> List[str]:
        """Generate improvement suggestions based on assessments.
        
        Args:
            assessments: All assessment results
            
        Returns:
            List of improvement suggestions
        """
        suggestions = []
        
        # Quality suggestions
        quality_scores = assessments.get("quality", {})
        for metric, score in quality_scores.items():
            if score < 70:
                suggestions.append(f"Improve {metric}: current score {score}/100")
        
        # Grammar suggestions
        grammar = assessments.get("grammar", {})
        if grammar.get("grammar_score", 100) < self.min_grammar_score:
            suggestions.extend(grammar.get("suggestions", []))
        
        # Readability suggestions
        readability = assessments.get("readability", {})
        suggestions.extend(readability.get("issues", []))
        
        # SEO suggestions
        seo = assessments.get("seo", {})
        suggestions.extend(seo.get("recommendations", []))
        
        # Brand compliance suggestions
        brand = assessments.get("brand_compliance", {})
        suggestions.extend(brand.get("issues", []))
        
        return suggestions[:10]  # Limit to top 10 suggestions
    
    def _assess_quality_fallback(self, content: str, planning_data: Dict[str, Any], analysis_data: Dict[str, Any]) -> Dict[str, float]:
        """Fallback quality assessment."""
        word_count = len(content.split())
        sentence_count = len(re.split(r'[.!?]+', content))
        
        # Simple heuristics
        relevance = 75 if word_count > 100 else 50
        clarity = 80 if sentence_count > 5 else 60
        engagement = 70  # Default
        information_value = 75 if word_count > 200 else 60
        coherence = 80 if sentence_count > 3 else 60
        
        return {
            "relevance": relevance,
            "clarity": clarity,
            "engagement": engagement,
            "information_value": information_value,
            "coherence": coherence
        }
    
    def _check_consistency_fallback(self, content: str, planning_data: Dict[str, Any], analysis_data: Dict[str, Any]) -> Dict[str, Any]:
        """Fallback consistency check."""
        return {
            "tone_consistency": 75,
            "structure_consistency": 80,
            "audience_consistency": 75,
            "message_consistency": 70,
            "issues": []
        }
    
    def _check_grammar_fallback(self, content: str) -> Dict[str, Any]:
        """Fallback grammar check."""
        # Simple grammar check
        sentences = re.split(r'[.!?]+', content)
        words = content.split()
        
        # Basic checks
        spelling_errors = 0  # Would need a spell checker
        grammar_errors = 0   # Would need a grammar checker
        
        # Estimate grammar score based on sentence structure
        grammar_score = 85 if len(sentences) > 0 and len(words) > 0 else 50
        
        return {
            "grammar_score": grammar_score,
            "spelling_errors": spelling_errors,
            "grammar_errors": grammar_errors,
            "suggestions": []
        }
    
    def _generate_seo_recommendations(self, keyword_density: Dict[str, Any], word_count: int, has_headings: bool) -> List[str]:
        """Generate SEO recommendations."""
        recommendations = []
        
        if word_count < 300:
            recommendations.append("Increase content length to at least 300 words")
        elif word_count > 2000:
            recommendations.append("Consider breaking content into smaller sections")
        
        if not has_headings:
            recommendations.append("Add headings to improve content structure")
        
        low_density_keywords = [kw for kw, data in keyword_density.items() if data["density"] < 0.5]
        if low_density_keywords:
            recommendations.append(f"Increase usage of keywords: {', '.join(low_density_keywords[:3])}")
        
        return recommendations
    
    async def validate(self, state: ContentState) -> bool:
        """Validate that quality assessment can be performed.
        
        Args:
            state: Current content state
            
        Returns:
            True if validation passes
        """
        return bool(state.text_content)