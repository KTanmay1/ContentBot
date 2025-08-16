"""
Utility functions and formatters for ViraLearn ContentBot.
Provides helper functions for content processing, formatting, and common operations.
"""

import re
import hashlib
import uuid
import json
import logging
from typing import Dict, List, Optional, Any, Union
from datetime import datetime, timedelta
from pathlib import Path
import base64
import mimetypes
from urllib.parse import urlparse, quote

logger = logging.getLogger(__name__)


def generate_id(prefix: str = "vl") -> str:
    """Generate a unique ID with optional prefix."""
    timestamp = datetime.utcnow().strftime("%Y%m%d%H%M%S")
    random_part = str(uuid.uuid4())[:8]
    return f"{prefix}_{timestamp}_{random_part}"


def generate_hash(content: str, algorithm: str = "sha256") -> str:
    """Generate hash of content using specified algorithm."""
    if algorithm == "md5":
        return hashlib.md5(content.encode()).hexdigest()
    elif algorithm == "sha1":
        return hashlib.sha1(content.encode()).hexdigest()
    elif algorithm == "sha256":
        return hashlib.sha256(content.encode()).hexdigest()
    else:
        raise ValueError(f"Unsupported hash algorithm: {algorithm}")


def sanitize_filename(filename: str) -> str:
    """Sanitize filename for safe file system operations."""
    # Remove or replace unsafe characters
    filename = re.sub(r'[<>:"/\\|?*]', '_', filename)
    # Remove leading/trailing spaces and dots
    filename = filename.strip('. ')
    # Limit length
    if len(filename) > 255:
        name, ext = filename.rsplit('.', 1) if '.' in filename else (filename, '')
        filename = name[:255-len(ext)-1] + ('.' + ext if ext else '')
    return filename


def format_file_size(size_bytes: int) -> str:
    """Format file size in human-readable format."""
    if size_bytes == 0:
        return "0B"
    
    size_names = ["B", "KB", "MB", "GB", "TB"]
    i = 0
    while size_bytes >= 1024 and i < len(size_names) - 1:
        size_bytes /= 1024.0
        i += 1
    
    return f"{size_bytes:.1f}{size_names[i]}"


def get_mime_type(file_path: str) -> str:
    """Get MIME type for a file."""
    mime_type, _ = mimetypes.guess_type(file_path)
    return mime_type or "application/octet-stream"


def is_valid_url(url: str) -> bool:
    """Check if a string is a valid URL."""
    try:
        result = urlparse(url)
        return all([result.scheme, result.netloc])
    except:
        return False


def extract_domain(url: str) -> str:
    """Extract domain from URL."""
    try:
        return urlparse(url).netloc
    except:
        return ""


def format_timestamp(timestamp: Union[datetime, str], format_str: str = "%Y-%m-%d %H:%M:%S") -> str:
    """Format timestamp to string."""
    if isinstance(timestamp, str):
        try:
            timestamp = datetime.fromisoformat(timestamp.replace('Z', '+00:00'))
        except:
            return timestamp
    
    return timestamp.strftime(format_str)


def parse_timestamp(timestamp_str: str) -> Optional[datetime]:
    """Parse timestamp string to datetime object."""
    try:
        return datetime.fromisoformat(timestamp_str.replace('Z', '+00:00'))
    except:
        return None


def calculate_readability_score(text: str) -> float:
    """Calculate Flesch Reading Ease score."""
    sentences = len(re.findall(r'[.!?]+', text))
    words = len(text.split())
    syllables = len(re.findall(r'[aeiouy]+', text.lower()))
    
    if sentences == 0 or words == 0:
        return 0.0
    
    # Flesch Reading Ease formula
    score = 206.835 - (1.015 * (words / sentences)) - (84.6 * (syllables / words))
    return max(0.0, min(100.0, score))


def extract_hashtags(text: str) -> List[str]:
    """Extract hashtags from text."""
    hashtags = re.findall(r'#\w+', text)
    return [tag.lower() for tag in hashtags]


def extract_mentions(text: str) -> List[str]:
    """Extract mentions from text."""
    mentions = re.findall(r'@\w+', text)
    return [mention.lower() for mention in mentions]


