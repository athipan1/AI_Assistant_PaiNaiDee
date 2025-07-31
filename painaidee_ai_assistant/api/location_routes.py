"""
Location-based Tourism API Routes
Provides endpoints for Google Places integration and accommodation booking
"""

from fastapi import APIRouter, HTTPException, Query
from pydantic import BaseModel
from typing import List, Optional, Dict, Any
from datetime import datetime
import logging

from models.external_apis import external_api_manager, Place, Accommodation, LocationSearchFilter

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Create router
router = APIRouter(prefix="/location", tags=["location"])

# Request/Response models
class LocationRequest(BaseModel):
    lat: float
    lng: float
    query: Optional[str] = ""
    radius: Optional[int] = 5000
    place_types: Optional[List[str]] = None
    min_rating: Optional[float] = None
    limit: Optional[int] = 20

class AccommodationSearchRequest(BaseModel):
    lat: float
    lng: float
    query: Optional[str] = ""
    min_rating: Optional[float] = None
    max_price: Optional[float] = None
    check_in: Optional[str] = None  # YYYY-MM-DD
    check_out: Optional[str] = None  # YYYY-MM-DD
    guests: Optional[int] = 2
    limit: Optional[int] = 20

class CombinedAccommodationRequest(BaseModel):
    lat: float
    lng: float
    query: Optional[str] = ""
    min_rating: Optional[float] = None
    max_price: Optional[float] = None
    check_in: Optional[str] = None  # YYYY-MM-DD
    check_out: Optional[str] = None  # YYYY-MM-DD
    guests: Optional[int] = 2
    limit: Optional[int] = 20
    # User preferences embedded
    budget: Optional[float] = None
    property_type: Optional[str] = None  # hotel, resort, guesthouse
    preferred_amenities: Optional[List[str]] = None
    style: Optional[str] = None  # luxury, budget, boutique, beach, city


class UserPreferencesRequest(BaseModel):
    budget: Optional[float] = None
    property_type: Optional[str] = None  # hotel, resort, guesthouse
    preferred_amenities: Optional[List[str]] = None
    style: Optional[str] = None  # luxury, budget, boutique, beach, city

class TourismRecommendationRequest(BaseModel):
    lat: float
    lng: float
    user_preferences: Optional[UserPreferencesRequest] = None
    include_accommodations: Optional[bool] = True
    include_restaurants: Optional[bool] = True
    include_attractions: Optional[bool] = True

class PlaceResponse(BaseModel):
    place_id: str
    name: str
    address: str
    location: Dict[str, float]
    rating: Optional[float] = None
    types: List[str] = []
    phone_number: Optional[str] = None
    website: Optional[str] = None
    photos: List[str] = []
    price_level: Optional[int] = None
    opening_hours: Optional[Dict] = None
    reviews: Optional[List[Dict]] = None
    business_status: str = "OPERATIONAL"

class AccommodationResponse(BaseModel):
    accommodation_id: str
    name: str
    address: str
    location: Dict[str, float]
    rating: Optional[float] = None
    review_count: int = 0
    price_per_night: Optional[float] = None
    currency: str = "THB"
    images: List[str] = []
    amenities: List[str] = []
    room_types: List[Dict] = []
    booking_url: str = ""
    affiliate_link: str = ""
    cancellation_policy: str = ""
    property_type: str = "hotel"
    match_analysis: Optional[Dict[str, Any]] = None

@router.post("/places/search", response_model=List[PlaceResponse])
async def search_places(request: LocationRequest):
    """Search for places using Google Places API"""
    try:
        location = {"lat": request.lat, "lng": request.lng}
        
        places = await external_api_manager.search_places_nearby(
            location=location,
            query=request.query,
            place_types=request.place_types,
            radius=request.radius,
            min_rating=request.min_rating,
            limit=request.limit
        )
        
        # Convert to response format
        response_places = []
        for place in places:
            response_places.append(PlaceResponse(
                place_id=place.place_id,
                name=place.name,
                address=place.address,
                location=place.location,
                rating=place.rating,
                types=place.types or [],
                phone_number=place.phone_number,
                website=place.website,
                photos=place.photos or [],
                price_level=place.price_level,
                opening_hours=place.opening_hours,
                reviews=place.reviews,
                business_status=place.business_status
            ))
        
        return response_places
        
    except Exception as e:
        logger.error(f"Error searching places: {e}")
        raise HTTPException(status_code=500, detail=f"Search failed: {str(e)}")

