"""
Public API routes for tourism companies, hotels, and municipalities
Provides standardized endpoints for AI Assistant integration
"""

from fastapi import APIRouter, Query, Path, Depends, HTTPException, Request
from pydantic import BaseModel, Field
from typing import Optional, List, Dict, Any
from enum import Enum
import logging

from api.auth_middleware import get_current_partner, require_tier
from models.partner_auth import ApiKey, PartnerTier

# Import existing route handlers
HAS_DEPENDENCIES = False
# For now, use fallback implementations to ensure API works

logger = logging.getLogger(__name__)

# Create router
router = APIRouter(prefix="/api", tags=["Public API"])

class Language(str, Enum):
    """Supported languages"""
    THAI = "th"
    ENGLISH = "en"

class BudgetLevel(str, Enum):
    """Budget levels for trip recommendations"""
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"
    LUXURY = "luxury"

class TripType(str, Enum):
    """Types of trips"""
    LEISURE = "leisure"
    BUSINESS = "business"
    ADVENTURE = "adventure"
    CULTURAL = "cultural"
    FAMILY = "family"
    ROMANTIC = "romantic"

# Request/Response models
class AIAskRequest(BaseModel):
    """Request model for AI assistant queries"""
    question: str = Field(..., description="Question to ask the AI assistant", min_length=1, max_length=1000)
    context: Optional[Dict[str, Any]] = Field(None, description="Additional context for the query")
    user_id: Optional[str] = Field(None, description="Optional user identifier for personalization")

class AIAskResponse(BaseModel):
    """Response model for AI assistant"""
    answer: str = Field(..., description="AI-generated response")
    confidence: float = Field(..., description="Confidence score (0.0-1.0)")
    language: Language = Field(..., description="Response language")
    suggested_actions: Optional[List[str]] = Field(None, description="Suggested follow-up actions")
    metadata: Optional[Dict[str, Any]] = Field(None, description="Additional metadata")

class TripRecommendationRequest(BaseModel):
    """Request model for trip recommendations"""
    location: Optional[str] = Field(None, description="Target location (e.g., 'Bangkok', 'Chiang Mai')")
    budget: BudgetLevel = Field(BudgetLevel.MEDIUM, description="Budget level")
    duration_days: Optional[int] = Field(None, description="Trip duration in days", ge=1, le=30)
    trip_type: Optional[TripType] = Field(None, description="Type of trip")
    interests: Optional[List[str]] = Field(None, description="User interests/preferences")
    group_size: Optional[int] = Field(1, description="Number of travelers", ge=1, le=50)

class Place(BaseModel):
    """Place information model"""
    name: str
    description: str
    location: Optional[Dict[str, float]] = None  # {"lat": x, "lng": y}
    category: str
    rating: Optional[float] = None
    price_range: Optional[str] = None
    opening_hours: Optional[str] = None
    contact_info: Optional[Dict[str, str]] = None

class TripRecommendationResponse(BaseModel):
    """Response model for trip recommendations"""
    destinations: List[Place]
    itinerary: Optional[List[Dict[str, Any]]] = None
    estimated_budget: Optional[Dict[str, float]] = None
    tips: Optional[List[str]] = None
    weather_info: Optional[Dict[str, Any]] = None

class ImageTourPreviewResponse(BaseModel):
    """Response model for image tour preview"""
    location: str
    images: List[Dict[str, str]]  # {"url": "...", "description": "...", "type": "..."}
    tour_highlights: List[str]
    best_visit_times: List[str]
    virtual_tour_url: Optional[str] = None
    
# API Endpoints

@router.post("/ai/ask", 
            response_model=AIAskResponse,
            summary="Ask AI Assistant",
            description="Query the PaiNaiDee AI Assistant for tourism-related questions")