def extract_urls(text: str) -> List[str]:
    """Extract URLs from text."""
    url_pattern = r'http[s]?://(?:[a-zA-Z]|[0-9]|[$-_@.&+]|[!*\\(\\),]|(?:%[0-9a-fA-F][0-9a-fA-F]))+'
    return re.findall(url_pattern, text)


def count_words(text: str) -> int:
    """Count words in text."""
    return len(text.split())


def count_characters(text: str) -> int:
    """Count characters in text (excluding whitespace)."""
    return len(text.replace(' ', ''))


def truncate_text(text: str, max_length: int, suffix: str = "...") -> str:
    """Truncate text to specified length."""
    if len(text) <= max_length:
        return text
    
    return text[:max_length - len(suffix)] + suffix


def clean_text(text: str) -> str:
    """Clean text by removing extra whitespace and normalizing."""
    # Remove extra whitespace
    text = re.sub(r'\s+', ' ', text)
    # Remove leading/trailing whitespace
    text = text.strip()
    # Normalize line breaks
    text = re.sub(r'\n\s*\n', '\n\n', text)
    return text


def extract_keywords(text: str, max_keywords: int = 10) -> List[str]:
    """Extract keywords from text using simple frequency analysis."""
    # Remove common words and punctuation
    stop_words = {
        'the', 'a', 'an', 'and', 'or', 'but', 'in', 'on', 'at', 'to', 'for', 'of', 'with', 'by',
        'is', 'are', 'was', 'were', 'be', 'been', 'being', 'have', 'has', 'had', 'do', 'does', 'did',
        'will', 'would', 'could', 'should', 'may', 'might', 'must', 'can', 'this', 'that', 'these', 'those'
    }
    
    # Clean and split text
    words = re.findall(r'\b\w+\b', text.lower())
    
    # Filter out stop words and short words
    words = [word for word in words if word not in stop_words and len(word) > 2]
    
    # Count frequency
    word_freq = {}
    for word in words:
        word_freq[word] = word_freq.get(word, 0) + 1
    
    # Sort by frequency and return top keywords
    sorted_words = sorted(word_freq.items(), key=lambda x: x[1], reverse=True)
    return [word for word, freq in sorted_words[:max_keywords]]


def format_duration(seconds: float) -> str:
    """Format duration in seconds to human-readable format."""
    if seconds < 60:
        return f"{seconds:.1f}s"
    elif seconds < 3600:
        minutes = seconds / 60
        return f"{minutes:.1f}m"
    else:
        hours = seconds / 3600
        return f"{hours:.1f}h"


def calculate_percentage(part: float, total: float) -> float:
    """Calculate percentage."""
    if total == 0:
        return 0.0
    return (part / total) * 100


def merge_dicts(dict1: Dict[str, Any], dict2: Dict[str, Any]) -> Dict[str, Any]:
    """Merge two dictionaries, with dict2 taking precedence."""
    result = dict1.copy()
    result.update(dict2)
    return result


def deep_merge_dicts(dict1: Dict[str, Any], dict2: Dict[str, Any]) -> Dict[str, Any]:
    """Deep merge two dictionaries."""
    result = dict1.copy()
    
    for key, value in dict2.items():
        if key in result and isinstance(result[key], dict) and isinstance(value, dict):
            result[key] = deep_merge_dicts(result[key], value)
        else:
            result[key] = value
    
    return result


def flatten_dict(d: Dict[str, Any], parent_key: str = '', sep: str = '.') -> Dict[str, Any]:
    """Flatten a nested dictionary."""
    items = []
    for k, v in d.items():
        new_key = f"{parent_key}{sep}{k}" if parent_key else k
        if isinstance(v, dict):
            items.extend(flatten_dict(v, new_key, sep=sep).items())
        else:
            items.append((new_key, v))
    return dict(items)


def safe_json_dumps(obj: Any, default: Any = None) -> str:
    """Safely serialize object to JSON string."""
    try:
        return json.dumps(obj, default=default or str)
    except Exception as e:
        logger.warning(f"Failed to serialize object to JSON: {e}")
        return json.dumps({"error": "Serialization failed"})