@router.get("/places/{place_id}", response_model=PlaceResponse)
async def get_place_details(place_id: str):
    """Get detailed information about a specific place"""
    try:
        connector = external_api_manager.connectors.get("google_places")
        if not connector:
            raise HTTPException(status_code=503, detail="Google Places API not configured")
        
        place = await connector.get_place_details(place_id)
        if not place:
            raise HTTPException(status_code=404, detail="Place not found")
        
        return PlaceResponse(
            place_id=place.place_id,
            name=place.name,
            address=place.address,
            location=place.location,
            rating=place.rating,
            types=place.types or [],
            phone_number=place.phone_number,
            website=place.website,
            photos=place.photos or [],
            price_level=place.price_level,
            opening_hours=place.opening_hours,
            reviews=place.reviews,
            business_status=place.business_status
        )
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error getting place details: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to get place details: {str(e)}")

@router.post("/accommodations/search", response_model=List[AccommodationResponse])
async def search_accommodations(request: AccommodationSearchRequest):
    """Search for accommodations near a location"""
    try:
        location = {"lat": request.lat, "lng": request.lng}
        
        accommodations = await external_api_manager.search_accommodations_nearby(
            location=location,
            query=request.query,
            min_rating=request.min_rating,
            limit=request.limit
        )
        
        # Convert to response format
        response_accommodations = []
        for accommodation in accommodations:
            # Filter by price if specified
            if request.max_price and accommodation.price_per_night and accommodation.price_per_night > request.max_price:
                continue
            
            response_accommodations.append(AccommodationResponse(
                accommodation_id=accommodation.accommodation_id,
                name=accommodation.name,
                address=accommodation.address,
                location=accommodation.location,
                rating=accommodation.rating,
                review_count=accommodation.review_count,
                price_per_night=accommodation.price_per_night,
                currency=accommodation.currency,
                images=accommodation.images or [],
                amenities=accommodation.amenities or [],
                room_types=accommodation.room_types or [],
                booking_url=accommodation.booking_url,
                affiliate_link=accommodation.affiliate_link,
                cancellation_policy=accommodation.cancellation_policy,
                property_type=accommodation.property_type
            ))
        
        return response_accommodations
        
    except Exception as e:
        logger.error(f"Error searching accommodations: {e}")
        raise HTTPException(status_code=500, detail=f"Search failed: {str(e)}")

@router.post("/accommodations/recommendations", response_model=List[AccommodationResponse])
async def get_accommodation_recommendations(request: AccommodationSearchRequest):
    """Get AI-powered accommodation recommendations based on user preferences"""
    try:
        location = {"lat": request.lat, "lng": request.lng}
        
        accommodations = await external_api_manager.search_accommodations_nearby(
            location=location,
            query=request.query,
            min_rating=request.min_rating,
            limit=request.limit * 2  # Get more results for better filtering
        )
        
        # Apply AI analysis for each accommodation
        analyzed_accommodations = []
        for accommodation in accommodations:
            # Filter by price if specified
            if request.max_price and accommodation.price_per_night and accommodation.price_per_night > request.max_price:
                continue
            
            # Analyze match with user preferences (create empty preferences if none provided)
            match_analysis = None
            preferences_dict = {
                "budget": request.max_price,
                "property_type": None,
                "preferred_amenities": [],
                "style": None
            }
            match_analysis = external_api_manager.analyze_accommodation_match(accommodation, preferences_dict)
            
            analyzed_accommodations.append((accommodation, match_analysis))
        
        # Sort by match score if available, otherwise by rating
        analyzed_accommodations.sort(key=lambda x: x[1]["match_score"] if x[1] else 0, reverse=True)
        
        # Convert to response format
        response_accommodations = []
        for accommodation, match_analysis in analyzed_accommodations[:request.limit]:
            response_accommodations.append(AccommodationResponse(
                accommodation_id=accommodation.accommodation_id,
                name=accommodation.name,
                address=accommodation.address,
                location=accommodation.location,
                rating=accommodation.rating,
                review_count=accommodation.review_count,
                price_per_night=accommodation.price_per_night,
                currency=accommodation.currency,
                images=accommodation.images or [],
                amenities=accommodation.amenities or [],
                room_types=accommodation.room_types or [],
                booking_url=accommodation.booking_url,
                affiliate_link=accommodation.affiliate_link,
                cancellation_policy=accommodation.cancellation_policy,
                property_type=accommodation.property_type,
                match_analysis=match_analysis
            ))
        
        return response_accommodations
        
    except Exception as e:
        logger.error(f"Error getting accommodation recommendations: {e}")
        raise HTTPException(status_code=500, detail=f"Recommendations failed: {str(e)}")

