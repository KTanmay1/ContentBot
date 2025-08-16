"""
Audio Service for ViraLearn ContentBot.
Handles text-to-speech and speech-to-text processing.
"""

import asyncio
import logging
import io
import base64
from typing import Dict, List, Optional, Any, Union
from dataclasses import dataclass
from enum import Enum
import time
from pathlib import Path

import httpx
from google.cloud import texttospeech, speech
from google.cloud.texttospeech_v1 import SynthesisInput, VoiceSelectionParams, AudioConfig
from google.cloud.speech_v1 import RecognitionAudio, RecognitionConfig

from config.settings import get_settings

logger = logging.getLogger(__name__)


class AudioFormat(Enum):
    """Supported audio formats."""
    MP3 = "mp3"
    WAV = "wav"
    FLAC = "flac"
    OGG = "ogg"


class VoiceGender(Enum):
    """Voice gender options."""
    MALE = "male"
    FEMALE = "female"
    NEUTRAL = "neutral"


@dataclass
class TTSRequest:
    """Request structure for text-to-speech."""
    text: str
    voice_name: str = "en-US-Standard-A"
    language_code: str = "en-US"
    gender: VoiceGender = VoiceGender.FEMALE
    format: AudioFormat = AudioFormat.MP3
    speaking_rate: float = 1.0  # 0.25 to 4.0
    pitch: float = 0.0  # -20.0 to 20.0
    volume_gain_db: float = 0.0  # -96.0 to 16.0


@dataclass
class TTSResponse:
    """Response structure for text-to-speech."""
    audio_content: bytes
    format: AudioFormat
    metadata: Dict[str, Any]
    generation_time: float


@dataclass
class STTRequest:
    """Request structure for speech-to-text."""
    audio_content: bytes
    language_code: str = "en-US"
    format: AudioFormat = AudioFormat.WAV
    sample_rate: int = 16000
    enable_word_time_offsets: bool = False
    enable_automatic_punctuation: bool = True


@dataclass
class STTResponse:
    """Response structure for speech-to-text."""
    transcript: str
    confidence: float
    alternatives: List[Dict[str, Any]]
    metadata: Dict[str, Any]
    processing_time: float


class AudioServiceError(Exception):
    """Custom exception for audio service errors."""
    pass


