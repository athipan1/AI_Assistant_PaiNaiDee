"""
Enhanced Avatar API Routes
Provides endpoints for advanced 3D avatar features including facial expressions,
eye gaze tracking, and Thai lip syncing
"""

from fastapi import APIRouter, HTTPException, BackgroundTasks
from pydantic import BaseModel, Field
from typing import Dict, List, Optional, Any
import logging
import asyncio
import json

try:
    from agents.enhanced_avatar import EnhancedAvatarSystem, AvatarAnimationFrame
    from agents.emotion_analysis import EmotionAnalysisAgent, EmotionType, FacialExpression, EyeGazeDirection
    HAS_ENHANCED_AVATAR = True
except ImportError as e:
    logging.warning(f"Enhanced avatar system not available: {e}")
    HAS_ENHANCED_AVATAR = False

logger = logging.getLogger(__name__)

# Initialize enhanced avatar system
if HAS_ENHANCED_AVATAR:
    avatar_system = EnhancedAvatarSystem()
    emotion_agent = EmotionAnalysisAgent()

# API Models
class AvatarAnimationRequest(BaseModel):
    text: str = Field(..., description="Text to be spoken by avatar")
    language: str = Field(default="thai", description="Language for TTS and lip sync")
    emotion_context: Optional[str] = Field(None, description="Additional emotional context")
    gesture_priority: str = Field(default="emotion", description="Priority: emotion or context")
    animation_speed: float = Field(default=1.0, description="Animation speed multiplier")

class FacialExpressionRequest(BaseModel):
    expression_type: str = Field(..., description="Type of facial expression")
    intensity: float = Field(default=0.8, description="Expression intensity (0.0-1.0)")
    duration: float = Field(default=2.0, description="Duration in seconds")
    blend_previous: bool = Field(default=True, description="Blend with previous expression")

class EyeGazeRequest(BaseModel):
    gaze_direction: str = Field(..., description="Eye gaze direction")
    focus_intensity: float = Field(default=0.8, description="Focus intensity (0.0-1.0)")
    duration: float = Field(default=3.0, description="Gaze duration in seconds")
    natural_variation: bool = Field(default=True, description="Add natural variations")

class LipSyncRequest(BaseModel):
    text: str = Field(..., description="Text for lip synchronization")
    language: str = Field(default="thai", description="Language for phoneme analysis")
    speech_speed: float = Field(default=1.0, description="Speech speed multiplier")
    emotion_modifier: Optional[str] = Field(None, description="Emotion affecting speech")

class AvatarAnimationResponse(BaseModel):
    animation_id: str
    duration: float
    total_frames: int
    fps: int
    facial_expression: Dict[str, Any]
    eye_gaze_data: Dict[str, Any]
    lip_sync_data: Optional[Dict[str, Any]]
    gesture_data: Dict[str, Any]
    animation_frames: List[Dict[str, Any]]

# Create router
router = APIRouter(prefix="/avatar", tags=["Enhanced Avatar"])