@router.post("/accommodations/ai-recommendations", response_model=List[AccommodationResponse])
async def get_ai_accommodation_recommendations(
    search_request: AccommodationSearchRequest,
    user_preferences: Optional[UserPreferencesRequest] = None
):
    """Get AI-powered accommodation recommendations with detailed user preferences"""
    try:
        location = {"lat": search_request.lat, "lng": search_request.lng}
        
        accommodations = await external_api_manager.search_accommodations_nearby(
            location=location,
            query=search_request.query,
            min_rating=search_request.min_rating,
            limit=search_request.limit * 2  # Get more results for better filtering
        )
        
        # Apply AI analysis for each accommodation
        analyzed_accommodations = []
        for accommodation in accommodations:
            # Filter by price if specified
            if search_request.max_price and accommodation.price_per_night and accommodation.price_per_night > search_request.max_price:
                continue
            
            # Analyze match with user preferences
            match_analysis = None
            if user_preferences:
                preferences_dict = {
                    "budget": user_preferences.budget,
                    "property_type": user_preferences.property_type,
                    "preferred_amenities": user_preferences.preferred_amenities or [],
                    "style": user_preferences.style
                }
                match_analysis = external_api_manager.analyze_accommodation_match(accommodation, preferences_dict)
            
            analyzed_accommodations.append((accommodation, match_analysis))
        
        # Sort by match score if available, otherwise by rating
        if user_preferences:
            analyzed_accommodations.sort(key=lambda x: x[1]["match_score"] if x[1] else 0, reverse=True)
        else:
            analyzed_accommodations.sort(key=lambda x: x[0].rating or 0, reverse=True)
        
        # Convert to response format
        response_accommodations = []
        for accommodation, match_analysis in analyzed_accommodations[:search_request.limit]:
            response_accommodations.append(AccommodationResponse(
                accommodation_id=accommodation.accommodation_id,
                name=accommodation.name,
                address=accommodation.address,
                location=accommodation.location,
                rating=accommodation.rating,
                review_count=accommodation.review_count,
                price_per_night=accommodation.price_per_night,
                currency=accommodation.currency,
                images=accommodation.images or [],
                amenities=accommodation.amenities or [],
                room_types=accommodation.room_types or [],
                booking_url=accommodation.booking_url,
                affiliate_link=accommodation.affiliate_link,
                cancellation_policy=accommodation.cancellation_policy,
                property_type=accommodation.property_type,
                match_analysis=match_analysis
            ))
        
        return response_accommodations
        
    except Exception as e:
        logger.error(f"Error getting AI accommodation recommendations: {e}")
        raise HTTPException(status_code=500, detail=f"AI recommendations failed: {str(e)}")