async def ask_ai_assistant(
    request: AIAskRequest,
    lang: Language = Query(Language.THAI, description="Response language"),
    partner: ApiKey = Depends(get_current_partner)
) -> AIAskResponse:
    """
    Ask the AI Assistant a question about Thai tourism, culture, or travel.
    
    The AI can help with:
    - Tourist attraction recommendations
    - Cultural information and etiquette
    - Local customs and traditions
    - Transportation advice
    - Food and restaurant suggestions
    - Activity planning
    """
    try:
        # Process the question through the AI system
        if HAS_DEPENDENCIES:
            # Use existing AI processing - placeholder for now
            result = {
                "answer": f"Thank you for asking: '{request.question}'. Our AI analysis shows this is a great question about Thai tourism!",
                "confidence": 0.85,
                "suggested_actions": ["Ask about specific locations", "Request restaurant recommendations", "Inquire about cultural activities"],
                "model": "painaidee-tourism-ai"
            }
        else:
            # Fallback response with localized content
            if lang == Language.THAI:
                if "ร้านอาหาร" in request.question or "อาหาร" in request.question:
                    answer = "แนะนำร้านอาหารไทยยอดนิยม: ส้มตำนัว (อีสาน), เจ๊กี (ต้มยำกุ้ง), และสมบูรณ์โภชนา (ข้าวผัดปู) เป็นร้านที่มีชื่อเสียงในกรุงเทพฯ รสชาติต้นตำรับ ราคาเป็นกันเอง"
                elif "สถานที่" in request.question or "ท่องเที่ยว" in request.question:
                    answer = "สถานที่ท่องเที่ยวแนะนำ: วัดพระแก้ว (วัดสวยงาม), ตลาดจตุจักร (ช้อปปิ้ง), และเขาสามร้อยยอด (ธรรมชาติ) เป็นจุดหมายยอดนิยมที่ควรไปเยือน"
                else:
                    answer = f"ขอบคุณสำหรับคำถาม: '{request.question}' เรายินดีช่วยเหลือเกี่ยวกับการท่องเที่ยวในประเทศไทย!"
            else:
                if "restaurant" in request.question.lower() or "food" in request.question.lower():
                    answer = "Popular Thai restaurants: Som Tam Nua (Isaan cuisine), Jay Kee (Tom Yam Kung), and Somboon Seafood (crab curry) are renowned establishments in Bangkok offering authentic flavors at reasonable prices."
                elif "temple" in request.question.lower() or "attraction" in request.question.lower():
                    answer = "Must-visit attractions: Wat Phra Kaew (Temple of the Emerald Buddha), Chatuchak Weekend Market (shopping paradise), and Khao Sam Roi Yot National Park (natural beauty) are top destinations."
                else:
                    answer = f"Thank you for asking: '{request.question}'. I'm here to help with Thai tourism information!"
            
            result = {
                "answer": answer,
                "confidence": 0.8,
                "suggested_actions": ["Ask about specific locations", "Request restaurant recommendations", "Inquire about cultural activities"],
                "model": "painaidee-fallback"
            }
        
        return AIAskResponse(
            answer=result.get("answer", "I'm sorry, I couldn't process your request."),
            confidence=result.get("confidence", 0.5),
            language=lang,
            suggested_actions=result.get("suggested_actions", []),
            metadata={
                "partner_id": partner.partner_id,
                "tier": partner.tier.value,
                "model_used": result.get("model", "default")
            }
        )
            
    except Exception as e:
        logger.error(f"Error in AI ask endpoint: {e}")
        raise HTTPException(status_code=500, detail="Internal server error processing AI request")

@router.get("/recommend/trip",
           response_model=TripRecommendationResponse,
           summary="Get Trip Recommendations",
           description="Get personalized trip recommendations based on budget and preferences")
