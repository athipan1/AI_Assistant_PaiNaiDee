"""
Group Trip Planning API Routes
Provides endpoints for group travel planning, user preferences, and AI-powered trip optimization
"""

from fastapi import APIRouter, HTTPException, BackgroundTasks, Query
from pydantic import BaseModel
from typing import List, Optional, Dict, Any, Union
from datetime import datetime
import logging
import uuid

from models.group_trip_models import (
    group_trip_manager, TripGroup, UserPreference, Location, GroupPlan, 
    TripStatus, PreferenceCategory
)
from models.tourist_interest_graph import tourist_graph
from models.contextual_recommendations import contextual_engine

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def create_group_trip_routes() -> APIRouter:
    """Create and configure group trip API routes"""
    router = APIRouter(prefix="/api", tags=["group_trip"])
    
    # Request/Response models
    class CreateGroupRequest(BaseModel):
        group_name: str
        creator_id: str
        creator_username: str
        destination_city: str
        start_date: str
        end_date: str
        
    class GroupResponse(BaseModel):
        group_id: str
        group_name: str
        creator_id: str
        member_ids: List[str]
        status: str
        destination_city: str
        trip_dates: Dict[str, str]
        member_count: int
        invitation_code: str
        public_link: Optional[str]
        created_at: str
        
    class JoinGroupRequest(BaseModel):
        user_id: str
        username: str
        invitation_code: Optional[str] = None
        
    class UserPreferencesRequest(BaseModel):
        user_id: str
        username: str
        interest_types: List[str]  # nature, culture, adventure, food, history, etc.
        activity_level: str  # low, medium, high
        budget_range: str  # budget, mid, luxury
        time_preferences: List[str]  # morning, afternoon, evening, night
        location_preferences: List[str]  # indoor, outdoor, mixed
        favorite_locations: Optional[List[str]] = []
        disliked_locations: Optional[List[str]] = []
        special_requirements: Optional[List[str]] = []
        
    class AddLocationRequest(BaseModel):
        location_name: str
        location_type: str  # attraction, restaurant, hotel, activity
        description: str
        coordinates: List[float]  # [lat, lng]
        tags: List[str]
        rating: Optional[float] = 0.0
        price_range: Optional[str] = "$$"
        duration_hours: Optional[float] = 2.0
        best_time: Optional[List[str]] = ["afternoon"]
        
    class GroupPlanRequest(BaseModel):
        group_id: str
        max_locations_per_day: Optional[int] = 4
        include_alternatives: Optional[bool] = False
        optimization_focus: Optional[str] = "balanced"  # balanced, cost, time, popularity
    
    class LocationResponse(BaseModel):
        location_id: str
        name: str
        location_type: str
        description: str
        coordinates: List[float]
        tags: List[str]
        rating: float
        price_range: str
        duration_hours: float
        best_time: List[str]
        added_by: Optional[str] = None
        
    class GroupPlanResponse(BaseModel):
        plan_id: str
        group_id: str
        itinerary: List[Dict[str, Any]]
        optimized_locations: List[LocationResponse]
        confidence_score: float
        compromise_analysis: Dict[str, Any]
        generated_at: str
        
    @router.post("/trip/group", response_model=GroupResponse)
    async def create_group_trip(request: CreateGroupRequest):
        """Create a new group trip"""
        try:
            trip_dates = {
                "start_date": request.start_date,
                "end_date": request.end_date
            }
            
            group = group_trip_manager.create_group(
                group_name=request.group_name,
                creator_id=request.creator_id,
                creator_username=request.creator_username,
                destination_city=request.destination_city,
                trip_dates=trip_dates
            )
            
            return GroupResponse(
                group_id=group.group_id,
                group_name=group.group_name,
                creator_id=group.creator_id,
                member_ids=group.member_ids,
                status=group.status.value,
                destination_city=group.destination_city,
                trip_dates=group.trip_dates,
                member_count=len(group.member_ids),
                invitation_code=group.invitation_code,
                public_link=group.public_link,
                created_at=group.created_at
            )
            
        except Exception as e:
            logger.error(f"Error creating group trip: {e}")
            raise HTTPException(status_code=500, detail=str(e))
    
    @router.get("/trip/group/{group_id}", response_model=GroupResponse)
    async def get_group_trip(group_id: str):
        """Get group trip details"""
        if group_id not in group_trip_manager.groups:
            raise HTTPException(status_code=404, detail="Group trip not found")
            
        group = group_trip_manager.groups[group_id]
        return GroupResponse(
            group_id=group.group_id,
            group_name=group.group_name,
            creator_id=group.creator_id,
            member_ids=group.member_ids,
            status=group.status.value,
            destination_city=group.destination_city,
            trip_dates=group.trip_dates,
            member_count=len(group.member_ids),
            invitation_code=group.invitation_code,
            public_link=group.public_link,
            created_at=group.created_at
        )
    
    @router.get("/trip/group/public/{public_id}", response_model=GroupResponse)
    async def get_public_group_trip(public_id: str):
        """Get group trip details via public link"""
        group = group_trip_manager.get_group_by_public_link(public_id)
        
        if not group:
            raise HTTPException(status_code=404, detail="Group trip not found")
            
        return GroupResponse(
            group_id=group.group_id,
            group_name=group.group_name,
            creator_id=group.creator_id,
            member_ids=group.member_ids,
            status=group.status.value,
            destination_city=group.destination_city,
            trip_dates=group.trip_dates,
            member_count=len(group.member_ids),
            invitation_code=group.invitation_code,
            public_link=group.public_link,
            created_at=group.created_at
        )
    
    @router.post("/trip/group/{group_id}/join")
    async def join_group_trip(group_id: str, request: JoinGroupRequest):
        """Join an existing group trip"""
        success = group_trip_manager.add_member(
            group_id=group_id,
            user_id=request.user_id,
            invitation_code=request.invitation_code
        )
        
        if not success:
            raise HTTPException(status_code=400, detail="Unable to join group trip")
            
        return {"status": "success", "message": "Successfully joined group trip"}
    
    @router.post("/trip/group/{group_id}/share")
    async def create_public_link(group_id: str):
        """Create public sharing link for group trip"""
        public_link = group_trip_manager.generate_public_link(group_id)
        
        if not public_link:
            raise HTTPException(status_code=404, detail="Group trip not found")
            
        return {"public_link": public_link, "full_url": f"/group-trip-viewer.html?id={public_link.split('/')[-1]}"}
    
    @router.get("/trip/group/{group_id}/locations")
    async def get_group_locations(group_id: str):
        """Get all locations added to group trip"""
        if group_id not in group_trip_manager.groups:
            raise HTTPException(status_code=404, detail="Group trip not found")
            
        group = group_trip_manager.groups[group_id]
        locations = []
        
        for location in group.shared_locations:
            locations.append(LocationResponse(
                location_id=location.location_id,
                name=location.name,
                location_type=location.location_type,
                description=location.description,
                coordinates=location.coordinates,
                tags=location.tags,
                rating=location.rating,
                price_range=location.price_range,
                duration_hours=location.duration_hours,
                best_time=location.best_time,
                added_by=getattr(location, 'added_by', None)
            ))
            
        return {"locations": locations, "total": len(locations)}
    
    @router.post("/trip/group/{group_id}/locations")
    async def add_location_to_group(group_id: str, request: AddLocationRequest, 
                                   user_id: str = Query(..., description="User adding the location")):
        """Add a location to group trip"""
        location = Location(
            location_id=str(uuid.uuid4()),
            name=request.location_name,
            location_type=request.location_type,
            coordinates=request.coordinates,
            description=request.description,
            tags=request.tags,
            rating=request.rating,
            price_range=request.price_range,
            duration_hours=request.duration_hours,
            best_time=request.best_time,
            requirements=[]
        )
        
        success = group_trip_manager.add_location_to_group(group_id, location, user_id)
        
        if not success:
            raise HTTPException(status_code=404, detail="Group trip not found")
            
        return {"status": "success", "location_id": location.location_id}
    
    @router.post("/user/preferences", response_model=Dict[str, Any])
    async def set_user_preferences(request: UserPreferencesRequest):
        """Set or update user travel preferences"""
        try:
            preferences = {
                "interest_types": request.interest_types,
                "activity_level": request.activity_level,
                "budget_range": request.budget_range,
                "time_preferences": request.time_preferences,
                "location_preferences": request.location_preferences
            }
            
            user_pref = group_trip_manager.set_user_preferences(
                user_id=request.user_id,
                username=request.username,
                preferences=preferences,
                favorite_locations=request.favorite_locations,
                disliked_locations=request.disliked_locations
            )
            
            return {
                "status": "success",
                "user_id": user_pref.user_id,
                "preferences": user_pref.preferences,
                "created_at": user_pref.created_at
            }
            
        except Exception as e:
            logger.error(f"Error setting user preferences: {e}")
            raise HTTPException(status_code=500, detail=str(e))
    
    @router.get("/user/{user_id}/preferences")
    async def get_user_preferences(user_id: str):
        """Get user travel preferences"""
        if user_id not in group_trip_manager.user_preferences:
            raise HTTPException(status_code=404, detail="User preferences not found")
            
        user_pref = group_trip_manager.user_preferences[user_id]
        return {
            "user_id": user_pref.user_id,
            "username": user_pref.username,
            "preferences": user_pref.preferences,
            "favorite_locations": user_pref.favorite_locations,
            "disliked_locations": user_pref.disliked_locations,
            "created_at": user_pref.created_at,
            "updated_at": user_pref.updated_at
        }
    
    @router.post("/group/plan", response_model=GroupPlanResponse)
    async def generate_group_plan(request: GroupPlanRequest):
        """AI-powered group trip planning"""
        try:
            if request.group_id not in group_trip_manager.groups:
                raise HTTPException(status_code=404, detail="Group trip not found")
                
            group = group_trip_manager.groups[request.group_id]
            
            # Analyze group preferences
            group_prefs = group_trip_manager.analyze_group_preferences(request.group_id)
            
            if not group_prefs:
                raise HTTPException(status_code=400, detail="No group member preferences found")
            
            # Get group locations
            locations = group.shared_locations
            
            if not locations:
                raise HTTPException(status_code=400, detail="No locations added to group trip")
            
            # AI-powered planning using existing tourism system
            optimized_locations = await _optimize_locations_for_group(
                locations, group_prefs, request.max_locations_per_day
            )
            
            # Generate itinerary
            itinerary = await _generate_itinerary(
                optimized_locations, group.trip_dates, request.max_locations_per_day
            )
            
            # Create group plan
            plan = GroupPlan(
                plan_id=str(uuid.uuid4()),
                group_id=request.group_id,
                itinerary=itinerary,
                optimized_locations=optimized_locations,
                travel_routes=[],  # Could be enhanced with routing API
                time_allocation={},
                compromise_analysis=group_prefs,
                confidence_score=group_prefs.get('consensus_strength', 0.5)
            )
            
            group_trip_manager.group_plans[plan.plan_id] = plan
            
            # Convert locations for response
            location_responses = []
            for loc in optimized_locations:
                location_responses.append(LocationResponse(
                    location_id=loc.location_id,
                    name=loc.name,
                    location_type=loc.location_type,
                    description=loc.description,
                    coordinates=loc.coordinates,
                    tags=loc.tags,
                    rating=loc.rating,
                    price_range=loc.price_range,
                    duration_hours=loc.duration_hours,
                    best_time=loc.best_time
                ))
            
            return GroupPlanResponse(
                plan_id=plan.plan_id,
                group_id=plan.group_id,
                itinerary=plan.itinerary,
                optimized_locations=location_responses,
                confidence_score=plan.confidence_score,
                compromise_analysis=plan.compromise_analysis,
                generated_at=plan.generated_at
            )
            
        except Exception as e:
            logger.error(f"Error generating group plan: {e}")
            raise HTTPException(status_code=500, detail=str(e))
    
    @router.get("/group/{group_id}/analysis")
    async def analyze_group_preferences(group_id: str):
        """Analyze group member preferences and compatibility"""
        if group_id not in group_trip_manager.groups:
            raise HTTPException(status_code=404, detail="Group trip not found")
            
        analysis = group_trip_manager.analyze_group_preferences(group_id)
        
        return {
            "group_id": group_id,
            "analysis": analysis,
            "recommendations": _get_preference_recommendations(analysis)
        }
    
    # Helper functions
    async def _optimize_locations_for_group(locations: List[Location], 
                                          group_prefs: Dict[str, Any], 
                                          max_per_day: int) -> List[Location]:
        """Use AI to optimize location selection for group preferences"""
        
        # Score each location based on group preferences
        scored_locations = []
        
        for location in locations:
            score = 0.0
            
            # Interest type matching
            top_interests = [item[0] for item in group_prefs.get('top_interests', [])]
            for interest in top_interests:
                if interest in location.tags:
                    score += 0.3
            
            # Activity level matching
            activity_level = group_prefs.get('activity_level', 'medium')
            if activity_level == 'low' and 'relaxing' in location.tags:
                score += 0.2
            elif activity_level == 'high' and 'adventure' in location.tags:
                score += 0.2
            elif activity_level == 'medium':
                score += 0.1
            
            # Budget matching
            budget_range = group_prefs.get('budget_range', 'mid')
            price_scores = {'budget': {'$': 0.3, '$$': 0.1}, 
                          'mid': {'$$': 0.3, '$$$': 0.2, '$': 0.1},
                          'luxury': {'$$$': 0.3, '$$$$': 0.3, '$$': 0.1}}
            
            score += price_scores.get(budget_range, {}).get(location.price_range, 0)
            
            # Base rating bonus
            score += location.rating * 0.1
            
            scored_locations.append((location, score))
        
        # Sort by score and return top locations
        scored_locations.sort(key=lambda x: x[1], reverse=True)
        max_locations = max_per_day * 3  # Allow some flexibility
        
        return [loc for loc, score in scored_locations[:max_locations]]
    
    async def _generate_itinerary(locations: List[Location], 
                                trip_dates: Dict[str, str], 
                                max_per_day: int) -> List[Dict[str, Any]]:
        """Generate day-by-day itinerary"""
        
        from datetime import datetime, timedelta
        
        start_date = datetime.fromisoformat(trip_dates['start_date'])
        end_date = datetime.fromisoformat(trip_dates['end_date'])
        
        days = (end_date - start_date).days + 1
        locations_per_day = min(max_per_day, len(locations) // max(days, 1))
        
        itinerary = []
        location_index = 0
        
        for day in range(days):
            current_date = start_date + timedelta(days=day)
            day_locations = []
            
            # Add locations for this day
            for _ in range(locations_per_day):
                if location_index < len(locations):
                    location = locations[location_index]
                    day_locations.append({
                        "location_id": location.location_id,
                        "name": location.name,
                        "type": location.location_type,
                        "duration_hours": location.duration_hours,
                        "best_time": location.best_time,
                        "coordinates": location.coordinates
                    })
                    location_index += 1
            
            itinerary.append({
                "day": day + 1,
                "date": current_date.strftime("%Y-%m-%d"),
                "locations": day_locations,
                "total_duration": sum(loc["duration_hours"] for loc in day_locations)
            })
        
        return itinerary
    
    def _get_preference_recommendations(analysis: Dict[str, Any]) -> List[str]:
        """Generate recommendations based on group analysis"""
        recommendations = []
        
        consensus = analysis.get('consensus_strength', 0)
        
        if consensus < 0.3:
            recommendations.append("Consider discussing preferences more to find common ground")
            recommendations.append("Try focusing on shared interests or compromise activities")
        elif consensus < 0.7:
            recommendations.append("Good compatibility! Consider mixed activities to satisfy different preferences")
        else:
            recommendations.append("Excellent group compatibility! You should have a great trip together")
        
        top_interests = analysis.get('top_interests', [])
        if top_interests:
            top_interest = top_interests[0][0]
            recommendations.append(f"Focus on {top_interest} activities as they're most popular in your group")
        
        activity_level = analysis.get('activity_level', 'medium')
        if activity_level == 'high':
            recommendations.append("Plan active adventures and outdoor activities")
        elif activity_level == 'low':
            recommendations.append("Focus on relaxing activities and comfortable experiences")
        
        return recommendations
    
    return router