"""
Tourism Enhancement API Routes
Provides endpoints for tourist interest graph and contextual recommendations
"""

from fastapi import APIRouter, HTTPException, BackgroundTasks
from pydantic import BaseModel
from typing import List, Optional, Dict, Any, Union
from datetime import datetime
import logging

from models.tourist_interest_graph import tourist_graph, TouristInterest
from models.contextual_recommendations import contextual_engine, ContextualFactors, WeatherCondition, Season
from models.lod_prediction import lod_predictor

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Request/Response models
class InteractionRequest(BaseModel):
    user_id: str
    session_id: str
    query: str
    selected_model: str
    context: Optional[Dict[str, Any]] = {}
    feedback: Optional[Dict[str, Any]] = {}
    interaction_time: Optional[int] = 0

class InterestResponse(BaseModel):
    interest_id: str
    interest_type: str
    specific_tags: List[str]
    confidence: float
    status: str

class RecommendationRequest(BaseModel):
    user_id: Optional[str] = None
    session_id: Optional[str] = None
    available_locations: List[str]
    user_preferences: Optional[Dict[str, Any]] = {}
    context_override: Optional[Dict[str, Any]] = {}
    top_k: Optional[int] = 5

class ContextualRecommendationRequest(BaseModel):
    available_locations: List[str]
    user_preferences: Optional[Dict[str, Any]] = {}
    weather_override: Optional[Dict[str, Any]] = {}
    scenario: Optional[str] = None
    top_k: Optional[int] = 5

class TimeSpecificRequest(BaseModel):
    target_time: str  # ISO format
    available_locations: List[str]
    scenario: Optional[str] = None

class TouristRecommendation(BaseModel):
    location_id: str
    score: float
    reasoning: List[str]
    matching_interests: List[str]
    confidence: float

class ContextualRecommendationResponse(BaseModel):
    location_id: str
    location_name: str
    suitability_score: float
    contextual_reasons: List[str]
    optimal_time_window: List[int]
    weather_dependency: str
    estimated_duration: int
    special_considerations: List[str]

class IntegratedRecommendationRequest(BaseModel):
    user_id: Optional[str] = None
    session_id: Optional[str] = None
    query: str
    available_locations: List[str]
    include_interest_graph: Optional[bool] = True
    include_contextual: Optional[bool] = True
    include_lod: Optional[bool] = True
    user_context: Optional[Dict[str, Any]] = {}

class IntegratedRecommendationResponse(BaseModel):
    selected_model: str
    confidence: float
    tourist_recommendations: List[TouristRecommendation]
    contextual_recommendations: List[ContextualRecommendationResponse]
    lod_prediction: Optional[Dict[str, Any]]
    integration_reasoning: List[str]
    status: str

