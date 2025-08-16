"""Validators for shared state and inputs."""

from __future__ import annotations

import re
from typing import Any, Dict, List, Optional, Union
from urllib.parse import urlparse

from src.core.error_handling import ValidationException
from src.models.state_models import ContentState, WorkflowStatus


def validate_content_state(state: ContentState) -> None:
    if not state.workflow_id or not isinstance(state.workflow_id, str):
        raise ValidationException("`workflow_id` must be a non-empty string")

    # Allow either enum or its string value (due to use_enum_values in model).
    if not (
        isinstance(state.status, WorkflowStatus)
        or (isinstance(state.status, str) and state.status in {m.value for m in WorkflowStatus})
    ):
        raise ValidationException("`status` must be a WorkflowStatus or its value string")

    if state.step_count < 0:
        raise ValidationException("`step_count` must be >= 0")

    if not isinstance(state.original_input, dict):
        raise ValidationException("`original_input` must be a dict of input fields")


def ensure_field_present(container: dict[str, Any], field_name: str) -> None:
    if field_name not in container:
        raise ValidationException(f"Missing required field: {field_name}")


def validate_email(email: str) -> bool:
    """Validate email format.
    
    Args:
        email: Email address to validate
        
    Returns:
        True if email is valid
        
    Raises:
        ValidationException: If email format is invalid
    """
    if not email or not isinstance(email, str):
        raise ValidationException("Email must be a non-empty string")
    
    email_pattern = r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$'
    if not re.match(email_pattern, email):
        raise ValidationException(f"Invalid email format: {email}")
    
    return True


def validate_url(url: str, require_https: bool = False) -> bool:
    """Validate URL format.
    
    Args:
        url: URL to validate
        require_https: Whether to require HTTPS protocol
        
    Returns:
        True if URL is valid
        
    Raises:
        ValidationException: If URL format is invalid
    """
    if not url or not isinstance(url, str):
        raise ValidationException("URL must be a non-empty string")
    
    try:
        parsed = urlparse(url)
        if not parsed.scheme or not parsed.netloc:
            raise ValidationException(f"Invalid URL format: {url}")
        
        if require_https and parsed.scheme != 'https':
            raise ValidationException(f"URL must use HTTPS: {url}")
        
        if parsed.scheme not in ['http', 'https']:
            raise ValidationException(f"URL must use HTTP or HTTPS: {url}")
        
    except Exception as e:
        raise ValidationException(f"Invalid URL: {url} - {str(e)}")
    
    return True


def validate_text_length(text: str, min_length: int = 0, max_length: int = 10000, field_name: str = "text") -> bool:
    """Validate text length constraints.
    
    Args:
        text: Text to validate
        min_length: Minimum allowed length
        max_length: Maximum allowed length
        field_name: Name of the field for error messages
        
    Returns:
        True if text length is valid
        
    Raises:
        ValidationException: If text length is invalid
    """
    if not isinstance(text, str):
        raise ValidationException(f"{field_name} must be a string")
    
    text_length = len(text.strip())
    
    if text_length < min_length:
        raise ValidationException(f"{field_name} must be at least {min_length} characters long")
    
    if text_length > max_length:
        raise ValidationException(f"{field_name} must be no more than {max_length} characters long")
    
    return True


