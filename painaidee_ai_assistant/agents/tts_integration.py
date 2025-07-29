"""
Text-to-Speech Integration for Multimodal AI Assistant
Provides TTS capabilities with SSML support for enhanced speech synthesis
"""

import logging
import os
import hashlib
from typing import Dict, Any, Optional
from dataclasses import dataclass
from enum import Enum
import json

logger = logging.getLogger(__name__)

class TTSProvider(Enum):
    """Available TTS providers"""
    WEB_SPEECH_API = "web_speech_api"
    AZURE_SPEECH = "azure_speech"
    GOOGLE_TTS = "google_tts"
    AMAZON_POLLY = "amazon_polly"

class VoiceStyle(Enum):
    """Voice style options for TTS"""
    FRIENDLY = "friendly"
    ENTHUSIASTIC = "enthusiastic"
    CALM = "calm"
    INFORMATIVE = "informative"
    FORMAL = "formal"

@dataclass
class TTSRequest:
    """TTS request configuration"""
    text: str
    language: str = "th-TH"
    voice_style: VoiceStyle = VoiceStyle.FRIENDLY
    speaking_rate: float = 1.0
    pitch: float = 1.0
    volume: float = 1.0
    use_ssml: bool = True
    provider: TTSProvider = TTSProvider.WEB_SPEECH_API

@dataclass
class TTSResponse:
    """TTS response data"""
    audio_url: str
    duration_ms: int
    text: str
    ssml: Optional[str] = None
    provider: str = "web_speech_api"
    cached: bool = False