def safe_json_loads(json_str: str) -> Any:
    """Safely deserialize JSON string."""
    try:
        return json.loads(json_str)
    except Exception as e:
        logger.warning(f"Failed to deserialize JSON: {e}")
        return None


def encode_base64(data: bytes) -> str:
    """Encode bytes to base64 string."""
    return base64.b64encode(data).decode('utf-8')


def decode_base64(data: str) -> bytes:
    """Decode base64 string to bytes."""
    return base64.b64decode(data)


def create_file_path(base_dir: str, filename: str, subdir: str = "") -> str:
    """Create a file path with proper directory structure."""
    base_path = Path(base_dir)
    if subdir:
        base_path = base_path / subdir
    
    # Create directory if it doesn't exist
    base_path.mkdir(parents=True, exist_ok=True)
    
    return str(base_path / sanitize_filename(filename))


def get_file_extension(filename: str) -> str:
    """Get file extension from filename."""
    return Path(filename).suffix.lower()


def is_image_file(filename: str) -> bool:
    """Check if file is an image based on extension."""
    image_extensions = {'.jpg', '.jpeg', '.png', '.gif', '.bmp', '.webp', '.svg'}
    return get_file_extension(filename) in image_extensions


def is_audio_file(filename: str) -> bool:
    """Check if file is an audio file based on extension."""
    audio_extensions = {'.mp3', '.wav', '.flac', '.ogg', '.m4a', '.aac'}
    return get_file_extension(filename) in audio_extensions


def is_video_file(filename: str) -> bool:
    """Check if file is a video file based on extension."""
    video_extensions = {'.mp4', '.avi', '.mov', '.wmv', '.flv', '.webm', '.mkv'}
    return get_file_extension(filename) in video_extensions


def format_platform_name(platform: str) -> str:
    """Format platform name for display."""
    platform_map = {
        'twitter': 'Twitter',
        'linkedin': 'LinkedIn',
        'instagram': 'Instagram',
        'facebook': 'Facebook',
        'tiktok': 'TikTok',
        'youtube': 'YouTube',
    }
    return platform_map.get(platform.lower(), platform.title())


def validate_email(email: str) -> bool:
    """Validate email address format."""
    pattern = r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$'
    return bool(re.match(pattern, email))


def validate_phone(phone: str) -> bool:
    """Validate phone number format."""
    # Remove all non-digit characters
    digits = re.sub(r'\D', '', phone)
    # Check if it's a valid length (7-15 digits)
    return 7 <= len(digits) <= 15


def generate_slug(text: str) -> str:
    """Generate URL-friendly slug from text."""
    # Convert to lowercase
    slug = text.lower()
    # Replace spaces and special characters with hyphens
    slug = re.sub(r'[^\w\s-]', '', slug)
    slug = re.sub(r'[-\s]+', '-', slug)
    # Remove leading/trailing hyphens
    slug = slug.strip('-')
    return slug


def mask_sensitive_data(data: str, mask_char: str = '*') -> str:
    """Mask sensitive data like emails and phone numbers."""
    # Mask email addresses
    data = re.sub(r'([a-zA-Z0-9._%+-]+)@([a-zA-Z0-9.-]+\.[a-zA-Z]{2,})', 
                  lambda m: f"{m.group(1)[:2]}{mask_char * (len(m.group(1))-2)}@{m.group(2)}", data)
    
    # Mask phone numbers
    data = re.sub(r'(\d{3})\d{3}(\d{4})', f"\\1{mask_char * 3}\\2", data)
    
    return data


def retry_with_backoff(func, max_retries: int = 3, base_delay: float = 1.0):
    """Decorator for retrying functions with exponential backoff."""
    import asyncio
    import functools
    
    @functools.wraps(func)
    async def wrapper(*args, **kwargs):
        last_exception = None
        
        for attempt in range(max_retries):
            try:
                if asyncio.iscoroutinefunction(func):
                    return await func(*args, **kwargs)
                else:
                    return func(*args, **kwargs)
            except Exception as e:
                last_exception = e
                if attempt < max_retries - 1:
                    delay = base_delay * (2 ** attempt)
                    logger.warning(f"Attempt {attempt + 1} failed, retrying in {delay}s: {e}")
                    await asyncio.sleep(delay)
        
        raise last_exception
    
    return wrapper 