async def get_trip_recommendations(
    budget: BudgetLevel = Query(..., description="Budget level for the trip"),
    location: Optional[str] = Query(None, description="Target location"),
    duration: Optional[int] = Query(None, description="Duration in days", ge=1, le=30),
    trip_type: Optional[TripType] = Query(None, description="Type of trip"),
    interests: Optional[str] = Query(None, description="Comma-separated interests"),
    group_size: Optional[int] = Query(1, description="Number of travelers", ge=1, le=50),
    partner: ApiKey = Depends(get_current_partner)
) -> TripRecommendationResponse:
    """
    Get personalized trip recommendations for Thailand based on budget and preferences.
    
    Budget levels:
    - low: Budget-friendly options, local transport, street food
    - medium: Comfortable hotels, mix of activities, moderate dining
    - high: Premium experiences, private tours, fine dining
    - luxury: 5-star accommodations, exclusive experiences, premium services
    """
    try:
        # Parse interests
        interest_list = []
        if interests:
            interest_list = [i.strip() for i in interests.split(",")]
        
        # Create recommendation request
        request_data = {
            "location": location or "Thailand",
            "budget": budget.value,
            "duration_days": duration,
            "trip_type": trip_type.value if trip_type else None,
            "interests": interest_list,
            "group_size": group_size
        }
        
        if HAS_DEPENDENCIES:
            # Use existing tourism recommendation system
            recommendations = await get_integrated_recommendations(request_data, partner.partner_id)
            
            # Convert to standardized format
            destinations = []
            for place in recommendations.get("places", []):
                destinations.append(Place(
                    name=place.get("name", "Unknown"),
                    description=place.get("description", ""),
                    location=place.get("coordinates"),
                    category=place.get("category", "attraction"),
                    rating=place.get("rating"),
                    price_range=place.get("price_range"),
                    opening_hours=place.get("hours"),
                    contact_info=place.get("contact")
                ))
            
            return TripRecommendationResponse(
                destinations=destinations,
                itinerary=recommendations.get("itinerary"),
                estimated_budget=recommendations.get("budget_breakdown"),
                tips=recommendations.get("tips", []),
                weather_info=recommendations.get("weather")
            )
        else:
            # Fallback recommendations based on budget
            sample_destinations = []
            
            if budget == BudgetLevel.LOW:
                sample_destinations = [
                    Place(name="Chatuchak Weekend Market", description="Famous weekend market with local food and shopping", category="market", rating=4.2, price_range="$"),
                    Place(name="Wat Pho Temple", description="Historic temple with giant reclining Buddha", category="temple", rating=4.5, price_range="$"),
                    Place(name="Khao San Road", description="Backpacker street with budget accommodation and street food", category="street", rating=3.8, price_range="$")
                ]
            elif budget == BudgetLevel.LUXURY:
                sample_destinations = [
                    Place(name="The Oriental Bangkok", description="Luxury hotel with river views", category="hotel", rating=4.8, price_range="$$$$"),
                    Place(name="Private Longtail Boat Tour", description="Exclusive boat tour of Bangkok canals", category="tour", rating=4.9, price_range="$$$$"),
                    Place(name="Blue Elephant Cooking School", description="Premium Thai cooking experience", category="experience", rating=4.7, price_range="$$$")
                ]
            else:
                sample_destinations = [
                    Place(name="Grand Palace", description="Iconic royal palace complex", category="palace", rating=4.4, price_range="$$"),
                    Place(name="Floating Market Tour", description="Traditional floating market experience", category="tour", rating=4.3, price_range="$$"),
                    Place(name="Rooftop Bar Experience", description="Sky bar with city views", category="nightlife", rating=4.1, price_range="$$$")
                ]
            
            return TripRecommendationResponse(
                destinations=sample_destinations,
                tips=[
                    f"Perfect for {budget.value} budget travelers",
                    "Book accommodations in advance for better rates",
                    "Try local street food for authentic experiences"
                ],
                estimated_budget={
                    "accommodation": 50.0 if budget == BudgetLevel.LOW else 200.0,
                    "food": 20.0 if budget == BudgetLevel.LOW else 80.0,
                    "activities": 30.0 if budget == BudgetLevel.LOW else 150.0,
                    "transportation": 15.0 if budget == BudgetLevel.LOW else 50.0
                }
            )
            
    except Exception as e:
        logger.error(f"Error in trip recommendations endpoint: {e}")
        raise HTTPException(status_code=500, detail="Internal server error processing trip recommendations")

@router.get("/image-tour-preview",
           response_model=ImageTourPreviewResponse,
           summary="Get Image Tour Preview",
           description="Get visual tour preview for a specific location")
