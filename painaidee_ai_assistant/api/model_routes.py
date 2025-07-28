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
    """Add enhanced model routes to FastAPI app"""
    
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