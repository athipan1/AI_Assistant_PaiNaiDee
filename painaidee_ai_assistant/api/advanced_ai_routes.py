"""
Advanced AI API Routes
Provides endpoints for llama.cpp, OpenChat, OpenHermes integration
"""

import asyncio
import logging
from typing import Dict, List, Optional, Any
from fastapi import APIRouter, HTTPException, BackgroundTasks
from pydantic import BaseModel, Field

from agents.advanced_ai_models import (
    ai_manager, 
    ModelCapability, 
    AIResponse,
    initialize_advanced_ai
)

logger = logging.getLogger(__name__)

# Pydantic models for API requests/responses
class AdvancedAIRequest(BaseModel):
    prompt: str = Field(..., description="Input prompt for the AI model")
    capability: str = Field(default="conversation", description="Required capability")
    language: str = Field(default="en", description="Language preference (en/th)")
    model_name: Optional[str] = Field(None, description="Specific model to use")
    max_tokens: Optional[int] = Field(None, description="Maximum tokens to generate")
    temperature: Optional[float] = Field(None, description="Temperature for generation")
    context: Optional[str] = Field(None, description="Additional context")

class AdvancedAIResponse(BaseModel):
    text: str
    model_used: str
    confidence: float
    capabilities_used: List[str]
    processing_time: float
    metadata: Dict[str, Any]

class TourismAIRequest(BaseModel):
    question: str = Field(..., description="Tourism-related question")
    location: Optional[str] = Field(None, description="Current location")
    preferences: Optional[Dict[str, Any]] = Field(None, description="User preferences")
    language: str = Field(default="en", description="Response language")

class ModelListResponse(BaseModel):
    models: List[Dict[str, Any]]
    total_count: int
    available_count: int

class ModelStatusResponse(BaseModel):
    model_name: str
    status: str
    capabilities: List[str]
    languages: List[str]
    metadata: Dict[str, Any]

# Create router
router = APIRouter(prefix="/advanced_ai", tags=["Advanced AI Models"])

# Initialization flag
_initialized = False

async def ensure_initialized():
    """Ensure the AI manager is initialized"""
    global _initialized
    if not _initialized:
        try:
            await initialize_advanced_ai()
            _initialized = True
            logger.info("Advanced AI system initialized successfully")
        except Exception as e:
            logger.error(f"Failed to initialize advanced AI system: {e}")
            raise HTTPException(status_code=500, detail="AI system initialization failed")

@router.on_event("startup")
async def startup_event():
    """Initialize AI models on startup"""
    await ensure_initialized()