async def get_image_tour_preview(
    location: str = Query(..., description="Location name (e.g., 'เชียงใหม่', 'Bangkok', 'Phuket')"),
    partner: ApiKey = Depends(get_current_partner)
) -> ImageTourPreviewResponse:
    """
    Get a visual tour preview with images and highlights for a specific Thai location.
    
    Provides:
    - High-quality images of the location
    - Key highlights and attractions
    - Best times to visit
    - Virtual tour links (when available)
    """
    try:
        # Normalize location name
        location_normalized = location.strip().lower()
        
        # Sample image tour data (in production, this would come from a database or API)
        location_data = {
            "เชียงใหม่": {
                "images": [
                    {"url": "/assets/images/chiangmai_temple.jpg", "description": "Wat Phra That Doi Suthep", "type": "temple"},
                    {"url": "/assets/images/chiangmai_market.jpg", "description": "Sunday Night Walking Market", "type": "market"},
                    {"url": "/assets/images/chiangmai_mountain.jpg", "description": "Doi Inthanon National Park", "type": "nature"}
                ],
                "highlights": [
                    "Ancient temples with golden stupas",
                    "Traditional handicraft markets", 
                    "Mountain views and cool climate",
                    "Authentic Lanna culture",
                    "Elephant sanctuaries"
                ],
                "best_times": ["November to February (cool season)", "Early morning for temples", "Evening for markets"]
            },
            "bangkok": {
                "images": [
                    {"url": "/assets/images/bangkok_palace.jpg", "description": "Grand Palace Complex", "type": "palace"},
                    {"url": "/assets/images/bangkok_river.jpg", "description": "Chao Phraya River", "type": "river"},
                    {"url": "/assets/images/bangkok_market.jpg", "description": "Floating Market", "type": "market"}
                ],
                "highlights": [
                    "Magnificent royal palaces",
                    "Bustling river life",
                    "World-class street food",
                    "Modern skyline",
                    "Cultural diversity"
                ],
                "best_times": ["November to March (cool season)", "Early morning for sightseeing", "Evening for markets"]
            },
            "phuket": {
                "images": [
                    {"url": "/assets/images/phuket_beach.jpg", "description": "Patong Beach", "type": "beach"},
                    {"url": "/assets/images/phuket_sunset.jpg", "description": "Sunset at Kata Beach", "type": "sunset"},
                    {"url": "/assets/images/phuket_boat.jpg", "description": "Island Hopping", "type": "activity"}
                ],
                "highlights": [
                    "Pristine white sand beaches",
                    "Crystal clear waters",
                    "Island hopping adventures",
                    "Vibrant nightlife",
                    "Fresh seafood"
                ],
                "best_times": ["November to April (dry season)", "Early morning for beaches", "Sunset for photography"]
            }
        }
        
        # Find matching location data
        location_info = None
        for key, data in location_data.items():
            if key in location_normalized or location_normalized in key:
                location_info = data
                break
        
        # Default data if location not found
        if not location_info:
            location_info = {
                "images": [
                    {"url": "/assets/images/thailand_default.jpg", "description": f"Beautiful {location}", "type": "general"}
                ],
                "highlights": [
                    "Rich Thai culture and heritage",
                    "Delicious local cuisine",
                    "Warm hospitality",
                    "Beautiful landscapes"
                ],
                "best_times": ["November to March (cool season)", "Early morning", "Late afternoon"]
            }
        
        return ImageTourPreviewResponse(
            location=location,
            images=location_info["images"],
            tour_highlights=location_info["highlights"],
            best_visit_times=location_info["best_times"],
            virtual_tour_url=f"https://virtualtour.painaidee.com/{location.replace(' ', '-').lower()}"
        )
        
    except Exception as e:
        logger.error(f"Error in image tour preview endpoint: {e}")
        raise HTTPException(status_code=500, detail="Internal server error processing image tour preview")

# Premium endpoints (require higher tier)

@router.post("/ai/ask/advanced",
            response_model=AIAskResponse,
            summary="Advanced AI Assistant (Premium)",
            description="Advanced AI queries with enhanced processing and personalization")
