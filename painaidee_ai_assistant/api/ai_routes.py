"""
AI Assistant API Routes
Handles greeting, search, and enhanced model selection with advanced AI
"""

from fastapi import APIRouter, HTTPException
from pydantic import BaseModel
from typing import List, Optional, Dict, Any
import logging

# Import agents
from agents.greeting_agent import GreetingAgent
from agents.search_agent import SearchAgent
from agents.enhanced_model_selector import get_enhanced_selector

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Create router
router = APIRouter()

# Initialize agents (lazy loading for better performance)
greeting_agent = None
search_agent = None
enhanced_selector = None

def get_greeting_agent():
    global greeting_agent
    if greeting_agent is None:
        greeting_agent = GreetingAgent()
    return greeting_agent

def get_search_agent():
    global search_agent
    if search_agent is None:
        search_agent = SearchAgent()
    return search_agent

def get_model_selector():
    global enhanced_selector
    if enhanced_selector is None:
        enhanced_selector = get_enhanced_selector()
    return enhanced_selector

# Request/Response models
class GreetRequest(BaseModel):
    name: Optional[str] = None
    language: Optional[str] = "en"  # th for Thai, en for English

class GreetResponse(BaseModel):
    greeting: str
    language: str
    status: str

class SearchRequest(BaseModel):
    place_name: str
    language: Optional[str] = "en"

class EnhancedModelRequest(BaseModel):
    question: str
    session_id: Optional[str] = None
    use_advanced_ai: bool = True
    language: str = "en"

class ConversationRequest(BaseModel):
    message: str
    conversation_history: Optional[List[Dict[str, str]]] = None
    language: str = "en"

class TourismAdviceRequest(BaseModel):
    question: str
    location: Optional[str] = None
    preferences: Optional[Dict[str, Any]] = None
    language: str = "en"

class SearchResponse(BaseModel):
    images: List[str]
    map_link: str
    description: str
    rating: float
    status: str

@router.post("/greet", response_model=GreetResponse)
async def greet_user(request: GreetRequest):
    """
    Generate a warm Thai-style greeting using an LLM
    Uses Falcon-7B-Instruct model for personalized greetings
    """
    try:
        logger.info(f"Generating greeting for user: {request.name}")
        
        agent = get_greeting_agent()
        greeting = await agent.generate_greeting(
            name=request.name,
            language=request.language
        )
        
        return GreetResponse(
            greeting=greeting,
            language=request.language,
            status="success"
        )
        
    except Exception as e:
        logger.error(f"Error generating greeting: {str(e)}")
        raise HTTPException(
            status_code=500,
            detail=f"Failed to generate greeting: {str(e)}"
        )

@router.post("/search_info", response_model=SearchResponse)
async def search_place_info(request: SearchRequest):
    """
    Search and summarize information about a place
    Uses BART model for summarization and multiple data sources
    """
    try:
        logger.info(f"Searching information for place: {request.place_name}")
        
        agent = get_search_agent()
        place_info = await agent.search_place_info(
            place_name=request.place_name,
            language=request.language
        )
        
        return SearchResponse(
            images=place_info["images"],
            map_link=place_info["map_link"],
            description=place_info["description"],
            rating=place_info["rating"],
            status="success"
        )
        
    except Exception as e:
        logger.error(f"Error searching place info: {str(e)}")
        # Return fallback data on error
        return SearchResponse(
            images=[
                "https://via.placeholder.com/400x300?text=No+Image+Available"
            ],
            map_link=f"https://www.google.com/maps/search/{request.place_name}",
            description=f"Sorry, we couldn't find detailed information about {request.place_name}. Please try again later.",
            rating=0.0,
            status="fallback"
        )

@router.post("/select_model_enhanced")
async def select_model_enhanced(request: EnhancedModelRequest):
    """
    Enhanced 3D model selection with advanced AI analysis
    
    Combines existing 3D model selection with advanced AI insights
    """
    try:
        logger.info(f"Enhanced model selection for question: {request.question}")
        
        selector = get_model_selector()
        result = await selector.analyze_question_with_ai(
            question=request.question,
            session_id=request.session_id,
            use_advanced_ai=request.use_advanced_ai,
            language=request.language
        )
        
        return {
            "status": "success",
            "model_selection": {
                "selected_model": result.get("selected_model"),
                "confidence": result.get("confidence"),
                "description": result.get("description"),
                "reasoning": result.get("comprehensive_reasoning")
            },
            "ai_enhancement": result.get("enhanced_analysis", {}),
            "ai_enhancement_used": result.get("ai_enhancement_used", False),
            "processing_time": result.get("enhanced_analysis", {}).get("processing_time", 0),
            "language": request.language
        }
        
    except Exception as e:
        logger.error(f"Error in enhanced model selection: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@router.post("/conversation")
async def ai_conversation(request: ConversationRequest):
    """
    Conversational AI with optional 3D model recommendations
    """
    try:
        logger.info(f"AI conversation for message: {request.message}")
        
        selector = get_model_selector()
        result = await selector.conversational_response(
            message=request.message,
            conversation_history=request.conversation_history,
            language=request.language
        )
        
        return {
            "status": "success",
            "response": result.get("response"),
            "suggested_3d_model": result.get("suggested_3d_model"),
            "model_description": result.get("model_description"),
            "ai_model_used": result.get("ai_model_used"),
            "processing_time": result.get("processing_time"),
            "confidence": result.get("confidence"),
            "language": request.language
        }
        
    except Exception as e:
        logger.error(f"Error in AI conversation: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@router.post("/tourism_advice")
async def ai_tourism_advice(request: TourismAdviceRequest):
    """
    AI-powered tourism advice with 3D model context
    """
    try:
        logger.info(f"Tourism advice for question: {request.question}")
        
        selector = get_model_selector()
        result = await selector.get_tourism_advice(
            question=request.question,
            location=request.location,
            preferences=request.preferences,
            language=request.language
        )
        
        return {
            "status": "success",
            "advice": result.get("advice"),
            "related_3d_model": result.get("related_3d_model"),
            "model_description": result.get("model_description"),
            "ai_model_used": result.get("ai_model_used"),
            "processing_time": result.get("processing_time"),
            "confidence": result.get("confidence"),
            "location_context": result.get("location_context"),
            "language": request.language
        }
        
    except Exception as e:
        logger.error(f"Error in tourism advice: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/models/available")
async def get_available_models():
    """
    Get information about all available AI and 3D models
    """
    try:
        selector = get_model_selector()
        result = await selector.get_available_ai_models()
        
        return {
            "status": "success",
            **result
        }
        
    except Exception as e:
        logger.error(f"Error getting available models: {e}")
        raise HTTPException(status_code=500, detail=str(e))