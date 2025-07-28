"""
3D Model API Routes
Handles 3D model selection and serving endpoints
"""

import os
import json
import re
from typing import List, Optional, Dict, Any
from pathlib import Path

# For now, create a simple implementation that can work without heavy dependencies
# Will be enhanced with proper FastAPI later

class ModelSelector:
    """AI-powered 3D model selector"""
    
    def __init__(self):
        self.models_dir = Path(__file__).parent.parent.parent / "assets" / "models" / "Fbx"
        self.model_mapping = {
            # Keywords mapped to model files
            "person": "Man.fbx",
            "human": "Man.fbx", 
            "man": "Man.fbx",
            "character": "Man.fbx",
            "idle": "Idle.fbx",
            "standing": "Idle.fbx",
            "still": "Idle.fbx",
            "walking": "Walking.fbx",
            "walk": "Walking.fbx",
            "move": "Walking.fbx",
            "running": "Running.fbx",
            "run": "Running.fbx",
            "fast": "Running.fbx",
            "rig": "Man_Rig.fbx",
            "rigged": "Man_Rig.fbx",
            "animation": "Man_Rig.fbx"
        }
        
        self.model_descriptions = {
            "Man.fbx": "3D character model of a human figure in neutral pose",
            "Idle.fbx": "Animated character in idle/standing position",
            "Walking.fbx": "Character animation showing walking motion",
            "Running.fbx": "Character animation demonstrating running movement", 
            "Man_Rig.fbx": "Rigged character model ready for custom animations"
        }

    def analyze_question(self, question: str) -> Dict[str, Any]:
        """
        Analyze user question and select appropriate 3D model
        Simple keyword matching - can be enhanced with AI models later
        """
        question_lower = question.lower()
        
        # Score each model based on keyword matches
        scores = {}
        for keyword, model in self.model_mapping.items():
            if keyword in question_lower:
                scores[model] = scores.get(model, 0) + 1
        
        # Default to Man.fbx if no matches
        if not scores:
            selected_model = "Man.fbx"
            confidence = 0.5
        else:
            selected_model = max(scores, key=scores.get)
            confidence = min(scores[selected_model] / len(question.split()), 1.0)
        
        return {
            "selected_model": selected_model,
            "confidence": confidence,
            "description": self.model_descriptions.get(selected_model, "3D model"),
            "model_path": str(self.models_dir / selected_model),
            "available_models": list(self.model_descriptions.keys())
        }

    def get_model_info(self, model_name: str) -> Dict[str, Any]:
        """Get detailed information about a specific model"""
        model_path = self.models_dir / model_name
        
        if not model_path.exists():
            raise FileNotFoundError(f"Model {model_name} not found")
        
        return {
            "name": model_name,
            "path": str(model_path),
            "size": model_path.stat().st_size,
            "description": self.model_descriptions.get(model_name, "3D model"),
            "format": "FBX",
            "interactions": ["rotate", "zoom", "pan", "click_info"]
        }

    def list_available_models(self) -> List[Dict[str, Any]]:
        """List all available 3D models"""
        models = []
        for model_file in self.models_dir.glob("*.fbx"):
            try:
                model_info = self.get_model_info(model_file.name)
                models.append(model_info)
            except Exception as e:
                print(f"Error loading model {model_file.name}: {e}")
        return models

# Global instance
model_selector = ModelSelector()

def create_model_routes(app):
    """Add model routes to FastAPI app when available"""
    
    @app.post("/ai/select_model")
    async def select_model_for_question(request: dict):
        """
        Analyze question and select appropriate 3D model
        """
        try:
            question = request.get("question", "")
            language = request.get("language", "en")
            
            if not question:
                raise ValueError("Question is required")
            
            result = model_selector.analyze_question(question)
            
            return {
                "question": question,
                "language": language,
                "model_selection": result,
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