class AudioService:
    """Service for audio processing (TTS and STT)."""
    
    def __init__(self):
        self.settings = get_settings()
        self.tts_client = None
        self.stt_client = None
        self._initialized = False
        
        # Available voices cache
        self._voices_cache = {}
        self._voices_cache_time = 0
        self._cache_duration = 3600  # 1 hour
    
    async def initialize(self) -> None:
        """Initialize the audio service clients."""
        if self._initialized:
            return
        
        try:
            # Initialize Text-to-Speech client with service account credentials
            # Uses GOOGLE_APPLICATION_CREDENTIALS environment variable
            self.tts_client = texttospeech.TextToSpeechClient()
            
            # Initialize Speech-to-Text client with service account credentials
            # Uses GOOGLE_APPLICATION_CREDENTIALS environment variable
            self.stt_client = speech.SpeechClient()
            
            self._initialized = True
            logger.info("Audio Service initialized successfully")
            
        except Exception as e:
            logger.error(f"Failed to initialize Audio Service: {e}")
            raise AudioServiceError(f"Audio service initialization failed: {e}")
    
    async def text_to_speech(
        self, 
        request: TTSRequest,
        retry_count: int = 0
    ) -> TTSResponse:
        """
        Convert text to speech using Google Cloud TTS.
        
        Args:
            request: TTS request with text and voice parameters
            retry_count: Current retry attempt (for internal use)
            
        Returns:
            TTSResponse with audio content and metadata
            
        Raises:
            AudioServiceError: If TTS fails after retries
        """
        if not self._initialized:
            await self.initialize()
        
        if not self.tts_client:
            raise AudioServiceError("TTS client not available - API key not configured")
        
        try:
            start_time = time.time()
            
            # Prepare synthesis input
            synthesis_input = SynthesisInput(text=request.text)
            
            # Prepare voice selection
            voice = VoiceSelectionParams(
                language_code=request.language_code,
                name=request.voice_name,
                ssml_gender=self._get_ssml_gender(request.gender)
            )
            
            # Prepare audio configuration
            audio_config = AudioConfig(
                audio_encoding=self._get_audio_encoding(request.format),
                speaking_rate=request.speaking_rate,
                pitch=request.pitch,
                volume_gain_db=request.volume_gain_db
            )
            
            # Perform synthesis
            response = await self._synthesize_speech(
                synthesis_input, voice, audio_config, retry_count
            )
            
            generation_time = time.time() - start_time
            
            return TTSResponse(
                audio_content=response.audio_content,
                format=request.format,
                metadata={
                    "voice_name": request.voice_name,
                    "language_code": request.language_code,
                    "gender": request.gender.value,
                    "speaking_rate": request.speaking_rate,
                    "pitch": request.pitch,
                    "volume_gain_db": request.volume_gain_db,
                    "text_length": len(request.text),
                },
                generation_time=generation_time
            )
            
        except Exception as e:
            logger.error(f"Text-to-speech failed: {e}")
            
            # Retry logic
            if retry_count < 3:  # Max 3 retries for TTS
                logger.info(f"Retrying TTS (attempt {retry_count + 1}/3)")
                await asyncio.sleep(2 ** retry_count)
                return await self.text_to_speech(request, retry_count + 1)
            
            raise AudioServiceError(f"Text-to-speech failed after 3 retries: {e}")
    
    async def _synthesize_speech(
        self, 
        synthesis_input: SynthesisInput,
        voice: VoiceSelectionParams,
        audio_config: AudioConfig,
        retry_count: int
    ) -> Any:
        """Synthesize speech with retry logic."""
        try:
            # Run TTS in thread pool since it's a blocking operation
            loop = asyncio.get_event_loop()
            response = await loop.run_in_executor(
                None,
                self.tts_client.synthesize_speech,
                synthesis_input,
                voice,
                audio_config
            )
            
            return response
            
        except Exception as e:
            raise AudioServiceError(f"Speech synthesis failed: {e}")
    
    async def speech_to_text(
        self, 
        request: STTRequest,
        retry_count: int = 0
    ) -> STTResponse:
        """
        Convert speech to text using Google Cloud STT.
        
        Args:
            request: STT request with audio content and parameters
            retry_count: Current retry attempt (for internal use)
            
        Returns:
            STTResponse with transcript and metadata
            
        Raises:
            AudioServiceError: If STT fails after retries
        """
        if not self._initialized:
            await self.initialize()
        
        if not self.stt_client:
            raise AudioServiceError("STT client not available - API key not configured")
        
        try:
            start_time = time.time()
            
            # Prepare recognition audio
            audio = RecognitionAudio(content=request.audio_content)
            
            # Prepare recognition config
            config = RecognitionConfig(
                encoding=self._get_recognition_encoding(request.format),
                sample_rate_hertz=request.sample_rate,
                language_code=request.language_code,
                enable_word_time_offsets=request.enable_word_time_offsets,
                enable_automatic_punctuation=request.enable_automatic_punctuation,
                model="latest_long",  # Best for longer audio
                use_enhanced=True
            )
            
            # Perform recognition
            response = await self._recognize_speech(
                audio, config, retry_count
            )
            
            processing_time = time.time() - start_time
            
            # Extract results
            if not response.results:
                return STTResponse(
                    transcript="",
                    confidence=0.0,
                    alternatives=[],
                    metadata={
                        "language_code": request.language_code,
                        "format": request.format.value,
                        "sample_rate": request.sample_rate,
                    },
                    processing_time=processing_time
                )
            
            # Get the best result
            result = response.results[0]
            transcript = result.alternatives[0].transcript
            confidence = result.alternatives[0].confidence
            
            # Prepare alternatives
            alternatives = []
            for alt in result.alternatives:
                alt_dict = {
                    "transcript": alt.transcript,
                    "confidence": alt.confidence
                }
                if request.enable_word_time_offsets and alt.words:
                    alt_dict["words"] = [
                        {
                            "word": word.word,
                            "start_time": word.start_time.total_seconds(),
                            "end_time": word.end_time.total_seconds()
                        }
                        for word in alt.words
                    ]
                alternatives.append(alt_dict)
            
            return STTResponse(
                transcript=transcript,
                confidence=confidence,
                alternatives=alternatives,
                metadata={
                    "language_code": request.language_code,
                    "format": request.format.value,
                    "sample_rate": request.sample_rate,
                    "total_alternatives": len(alternatives),
                },
                processing_time=processing_time
            )
            
        except Exception as e:
            logger.error(f"Speech-to-text failed: {e}")
            
            # Retry logic
            if retry_count < 3:  # Max 3 retries for STT
                logger.info(f"Retrying STT (attempt {retry_count + 1}/3)")
                await asyncio.sleep(2 ** retry_count)
                return await self.speech_to_text(request, retry_count + 1)
            
            raise AudioServiceError(f"Speech-to-text failed after 3 retries: {e}")
    
    async def _recognize_speech(
        self, 
        audio: RecognitionAudio,
        config: RecognitionConfig,
        retry_count: int
    ) -> Any:
        """Recognize speech with retry logic."""
        try:
            # Run STT in thread pool since it's a blocking operation
            loop = asyncio.get_event_loop()
            response = await loop.run_in_executor(
                None,
                self.stt_client.recognize,
                config,
                audio
            )
            
            return response
            
        except Exception as e:
            raise AudioServiceError(f"Speech recognition failed: {e}")
    
    async def get_available_voices(self, language_code: str = "en-US") -> List[Dict[str, Any]]:
        """Get available voices for a language."""
        if not self._initialized:
            await self.initialize()
        
        if not self.tts_client:
            raise AudioServiceError("TTS client not available")
        
        # Check cache
        cache_key = f"voices_{language_code}"
        current_time = time.time()
        
        if (cache_key in self._voices_cache and 
            current_time - self._voices_cache_time < self._cache_duration):
            return self._voices_cache[cache_key]
        
        try:
            # Get voices from API
            loop = asyncio.get_event_loop()
            response = await loop.run_in_executor(
                None,
                self.tts_client.list_voices,
                language_code
            )
            
            # Process voices
            voices = []
            for voice in response.voices:
                voice_info = {
                    "name": voice.name,
                    "language_code": voice.language_codes[0] if voice.language_codes else language_code,
                    "gender": self._get_gender_from_ssml(voice.ssml_gender),
                    "natural_sample_rate_hertz": voice.natural_sample_rate_hertz,
                }
                voices.append(voice_info)
            
            # Update cache
            self._voices_cache[cache_key] = voices
            self._voices_cache_time = current_time
            
            return voices
            
        except Exception as e:
            logger.error(f"Failed to get available voices: {e}")
            return []
    
    async def create_audio_summary(
        self, 
        text: str, 
        voice_name: str = "en-US-Standard-A",
        max_length: int = 500
    ) -> TTSResponse:
        """Create an audio summary of text content."""
        # Truncate text if too long
        if len(text) > max_length:
            text = text[:max_length] + "..."
        
        request = TTSRequest(
            text=text,
            voice_name=voice_name,
            speaking_rate=1.2,  # Slightly faster for summaries
            pitch=0.0,
            volume_gain_db=2.0  # Slightly louder
        )
        
        return await self.text_to_speech(request)
    
    async def transcribe_audio_file(self, file_path: str) -> STTResponse:
        """Transcribe an audio file."""
        try:
            # Read audio file
            with open(file_path, 'rb') as f:
                audio_content = f.read()
            
            # Determine format from file extension
            file_ext = Path(file_path).suffix.lower()
            if file_ext == '.mp3':
                format = AudioFormat.MP3
            elif file_ext == '.wav':
                format = AudioFormat.WAV
            elif file_ext == '.flac':
                format = AudioFormat.FLAC
            elif file_ext == '.ogg':
                format = AudioFormat.OGG
            else:
                format = AudioFormat.WAV  # Default
            
            request = STTRequest(
                audio_content=audio_content,
                format=format,
                enable_automatic_punctuation=True,
                enable_word_time_offsets=True
            )
            
            return await self.speech_to_text(request)
            
        except Exception as e:
            raise AudioServiceError(f"Failed to transcribe audio file: {e}")
    
    def _get_audio_encoding(self, format: AudioFormat) -> int:
        """Convert AudioFormat to Google Cloud encoding."""
        encoding_map = {
            AudioFormat.MP3: texttospeech.AudioEncoding.MP3,
            AudioFormat.WAV: texttospeech.AudioEncoding.LINEAR16,
            AudioFormat.FLAC: texttospeech.AudioEncoding.FLAC,
            AudioFormat.OGG: texttospeech.AudioEncoding.OGG_OPUS,
        }
        return encoding_map.get(format, texttospeech.AudioEncoding.MP3)
    
    def _get_recognition_encoding(self, format: AudioFormat) -> int:
        """Convert AudioFormat to Google Cloud recognition encoding."""
        encoding_map = {
            AudioFormat.MP3: speech.RecognitionConfig.AudioEncoding.MP3,
            AudioFormat.WAV: speech.RecognitionConfig.AudioEncoding.LINEAR16,
            AudioFormat.FLAC: speech.RecognitionConfig.AudioEncoding.FLAC,
            AudioFormat.OGG: speech.RecognitionConfig.AudioEncoding.OGG_OPUS,
        }
        return encoding_map.get(format, speech.RecognitionConfig.AudioEncoding.LINEAR16)
    
    def _get_ssml_gender(self, gender: VoiceGender) -> int:
        """Convert VoiceGender to SSML gender."""
        gender_map = {
            VoiceGender.MALE: texttospeech.SsmlVoiceGender.MALE,
            VoiceGender.FEMALE: texttospeech.SsmlVoiceGender.FEMALE,
            VoiceGender.NEUTRAL: texttospeech.SsmlVoiceGender.NEUTRAL,
        }
        return gender_map.get(gender, texttospeech.SsmlVoiceGender.FEMALE)
    
    def _get_gender_from_ssml(self, ssml_gender) -> str:
        """Convert SSML gender to string."""
        gender_map = {
            texttospeech.SsmlVoiceGender.MALE: "male",
            texttospeech.SsmlVoiceGender.FEMALE: "female",
            texttospeech.SsmlVoiceGender.NEUTRAL: "neutral",
        }
        return gender_map.get(ssml_gender, "neutral")
    
    async def health_check(self) -> Dict[str, Any]:
        """Check the health of the audio service."""
        try:
            if not self._initialized:
                return {"status": "not_initialized", "error": "Service not initialized"}
            
            health_status = {
                "status": "healthy",
                "tts_available": self.tts_client is not None,
                "stt_available": self.stt_client is not None,
            }
            
            # Test TTS if available
            if self.tts_client:
                try:
                    test_request = TTSRequest(
                        text="Audio service health check.",
                        voice_name="en-US-Standard-A",
                        format=AudioFormat.MP3
                    )
                    response = await self.text_to_speech(test_request)
                    health_status["tts_test"] = {
                        "success": True,
                        "generation_time": response.generation_time,
                        "audio_size": len(response.audio_content)
                    }
                except Exception as e:
                    health_status["tts_test"] = {
                        "success": False,
                        "error": str(e)
                    }
            
            return health_status
            
        except Exception as e:
            return {"status": "unhealthy", "error": str(e)}


# Global audio service instance
audio_service = AudioService()


async def get_audio_service() -> AudioService:
    """Get the global audio service instance."""
    if not audio_service._initialized:
        await audio_service.initialize()
    return audio_service