def validate_workflow_input(input_data: Dict[str, Any]) -> bool:
    """Validate workflow input data.
    
    Args:
        input_data: Input data to validate
        
    Returns:
        True if input is valid
        
    Raises:
        ValidationException: If input is invalid
    """
    if not isinstance(input_data, dict):
        raise ValidationException("Input data must be a dictionary")
    
    # Check for required fields
    required_fields = ['text_content']
    for field in required_fields:
        if field not in input_data:
            raise ValidationException(f"Missing required field: {field}")
    
    # Validate text content
    text_content = input_data.get('text_content', '')
    validate_text_length(text_content, min_length=1, max_length=50000, field_name="text_content")
    
    # Validate optional fields
    if 'user_id' in input_data:
        user_id = input_data['user_id']
        if not isinstance(user_id, str) or not user_id.strip():
            raise ValidationException("user_id must be a non-empty string")
    
    if 'content_type' in input_data:
        content_type = input_data['content_type']
        valid_types = ['blog_post', 'social_post', 'article', 'email', 'press_release', 'general']
        if content_type not in valid_types:
            raise ValidationException(f"content_type must be one of: {', '.join(valid_types)}")
    
    if 'target_audience' in input_data:
        target_audience = input_data['target_audience']
        validate_text_length(target_audience, min_length=1, max_length=500, field_name="target_audience")
    
    if 'platform' in input_data:
        platform = input_data['platform']
        valid_platforms = ['twitter', 'facebook', 'linkedin', 'instagram', 'blog', 'email', 'general']
        if platform not in valid_platforms:
            raise ValidationException(f"platform must be one of: {', '.join(valid_platforms)}")
    
    if 'priority' in input_data:
        priority = input_data['priority']
        valid_priorities = ['low', 'medium', 'high', 'urgent']
        if priority not in valid_priorities:
            raise ValidationException(f"priority must be one of: {', '.join(valid_priorities)}")
    
    return True


def validate_agent_result(result: Dict[str, Any]) -> bool:
    """Validate agent result structure.
    
    Args:
        result: Agent result to validate
        
    Returns:
        True if result is valid
        
    Raises:
        ValidationException: If result is invalid
    """
    if not isinstance(result, dict):
        raise ValidationException("Agent result must be a dictionary")
    
    # Check required fields
    required_fields = ['success', 'agent_name']
    for field in required_fields:
        if field not in result:
            raise ValidationException(f"Missing required field in agent result: {field}")
    
    # Validate success field
    if not isinstance(result['success'], bool):
        raise ValidationException("success field must be a boolean")
    
    # Validate agent_name
    if not isinstance(result['agent_name'], str) or not result['agent_name'].strip():
        raise ValidationException("agent_name must be a non-empty string")
    
    # Validate data field if present
    if 'data' in result and not isinstance(result['data'], dict):
        raise ValidationException("data field must be a dictionary")
    
    # Validate error field if present
    if 'error' in result and not isinstance(result['error'], str):
        raise ValidationException("error field must be a string")
    
    return True


def validate_quality_scores(scores: Dict[str, Any]) -> bool:
    """Validate quality scores structure.
    
    Args:
        scores: Quality scores to validate
        
    Returns:
        True if scores are valid
        
    Raises:
        ValidationException: If scores are invalid
    """
    if not isinstance(scores, dict):
        raise ValidationException("Quality scores must be a dictionary")
    
    # Validate score values
    for key, value in scores.items():
        if isinstance(value, dict):
            # Nested scores (e.g., grammar_check)
            validate_quality_scores(value)
        elif isinstance(value, (int, float)):
            # Individual score
            if not 0 <= value <= 100:
                raise ValidationException(f"Score {key} must be between 0 and 100, got {value}")
        elif not isinstance(value, (str, bool, list)):
            # Allow strings, booleans, and lists for metadata
            raise ValidationException(f"Invalid score type for {key}: {type(value)}")
    
    return True


def validate_content_metadata(metadata: Dict[str, Any]) -> bool:
    """Validate content metadata structure.
    
    Args:
        metadata: Content metadata to validate
        
    Returns:
        True if metadata is valid
        
    Raises:
        ValidationException: If metadata is invalid
    """
    if not isinstance(metadata, dict):
        raise ValidationException("Content metadata must be a dictionary")
    
    # Validate optional fields
    if 'keywords' in metadata:
        keywords = metadata['keywords']
        if not isinstance(keywords, list):
            raise ValidationException("keywords must be a list")
        for keyword in keywords:
            if not isinstance(keyword, str):
                raise ValidationException("All keywords must be strings")
    
    if 'tags' in metadata:
        tags = metadata['tags']
        if not isinstance(tags, list):
            raise ValidationException("tags must be a list")
        for tag in tags:
            if not isinstance(tag, str):
                raise ValidationException("All tags must be strings")
    
    if 'sentiment' in metadata:
        sentiment = metadata['sentiment']
        valid_sentiments = ['positive', 'negative', 'neutral']
        if sentiment not in valid_sentiments:
            raise ValidationException(f"sentiment must be one of: {', '.join(valid_sentiments)}")
    
    if 'confidence_score' in metadata:
        confidence = metadata['confidence_score']
        if not isinstance(confidence, (int, float)) or not 0 <= confidence <= 1:
            raise ValidationException("confidence_score must be a number between 0 and 1")
    
    return True


