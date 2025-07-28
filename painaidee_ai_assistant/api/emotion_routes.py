"""
Emotion Analysis API Routes
Provides endpoints for sentiment analysis and emotion-based gesture recommendations
"""

from fastapi import APIRouter, HTTPException
from pydantic import BaseModel
from typing import List, Optional, Dict, Any
import logging

# Import emotion analysis agent
try:
    from agents.emotion_analysis import EmotionAnalysisAgent, EmotionType, GestureType
    HAS_EMOTION_AGENT = True
except ImportError as e:
    logging.warning(f"Emotion analysis agent not available: {e}")
    HAS_EMOTION_AGENT = False

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Create router
router = APIRouter()

# Initialize emotion analysis agent (lazy loading)
emotion_agent = None

def get_emotion_agent():
    global emotion_agent
    if emotion_agent is None and HAS_EMOTION_AGENT:
        emotion_agent = EmotionAnalysisAgent()
    return emotion_agent

# Request/Response models
class EmotionAnalysisRequest(BaseModel):
    text: str
    context: Optional[str] = None
    language: Optional[str] = "en"
    user_id: Optional[str] = None

class EmotionAnalysisResponse(BaseModel):
    primary_emotion: str
    confidence: float
    emotion_scores: Dict[str, float]
    suggested_gesture: str
    tone_adjustment: str
    context_analysis: str
    status: str

class GestureRecommendationRequest(BaseModel):
    emotion: str
    current_gesture: Optional[str] = None
    model_name: Optional[str] = None

class GestureRecommendationResponse(BaseModel):
    recommended_gesture: str
    expression: str
    animation_style: str
    description: str
    adjustment_reason: str
    model_compatibility: Dict[str, Any]
    status: str

class GestureMappingResponse(BaseModel):
    emotion_gesture_mappings: Dict[str, Dict[str, str]]
    available_emotions: List[str]
    available_gestures: List[str]
    status: str

@router.post("/analyze_emotion", response_model=EmotionAnalysisResponse)
async def analyze_emotion(request: EmotionAnalysisRequest):
    """
    Analyze emotion from user text and suggest appropriate gestures
    Uses BERT-based sentiment analysis for emotion detection
    """
    try:
        if not HAS_EMOTION_AGENT:
            raise HTTPException(
                status_code=503,
                detail="Emotion analysis service is not available"
            )
        
        logger.info(f"Analyzing emotion for text: {request.text[:50]}...")
        
        agent = get_emotion_agent()
        if not agent:
            raise HTTPException(
                status_code=503,
                detail="Failed to initialize emotion analysis agent"
            )
        
        # Analyze emotion
        emotion_result = await agent.analyze_emotion(
            text=request.text,
            context=request.context
        )
        
        return EmotionAnalysisResponse(
            primary_emotion=emotion_result.primary_emotion.value,
            confidence=emotion_result.confidence,
            emotion_scores=emotion_result.emotion_scores,
            suggested_gesture=emotion_result.suggested_gesture.value,
            tone_adjustment=emotion_result.tone_adjustment,
            context_analysis=emotion_result.context_analysis,
            status="success"
        )
        
    except Exception as e:
        logger.error(f"Error analyzing emotion: {str(e)}")
        raise HTTPException(
            status_code=500,
            detail=f"Failed to analyze emotion: {str(e)}"
        )

@router.post("/recommend_gesture", response_model=GestureRecommendationResponse)
async def recommend_gesture(request: GestureRecommendationRequest):
    """
    Get gesture recommendation based on detected emotion
    Provides specific gesture adjustments for 3D models
    """
    try:
        if not HAS_EMOTION_AGENT:
            raise HTTPException(
                status_code=503,
                detail="Emotion analysis service is not available"
            )
        
        logger.info(f"Recommending gesture for emotion: {request.emotion}")
        
        agent = get_emotion_agent()
        if not agent:
            raise HTTPException(
                status_code=503,
                detail="Failed to initialize emotion analysis agent"
            )
        
        # Convert emotion string to EmotionType
        try:
            emotion_type = EmotionType(request.emotion.lower())
        except ValueError:
            raise HTTPException(
                status_code=400,
                detail=f"Invalid emotion type: {request.emotion}. Available emotions: {[e.value for e in EmotionType]}"
            )
        
        # Get gesture mapping
        gesture_mapping = agent.get_gesture_for_emotion(emotion_type)
        if not gesture_mapping:
            raise HTTPException(
                status_code=404,
                detail=f"No gesture mapping found for emotion: {request.emotion}"
            )
        
        # Get gesture adjustments if current gesture is provided
        adjustments = {}
        if request.current_gesture:
            adjustments = agent.suggest_gesture_adjustments(
                request.current_gesture, emotion_type
            )
        
        # Determine model compatibility
        model_compatibility = {
            "compatible_models": ["Man.fbx", "Idle.fbx", "Walking.fbx", "Running.fbx", "Man_Rig.fbx"],
            "recommended_model": "Man_Rig.fbx" if gesture_mapping.animation_style == "dynamic" else "Idle.fbx",
            "gesture_requirements": {
                "facial_expression": gesture_mapping.model_expression,
                "body_animation": gesture_mapping.animation_style,
                "gesture_type": gesture_mapping.gesture.value
            }
        }
        
        return GestureRecommendationResponse(
            recommended_gesture=gesture_mapping.gesture.value,
            expression=gesture_mapping.model_expression,
            animation_style=gesture_mapping.animation_style,
            description=gesture_mapping.description,
            adjustment_reason=adjustments.get("adjustment_reason", f"Optimized for {emotion_type.value} emotion"),
            model_compatibility=model_compatibility,
            status="success"
        )
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error recommending gesture: {str(e)}")
        raise HTTPException(
            status_code=500,
            detail=f"Failed to recommend gesture: {str(e)}"
        )