@router.post("/generate_animation", response_model=AvatarAnimationResponse)
async def generate_avatar_animation(request: AvatarAnimationRequest):
    """
    Generate complete avatar animation including facial expressions, eye gaze, and lip sync
    
    This endpoint analyzes the input text for emotion and context, then generates
    a comprehensive animation sequence for the 3D avatar.
    """
    if not HAS_ENHANCED_AVATAR:
        raise HTTPException(
            status_code=503,
            detail="Enhanced avatar system not available"
        )
    
    try:
        # Analyze emotion and context
        emotion_result = await emotion_agent.analyze_emotion(
            request.text, 
            context=request.emotion_context
        )
        
        # Generate avatar animation
        animation_frames = await avatar_system.generate_avatar_animation(
            emotion_result=emotion_result,
            text=request.text,
            language=request.language
        )
        
        # Export animation data
        animation_data = avatar_system.export_animation_data(animation_frames)
        
        # Create response
        response = AvatarAnimationResponse(
            animation_id=f"anim_{int(asyncio.get_event_loop().time() * 1000)}",
            duration=animation_data["duration"],
            total_frames=animation_data["total_frames"],
            fps=animation_data["fps"],
            facial_expression={
                "primary_expression": emotion_result.facial_expression.value,
                "intensity": 0.8,
                "emotion": emotion_result.primary_emotion.value
            },
            eye_gaze_data={
                "direction": emotion_result.eye_gaze_direction.value,
                "pattern": "natural_conversation",
                "focus_intensity": 0.8
            },
            lip_sync_data={
                "language": request.language,
                "phoneme_count": len(emotion_result.lip_sync_data.get("phoneme_sequence", [])) if emotion_result.lip_sync_data else 0,
                "total_duration": emotion_result.lip_sync_data.get("total_duration", 0) if emotion_result.lip_sync_data else 0
            } if emotion_result.lip_sync_data else None,
            gesture_data={
                "primary_gesture": emotion_result.suggested_gesture.value,
                "context": emotion_result.gesture_context.get("primary_context", "general") if emotion_result.gesture_context else "general",
                "intensity": emotion_result.gesture_context.get("animation_modifiers", {}).get("intensity", 0.8) if emotion_result.gesture_context else 0.8
            },
            animation_frames=animation_data["frames"]
        )
        
        return response
        
    except Exception as e:
        logger.error(f"Error generating avatar animation: {e}")
        raise HTTPException(
            status_code=500,
            detail=f"Failed to generate avatar animation: {str(e)}"
        )