@router.post("/accommodations/smart-search", response_model=List[AccommodationResponse])
async def smart_accommodation_search(request: CombinedAccommodationRequest):
    """Smart accommodation search with integrated AI analysis"""
    try:
        location = {"lat": request.lat, "lng": request.lng}
        
        accommodations = await external_api_manager.search_accommodations_nearby(
            location=location,
            query=request.query,
            min_rating=request.min_rating,
            limit=request.limit * 2  # Get more results for better filtering
        )
        
        # Apply AI analysis for each accommodation
        analyzed_accommodations = []
        for accommodation in accommodations:
            # Filter by price if specified
            max_price = request.max_price or request.budget
            if max_price and accommodation.price_per_night and accommodation.price_per_night > max_price:
                continue
            
            # Analyze match with user preferences
            preferences_dict = {
                "budget": request.budget,
                "property_type": request.property_type,
                "preferred_amenities": request.preferred_amenities or [],
                "style": request.style
            }
            match_analysis = external_api_manager.analyze_accommodation_match(accommodation, preferences_dict)
            
            analyzed_accommodations.append((accommodation, match_analysis))
        
        # Sort by match score
        analyzed_accommodations.sort(key=lambda x: x[1]["match_score"] if x[1] else 0, reverse=True)
        
        # Convert to response format
        response_accommodations = []
        for accommodation, match_analysis in analyzed_accommodations[:request.limit]:
            response_accommodations.append(AccommodationResponse(
                accommodation_id=accommodation.accommodation_id,
                name=accommodation.name,
                address=accommodation.address,
                location=accommodation.location,
                rating=accommodation.rating,
                review_count=accommodation.review_count,
                price_per_night=accommodation.price_per_night,
                currency=accommodation.currency,
                images=accommodation.images or [],
                amenities=accommodation.amenities or [],
                room_types=accommodation.room_types or [],
                booking_url=accommodation.booking_url,
                affiliate_link=accommodation.affiliate_link,
                cancellation_policy=accommodation.cancellation_policy,
                property_type=accommodation.property_type,
                match_analysis=match_analysis
            ))
        
        return response_accommodations
        
    except Exception as e:
        logger.error(f"Error in smart accommodation search: {e}")
        raise HTTPException(status_code=500, detail=f"Smart search failed: {str(e)}")

@router.post("/tourism/comprehensive", response_model=Dict[str, List])
async def get_comprehensive_tourism_recommendations(request: TourismRecommendationRequest):
    """Get comprehensive tourism recommendations including places and accommodations"""
    try:
        location = {"lat": request.lat, "lng": request.lng}
        
        user_prefs = {}
        if request.user_preferences:
            user_prefs = {
                "budget": request.user_preferences.budget,
                "property_type": request.user_preferences.property_type,
                "preferred_amenities": request.user_preferences.preferred_amenities or [],
                "style": request.user_preferences.style
            }
        
        recommendations = await external_api_manager.get_tourism_recommendations(
            location=location,
            user_preferences=user_prefs
        )
        
        # Format response
        formatted_recommendations = {}
        
        if request.include_restaurants:
            formatted_recommendations["restaurants"] = [
                {
                    "place_id": place.place_id,
                    "name": place.name,
                    "address": place.address,
                    "location": place.location,
                    "rating": place.rating,
                    "price_level": place.price_level,
                    "photos": place.photos[:2] if place.photos else []
                }
                for place in recommendations.get("restaurants", [])
            ]
        
        if request.include_attractions:
            formatted_recommendations["attractions"] = [
                {
                    "place_id": place.place_id,
                    "name": place.name,
                    "address": place.address,
                    "location": place.location,
                    "rating": place.rating,
                    "types": place.types,
                    "photos": place.photos[:2] if place.photos else []
                }
                for place in recommendations.get("attractions", [])
            ]
        
        if request.include_accommodations:
            accommodations_with_analysis = []
            for accommodation in recommendations.get("accommodations", []):
                match_analysis = external_api_manager.analyze_accommodation_match(accommodation, user_prefs)
                accommodations_with_analysis.append({
                    "accommodation_id": accommodation.accommodation_id,
                    "name": accommodation.name,
                    "address": accommodation.address,
                    "location": accommodation.location,
                    "rating": accommodation.rating,
                    "price_per_night": accommodation.price_per_night,
                    "currency": accommodation.currency,
                    "property_type": accommodation.property_type,
                    "amenities": accommodation.amenities[:5] if accommodation.amenities else [],
                    "affiliate_link": accommodation.affiliate_link,
                    "match_analysis": match_analysis
                })
            
            # Sort by match score
            accommodations_with_analysis.sort(
                key=lambda x: x["match_analysis"]["match_score"], 
                reverse=True
            )
            formatted_recommendations["accommodations"] = accommodations_with_analysis
        
        formatted_recommendations["activities"] = [
            {
                "place_id": place.place_id,
                "name": place.name,
                "address": place.address,
                "location": place.location,
                "rating": place.rating,
                "types": place.types,
                "photos": place.photos[:2] if place.photos else []
            }
            for place in recommendations.get("activities", [])
        ]
        
        return formatted_recommendations
        
    except Exception as e:
        logger.error(f"Error getting comprehensive recommendations: {e}")
        raise HTTPException(status_code=500, detail=f"Comprehensive recommendations failed: {str(e)}")

