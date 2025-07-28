"""
API routes for ML-powered LOD Prediction
Provides RESTful endpoints for Level of Detail prediction and optimization
"""

from fastapi import APIRouter, HTTPException, Query
from typing import List, Optional, Dict, Any
from pydantic import BaseModel
from datetime import datetime

from ..models.lod_prediction import lod_predictor, UserBehavior, LODPrediction


# Pydantic models for request/response
class LODPredictionRequest(BaseModel):
    model_name: str
    device_type: str = "desktop"  # mobile, tablet, desktop, vr
    connection_speed: str = "medium"  # slow, medium, fast
    gpu_tier: str = "medium"  # low, medium, high
    viewport_size: List[int] = [1920, 1080]
    detail_preference: float = 0.5  # 0.0 to 1.0
    performance_tolerance: float = 0.5  # 0.0 to 1.0
    session_id: Optional[str] = None


class SessionStartRequest(BaseModel):
    user_id: str
    session_id: str
    device_type: str
    connection_speed: str
    gpu_tier: str
    viewport_size: List[int]
    user_agent: str = ""


class LODFeedbackRequest(BaseModel):
    session_id: str
    prediction_index: int
    satisfaction: float  # 0.0 to 1.0
    performance: float  # 0.0 to 1.0
    quality: float  # 0.0 to 1.0
    load_time_actual: Optional[float] = None
    fps_actual: Optional[float] = None
    comments: str = ""


class UserBehaviorRequest(BaseModel):
    user_id: str
    session_id: str
    device_type: str
    connection_speed: str
    gpu_tier: str
    viewport_size: List[int]
    avg_interaction_time: float
    zoom_frequency: int
    rotate_frequency: int
    detail_preference: float
    performance_tolerance: float


