"""
Enhanced 3D Model API Routes with AI-Driven Selection
Integrates Intent Disambiguation, Semantic Search, and Personalization layers
"""

import os
import json
import re
from typing import List, Optional, Dict, Any
from pathlib import Path

# Import the integrated model selector
try:
    from ..agents.model_selection_agent import integrated_model_selector
except ImportError:
    # Handle direct execution
    import sys
    sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'agents'))
    from model_selection_agent import integrated_model_selector

# Use the integrated model selector as the main selector
model_selector = integrated_model_selector

def create_model_routes(app):
    """Add enhanced model routes to FastAPI app with smart tagging and favorites"""
    
    # In-memory storage for demonstration (use database in production)
    user_favorites = {}
    model_tags_db = {}
    user_sessions = {}
    
    @app.post("/ai/select_model")
    async def select_model_for_question(request: dict):
        """
        AI-powered model selection using integrated layers:
        - Intent Disambiguation Engine
        - Semantic Search
        - Personalization Layer
        """
        try:
            question = request.get("question", "")
            language = request.get("language", "en")
            session_id = request.get("session_id", None)
            user_id = request.get("user_id", None)
            
            if not question:
                raise ValueError("Question is required")
            
            # Start session if not provided
            if not session_id and user_id:
                session_id = model_selector.start_user_session(user_id)
            elif not session_id:
                session_id = model_selector.start_user_session()
            
            # Get comprehensive analysis
            result = model_selector.analyze_question_comprehensive(question, session_id, user_id)
            
            return {
                "question": question,
                "language": language,
                "session_id": session_id,
                "model_selection": {
                    "selected_model": result["selected_model"],
                    "confidence": result["confidence"],
                    "description": result["description"],
                    "model_path": result["model_path"],
                    "reasoning": result["comprehensive_reasoning"]
                },
                "ai_analysis": {
                    "intent": result["intent_analysis"],
                    "semantic_results": result["semantic_analysis"][:3],  # Top 3
                    "personalization": result["personalization_analysis"][:3] if result["personalization_analysis"] else [],
                    "method": result["ai_method"]
                },
                "status": "success"
            }
            
        except Exception as e:
            return {
                "error": str(e),
                "status": "error"
            }
    
    @app.post("/ai/start_session")
    async def start_user_session(request: dict):
        """Start a new personalization session"""
        try:
            user_id = request.get("user_id", None)
            session_id = model_selector.start_user_session(user_id)
            
            return {
                "session_id": session_id,
                "message": f"Started session for {'user ' + user_id if user_id else 'anonymous user'}",
                "status": "success"
            }
        except Exception as e:
            return {
                "error": str(e),
                "status": "error"
            }
    
    @app.post("/ai/feedback")
    async def submit_feedback(request: dict):
        """Submit feedback for personalization learning"""
        try:
            session_id = request.get("session_id", "")
            interaction_index = request.get("interaction_index", 0)
            feedback = request.get("feedback", "")  # positive, negative, neutral
            
            if not session_id or feedback not in ["positive", "negative", "neutral"]:
                raise ValueError("Valid session_id and feedback (positive/negative/neutral) required")
            
            model_selector.update_user_feedback(session_id, interaction_index, feedback)
            
            return {
                "message": "Feedback recorded successfully",
                "session_id": session_id,
                "status": "success"
            }
        except Exception as e:
            return {
                "error": str(e),
                "status": "error"
            }
    
    @app.get("/ai/session/{session_id}/summary")
    async def get_session_summary(session_id: str):
        """Get session summary and statistics"""
        try:
            summary = model_selector.get_session_summary(session_id)
            return {
                "session_summary": summary,
                "status": "success"
            }
        except Exception as e:
            return {
                "error": str(e),
                "status": "error"
            }
    
    @app.post("/ai/explain")
    async def explain_recommendation(request: dict):
        """Get detailed explanation of recommendation process"""
        try:
            question = request.get("question", "")
            session_id = request.get("session_id", None)
            
            if not question:
                raise ValueError("Question is required")
            
            explanation = model_selector.explain_recommendation(question, session_id)
            
            return {
                "explanation": explanation,
                "status": "success"
            }
        except Exception as e:
            return {
                "error": str(e),
                "status": "error"
            }

    @app.get("/ai/models")
    async def list_models():
        """List all available 3D models"""
        try:
            models = model_selector.list_available_models()
            return {
                "models": models,
                "count": len(models),
                "status": "success"
            }
        except Exception as e:
            return {
                "error": str(e),
                "status": "error"
            }

    @app.get("/ai/models/{model_name}")
    async def get_model_info(model_name: str):
        """Get detailed information about a specific model"""
        try:
            model_info = model_selector.get_model_info(model_name)
            
            # Enhance with tags and metadata
            model_info["tags"] = model_tags_db.get(model_name, [])
            model_info["favorite_count"] = sum(1 for favs in user_favorites.values() if model_name in favs)
            
            return {
                "model": model_info,
                "status": "success"
            }
        except FileNotFoundError:
            return {
                "error": f"Model {model_name} not found",
                "status": "not_found"
            }
        except Exception as e:
            return {
                "error": str(e),
                "status": "error"
            }

    @app.post("/api/models/{model_name}/tags")
    async def add_model_tags(model_name: str, request: dict):
        """Add tags to a model (admin or AI-generated)"""
        try:
            tags = request.get("tags", [])
            tag_type = request.get("type", "manual")  # manual or ai-generated
            admin_key = request.get("admin_key", "")
            
            # Simple admin verification (use proper auth in production)
            if tag_type == "manual" and admin_key != "admin123":
                return {
                    "error": "Admin access required for manual tagging",
                    "status": "unauthorized"
                }
            
            if model_name not in model_tags_db:
                model_tags_db[model_name] = []
            
            # Add new tags, avoiding duplicates
            existing_tags = set(model_tags_db[model_name])
            new_tags = [tag for tag in tags if tag not in existing_tags]
            model_tags_db[model_name].extend(new_tags)
            
            return {
                "message": f"Added {len(new_tags)} new tags to {model_name}",
                "tags": model_tags_db[model_name],
                "status": "success"
            }
        except Exception as e:
            return {
                "error": str(e),
                "status": "error"
            }

    @app.get("/api/models/{model_name}/tags")
    async def get_model_tags(model_name: str):
        """Get all tags for a specific model"""
        try:
            tags = model_tags_db.get(model_name, [])
            return {
                "model_name": model_name,
                "tags": tags,
                "count": len(tags),
                "status": "success"
            }
        except Exception as e:
            return {
                "error": str(e),
                "status": "error"
            }

    @app.post("/api/models/generate_tags")
    async def generate_ai_tags(request: dict):
        """Generate AI-based tags for models"""
        try:
            model_names = request.get("models", [])
            
            if not model_names:
                # Generate tags for all models
                available_models = model_selector.list_available_models()
                model_names = [model["name"] for model in available_models]
            
            generated_tags = {}
            
            for model_name in model_names:
                try:
                    model_info = model_selector.get_model_info(model_name)
                    ai_tags = generate_ai_tags_for_model(model_info)
                    
                    # Add to tags database
                    if model_name not in model_tags_db:
                        model_tags_db[model_name] = []
                    
                    existing_tags = set(model_tags_db[model_name])
                    new_ai_tags = [tag for tag in ai_tags if tag not in existing_tags]
                    model_tags_db[model_name].extend(new_ai_tags)
                    
                    generated_tags[model_name] = new_ai_tags
                    
                except Exception as e:
                    generated_tags[model_name] = {"error": str(e)}
            
            return {
                "generated_tags": generated_tags,
                "processed_models": len(model_names),
                "status": "success"
            }
        except Exception as e:
            return {
                "error": str(e),
                "status": "error"
            }

    @app.post("/api/favorites/toggle")
    async def toggle_favorite(request: dict):
        """Toggle favorite status for a model"""
        try:
            user_id = request.get("user_id", "anonymous")
            model_name = request.get("model_name", "")
            session_id = request.get("session_id", "")
            
            if not model_name:
                raise ValueError("Model name is required")
            
            # Use session_id as fallback for user identification
            user_key = user_id if user_id != "anonymous" else f"session_{session_id}"
            
            if user_key not in user_favorites:
                user_favorites[user_key] = set()
            
            is_favorited = model_name in user_favorites[user_key]
            
            if is_favorited:
                user_favorites[user_key].remove(model_name)
                action = "removed"
            else:
                user_favorites[user_key].add(model_name)
                action = "added"
            
            return {
                "model_name": model_name,
                "action": action,
                "is_favorited": not is_favorited,
                "total_favorites": len(user_favorites[user_key]),
                "status": "success"
            }
        except Exception as e:
            return {
                "error": str(e),
                "status": "error"
            }

    @app.get("/api/favorites/{user_id}")
    async def get_user_favorites(user_id: str, session_id: Optional[str] = None):
        """Get all favorite models for a user"""
        try:
            user_key = user_id if user_id != "anonymous" else f"session_{session_id}"
            favorites = list(user_favorites.get(user_key, set()))
            
            # Get detailed info for each favorite
            favorite_details = []
            for model_name in favorites:
                try:
                    model_info = model_selector.get_model_info(model_name)
                    model_info["tags"] = model_tags_db.get(model_name, [])
                    favorite_details.append(model_info)
                except Exception as e:
                    print(f"Error getting info for {model_name}: {e}")
            
            return {
                "user_id": user_id,
                "favorites": favorite_details,
                "count": len(favorite_details),
                "status": "success"
            }
        except Exception as e:
            return {
                "error": str(e),
                "status": "error"
            }

    @app.get("/api/tags/popular")
    async def get_popular_tags():
        """Get most popular tags across all models"""
        try:
            tag_counts = {}
            for model_tags in model_tags_db.values():
                for tag in model_tags:
                    tag_counts[tag] = tag_counts.get(tag, 0) + 1
            
            # Sort by popularity
            popular_tags = sorted(tag_counts.items(), key=lambda x: x[1], reverse=True)
            
            return {
                "popular_tags": [{"tag": tag, "count": count} for tag, count in popular_tags[:20]],
                "total_tags": len(tag_counts),
                "status": "success"
            }
        except Exception as e:
            return {
                "error": str(e),
                "status": "error"
            }

    @app.post("/api/session/sync")
    async def sync_user_session(request: dict):
        """Sync user data across sessions"""
        try:
            user_id = request.get("user_id", "")
            session_id = request.get("session_id", "")
            favorites_to_sync = request.get("favorites", [])
            
            if not user_id or not session_id:
                raise ValueError("User ID and session ID are required")
            
            # Merge session data with user data
            user_key = user_id
            session_key = f"session_{session_id}"
            
            if user_key not in user_favorites:
                user_favorites[user_key] = set()
            
            # Add session favorites to user favorites
            if session_key in user_favorites:
                user_favorites[user_key].update(user_favorites[session_key])
            
            # Add any additional favorites from request
            user_favorites[user_key].update(favorites_to_sync)
            
            return {
                "user_id": user_id,
                "synced_favorites": list(user_favorites[user_key]),
                "total_favorites": len(user_favorites[user_key]),
                "status": "success"
            }
        except Exception as e:
            return {
                "error": str(e),
                "status": "error"
            }