@router.get("/nearby")
async def get_nearby_everything(
    lat: float = Query(..., description="Latitude"),
    lng: float = Query(..., description="Longitude"),
    radius: int = Query(2000, description="Search radius in meters"),
    include_restaurants: bool = Query(True),
    include_attractions: bool = Query(True),
    include_accommodations: bool = Query(True)
):
    """Quick endpoint to get everything nearby - convenience method for 'near me now' functionality"""
    try:
        location = {"lat": lat, "lng": lng}
        
        results = {
            "location": location,
            "radius": radius,
            "timestamp": datetime.now().isoformat()
        }
        
        # Get different types of places concurrently
        tasks = []
        
        if include_restaurants:
            tasks.append(("restaurants", external_api_manager.search_places_nearby(
                location=location,
                place_types=["restaurant", "food"],
                radius=radius,
                min_rating=3.5,
                limit=10
            )))
        
        if include_attractions:
            tasks.append(("attractions", external_api_manager.search_places_nearby(
                location=location,
                place_types=["tourist_attraction", "point_of_interest"],
                radius=radius,
                min_rating=4.0,
                limit=10
            )))
        
        if include_accommodations:
            tasks.append(("accommodations", external_api_manager.search_accommodations_nearby(
                location=location,
                min_rating=3.5,
                limit=10
            )))
        
        # Execute all searches
        import asyncio
        task_results = await asyncio.gather(*[task[1] for task in tasks], return_exceptions=True)
        
        # Process results
        for i, (category, _) in enumerate(tasks):
            if i < len(task_results) and not isinstance(task_results[i], Exception):
                if category == "accommodations":
                    results[category] = [
                        {
                            "id": item.accommodation_id,
                            "name": item.name,
                            "address": item.address,
                            "rating": item.rating,
                            "price": item.price_per_night,
                            "type": "accommodation"
                        }
                        for item in task_results[i][:5]
                    ]
                else:
                    results[category] = [
                        {
                            "id": item.place_id,
                            "name": item.name,
                            "address": item.address,
                            "rating": item.rating,
                            "types": item.types,
                            "type": "place"
                        }
                        for item in task_results[i][:5]
                    ]
            else:
                results[category] = []
        
        return results
        
    except Exception as e:
        logger.error(f"Error getting nearby places: {e}")
        raise HTTPException(status_code=500, detail=f"Nearby search failed: {str(e)}")

@router.get("/health")
async def location_service_health():
    """Health check for location services"""
    health_status = {
        "status": "healthy",
        "timestamp": datetime.now().isoformat(),
        "services": {}
    }
    
    # Check Google Places API
    google_places_connector = external_api_manager.connectors.get("google_places")
    if google_places_connector and google_places_connector.client:
        health_status["services"]["google_places"] = "configured"
    else:
        health_status["services"]["google_places"] = "not_configured"
    
    # Check accommodation booking API
    accommodation_connector = external_api_manager.connectors.get("accommodation")
    if accommodation_connector:
        health_status["services"]["accommodation_booking"] = "configured"
    else:
        health_status["services"]["accommodation_booking"] = "not_configured"
    
    # Check Redis cache
    redis_cache = external_api_manager.redis_cache
    if redis_cache.enabled:
        health_status["services"]["redis_cache"] = "enabled"
    else:
        health_status["services"]["redis_cache"] = "disabled"
    
    return health_status

# Export router creation function for main.py
def create_location_routes():
    """Create and return the location API router"""
    return router