def create_lod_routes(app):
    """Add LOD prediction routes to FastAPI app"""
    
    @app.post("/api/lod/predict")
    async def predict_lod(request: LODPredictionRequest):
        """Predict optimal LOD for a model based on user context"""
        try:
            user_context = {
                "device_type": request.device_type,
                "connection_speed": request.connection_speed,
                "gpu_tier": request.gpu_tier,
                "viewport_size": request.viewport_size,
                "detail_preference": request.detail_preference,
                "performance_tolerance": request.performance_tolerance
            }
            
            prediction = lod_predictor.predict_lod(
                model_name=request.model_name,
                user_context=user_context,
                session_id=request.session_id
            )
            
            return {
                "model_name": request.model_name,
                "prediction": {
                    "recommended_lod": prediction.recommended_lod,
                    "confidence": prediction.confidence,
                    "reasoning": prediction.reasoning,
                    "alternatives": prediction.alternatives,
                    "performance_estimate": prediction.performance_estimate,
                    "quality_estimate": prediction.quality_estimate
                },
                "status": "success"
            }
            
        except Exception as e:
            raise HTTPException(status_code=500, detail=str(e))
    
    @app.post("/api/lod/session/start")
    async def start_lod_session(request: SessionStartRequest):
        """Start a new session for LOD tracking and learning"""
        try:
            device_info = {
                "device_type": request.device_type,
                "connection_speed": request.connection_speed,
                "gpu_tier": request.gpu_tier,
                "viewport_size": request.viewport_size,
                "user_agent": request.user_agent
            }
            
            result = lod_predictor.start_session(
                user_id=request.user_id,
                session_id=request.session_id,
                device_info=device_info
            )
            
            return result
            
        except Exception as e:
            raise HTTPException(status_code=500, detail=str(e))
    
    @app.post("/api/lod/feedback")
    async def provide_lod_feedback(request: LODFeedbackRequest):
        """Provide feedback on LOD prediction for ML learning"""
        try:
            feedback = {
                "satisfaction": request.satisfaction,
                "performance": request.performance,
                "quality": request.quality,
                "load_time_actual": request.load_time_actual,
                "fps_actual": request.fps_actual,
                "comments": request.comments
            }
            
            result = lod_predictor.provide_feedback(
                session_id=request.session_id,
                prediction_index=request.prediction_index,
                feedback=feedback
            )
            
            return result
            
        except Exception as e:
            raise HTTPException(status_code=500, detail=str(e))
    
    @app.post("/api/lod/behavior/track")
    async def track_user_behavior(request: UserBehaviorRequest):
        """Track user behavior for improving LOD predictions"""
        try:
            behavior = UserBehavior(
                user_id=request.user_id,
                session_id=request.session_id,
                device_type=request.device_type,
                connection_speed=request.connection_speed,
                gpu_tier=request.gpu_tier,
                viewport_size=tuple(request.viewport_size),
                avg_interaction_time=request.avg_interaction_time,
                zoom_frequency=request.zoom_frequency,
                rotate_frequency=request.rotate_frequency,
                detail_preference=request.detail_preference,
                performance_tolerance=request.performance_tolerance,
                timestamp=datetime.now().isoformat()
            )
            
            lod_predictor.track_user_behavior(behavior)
            
            return {
                "message": "User behavior tracked successfully",
                "status": "success"
            }
            
        except Exception as e:
            raise HTTPException(status_code=500, detail=str(e))
    
    @app.get("/api/lod/models/{model_name}/options")
    async def get_lod_options(model_name: str):
        """Get available LOD options for a specific model"""
        try:
            options = lod_predictor.get_lod_options(model_name)
            
            if not options:
                raise HTTPException(status_code=404, detail="Model not found or no LOD options available")
            
            return {
                "model_name": model_name,
                "lod_options": options,
                "count": len(options),
                "status": "success"
            }
            
        except HTTPException:
            raise
        except Exception as e:
            raise HTTPException(status_code=500, detail=str(e))
    
    @app.get("/api/lod/models")
    async def list_lod_models():
        """List all models with LOD support"""
        try:
            models = []
            for model_name in lod_predictor.model_lods.keys():
                options = lod_predictor.get_lod_options(model_name)
                models.append({
                    "model_name": model_name,
                    "lod_count": len(options),
                    "max_quality": max(opt["quality_score"] for opt in options) if options else 0,
                    "min_performance": min(opt["performance_score"] for opt in options) if options else 0
                })
            
            return {
                "models": models,
                "count": len(models),
                "status": "success"
            }
            
        except Exception as e:
            raise HTTPException(status_code=500, detail=str(e))
    
    @app.get("/api/lod/analytics")
    async def get_lod_analytics():
        """Get LOD prediction analytics and ML performance metrics"""
        try:
            analytics = lod_predictor.get_analytics()
            
            return {
                "analytics": analytics,
                "status": "success"
            }
            
        except Exception as e:
            raise HTTPException(status_code=500, detail=str(e))
    
    @app.get("/api/lod/weights")
    async def get_ml_weights():
        """Get current ML model weights (for debugging/monitoring)"""
        try:
            return {
                "weights": lod_predictor.feature_weights,
                "learning_rate": lod_predictor.learning_rate,
                "adaptation_threshold": lod_predictor.adaptation_threshold,
                "status": "success"
            }
            
        except Exception as e:
            raise HTTPException(status_code=500, detail=str(e))
    
    @app.post("/api/lod/weights/reset")
    async def reset_ml_weights():
        """Reset ML model weights to defaults (admin function)"""
        try:
            # Backup current weights
            backup_weights = lod_predictor.feature_weights.copy()
            
            # Reset to defaults
            lod_predictor.feature_weights = lod_predictor._load_or_initialize_weights()
            lod_predictor._save_weights()
            
            return {
                "message": "ML weights reset to defaults",
                "backup_weights": backup_weights,
                "new_weights": lod_predictor.feature_weights,
                "status": "success"
            }
            
        except Exception as e:
            raise HTTPException(status_code=500, detail=str(e))
    
    @app.get("/api/lod/performance/comparison")
    async def compare_lod_performance(
        model_name: str = Query(..., description="Model name"),
        device_type: str = Query("desktop", description="Device type"),
        connection_speed: str = Query("medium", description="Connection speed")
    ):
        """Compare performance estimates across all LOD levels for a model"""
        try:
            if model_name not in lod_predictor.model_lods:
                raise HTTPException(status_code=404, detail="Model not found")
            
            user_context = {
                "device_type": device_type,
                "connection_speed": connection_speed,
                "gpu_tier": "medium",
                "viewport_size": [1920, 1080]
            }
            
            comparisons = []
            for lod in lod_predictor.model_lods[model_name]:
                performance = lod_predictor._estimate_performance(lod, user_context)
                comparisons.append({
                    "lod_level": lod.lod_level,
                    "triangle_count": lod.triangle_count,
                    "file_size_mb": round(lod.file_size / (1024 * 1024), 2),
                    "quality_score": lod.quality_score,
                    "performance_estimate": performance
                })
            
            return {
                "model_name": model_name,
                "device_context": {
                    "device_type": device_type,
                    "connection_speed": connection_speed
                },
                "lod_comparisons": comparisons,
                "status": "success"
            }
            
        except HTTPException:
            raise
        except Exception as e:
            raise HTTPException(status_code=500, detail=str(e))
    
    @app.post("/api/lod/optimize/batch")
    async def batch_lod_optimization(models: List[str], user_context: Dict[str, Any]):
        """Get LOD recommendations for multiple models at once"""
        try:
            optimizations = []
            
            for model_name in models:
                try:
                    prediction = lod_predictor.predict_lod(model_name, user_context)
                    optimizations.append({
                        "model_name": model_name,
                        "recommended_lod": prediction.recommended_lod,
                        "confidence": prediction.confidence,
                        "performance_estimate": prediction.performance_estimate,
                        "status": "success"
                    })
                except Exception as e:
                    optimizations.append({
                        "model_name": model_name,
                        "error": str(e),
                        "status": "error"
                    })
            
            return {
                "user_context": user_context,
                "optimizations": optimizations,
                "total_models": len(models),
                "successful": len([o for o in optimizations if o["status"] == "success"]),
                "status": "success"
            }
            
        except Exception as e:
            raise HTTPException(status_code=500, detail=str(e))