def create_tourism_routes(app):
    """Create and add tourism enhancement routes to FastAPI app"""
    
    router = APIRouter()
    
    @router.post("/capture_interest", response_model=InterestResponse)
    async def capture_tourist_interest(request: InteractionRequest):
        """
        Capture and analyze tourist interest from user interaction
        """
        try:
            logger.info(f"Capturing interest for user: {request.user_id}")
            
            # Prepare interaction data
            interaction_data = {
                'query': request.query,
                'selected_model': request.selected_model,
                'context': request.context,
                'feedback': request.feedback,
                'interaction_time': request.interaction_time
            }
            
            # Capture interest using tourist graph
            interest = tourist_graph.capture_interest_from_interaction(
                request.user_id, request.session_id, interaction_data
            )
            
            return InterestResponse(
                interest_id=interest.interest_id,
                interest_type=interest.interest_type,
                specific_tags=interest.specific_tags,
                confidence=interest.confidence,
                status="success"
            )
            
        except Exception as e:
            logger.error(f"Error capturing tourist interest: {str(e)}")
            raise HTTPException(status_code=500, detail=str(e))
    
    @router.post("/recommendations/tourist", response_model=List[TouristRecommendation])
    async def get_tourist_recommendations(request: RecommendationRequest):
        """
        Get personalized recommendations based on tourist interest graph
        """
        try:
            logger.info(f"Getting tourist recommendations for user: {request.user_id}")
            
            if not request.user_id:
                # Return default recommendations for anonymous users
                recommendations = []
                for location in request.available_locations[:request.top_k]:
                    recommendations.append(TouristRecommendation(
                        location_id=location,
                        score=0.5,
                        reasoning=["Default recommendation for new user"],
                        matching_interests=[],
                        confidence=0.3
                    ))
                return recommendations
            
            # Get recommendations from tourist graph
            context = request.context_override or {}
            recommendations = tourist_graph.get_recommendations_for_user(
                request.user_id, context, request.available_locations, request.top_k
            )
            
            # Convert to response format
            response_recommendations = []
            for rec in recommendations:
                response_recommendations.append(TouristRecommendation(
                    location_id=rec['location_id'],
                    score=rec['score'],
                    reasoning=rec['reasoning'],
                    matching_interests=rec['matching_interests'],
                    confidence=rec['confidence']
                ))
            
            return response_recommendations
            
        except Exception as e:
            logger.error(f"Error getting tourist recommendations: {str(e)}")
            raise HTTPException(status_code=500, detail=str(e))
    
    @router.post("/recommendations/contextual", response_model=List[ContextualRecommendationResponse])
    async def get_contextual_recommendations(request: ContextualRecommendationRequest):
        """
        Get contextual recommendations based on real-time factors
        """
        try:
            logger.info("Getting contextual recommendations")
            
            # Get contextual recommendations
            recommendations = contextual_engine.generate_contextual_recommendations(
                request.available_locations,
                request.user_preferences,
                top_k=request.top_k
            )
            
            # Convert to response format
            response_recommendations = []
            for rec in recommendations:
                response_recommendations.append(ContextualRecommendationResponse(
                    location_id=rec.location_id,
                    location_name=rec.location_name,
                    suitability_score=rec.suitability_score,
                    contextual_reasons=rec.contextual_reasons,
                    optimal_time_window=list(rec.optimal_time_window),
                    weather_dependency=rec.weather_dependency,
                    estimated_duration=rec.estimated_duration,
                    special_considerations=rec.special_considerations
                ))
            
            return response_recommendations
            
        except Exception as e:
            logger.error(f"Error getting contextual recommendations: {str(e)}")
            raise HTTPException(status_code=500, detail=str(e))
    
    @router.post("/recommendations/time_specific", response_model=List[ContextualRecommendationResponse])
    async def get_time_specific_recommendations(request: TimeSpecificRequest):
        """
        Get recommendations for specific time scenarios
        """
        try:
            logger.info(f"Getting time-specific recommendations for: {request.target_time}")
            
            # Parse target time
            target_time = datetime.fromisoformat(request.target_time.replace('Z', '+00:00'))
            
            # Get time-specific recommendations
            recommendations = contextual_engine.get_time_specific_recommendations(
                target_time, request.available_locations, request.scenario
            )
            
            # Convert to response format
            response_recommendations = []
            for rec in recommendations:
                response_recommendations.append(ContextualRecommendationResponse(
                    location_id=rec.location_id,
                    location_name=rec.location_name,
                    suitability_score=rec.suitability_score,
                    contextual_reasons=rec.contextual_reasons,
                    optimal_time_window=list(rec.optimal_time_window),
                    weather_dependency=rec.weather_dependency,
                    estimated_duration=rec.estimated_duration,
                    special_considerations=rec.special_considerations
                ))
            
            return response_recommendations
            
        except Exception as e:
            logger.error(f"Error getting time-specific recommendations: {str(e)}")
            raise HTTPException(status_code=500, detail=str(e))
    
    @router.post("/recommendations/integrated", response_model=IntegratedRecommendationResponse)
    async def get_integrated_recommendations(request: IntegratedRecommendationRequest):
        """
        Get integrated recommendations combining tourist interests, contextual factors, and LOD optimization
        """
        try:
            logger.info(f"Getting integrated recommendations for query: {request.query}")
            
            # Start with basic model selection (fallback)
            from api.model_routes import model_selector
            basic_selection = model_selector.analyze_question(request.query)
            selected_model = basic_selection['selected_model']
            base_confidence = basic_selection['confidence']
            
            tourist_recommendations = []
            contextual_recommendations = []
            lod_prediction = None
            integration_reasoning = []
            
            # Get tourist interest recommendations if requested and user provided
            if request.include_interest_graph and request.user_id:
                try:
                    tourist_recs = tourist_graph.get_recommendations_for_user(
                        request.user_id, request.user_context, request.available_locations, 5
                    )
                    
                    for rec in tourist_recs:
                        tourist_recommendations.append(TouristRecommendation(
                            location_id=rec['location_id'],
                            score=rec['score'],
                            reasoning=rec['reasoning'],
                            matching_interests=rec['matching_interests'],
                            confidence=rec['confidence']
                        ))
                    
                    # If tourist interests strongly favor a different model, consider switching
                    if tourist_recommendations and tourist_recommendations[0].score > 0.8:
                        if tourist_recommendations[0].location_id != selected_model:
                            integration_reasoning.append("Switched model based on strong tourist interest match")
                            selected_model = tourist_recommendations[0].location_id
                            base_confidence = min(1.0, base_confidence + 0.2)
                    
                except Exception as e:
                    logger.warning(f"Tourist recommendations failed: {e}")
                    integration_reasoning.append("Tourist interest analysis unavailable")
            
            # Get contextual recommendations if requested
            if request.include_contextual:
                try:
                    contextual_recs = contextual_engine.generate_contextual_recommendations(
                        request.available_locations, top_k=5
                    )
                    
                    for rec in contextual_recs:
                        contextual_recommendations.append(ContextualRecommendationResponse(
                            location_id=rec.location_id,
                            location_name=rec.location_name,
                            suitability_score=rec.suitability_score,
                            contextual_reasons=rec.contextual_reasons,
                            optimal_time_window=list(rec.optimal_time_window),
                            weather_dependency=rec.weather_dependency,
                            estimated_duration=rec.estimated_duration,
                            special_considerations=rec.special_considerations
                        ))
                    
                    # Check if contextual factors strongly favor a different model
                    selected_contextual = None
                    for rec in contextual_recs:
                        if rec.location_id == selected_model and rec.suitability_score < 0.3:
                            # Current selection is poor for context, find better alternative
                            for alt_rec in contextual_recs:
                                if alt_rec.suitability_score > 0.7:
                                    selected_contextual = alt_rec.location_id
                                    break
                    
                    if selected_contextual and selected_contextual != selected_model:
                        integration_reasoning.append("Adjusted for current contextual conditions")
                        selected_model = selected_contextual
                        base_confidence = min(1.0, base_confidence + 0.1)
                    
                except Exception as e:
                    logger.warning(f"Contextual recommendations failed: {e}")
                    integration_reasoning.append("Contextual analysis unavailable")
            
            # Get LOD prediction if requested and session provided
            if request.include_lod and request.session_id:
                try:
                    lod_result = lod_predictor.predict_lod(
                        selected_model, request.user_context, request.session_id
                    )
                    
                    lod_prediction = {
                        'recommended_lod': lod_result.recommended_lod,
                        'confidence': lod_result.confidence,
                        'reasoning': lod_result.reasoning,
                        'performance_estimate': lod_result.performance_estimate,
                        'quality_estimate': lod_result.quality_estimate
                    }
                    
                    integration_reasoning.append(f"LOD {lod_result.recommended_lod} recommended for optimal performance")
                    
                except Exception as e:
                    logger.warning(f"LOD prediction failed: {e}")
                    integration_reasoning.append("LOD optimization unavailable")
            
            # Capture interaction for future learning
            if request.user_id and request.session_id:
                try:
                    interaction_data = {
                        'query': request.query,
                        'selected_model': selected_model,
                        'context': request.user_context,
                        'feedback': {},
                        'interaction_time': 0
                    }
                    
                    # Capture interest asynchronously
                    tourist_graph.capture_interest_from_interaction(
                        request.user_id, request.session_id, interaction_data
                    )
                    
                except Exception as e:
                    logger.warning(f"Interest capture failed: {e}")
            
            # Final confidence calculation
            final_confidence = base_confidence
            if tourist_recommendations:
                final_confidence = min(1.0, final_confidence + 0.1)
            if contextual_recommendations:
                final_confidence = min(1.0, final_confidence + 0.1)
            if lod_prediction:
                final_confidence = min(1.0, final_confidence + 0.05)
            
            if not integration_reasoning:
                integration_reasoning.append("Standard AI model selection")
            
            return IntegratedRecommendationResponse(
                selected_model=selected_model,
                confidence=final_confidence,
                tourist_recommendations=tourist_recommendations,
                contextual_recommendations=contextual_recommendations,
                lod_prediction=lod_prediction,
                integration_reasoning=integration_reasoning,
                status="success"
            )
            
        except Exception as e:
            logger.error(f"Error getting integrated recommendations: {str(e)}")
            raise HTTPException(status_code=500, detail=str(e))
    
    @router.post("/clustering/trigger")
    async def trigger_clustering(background_tasks: BackgroundTasks):
        """
        Manually trigger interest clustering analysis
        """
        try:
            def run_clustering():
                tourist_graph.perform_interest_clustering()
            
            background_tasks.add_task(run_clustering)
            
            return {
                "message": "Interest clustering triggered",
                "status": "success"
            }
            
        except Exception as e:
            logger.error(f"Error triggering clustering: {str(e)}")
            raise HTTPException(status_code=500, detail=str(e))
    
    @router.get("/analytics/tourist_graph")
    async def get_tourist_graph_analytics():
        """
        Get analytics about the tourist interest graph
        """
        try:
            analytics = tourist_graph.get_analytics()
            return {
                "analytics": analytics,
                "status": "success"
            }
            
        except Exception as e:
            logger.error(f"Error getting tourist graph analytics: {str(e)}")
            raise HTTPException(status_code=500, detail=str(e))
    
    @router.get("/analytics/contextual")
    async def get_contextual_analytics():
        """
        Get analytics about contextual recommendations
        """
        try:
            analytics = contextual_engine.get_analytics()
            return {
                "analytics": analytics,
                "status": "success"
            }
            
        except Exception as e:
            logger.error(f"Error getting contextual analytics: {str(e)}")
            raise HTTPException(status_code=500, detail=str(e))
    
    @router.get("/context/current")
    async def get_current_context():
        """
        Get current contextual factors
        """
        try:
            context = contextual_engine.get_current_context()
            
            # Convert to serializable format
            context_dict = {
                'timestamp': context.timestamp,
                'time_of_day': context.time_of_day.value,
                'season': context.season.value,
                'weather_condition': context.weather_condition.value,
                'temperature': context.temperature,
                'humidity': context.humidity,
                'wind_speed': context.wind_speed,
                'precipitation_chance': context.precipitation_chance,
                'uv_index': context.uv_index,
                'location': context.location,
                'special_events': context.special_events,
                'crowd_level': context.crowd_level
            }
            
            return {
                "current_context": context_dict,
                "status": "success"
            }
            
        except Exception as e:
            logger.error(f"Error getting current context: {str(e)}")
            raise HTTPException(status_code=500, detail=str(e))
    
    @router.get("/health/tourism")
    async def tourism_health_check():
        """
        Health check for tourism enhancement systems
        """
        try:
            # Check tourist graph
            tourist_analytics = tourist_graph.get_analytics()
            
            # Check contextual engine
            contextual_analytics = contextual_engine.get_analytics()
            
            return {
                "status": "healthy",
                "systems": {
                    "tourist_interest_graph": {
                        "status": "operational",
                        "total_users": tourist_analytics.get('total_users', 0),
                        "total_interests": tourist_analytics.get('total_interests', 0),
                        "total_clusters": tourist_analytics.get('cluster_statistics', {}).get('total_clusters', 0)
                    },
                    "contextual_recommendations": {
                        "status": "operational",
                        "total_locations": contextual_analytics.get('total_locations', 0),
                        "avg_suitability": contextual_analytics.get('avg_suitability', 0),
                        "current_weather": contextual_analytics.get('current_context', {}).get('weather_condition', 'unknown')
                    }
                },
                "version": "1.0.0",
                "last_updated": datetime.now().isoformat()
            }
            
        except Exception as e:
            logger.error(f"Error in tourism health check: {str(e)}")
            return {
                "status": "degraded",
                "error": str(e),
                "version": "1.0.0"
            }
    
    # Add routes to app
    app.include_router(router, prefix="/tourism", tags=["Tourism Enhancements"])


def create_tourism_routes_standalone() -> APIRouter:
    """Create tourism routes as standalone router"""
    router = APIRouter()
    
    # Re-implement all the routes here for standalone use
    # (This is for backward compatibility if needed)
    
    return router