@router.post("/facial_expression")
async def set_facial_expression(request: FacialExpressionRequest):
    """
    Set specific facial expression for the avatar
    
    Allows direct control of facial expressions independent of emotion analysis.
    """
    if not HAS_ENHANCED_AVATAR:
        raise HTTPException(
            status_code=503,
            detail="Enhanced avatar system not available"
        )
    
    try:
        # Validate expression type
        try:
            expression = FacialExpression(request.expression_type)
        except ValueError:
            available_expressions = [e.value for e in FacialExpression]
            raise HTTPException(
                status_code=400,
                detail=f"Invalid expression type. Available: {available_expressions}"
            )
        
        # Generate facial animation
        facial_animation = avatar_system._generate_facial_animation(expression)
        
        return {
            "status": "success",
            "expression": {
                "type": expression.value,
                "intensity": request.intensity,
                "duration": request.duration,
                "blend_previous": request.blend_previous
            },
            "animation_data": {
                "transition_in": facial_animation.transition_in,
                "transition_out": facial_animation.transition_out,
                "intensity": facial_animation.intensity
            }
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error setting facial expression: {e}")
        raise HTTPException(
            status_code=500,
            detail=f"Failed to set facial expression: {str(e)}"
        )

@router.post("/eye_gaze")
async def set_eye_gaze(request: EyeGazeRequest):
    """
    Control avatar eye gaze direction and behavior
    
    Provides precise control over where the avatar looks and how eyes behave.
    """
    if not HAS_ENHANCED_AVATAR:
        raise HTTPException(
            status_code=503,
            detail="Enhanced avatar system not available"
        )
    
    try:
        # Validate gaze direction
        try:
            gaze_direction = EyeGazeDirection(request.gaze_direction)
        except ValueError:
            available_directions = [d.value for d in EyeGazeDirection]
            raise HTTPException(
                status_code=400,
                detail=f"Invalid gaze direction. Available: {available_directions}"
            )
        
        # Generate eye gaze sequence
        eye_gaze_sequence = avatar_system._generate_eye_gaze_sequence(
            gaze_direction, 
            EmotionType.NEUTRAL  # Default emotion for direct gaze control
        )
        
        return {
            "status": "success",
            "eye_gaze": {
                "direction": gaze_direction.value,
                "focus_intensity": request.focus_intensity,
                "duration": request.duration,
                "natural_variation": request.natural_variation
            },
            "sequence_data": {
                "frames": len(eye_gaze_sequence),
                "average_target": {
                    "x": sum(g.target_x for g in eye_gaze_sequence) / len(eye_gaze_sequence),
                    "y": sum(g.target_y for g in eye_gaze_sequence) / len(eye_gaze_sequence)
                }
            }
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error setting eye gaze: {e}")
        raise HTTPException(
            status_code=500,
            detail=f"Failed to set eye gaze: {str(e)}"
        )

@router.post("/lip_sync")
async def generate_lip_sync(request: LipSyncRequest):
    """
    Generate lip synchronization data for Thai/English text
    
    Creates detailed mouth animation synchronized with speech phonemes.
    """
    if not HAS_ENHANCED_AVATAR:
        raise HTTPException(
            status_code=503,
            detail="Enhanced avatar system not available"
        )
    
    try:
        # Generate emotion result for lip sync context
        emotion_modifier = EmotionType.NEUTRAL
        if request.emotion_modifier:
            try:
                emotion_modifier = EmotionType(request.emotion_modifier)
            except ValueError:
                pass
        
        # Create mock emotion result for lip sync generation
        class MockEmotionResult:
            def __init__(self):
                self.primary_emotion = emotion_modifier
                self.lip_sync_data = None
        
        mock_result = MockEmotionResult()
        
        # Generate lip sync data
        lip_sync_data = await emotion_agent._generate_lip_sync_data(
            request.text, 
            emotion_modifier
        )
        
        # Generate lip sync sequence
        lip_sync_sequence = await avatar_system._generate_lip_sync_sequence(
            lip_sync_data, 
            request.text, 
            request.language
        )
        
        return {
            "status": "success",
            "lip_sync": {
                "text": request.text,
                "language": request.language,
                "speech_speed": request.speech_speed,
                "emotion_modifier": emotion_modifier.value
            },
            "phoneme_data": {
                "total_phonemes": len(lip_sync_data.get("phoneme_sequence", [])),
                "total_duration": lip_sync_data.get("total_duration", 0),
                "speed_modifier": lip_sync_data.get("emotion_modifier", 1.0)
            },
            "animation_sequence": [
                {
                    "timestamp": frame.timestamp,
                    "mouth_open": frame.mouth_open,
                    "mouth_width": frame.mouth_width,
                    "jaw_open": frame.jaw_open,
                    "phoneme": frame.phoneme,
                    "viseme": frame.viseme
                }
                for frame in lip_sync_sequence[:50]  # Limit response size
            ],
            "total_frames": len(lip_sync_sequence)
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error generating lip sync: {e}")
        raise HTTPException(
            status_code=500,
            detail=f"Failed to generate lip sync: {str(e)}"
        )

@router.get("/capabilities")
async def get_avatar_capabilities():
    """
    Get information about avatar capabilities and available options
    """
    if not HAS_ENHANCED_AVATAR:
        return {
            "status": "unavailable",
            "message": "Enhanced avatar system not available",
            "capabilities": {}
        }
    
    return {
        "status": "available",
        "capabilities": {
            "facial_expressions": [e.value for e in FacialExpression],
            "eye_gaze_directions": [d.value for d in EyeGazeDirection],
            "emotion_types": [e.value for e in EmotionType],
            "supported_languages": ["thai", "english", "thai_english_mixed"],
            "features": {
                "facial_expressions": True,
                "eye_gaze_tracking": True,
                "lip_sync_thai": True,
                "ai_gesture_context": True,
                "thai_cultural_gestures": True,
                "emotion_based_animation": True
            }
        },
        "gaze_patterns": list(avatar_system.gaze_patterns.keys()) if HAS_ENHANCED_AVATAR else [],
        "expression_library": list(avatar_system.expression_library.keys()) if HAS_ENHANCED_AVATAR else [],
        "thai_phoneme_support": len(avatar_system.thai_viseme_mapping) if HAS_ENHANCED_AVATAR else 0
    }

@router.get("/animation_presets")
async def get_animation_presets():
    """
    Get predefined animation presets for common scenarios
    """
    if not HAS_ENHANCED_AVATAR:
        raise HTTPException(
            status_code=503,
            detail="Enhanced avatar system not available"
        )
    
    presets = {
        "thai_greeting": {
            "name": "Thai Greeting",
            "description": "Traditional Thai wai greeting with respectful expression",
            "facial_expression": "smile_gentle",
            "eye_gaze": "looking_at_user",
            "gesture": "thai_wai",
            "duration": 3.0
        },
        "excited_welcome": {
            "name": "Excited Welcome",
            "description": "Enthusiastic welcome with big smile and animated gestures",
            "facial_expression": "smile_excited",
            "eye_gaze": "looking_at_user",
            "gesture": "thai_welcome",
            "duration": 4.0
        },
        "thoughtful_explanation": {
            "name": "Thoughtful Explanation",
            "description": "Contemplative expression for explaining complex topics",
            "facial_expression": "thoughtful_contemplative",
            "eye_gaze": "looking_away_thoughtful",
            "gesture": "explaining_gesture",
            "duration": 5.0
        },
        "concerned_support": {
            "name": "Concerned Support",
            "description": "Supportive expression for addressing worries",
            "facial_expression": "worried_slight",
            "eye_gaze": "looking_at_user",
            "gesture": "reassuring_gesture",
            "duration": 4.0
        },
        "confident_presentation": {
            "name": "Confident Presentation",
            "description": "Confident stance for presenting information",
            "facial_expression": "confident_assured",
            "eye_gaze": "looking_at_user",
            "gesture": "confident_pose",
            "duration": 6.0
        }
    }
    
    return {
        "status": "success",
        "presets": presets,
        "total_presets": len(presets)
    }

@router.post("/apply_preset/{preset_name}")
async def apply_animation_preset(preset_name: str, text: Optional[str] = None):
    """
    Apply a predefined animation preset
    """
    if not HAS_ENHANCED_AVATAR:
        raise HTTPException(
            status_code=503,
            detail="Enhanced avatar system not available"
        )
    
    # Get available presets
    presets_response = await get_animation_presets()
    presets = presets_response["presets"]
    
    if preset_name not in presets:
        raise HTTPException(
            status_code=404,
            detail=f"Preset '{preset_name}' not found. Available: {list(presets.keys())}"
        )
    
    preset = presets[preset_name]
    
    try:
        # Create animation request based on preset
        animation_request = AvatarAnimationRequest(
            text=text or f"Applying {preset['name']} preset",
            language="thai",
            emotion_context=preset["description"],
            gesture_priority="context"
        )
        
        # Generate animation
        animation_response = await generate_avatar_animation(animation_request)
        
        return {
            "status": "success",
            "preset_applied": preset_name,
            "preset_description": preset["description"],
            "animation": animation_response
        }
        
    except Exception as e:
        logger.error(f"Error applying preset {preset_name}: {e}")
        raise HTTPException(
            status_code=500,
            detail=f"Failed to apply preset: {str(e)}"
        )

# Health check endpoint
@router.get("/health")
async def avatar_health_check():
    """Check the health of the enhanced avatar system"""
    try:
        if not HAS_ENHANCED_AVATAR:
            return {
                "status": "unavailable",
                "message": "Enhanced avatar system not available",
                "dependencies": {
                    "emotion_analysis": False,
                    "avatar_system": False,
                    "numpy": False
                }
            }
        
        # Test basic functionality
        test_text = "Hello, this is a test"
        emotion_result = await emotion_agent.analyze_emotion(test_text)
        
        return {
            "status": "healthy",
            "message": "Enhanced avatar system operational",
            "dependencies": {
                "emotion_analysis": True,
                "avatar_system": True,
                "numpy": True
            },
            "test_result": {
                "emotion_detected": emotion_result.primary_emotion.value,
                "confidence": emotion_result.confidence,
                "facial_expression": emotion_result.facial_expression.value,
                "eye_gaze": emotion_result.eye_gaze_direction.value
            }
        }
        
    except Exception as e:
        logger.error(f"Avatar health check failed: {e}")
        return {
            "status": "unhealthy",
            "message": f"Avatar system error: {str(e)}",
            "dependencies": {
                "emotion_analysis": False,
                "avatar_system": False,
                "numpy": False
            }
        }

def create_enhanced_avatar_routes():
    """Create and return the enhanced avatar API router"""
    if HAS_ENHANCED_AVATAR:
        logger.info("Enhanced Avatar API routes initialized successfully")
    else:
        logger.warning("Enhanced Avatar API routes initialized in limited mode")
    
    return router