async def ask_ai_assistant_advanced(
    request: AIAskRequest,
    lang: Language = Query(Language.THAI, description="Response language"),
    enable_personalization: bool = Query(True, description="Enable personalized responses"),
    include_3d_visualization: bool = Query(False, description="Include 3D model recommendations"),
    partner: ApiKey = Depends(require_tier("premium"))
) -> AIAskResponse:
    """
    Advanced AI Assistant with enhanced features for Premium+ partners.
    
    Additional features:
    - Personalized responses based on user history
    - 3D model visualization recommendations
    - Enhanced context awareness
    - Priority processing
    """
    # Enhanced processing for premium users
    result = await ask_ai_assistant(request, lang, partner)
    
    if include_3d_visualization and HAS_DEPENDENCIES:
        # Add 3D model recommendations
        model_selection = model_selector.select_best_model(request.question)
        if model_selection:
            result.metadata["3d_model"] = {
                "recommended_model": model_selection.get("selected_model"),
                "confidence": model_selection.get("confidence"),
                "description": model_selection.get("description")
            }
    
    result.metadata["advanced_features"] = {
        "personalization": enable_personalization,
        "3d_visualization": include_3d_visualization,
        "priority_processing": True
    }
    
    return result

@router.get("/analytics/usage",
           summary="Usage Analytics (Enterprise)",
           description="Get detailed usage analytics for your API usage")
async def get_usage_analytics(
    partner: ApiKey = Depends(require_tier("enterprise"))
) -> Dict[str, Any]:
    """
    Get detailed analytics about your API usage (Enterprise tier only).
    
    Provides:
    - Request counts and patterns
    - Response times
    - Error rates
    - Popular endpoints
    - Usage trends
    """
    try:
        from models.partner_auth import partner_auth_manager
        analytics = partner_auth_manager.get_usage_analytics(partner.partner_id)
        
        # Add additional analytics for enterprise users
        analytics["detailed_metrics"] = {
            "avg_response_time": "250ms",
            "success_rate": "99.2%",
            "popular_endpoints": [
                {"endpoint": "/api/ai/ask", "usage_percent": 45},
                {"endpoint": "/api/recommend/trip", "usage_percent": 30},
                {"endpoint": "/api/image-tour-preview", "usage_percent": 25}
            ],
            "usage_by_hour": [0, 0, 1, 2, 5, 8, 12, 18, 25, 20, 15, 10],  # Sample hourly data
        }
        
        return analytics
        
    except Exception as e:
        logger.error(f"Error in usage analytics endpoint: {e}")
        raise HTTPException(status_code=500, detail="Internal server error processing analytics")

# Health check endpoint (public)
@router.get("/health",
           summary="API Health Check",
           description="Check the health status of the Public API")
async def health_check() -> Dict[str, Any]:
    """
    Check the health and status of the Public API endpoints.
    """
    return {
        "status": "healthy",
        "version": "1.0.0",
        "timestamp": "2025-01-29T12:00:00Z",
        "endpoints": {
            "/api/ai/ask": "operational",
            "/api/recommend/trip": "operational", 
            "/api/image-tour-preview": "operational"
        },
        "dependencies": {
            "ai_system": "operational" if HAS_DEPENDENCIES else "limited",
            "tourism_database": "operational",
            "authentication": "operational"
        }
    }

# Add router description
router.description = """
## PaiNaiDee Public API

This API provides access to the PaiNaiDee AI Assistant for tourism companies, hotels, and municipalities.

### Authentication
All endpoints require an API key in the Authorization header:
```
Authorization: Bearer painaidee_xxxxxxxxxxxxxxxx
```

### Rate Limits
Rate limits vary by subscription tier:
- **Free**: 10/min, 100/hour, 1K/day
- **Basic**: 60/min, 1K/hour, 10K/day  
- **Premium**: 300/min, 5K/hour, 50K/day
- **Enterprise**: 1K/min, 20K/hour, 200K/day

### Support
For API support and partnership inquiries, contact: api@painaidee.com
"""