def generate_ai_tags_for_model(model_info):
    """Generate AI-based tags for a model based on its properties"""
    tags = []
    name = model_info.get("name", "").lower()
    description = model_info.get("description", "").lower()
    size = model_info.get("size", 0)
    format_type = model_info.get("format", "").lower()
    
    # Animation-based tags
    if any(keyword in name for keyword in ["walk", "walking"]):
        tags.extend(["animation", "walking", "movement", "locomotion"])
    elif any(keyword in name for keyword in ["run", "running"]):
        tags.extend(["animation", "running", "sport", "fast-movement"])
    elif any(keyword in name for keyword in ["idle", "standing"]):
        tags.extend(["pose", "idle", "static", "standing"])
    elif any(keyword in name for keyword in ["dance", "dancing"]):
        tags.extend(["animation", "dance", "performance", "entertainment"])
    
    # Character-based tags
    if any(keyword in name for keyword in ["man", "person", "human", "character"]):
        tags.extend(["character", "human", "figure", "anthropomorphic"])
    elif any(keyword in name for keyword in ["woman", "female"]):
        tags.extend(["character", "human", "female", "figure"])
    elif any(keyword in name for keyword in ["child", "kid"]):
        tags.extend(["character", "human", "child", "young"])
    
    # Technical tags
    if "rig" in name:
        tags.extend(["rigged", "animation-ready", "development", "technical"])
    if any(keyword in description for keyword in ["low poly", "optimized"]):
        tags.extend(["low-poly", "optimized", "performance"])
    elif any(keyword in description for keyword in ["high poly", "detailed"]):
        tags.extend(["high-poly", "detailed", "realistic"])
    
    # Size-based tags
    if size > 2000000:  # > 2MB
        tags.extend(["large", "detailed", "high-quality"])
    elif size < 500000:  # < 500KB
        tags.extend(["small", "optimized", "lightweight"])
    else:
        tags.extend(["medium", "balanced"])
    
    # Format-based tags
    tags.append(format_type)
    if format_type == "fbx":
        tags.extend(["autodesk", "animation-support"])
    elif format_type == "gltf":
        tags.extend(["web-optimized", "modern", "pbr-support"])
    elif format_type == "obj":
        tags.extend(["universal", "simple", "geometry"])
    
    # Context-based tags
    if any(keyword in description for keyword in ["game", "gaming"]):
        tags.extend(["game-ready", "interactive", "real-time"])
    elif any(keyword in description for keyword in ["archviz", "architectural"]):
        tags.extend(["architectural", "visualization", "building"])
    elif any(keyword in description for keyword in ["medical", "anatomy"]):
        tags.extend(["medical", "educational", "anatomy"])
    
    # Quality indicators
    if any(keyword in description for keyword in ["professional", "commercial"]):
        tags.extend(["professional", "commercial-grade"])
    elif any(keyword in description for keyword in ["free", "open"]):
        tags.extend(["free", "open-source", "community"])
    
    # Remove duplicates and return
    return list(set(tags))

# Standalone testing function
def test_model_selector():
    """Test the model selector functionality"""
    selector = ModelSelector()
    
    test_questions = [
        "Show me a person",
        "I want to see walking animation", 
        "Display running character",
        "Show me an idle pose",
        "Can you show a rigged model?",
        "Random question about something else"
    ]
    
    print("Testing Model Selector:")
    print("=" * 50)
    
    for question in test_questions:
        result = selector.analyze_question(question)
        print(f"Question: {question}")
        print(f"Selected Model: {result['selected_model']}")
        print(f"Confidence: {result['confidence']:.2f}")
        print(f"Description: {result['description']}")
        print("-" * 30)
    
    print("\nAvailable Models:")
    for model in selector.list_available_models():
        print(f"- {model['name']}: {model['description']}")

if __name__ == "__main__":
    test_model_selector()