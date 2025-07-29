"""
TTS API Routes
Provides endpoints for text-to-speech synthesis and audio serving
"""

from fastapi import APIRouter, HTTPException, Request
from fastapi.responses import FileResponse, JSONResponse
from pydantic import BaseModel
from typing import Optional, Dict, Any
import logging
import os

# Import TTS integration
try:
    from agents.tts_integration import tts_integration, TTSRequest, VoiceStyle
    HAS_TTS = True
except ImportError as e:
    logging.warning(f"TTS integration not available: {e}")
    HAS_TTS = False

logger = logging.getLogger(__name__)

# Create router
router = APIRouter()

# Request/Response models
class TTSSynthesisRequest(BaseModel):
    text: str
    language: Optional[str] = "th-TH"
    voice_style: Optional[str] = "friendly"
    speaking_rate: Optional[float] = 1.0
    pitch: Optional[float] = 1.0
    volume: Optional[float] = 1.0
    use_ssml: Optional[bool] = True

class TTSSynthesisResponse(BaseModel):
    audio_url: str
    duration_ms: int
    text: str
    ssml: Optional[str] = None
    provider: str
    cached: bool

@router.post("/synthesize", response_model=TTSSynthesisResponse)
async def synthesize_speech(request: TTSSynthesisRequest):
    """
    Synthesize speech from text with style and SSML support
    """
    if not HAS_TTS:
        raise HTTPException(
            status_code=503,
            detail="TTS integration not available"
        )
    
    try:
        logger.info(f"TTS synthesis request: {request.text[:50]}...")
        
        # Map string voice style to enum
        voice_style_mapping = {
            "friendly": VoiceStyle.FRIENDLY,
            "enthusiastic": VoiceStyle.ENTHUSIASTIC,
            "calm": VoiceStyle.CALM,
            "informative": VoiceStyle.INFORMATIVE,
            "formal": VoiceStyle.FORMAL
        }
        
        voice_style = voice_style_mapping.get(request.voice_style, VoiceStyle.FRIENDLY)
        
        tts_request = TTSRequest(
            text=request.text,
            language=request.language,
            voice_style=voice_style,
            speaking_rate=request.speaking_rate,
            pitch=request.pitch,
            volume=request.volume,
            use_ssml=request.use_ssml
        )
        
        tts_response = await tts_integration.synthesize_speech(tts_request)
        
        return TTSSynthesisResponse(
            audio_url=tts_response.audio_url,
            duration_ms=tts_response.duration_ms,
            text=tts_response.text,
            ssml=tts_response.ssml,
            provider=tts_response.provider,
            cached=tts_response.cached
        )
        
    except Exception as e:
        logger.error(f"Error in TTS synthesis: {e}")
        raise HTTPException(
            status_code=500,
            detail=f"TTS synthesis failed: {str(e)}"
        )

@router.get("/audio/{audio_id}")
async def serve_audio(audio_id: str):
    """
    Serve generated audio files
    """
    try:
        # Remove extension for cache key
        cache_key = audio_id.replace('.mp3', '').replace('.wav', '')
        
        # Check if audio file exists in cache
        audio_file = os.path.join(tts_integration.cache_dir, f"{cache_key}.mp3")
        
        if os.path.exists(audio_file):
            return FileResponse(
                audio_file,
                media_type="audio/mpeg",
                filename=f"{cache_key}.mp3"
            )
        else:
            # Return a placeholder or generate audio on-the-fly
            logger.warning(f"Audio file not found: {audio_id}")
            raise HTTPException(
                status_code=404,
                detail="Audio file not found"
            )
            
    except Exception as e:
        logger.error(f"Error serving audio: {e}")
        raise HTTPException(
            status_code=500,
            detail=f"Failed to serve audio: {str(e)}"
        )

@router.get("/estimate_duration")
async def estimate_speech_duration(text: str, language: str = "th-TH", speaking_rate: float = 1.0):
    """
    Estimate speech duration for given text
    """
    if not HAS_TTS:
        raise HTTPException(
            status_code=503,
            detail="TTS integration not available"
        )
    
    try:
        duration_ms = tts_integration.estimate_speech_duration(text, language, speaking_rate)
        
        return {
            "text": text,
            "language": language,
            "speaking_rate": speaking_rate,
            "estimated_duration_ms": duration_ms,
            "estimated_duration_seconds": duration_ms / 1000
        }
        
    except Exception as e:
        logger.error(f"Error estimating duration: {e}")
        raise HTTPException(
            status_code=500,
            detail=f"Duration estimation failed: {str(e)}"
        )

@router.get("/voices")
async def list_available_voices():
    """
    List available voices and styles
    """
    return {
        "languages": {
            "th-TH": {
                "name": "Thai (Thailand)",
                "voices": {
                    "friendly": "PremwadeeNeural - Friendly female voice",
                    "enthusiastic": "NiwatNeural - Enthusiastic male voice", 
                    "calm": "PremwadeeNeural - Calm female voice",
                    "informative": "PremwadeeNeural - Informative female voice",
                    "formal": "NiwatNeural - Formal male voice"
                }
            },
            "en-US": {
                "name": "English (United States)",
                "voices": {
                    "friendly": "JennyNeural - Friendly female voice",
                    "enthusiastic": "AriaNeural - Enthusiastic female voice",
                    "calm": "JennyNeural - Calm female voice", 
                    "informative": "RyanNeural - Informative male voice",
                    "formal": "RyanNeural - Formal male voice"
                }
            }
        },
        "voice_styles": [
            "friendly",
            "enthusiastic", 
            "calm",
            "informative",
            "formal"
        ],
        "supported_formats": ["mp3", "wav"],
        "features": {
            "ssml_support": True,
            "emotion_synthesis": True,
            "voice_cloning": False,
            "real_time_synthesis": True
        }
    }

@router.get("/health")
async def tts_health_check():
    """Health check for TTS service"""
    return {
        "service": "tts_integration",
        "status": "healthy" if HAS_TTS else "unavailable",
        "features": {
            "synthesis": HAS_TTS,
            "ssml_support": HAS_TTS,
            "caching": HAS_TTS,
            "multi_language": HAS_TTS
        },
        "cache_directory": tts_integration.cache_dir if HAS_TTS else None
    }

def create_tts_routes(app):
    """Add TTS routes to FastAPI app"""
    app.include_router(router, prefix="/tts", tags=["Text-to-Speech"])
    logger.info("TTS API routes added")