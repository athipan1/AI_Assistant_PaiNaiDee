"""
ML-powered Level of Detail (LOD) Prediction System
Predicts optimal LOD based on user behavior, device capabilities, and performance metrics
"""

import json
import numpy as np
from typing import Dict, List, Optional, Any, Tuple
from dataclasses import dataclass, asdict
from datetime import datetime, timedelta
from pathlib import Path
import pickle
from collections import defaultdict, deque
import threading
import time


@dataclass
class UserBehavior:
    """Represents user interaction behavior for LOD prediction"""
    user_id: str
    session_id: str
    device_type: str  # mobile, tablet, desktop, vr
    connection_speed: str  # slow, medium, fast
    gpu_tier: str  # low, medium, high
    viewport_size: Tuple[int, int]
    avg_interaction_time: float
    zoom_frequency: int
    rotate_frequency: int
    detail_preference: float  # 0.0 to 1.0
    performance_tolerance: float  # 0.0 to 1.0
    timestamp: str


@dataclass
class ModelLOD:
    """Represents a Level of Detail for a 3D model"""
    model_name: str
    lod_level: int  # 0 = highest detail, higher numbers = lower detail
    vertex_count: int
    triangle_count: int
    file_size: int
    texture_resolution: int
    performance_score: float  # estimated performance impact (0-1)
    quality_score: float  # visual quality score (0-1)
    file_path: str


@dataclass
class LODPrediction:
    """Represents a LOD prediction result"""
    recommended_lod: int
    confidence: float
    reasoning: List[str]
    alternatives: List[int]
    performance_estimate: Dict[str, float]
    quality_estimate: float