@router.post("/generate", response_model=AdvancedAIResponse)
async def generate_text(request: AdvancedAIRequest):
    """
    Generate text using advanced AI models
    
    Supports llama.cpp, OpenChat, and OpenHermes models
    """
    await ensure_initialized()
    
    try:
        # Map capability string to enum
        capability_map = {
            "conversation": ModelCapability.CONVERSATION,
            "question_answering": ModelCapability.QUESTION_ANSWERING,
            "text_generation": ModelCapability.TEXT_GENERATION,
            "tourism_advice": ModelCapability.TOURISM_ADVICE,
            "emotion_analysis": ModelCapability.EMOTION_ANALYSIS
        }
        
        capability = capability_map.get(request.capability, ModelCapability.CONVERSATION)
        
        # Generate response
        ai_response = await ai_manager.generate_response(
            prompt=request.prompt,
            capability=capability,
            language=request.language,
            model_name=request.model_name,
            max_tokens=request.max_tokens,
            temperature=request.temperature
        )
        
        return AdvancedAIResponse(
            text=ai_response.text,
            model_used=ai_response.model_used,
            confidence=ai_response.confidence,
            capabilities_used=[cap.value for cap in ai_response.capabilities_used],
            processing_time=ai_response.processing_time,
            metadata=ai_response.metadata
        )
        
    except Exception as e:
        logger.error(f"Error in advanced AI generation: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@router.post("/tourism_advisor")
async def tourism_advisor(request: TourismAIRequest):
    """
    Specialized tourism advice using advanced AI models
    
    Provides intelligent tourism recommendations using context-aware AI
    """
    await ensure_initialized()
    
    try:
        # Build tourism-specific prompt
        prompt_parts = [
            f"Tourism Question: {request.question}"
        ]
        
        if request.location:
            prompt_parts.append(f"Current Location: {request.location}")
        
        if request.preferences:
            pref_text = ", ".join([f"{k}: {v}" for k, v in request.preferences.items()])
            prompt_parts.append(f"User Preferences: {pref_text}")
        
        prompt_parts.append("Please provide helpful tourism advice in a friendly, informative manner.")
        
        full_prompt = "\n".join(prompt_parts)
        
        # Generate response using tourism capability
        ai_response = await ai_manager.generate_response(
            prompt=full_prompt,
            capability=ModelCapability.TOURISM_ADVICE,
            language=request.language
        )
        
        return {
            "advice": ai_response.text,
            "model_used": ai_response.model_used,
            "confidence": ai_response.confidence,
            "processing_time": ai_response.processing_time,
            "location_context": request.location,
            "language": request.language
        }
        
    except Exception as e:
        logger.error(f"Error in tourism advisor: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/models", response_model=ModelListResponse)
async def list_models():
    """
    List all available advanced AI models
    """
    await ensure_initialized()
    
    try:
        models = ai_manager.get_available_models()
        available_count = sum(1 for model in models if model.get("available", False))
        
        return ModelListResponse(
            models=models,
            total_count=len(models),
            available_count=available_count
        )
        
    except Exception as e:
        logger.error(f"Error listing models: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/models/{model_name}/status", response_model=ModelStatusResponse)
async def get_model_status(model_name: str):
    """
    Get detailed status of a specific model
    """
    await ensure_initialized()
    
    try:
        models = ai_manager.get_available_models()
        model_info = next((m for m in models if m["name"] == model_name), None)
        
        if not model_info:
            raise HTTPException(status_code=404, detail=f"Model {model_name} not found")
        
        # Check if model is loaded
        is_loaded = model_name in ai_manager.models
        
        return ModelStatusResponse(
            model_name=model_name,
            status="loaded" if is_loaded else ("available" if model_info["available"] else "unavailable"),
            capabilities=model_info["capabilities"],
            languages=model_info["languages"],
            metadata={
                "type": model_info["type"],
                "is_local": model_info["is_local"],
                "priority": model_info["priority"],
                "loaded": is_loaded
            }
        )
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error getting model status: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@router.post("/models/{model_name}/load")
async def load_model(model_name: str, background_tasks: BackgroundTasks):
    """
    Preload a specific model for faster responses
    """
    await ensure_initialized()
    
    try:
        # Check if model exists
        models = ai_manager.get_available_models()
        model_info = next((m for m in models if m["name"] == model_name), None)
        
        if not model_info:
            raise HTTPException(status_code=404, detail=f"Model {model_name} not found")
        
        if not model_info["available"]:
            raise HTTPException(status_code=400, detail=f"Model {model_name} is not available")
        
        # Check if already loaded
        if model_name in ai_manager.models:
            return {"message": f"Model {model_name} is already loaded", "status": "loaded"}
        
        # Load model in background
        async def load_model_task():
            try:
                await ai_manager.get_model(model_name)
                logger.info(f"Successfully loaded model {model_name}")
            except Exception as e:
                logger.error(f"Failed to load model {model_name}: {e}")
        
        background_tasks.add_task(load_model_task)
        
        return {"message": f"Loading model {model_name}...", "status": "loading"}
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error loading model: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@router.post("/conversation")
async def conversation(request: AdvancedAIRequest):
    """
    Conversational AI endpoint optimized for natural dialogue
    """
    await ensure_initialized()
    
    # Force conversation capability
    request.capability = "conversation"
    
    # Add conversational context to prompt if provided
    if request.context:
        enhanced_prompt = f"Context: {request.context}\n\nUser: {request.prompt}\nAssistant:"
    else:
        enhanced_prompt = f"User: {request.prompt}\nAssistant:"
    
    request.prompt = enhanced_prompt
    
    # Call the general generate endpoint
    return await generate_text(request)

@router.post("/question_answering")
async def question_answering(request: AdvancedAIRequest):
    """
    Question answering endpoint optimized for factual responses
    """
    await ensure_initialized()
    
    # Force question answering capability
    request.capability = "question_answering"
    
    # Add Q&A context to prompt
    enhanced_prompt = f"Question: {request.prompt}\nAnswer:"
    request.prompt = enhanced_prompt
    
    # Call the general generate endpoint
    return await generate_text(request)

@router.get("/capabilities")
async def get_capabilities():
    """
    Get list of all supported AI capabilities
    """
    capabilities = [
        {
            "name": "conversation",
            "description": "Natural conversation and dialogue"
        },
        {
            "name": "question_answering", 
            "description": "Factual question answering"
        },
        {
            "name": "text_generation",
            "description": "Creative text generation"
        },
        {
            "name": "tourism_advice",
            "description": "Tourism and travel recommendations"
        },
        {
            "name": "emotion_analysis",
            "description": "Emotion detection and analysis"
        }
    ]
    
    return {
        "capabilities": capabilities,
        "total_count": len(capabilities)
    }

@router.get("/health")
async def health_check():
    """
    Health check for advanced AI system
    """
    try:
        await ensure_initialized()
        
        models = ai_manager.get_available_models()
        available_count = sum(1 for model in models if model.get("available", False))
        loaded_count = len(ai_manager.models)
        
        return {
            "status": "healthy",
            "models_configured": len(models),
            "models_available": available_count,
            "models_loaded": loaded_count,
            "capabilities": [cap.value for cap in ModelCapability],
            "languages_supported": ["en", "th"]
        }
        
    except Exception as e:
        logger.error(f"Health check failed: {e}")
        return {
            "status": "unhealthy",
            "error": str(e)
        }

# Export router
__all__ = ["router"]