@router.get("/gesture_mappings", response_model=GestureMappingResponse)
async def get_gesture_mappings():
    """
    Get all available emotion-to-gesture mappings
    Provides complete mapping reference for frontend integration
    """
    try:
        if not HAS_EMOTION_AGENT:
            # Return fallback mappings
            return GestureMappingResponse(
                emotion_gesture_mappings={
                    "neutral": {
                        "gesture": "neutral_idle",
                        "expression": "neutral",
                        "animation_style": "standard",
                        "description": "Standard idle pose with neutral expression"
                    }
                },
                available_emotions=["neutral"],
                available_gestures=["neutral_idle"],
                status="fallback"
            )
        
        agent = get_emotion_agent()
        if not agent:
            raise HTTPException(
                status_code=503,
                detail="Failed to initialize emotion analysis agent"
            )
        
        # Get all gesture mappings
        all_mappings = agent.get_all_gesture_mappings()
        
        # Convert to response format
        emotion_gesture_mappings = {}
        for emotion_type, mapping in all_mappings.items():
            emotion_gesture_mappings[emotion_type.value] = {
                "gesture": mapping.gesture.value,
                "expression": mapping.model_expression,
                "animation_style": mapping.animation_style,
                "description": mapping.description
            }
        
        available_emotions = [emotion.value for emotion in EmotionType]
        available_gestures = [gesture.value for gesture in GestureType]
        
        return GestureMappingResponse(
            emotion_gesture_mappings=emotion_gesture_mappings,
            available_emotions=available_emotions,
            available_gestures=available_gestures,
            status="success"
        )
        
    except Exception as e:
        logger.error(f"Error getting gesture mappings: {str(e)}")
        raise HTTPException(
            status_code=500,
            detail=f"Failed to get gesture mappings: {str(e)}"
        )

@router.post("/analyze_and_recommend", response_model=Dict[str, Any])
async def analyze_emotion_and_recommend_gesture(request: EmotionAnalysisRequest):
    """
    Combined endpoint: analyze emotion and recommend gesture in one call
    Optimized for real-time applications requiring immediate gesture updates
    """
    try:
        if not HAS_EMOTION_AGENT:
            raise HTTPException(
                status_code=503,
                detail="Emotion analysis service is not available"
            )
        
        logger.info(f"Combined analysis for text: {request.text[:50]}...")
        
        agent = get_emotion_agent()
        if not agent:
            raise HTTPException(
                status_code=503,
                detail="Failed to initialize emotion analysis agent"
            )
        
        # Analyze emotion
        emotion_result = await agent.analyze_emotion(
            text=request.text,
            context=request.context
        )
        
        # Get gesture mapping
        gesture_mapping = agent.get_gesture_for_emotion(emotion_result.primary_emotion)
        
        # Create combined response
        response = {
            "emotion_analysis": {
                "primary_emotion": emotion_result.primary_emotion.value,
                "confidence": emotion_result.confidence,
                "emotion_scores": emotion_result.emotion_scores,
                "tone_adjustment": emotion_result.tone_adjustment,
                "context_analysis": emotion_result.context_analysis
            },
            "gesture_recommendation": {
                "recommended_gesture": gesture_mapping.gesture.value if gesture_mapping else "neutral_idle",
                "expression": gesture_mapping.model_expression if gesture_mapping else "neutral",
                "animation_style": gesture_mapping.animation_style if gesture_mapping else "standard",
                "description": gesture_mapping.description if gesture_mapping else "Default neutral pose"
            },
            "model_integration": {
                "recommended_model": "Man_Rig.fbx",
                "gesture_parameters": {
                    "facial_expression": gesture_mapping.model_expression if gesture_mapping else "neutral",
                    "body_gesture": gesture_mapping.gesture.value if gesture_mapping else "neutral_idle",
                    "animation_speed": "normal" if emotion_result.confidence > 0.7 else "slow",
                    "transition_duration": "1.5s"
                }
            },
            "status": "success"
        }
        
        return response
        
    except Exception as e:
        logger.error(f"Error in combined analysis: {str(e)}")
        raise HTTPException(
            status_code=500,
            detail=f"Failed to analyze emotion and recommend gesture: {str(e)}"
        )

@router.get("/health")
async def emotion_service_health():
    """Health check for emotion analysis service"""
    try:
        status = {
            "service": "emotion_analysis",
            "status": "healthy" if HAS_EMOTION_AGENT else "degraded",
            "agent_available": HAS_EMOTION_AGENT,
            "available_endpoints": [
                "/analyze_emotion",
                "/recommend_gesture", 
                "/gesture_mappings",
                "/analyze_and_recommend",
                "/health"
            ]
        }
        
        if HAS_EMOTION_AGENT:
            agent = get_emotion_agent()
            status["agent_initialized"] = agent is not None
            if agent:
                status["available_emotions"] = [e.value for e in EmotionType]
                status["available_gestures"] = [g.value for g in GestureType]
        
        return status
        
    except Exception as e:
        return {
            "service": "emotion_analysis",
            "status": "error",
            "error": str(e)
        }