class TTSIntegration:
    """Text-to-Speech integration with caching and SSML support"""
    
    def __init__(self, cache_dir: str = "cache/tts"):
        self.cache_dir = cache_dir
        self._ensure_cache_dir()
        self._voice_mappings = self._initialize_voice_mappings()
        
    def _ensure_cache_dir(self):
        """Ensure TTS cache directory exists"""
        os.makedirs(self.cache_dir, exist_ok=True)
        
    def _initialize_voice_mappings(self) -> Dict[str, Dict[str, Any]]:
        """Initialize voice mappings for different styles"""
        return {
            "th-TH": {
                VoiceStyle.FRIENDLY.value: {
                    "voice_name": "th-TH-PremwadeeNeural",
                    "rate": "medium",
                    "pitch": "+5%"
                },
                VoiceStyle.ENTHUSIASTIC.value: {
                    "voice_name": "th-TH-NiwatNeural", 
                    "rate": "fast",
                    "pitch": "+10%"
                },
                VoiceStyle.CALM.value: {
                    "voice_name": "th-TH-PremwadeeNeural",
                    "rate": "slow",
                    "pitch": "-5%"
                },
                VoiceStyle.INFORMATIVE.value: {
                    "voice_name": "th-TH-PremwadeeNeural",
                    "rate": "medium",
                    "pitch": "0%"
                },
                VoiceStyle.FORMAL.value: {
                    "voice_name": "th-TH-NiwatNeural",
                    "rate": "medium",
                    "pitch": "0%"
                }
            },
            "en-US": {
                VoiceStyle.FRIENDLY.value: {
                    "voice_name": "en-US-JennyNeural",
                    "rate": "medium", 
                    "pitch": "+5%"
                },
                VoiceStyle.ENTHUSIASTIC.value: {
                    "voice_name": "en-US-AriaNeural",
                    "rate": "fast",
                    "pitch": "+10%"
                },
                VoiceStyle.CALM.value: {
                    "voice_name": "en-US-JennyNeural",
                    "rate": "slow",
                    "pitch": "-5%"
                },
                VoiceStyle.INFORMATIVE.value: {
                    "voice_name": "en-US-RyanNeural",
                    "rate": "medium",
                    "pitch": "0%"
                },
                VoiceStyle.FORMAL.value: {
                    "voice_name": "en-US-RyanNeural",
                    "rate": "medium",
                    "pitch": "0%"
                }
            }
        }
    
    async def synthesize_speech(self, request: TTSRequest) -> TTSResponse:
        """
        Synthesize speech from text with style and SSML support
        """
        try:
            # Check cache first
            cache_key = self._generate_cache_key(request)
            cached_response = self._get_cached_response(cache_key)
            if cached_response:
                logger.info(f"Using cached TTS for: {request.text[:50]}...")
                return cached_response
            
            # Generate SSML if requested
            ssml = None
            if request.use_ssml:
                ssml = self._generate_ssml(request)
            
            # For now, generate a mock response since actual TTS requires external services
            response = self._generate_mock_response(request, ssml)
            
            # Cache the response
            self._cache_response(cache_key, response)
            
            logger.info(f"Generated TTS for: {request.text[:50]}...")
            return response
            
        except Exception as e:
            logger.error(f"Error in TTS synthesis: {e}")
            raise
    
    def _generate_ssml(self, request: TTSRequest) -> str:
        """Generate SSML markup for enhanced speech synthesis"""
        
        voice_config = self._voice_mappings.get(request.language, {}).get(
            request.voice_style.value, {}
        )
        
        voice_name = voice_config.get("voice_name", "th-TH-PremwadeeNeural")
        rate = voice_config.get("rate", "medium")
        pitch = voice_config.get("pitch", "0%")
        
        # Apply speaking rate and pitch from request
        if request.speaking_rate != 1.0:
            if request.speaking_rate > 1.2:
                rate = "fast"
            elif request.speaking_rate < 0.8:
                rate = "slow"
        
        # Enhanced SSML with emotion and timing
        ssml = f"""<speak version="1.0" xmlns="http://www.w3.org/2001/10/synthesis" xml:lang="{request.language}">
    <voice name="{voice_name}">
        <prosody rate="{rate}" pitch="{pitch}" volume="{int(request.volume * 100)}%">
            {self._add_emphasis_tags(request.text, request.voice_style)}
        </prosody>
    </voice>
</speak>"""
        
        return ssml
    
    def _add_emphasis_tags(self, text: str, style: VoiceStyle) -> str:
        """Add SSML emphasis tags based on voice style"""
        
        if style == VoiceStyle.ENTHUSIASTIC:
            # Add emphasis to exclamatory phrases
            text = text.replace("!", '<break time="200ms"/>!')
            if "ลองไป" in text:
                text = text.replace("ลองไป", '<emphasis level="strong">ลองไป</emphasis>')
            if "ดูไหม" in text:
                text = text.replace("ดูไหม", '<emphasis level="moderate">ดูไหม</emphasis>')
                
        elif style == VoiceStyle.CALM:
            # Add pauses for calm delivery
            text = text.replace(",", '<break time="300ms"/>,')
            text = text.replace(".", '<break time="500ms"/>.')
            
        elif style == VoiceStyle.INFORMATIVE:
            # Add slight emphasis to key information
            text = text.replace("พิพิธภัณฑ์", '<emphasis level="moderate">พิพิธภัณฑ์</emphasis>')
            
        return text
    
    def _generate_cache_key(self, request: TTSRequest) -> str:
        """Generate cache key for TTS request"""
        content = f"{request.text}_{request.language}_{request.voice_style.value}_{request.speaking_rate}_{request.pitch}"
        return hashlib.md5(content.encode()).hexdigest()
    
    def _get_cached_response(self, cache_key: str) -> Optional[TTSResponse]:
        """Get cached TTS response if available"""
        cache_file = os.path.join(self.cache_dir, f"{cache_key}.json")
        if os.path.exists(cache_file):
            try:
                with open(cache_file, 'r', encoding='utf-8') as f:
                    data = json.load(f)
                return TTSResponse(**data, cached=True)
            except Exception as e:
                logger.warning(f"Failed to load cached TTS: {e}")
        return None
    
    def _cache_response(self, cache_key: str, response: TTSResponse):
        """Cache TTS response"""
        cache_file = os.path.join(self.cache_dir, f"{cache_key}.json")
        try:
            data = {
                "audio_url": response.audio_url,
                "duration_ms": response.duration_ms,
                "text": response.text,
                "ssml": response.ssml,
                "provider": response.provider
            }
            with open(cache_file, 'w', encoding='utf-8') as f:
                json.dump(data, f, ensure_ascii=False, indent=2)
        except Exception as e:
            logger.warning(f"Failed to cache TTS response: {e}")
    
    def _generate_mock_response(self, request: TTSRequest, ssml: Optional[str]) -> TTSResponse:
        """Generate mock TTS response for development/testing"""
        
        # Estimate duration based on text length and speaking rate
        # Average Thai speech: 4-5 syllables per second
        estimated_syllables = len(request.text) * 0.7  # Rough estimate
        base_duration_ms = int((estimated_syllables / 4.5) * 1000)
        adjusted_duration_ms = int(base_duration_ms / request.speaking_rate)
        
        # Generate mock audio URL (in production, this would be actual audio file)
        cache_key = self._generate_cache_key(request)
        audio_url = f"/tts/audio/{cache_key}.mp3"
        
        return TTSResponse(
            audio_url=audio_url,
            duration_ms=adjusted_duration_ms,
            text=request.text,
            ssml=ssml,
            provider=request.provider.value,
            cached=False
        )
    
    def estimate_speech_duration(self, text: str, language: str = "th-TH", 
                                speaking_rate: float = 1.0) -> int:
        """Estimate speech duration in milliseconds"""
        if language.startswith("th"):
            # Thai: approximately 4-5 syllables per second
            syllables = len(text) * 0.7
            base_duration = (syllables / 4.5) * 1000
        else:
            # English: approximately 4-5 words per second
            words = len(text.split())
            base_duration = (words / 4.5) * 1000
            
        return int(base_duration / speaking_rate)

# Global TTS instance
tts_integration = TTSIntegration()