class MLLODPredictor:
    """Machine Learning LOD Predictor using behavioral analysis"""
    
    def __init__(self, model_dir: str = "lod_models"):
        self.model_dir = Path(model_dir)
        self.model_dir.mkdir(exist_ok=True)
        
        # User behavior tracking
        self.user_behaviors: Dict[str, List[UserBehavior]] = defaultdict(list)
        self.session_data: Dict[str, Dict] = {}
        
        # LOD definitions for models
        self.model_lods: Dict[str, List[ModelLOD]] = {}
        
        # ML model weights (simplified neural network approach)
        self.feature_weights = self._load_or_initialize_weights()
        
        # Performance tracking
        self.performance_history: Dict[str, deque] = defaultdict(lambda: deque(maxlen=100))
        
        # Learning parameters
        self.learning_rate = 0.01
        self.adaptation_threshold = 0.1
        
        # Background learning thread
        self._learning_thread = None
        self._stop_learning = False
        
        self._initialize_default_lods()
        self._start_background_learning()
    
    def _load_or_initialize_weights(self) -> Dict[str, float]:
        """Load ML model weights or initialize defaults"""
        weights_file = self.model_dir / "lod_weights.json"
        
        default_weights = {
            "device_mobile": -0.3,
            "device_tablet": -0.1,
            "device_desktop": 0.2,
            "device_vr": 0.4,
            "connection_slow": -0.4,
            "connection_medium": 0.0,
            "connection_fast": 0.3,
            "gpu_low": -0.5,
            "gpu_medium": 0.0,
            "gpu_high": 0.4,
            "viewport_small": -0.2,
            "viewport_medium": 0.0,
            "viewport_large": 0.3,
            "interaction_time_short": -0.1,
            "interaction_time_long": 0.2,
            "zoom_frequency_high": 0.3,
            "rotate_frequency_high": 0.2,
            "detail_preference": 0.5,
            "performance_tolerance": -0.3,
            "time_of_day": 0.1,
            "model_complexity": -0.4
        }
        
        if weights_file.exists():
            try:
                with open(weights_file, 'r') as f:
                    loaded_weights = json.load(f)
                    default_weights.update(loaded_weights)
            except Exception as e:
                print(f"Error loading weights: {e}")
        
        return default_weights
    
    def _save_weights(self):
        """Save ML model weights"""
        try:
            with open(self.model_dir / "lod_weights.json", 'w') as f:
                json.dump(self.feature_weights, f, indent=2)
        except Exception as e:
            print(f"Error saving weights: {e}")
    
    def _initialize_default_lods(self):
        """Initialize default LOD configurations for models"""
        # Example LOD configurations for existing models
        model_configs = {
            "Man.fbx": [
                ModelLOD("Man.fbx", 0, 5000, 8000, 303280, 1024, 0.8, 1.0, "Man_LOD0.fbx"),
                ModelLOD("Man.fbx", 1, 2500, 4000, 200000, 512, 0.5, 0.8, "Man_LOD1.fbx"),
                ModelLOD("Man.fbx", 2, 1000, 1500, 100000, 256, 0.3, 0.6, "Man_LOD2.fbx"),
                ModelLOD("Man.fbx", 3, 500, 750, 50000, 128, 0.1, 0.4, "Man_LOD3.fbx")
            ],
            "Walking.fbx": [
                ModelLOD("Walking.fbx", 0, 5000, 8000, 760528, 1024, 0.9, 1.0, "Walking_LOD0.fbx"),
                ModelLOD("Walking.fbx", 1, 2500, 4000, 400000, 512, 0.6, 0.8, "Walking_LOD1.fbx"),
                ModelLOD("Walking.fbx", 2, 1000, 1500, 200000, 256, 0.4, 0.6, "Walking_LOD2.fbx"),
                ModelLOD("Walking.fbx", 3, 500, 750, 100000, 128, 0.2, 0.4, "Walking_LOD3.fbx")
            ],
            "Running.fbx": [
                ModelLOD("Running.fbx", 0, 5000, 8000, 751104, 1024, 0.9, 1.0, "Running_LOD0.fbx"),
                ModelLOD("Running.fbx", 1, 2500, 4000, 400000, 512, 0.6, 0.8, "Running_LOD1.fbx"),
                ModelLOD("Running.fbx", 2, 1000, 1500, 200000, 256, 0.4, 0.6, "Running_LOD2.fbx"),
                ModelLOD("Running.fbx", 3, 500, 750, 100000, 128, 0.2, 0.4, "Running_LOD3.fbx")
            ],
            "Idle.fbx": [
                ModelLOD("Idle.fbx", 0, 5000, 8000, 1140880, 1024, 0.8, 1.0, "Idle_LOD0.fbx"),
                ModelLOD("Idle.fbx", 1, 2500, 4000, 600000, 512, 0.5, 0.8, "Idle_LOD1.fbx"),
                ModelLOD("Idle.fbx", 2, 1000, 1500, 300000, 256, 0.3, 0.6, "Idle_LOD2.fbx"),
                ModelLOD("Idle.fbx", 3, 500, 750, 150000, 128, 0.1, 0.4, "Idle_LOD3.fbx")
            ],
            "Man_Rig.fbx": [
                ModelLOD("Man_Rig.fbx", 0, 5000, 8000, 714496, 1024, 0.8, 1.0, "Man_Rig_LOD0.fbx"),
                ModelLOD("Man_Rig.fbx", 1, 2500, 4000, 400000, 512, 0.5, 0.8, "Man_Rig_LOD1.fbx"),
                ModelLOD("Man_Rig.fbx", 2, 1000, 1500, 200000, 256, 0.3, 0.6, "Man_Rig_LOD2.fbx"),
                ModelLOD("Man_Rig.fbx", 3, 500, 750, 100000, 128, 0.1, 0.4, "Man_Rig_LOD3.fbx")
            ]
        }
        
        self.model_lods.update(model_configs)
    
    def track_user_behavior(self, behavior: UserBehavior):
        """Track user behavior for learning"""
        self.user_behaviors[behavior.user_id].append(behavior)
        
        # Keep only recent behaviors (last 100 per user)
        if len(self.user_behaviors[behavior.user_id]) > 100:
            self.user_behaviors[behavior.user_id] = self.user_behaviors[behavior.user_id][-100:]
    
    def start_session(self, user_id: str, session_id: str, device_info: Dict[str, Any]) -> Dict[str, Any]:
        """Start a new user session for behavior tracking"""
        self.session_data[session_id] = {
            "user_id": user_id,
            "start_time": datetime.now().isoformat(),
            "device_info": device_info,
            "interactions": [],
            "performance_metrics": []
        }
        
        return {
            "session_id": session_id,
            "message": "Session started for LOD tracking",
            "status": "success"
        }
    
    def predict_lod(self, model_name: str, user_context: Dict[str, Any], 
                   session_id: str = None) -> LODPrediction:
        """Predict optimal LOD based on user context and ML model"""
        
        if model_name not in self.model_lods:
            # Default to medium LOD if model not found
            return LODPrediction(
                recommended_lod=1,
                confidence=0.5,
                reasoning=["Model not found, using default medium LOD"],
                alternatives=[0, 2],
                performance_estimate={"fps": 30, "load_time": 2.0},
                quality_estimate=0.8
            )
        
        # Extract features from user context
        features = self._extract_features(user_context, session_id)
        
        # Calculate LOD score using ML model
        lod_scores = []
        available_lods = self.model_lods[model_name]
        
        for lod in available_lods:
            score = self._calculate_lod_score(features, lod)
            lod_scores.append((lod.lod_level, score))
        
        # Sort by score and select best LOD
        lod_scores.sort(key=lambda x: x[1], reverse=True)
        recommended_lod = lod_scores[0][0]
        confidence = lod_scores[0][1]
        
        # Get alternatives
        alternatives = [lod for lod, score in lod_scores[1:3]]
        
        # Generate reasoning
        reasoning = self._generate_reasoning(features, recommended_lod, available_lods)
        
        # Estimate performance
        performance_estimate = self._estimate_performance(
            available_lods[recommended_lod], user_context
        )
        
        # Quality estimate
        quality_estimate = available_lods[recommended_lod].quality_score
        
        prediction = LODPrediction(
            recommended_lod=recommended_lod,
            confidence=confidence,
            reasoning=reasoning,
            alternatives=alternatives,
            performance_estimate=performance_estimate,
            quality_estimate=quality_estimate
        )
        
        # Track prediction for learning
        self._track_prediction(session_id, model_name, prediction, user_context)
        
        return prediction
    
    def _extract_features(self, user_context: Dict[str, Any], session_id: str = None) -> Dict[str, float]:
        """Extract numerical features from user context"""
        features = {}
        
        # Device type features
        device_type = user_context.get("device_type", "desktop").lower()
        features["device_mobile"] = 1.0 if device_type == "mobile" else 0.0
        features["device_tablet"] = 1.0 if device_type == "tablet" else 0.0
        features["device_desktop"] = 1.0 if device_type == "desktop" else 0.0
        features["device_vr"] = 1.0 if device_type == "vr" else 0.0
        
        # Connection speed features
        connection = user_context.get("connection_speed", "medium").lower()
        features["connection_slow"] = 1.0 if connection == "slow" else 0.0
        features["connection_medium"] = 1.0 if connection == "medium" else 0.0
        features["connection_fast"] = 1.0 if connection == "fast" else 0.0
        
        # GPU tier features
        gpu_tier = user_context.get("gpu_tier", "medium").lower()
        features["gpu_low"] = 1.0 if gpu_tier == "low" else 0.0
        features["gpu_medium"] = 1.0 if gpu_tier == "medium" else 0.0
        features["gpu_high"] = 1.0 if gpu_tier == "high" else 0.0
        
        # Viewport size features
        viewport = user_context.get("viewport_size", [1920, 1080])
        area = viewport[0] * viewport[1]
        if area < 500000:  # Small screen
            features["viewport_small"] = 1.0
            features["viewport_medium"] = 0.0
            features["viewport_large"] = 0.0
        elif area < 2000000:  # Medium screen
            features["viewport_small"] = 0.0
            features["viewport_medium"] = 1.0
            features["viewport_large"] = 0.0
        else:  # Large screen
            features["viewport_small"] = 0.0
            features["viewport_medium"] = 0.0
            features["viewport_large"] = 1.0
        
        # User preference features
        features["detail_preference"] = user_context.get("detail_preference", 0.5)
        features["performance_tolerance"] = user_context.get("performance_tolerance", 0.5)
        
        # Time-based features
        current_hour = datetime.now().hour
        features["time_of_day"] = current_hour / 24.0  # Normalize to 0-1
        
        # Session-based features
        if session_id and session_id in self.session_data:
            session = self.session_data[session_id]
            interactions = session.get("interactions", [])
            
            if interactions:
                features["interaction_time_short"] = 1.0 if len(interactions) < 10 else 0.0
                features["interaction_time_long"] = 1.0 if len(interactions) > 50 else 0.0
                
                zoom_count = sum(1 for i in interactions if i.get("type") == "zoom")
                rotate_count = sum(1 for i in interactions if i.get("type") == "rotate")
                
                features["zoom_frequency_high"] = 1.0 if zoom_count > 10 else 0.0
                features["rotate_frequency_high"] = 1.0 if rotate_count > 20 else 0.0
            else:
                features["interaction_time_short"] = 0.0
                features["interaction_time_long"] = 0.0
                features["zoom_frequency_high"] = 0.0
                features["rotate_frequency_high"] = 0.0
        
        return features
    
    def _calculate_lod_score(self, features: Dict[str, float], lod: ModelLOD) -> float:
        """Calculate LOD score using ML model weights"""
        score = 0.0
        
        # Apply feature weights
        for feature, value in features.items():
            if feature in self.feature_weights:
                score += self.feature_weights[feature] * value
        
        # Model complexity penalty
        complexity_factor = lod.performance_score
        score += self.feature_weights.get("model_complexity", -0.4) * complexity_factor
        
        # Quality bonus
        score += lod.quality_score * 0.3
        
        # Normalize score to 0-1 range
        score = max(0.0, min(1.0, (score + 1.0) / 2.0))
        
        return score
    
    def _generate_reasoning(self, features: Dict[str, float], recommended_lod: int, 
                          lods: List[ModelLOD]) -> List[str]:
        """Generate human-readable reasoning for LOD selection"""
        reasoning = []
        
        # Device-based reasoning
        if features.get("device_mobile", 0) > 0:
            reasoning.append("Mobile device detected - optimizing for battery and performance")
        elif features.get("device_vr", 0) > 0:
            reasoning.append("VR device detected - prioritizing high frame rate")
        elif features.get("gpu_high", 0) > 0:
            reasoning.append("High-end GPU detected - can handle higher detail")
        
        # Connection-based reasoning
        if features.get("connection_slow", 0) > 0:
            reasoning.append("Slow connection detected - reducing file size")
        elif features.get("connection_fast", 0) > 0:
            reasoning.append("Fast connection allows for higher quality models")
        
        # User preference reasoning
        detail_pref = features.get("detail_preference", 0.5)
        if detail_pref > 0.7:
            reasoning.append("High detail preference detected")
        elif detail_pref < 0.3:
            reasoning.append("Performance preference over detail detected")
        
        # LOD-specific reasoning
        selected_lod = lods[recommended_lod]
        reasoning.append(f"Selected LOD {recommended_lod} with {selected_lod.triangle_count} triangles")
        
        if not reasoning:
            reasoning.append("Balanced LOD selection based on overall context")
        
        return reasoning
    
    def _estimate_performance(self, lod: ModelLOD, user_context: Dict[str, Any]) -> Dict[str, float]:
        """Estimate performance metrics for selected LOD"""
        
        # Base performance estimates
        base_fps = 60.0
        base_load_time = 1.0
        
        # Adjust based on LOD complexity
        performance_factor = 1.0 - lod.performance_score
        fps = base_fps * (0.5 + performance_factor * 0.5)
        load_time = base_load_time * (0.5 + lod.performance_score * 1.5)
        
        # Adjust based on device capabilities
        device_type = user_context.get("device_type", "desktop").lower()
        if device_type == "mobile":
            fps *= 0.7
            load_time *= 1.5
        elif device_type == "vr":
            fps *= 1.2  # VR needs higher FPS
            load_time *= 0.8
        
        # Adjust based on connection speed
        connection = user_context.get("connection_speed", "medium").lower()
        if connection == "slow":
            load_time *= 2.0
        elif connection == "fast":
            load_time *= 0.5
        
        return {
            "estimated_fps": round(fps, 1),
            "estimated_load_time": round(load_time, 2),
            "memory_usage_mb": round(lod.file_size / (1024 * 1024) * 2, 1),
            "bandwidth_usage_mb": round(lod.file_size / (1024 * 1024), 2)
        }
    
    def _track_prediction(self, session_id: str, model_name: str, 
                         prediction: LODPrediction, user_context: Dict[str, Any]):
        """Track prediction for learning"""
        if session_id and session_id in self.session_data:
            self.session_data[session_id].setdefault("predictions", []).append({
                "timestamp": datetime.now().isoformat(),
                "model_name": model_name,
                "predicted_lod": prediction.recommended_lod,
                "confidence": prediction.confidence,
                "user_context": user_context
            })
    
    def provide_feedback(self, session_id: str, prediction_index: int, 
                        feedback: Dict[str, Any]) -> Dict[str, Any]:
        """Provide feedback on LOD prediction for learning"""
        if session_id not in self.session_data:
            return {"error": "Session not found", "status": "error"}
        
        predictions = self.session_data[session_id].get("predictions", [])
        if prediction_index >= len(predictions):
            return {"error": "Prediction not found", "status": "error"}
        
        # Store feedback
        predictions[prediction_index]["feedback"] = feedback
        predictions[prediction_index]["feedback_timestamp"] = datetime.now().isoformat()
        
        # Trigger learning update
        self._update_weights_from_feedback(predictions[prediction_index])
        
        return {
            "message": "Feedback recorded successfully",
            "status": "success"
        }
    
    def _update_weights_from_feedback(self, prediction_data: Dict[str, Any]):
        """Update ML weights based on user feedback"""
        feedback = prediction_data.get("feedback", {})
        satisfaction = feedback.get("satisfaction", 0.5)  # 0-1 scale
        performance_rating = feedback.get("performance", 0.5)  # 0-1 scale
        
        # Extract features from the prediction
        user_context = prediction_data["user_context"]
        features = self._extract_features(user_context)
        
        # Calculate error (how far off we were)
        target_score = (satisfaction + performance_rating) / 2.0
        actual_score = prediction_data["confidence"]
        error = target_score - actual_score
        
        # Update weights using gradient descent
        for feature, value in features.items():
            if feature in self.feature_weights:
                self.feature_weights[feature] += self.learning_rate * error * value
        
        # Save updated weights
        self._save_weights()
    
    def _start_background_learning(self):
        """Start background thread for continuous learning"""
        def learning_loop():
            while not self._stop_learning:
                try:
                    self._periodic_learning_update()
                    time.sleep(3600)  # Update every hour
                except Exception as e:
                    print(f"Error in background learning: {e}")
                    time.sleep(300)  # Wait 5 minutes on error
        
        self._learning_thread = threading.Thread(target=learning_loop, daemon=True)
        self._learning_thread.start()
    
    def _periodic_learning_update(self):
        """Perform periodic learning updates"""
        # Analyze recent predictions and performance
        recent_feedback = []
        
        for session_id, session in self.session_data.items():
            predictions = session.get("predictions", [])
            for pred in predictions:
                if "feedback" in pred:
                    recent_feedback.append(pred)
        
        if len(recent_feedback) >= 10:  # Need minimum feedback for learning
            # Batch update weights
            for pred_data in recent_feedback[-50:]:  # Use last 50 feedback items
                self._update_weights_from_feedback(pred_data)
    
    def get_lod_options(self, model_name: str) -> List[Dict[str, Any]]:
        """Get available LOD options for a model"""
        if model_name not in self.model_lods:
            return []
        
        return [
            {
                "lod_level": lod.lod_level,
                "vertex_count": lod.vertex_count,
                "triangle_count": lod.triangle_count,
                "file_size": lod.file_size,
                "texture_resolution": lod.texture_resolution,
                "performance_score": lod.performance_score,
                "quality_score": lod.quality_score,
                "description": f"LOD {lod.lod_level} - {lod.triangle_count} triangles"
            }
            for lod in self.model_lods[model_name]
        ]
    
    def get_analytics(self) -> Dict[str, Any]:
        """Get LOD prediction analytics"""
        total_predictions = 0
        total_feedback = 0
        avg_confidence = 0.0
        
        for session in self.session_data.values():
            predictions = session.get("predictions", [])
            total_predictions += len(predictions)
            
            confidences = []
            for pred in predictions:
                confidences.append(pred["confidence"])
                if "feedback" in pred:
                    total_feedback += 1
            
            if confidences:
                avg_confidence += sum(confidences) / len(confidences)
        
        if total_predictions > 0:
            avg_confidence /= len([s for s in self.session_data.values() if s.get("predictions")])
        
        return {
            "total_sessions": len(self.session_data),
            "total_predictions": total_predictions,
            "total_feedback": total_feedback,
            "feedback_rate": total_feedback / total_predictions if total_predictions > 0 else 0,
            "average_confidence": round(avg_confidence, 3),
            "available_models": len(self.model_lods),
            "ml_weights_count": len(self.feature_weights),
            "last_update": datetime.now().isoformat()
        }


# Initialize global LOD predictor
lod_predictor = MLLODPredictor()