def validate_file_upload(file_data: Dict[str, Any]) -> bool:
    """Validate file upload data.
    
    Args:
        file_data: File upload data to validate
        
    Returns:
        True if file data is valid
        
    Raises:
        ValidationException: If file data is invalid
    """
    if not isinstance(file_data, dict):
        raise ValidationException("File data must be a dictionary")
    
    # Check required fields
    required_fields = ['filename', 'content_type']
    for field in required_fields:
        if field not in file_data:
            raise ValidationException(f"Missing required field: {field}")
    
    # Validate filename
    filename = file_data['filename']
    if not isinstance(filename, str) or not filename.strip():
        raise ValidationException("filename must be a non-empty string")
    
    # Validate content type
    content_type = file_data['content_type']
    allowed_types = [
        'image/jpeg', 'image/png', 'image/gif', 'image/webp',
        'text/plain', 'text/csv', 'application/json',
        'application/pdf', 'application/msword',
        'application/vnd.openxmlformats-officedocument.wordprocessingml.document'
    ]
    
    if content_type not in allowed_types:
        raise ValidationException(f"Unsupported content type: {content_type}")
    
    # Validate file size if present
    if 'size' in file_data:
        size = file_data['size']
        if not isinstance(size, int) or size <= 0:
            raise ValidationException("File size must be a positive integer")
        
        # 10MB limit
        max_size = 10 * 1024 * 1024
        if size > max_size:
            raise ValidationException(f"File size exceeds maximum allowed size of {max_size} bytes")
    
    return True


def sanitize_input(text: str) -> str:
    """Sanitize input text by removing potentially harmful content.
    
    Args:
        text: Text to sanitize
        
    Returns:
        Sanitized text
    """
    if not isinstance(text, str):
        return str(text)
    
    # Remove potential script tags and other dangerous content
    dangerous_patterns = [
        r'<script[^>]*>.*?</script>',
        r'<iframe[^>]*>.*?</iframe>',
        r'javascript:',
        r'vbscript:',
        r'onload=',
        r'onerror=',
        r'onclick='
    ]
    
    sanitized = text
    for pattern in dangerous_patterns:
        sanitized = re.sub(pattern, '', sanitized, flags=re.IGNORECASE | re.DOTALL)
    
    # Normalize whitespace
    sanitized = re.sub(r'\s+', ' ', sanitized).strip()
    
    return sanitized


def validate_api_key(api_key: str, service_name: str = "service") -> bool:
    """Validate API key format.
    
    Args:
        api_key: API key to validate
        service_name: Name of the service for error messages
        
    Returns:
        True if API key is valid
        
    Raises:
        ValidationException: If API key is invalid
    """
    if not api_key or not isinstance(api_key, str):
        raise ValidationException(f"{service_name} API key must be a non-empty string")
    
    # Basic format validation (adjust based on specific service requirements)
    if len(api_key.strip()) < 10:
        raise ValidationException(f"{service_name} API key appears to be too short")
    
    # Check for common invalid patterns
    invalid_patterns = ['your_api_key', 'api_key_here', 'replace_me', 'test_key']
    if api_key.lower() in invalid_patterns:
        raise ValidationException(f"{service_name} API key appears to be a placeholder")
    
    return True