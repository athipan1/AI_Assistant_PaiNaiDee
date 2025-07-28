"""
AI Assistant API Routes
Handles greeting and search information endpoints
"""

from fastapi import APIRouter, HTTPException
from pydantic import BaseModel
from typing import List, Optional
import logging

# Import agents
from agents.greeting_agent import GreetingAgent
from agents.search_agent import SearchAgent

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Create router
router = APIRouter()

# Initialize agents (lazy loading for better performance)
greeting_agent = None
search_agent = None

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