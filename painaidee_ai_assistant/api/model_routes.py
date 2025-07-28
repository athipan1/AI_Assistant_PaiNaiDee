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
            # English keywords mapped to model files
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
            "animation": "Man_Rig.fbx",
            
            # Thai keywords
            "คน": "Man.fbx",
            "ตัวละคร": "Man.fbx",
            "มนุษย์": "Man.fbx",
            "คนเดิน": "Walking.fbx",
            "เดิน": "Walking.fbx",
            "คนวิ่ง": "Running.fbx",
            "วิ่ง": "Running.fbx",
            "คนยืน": "Idle.fbx",
            "ยืน": "Idle.fbx",
            "แสดง": "Man.fbx",  # Show/display - default to man
            "โมเดล": "Man.fbx",
            "แอนิเมชัน": "Man_Rig.fbx"
        }
        
        self.model_descriptions = {
            "Man.fbx": "3D character model of a human figure in neutral pose",
            "Idle.fbx": "Animated character in idle/standing position",
            "Walking.fbx": "Character animation showing walking motion",
            "Running.fbx": "Character animation demonstrating running movement", 
            "Man_Rig.fbx": "Rigged character model ready for custom animations"
        }

    def analyze_question(self, question: str, language: str = "en") -> Dict[str, Any]:
        """
        Analyze user question and select appropriate 3D model
        Simple keyword matching - can be enhanced with AI models later
        """
        question_lower = question.lower()
        
        # Score each model based on keyword matches
        scores = {}
        matched_keywords = []
        
        for keyword, model in self.model_mapping.items():
            if keyword in question_lower:
                # Give higher score for more specific keywords
                keyword_weight = len(keyword)  # Longer keywords get higher weight
                scores[model] = scores.get(model, 0) + keyword_weight
                matched_keywords.append(keyword)
        
        # Default to Man.fbx if no matches
        if not scores:
            selected_model = "Man.fbx"
            confidence = 0.3  # Lower confidence for default selection
        else:
            selected_model = max(scores, key=scores.get)
            # Better confidence calculation based on specificity
            max_score = scores[selected_model]
            confidence = min(max_score / (len(question) * 0.5), 1.0)
        
        # Generate suggestions if confidence is low
        suggestions = self._generate_suggestions(question_lower, confidence, language)
        
        return {
            "selected_model": selected_model,
            "confidence": confidence,
            "description": self.model_descriptions.get(selected_model, "3D model"),
            "model_path": str(self.models_dir / selected_model),
            "available_models": list(self.model_descriptions.keys()),
            "matched_keywords": matched_keywords,
            "suggestions": suggestions
        }

    def _generate_suggestions(self, question_lower: str, confidence: float, language: str = "en") -> List[Dict[str, Any]]:
        """Generate suggestions when confidence is low"""
        suggestions = []
        
        # Only suggest if confidence is below threshold
        if confidence >= 0.6:
            return suggestions
        
        # Find partial matches for suggestions
        partial_matches = []
        
        # Check for partial keyword matches
        for keyword, model in self.model_mapping.items():
            if any(part in keyword for part in question_lower.split()) or any(part in question_lower for part in keyword.split()):
                if model not in [s.get("model") for s in partial_matches]:
                    partial_matches.append({
                        "model": model,
                        "keyword": keyword,
                        "description": self.model_descriptions.get(model, "3D model")
                    })
        
        # Generate suggestion text based on language
        if partial_matches:
            if language == "th":
                suggestion_text = "คุณหมายถึง"
                if len(partial_matches) == 1:
                    suggestion_text += f" {self._get_thai_model_name(partial_matches[0]['model'])} ใช่ไหม?"
                else:
                    model_names = [self._get_thai_model_name(m['model']) for m in partial_matches[:3]]
                    suggestion_text += f" {' หรือ '.join(model_names)} ใช่ไหม?"
            else:
                suggestion_text = "Did you mean"
                if len(partial_matches) == 1:
                    suggestion_text += f" {self._get_english_model_name(partial_matches[0]['model'])}?"
                else:
                    model_names = [self._get_english_model_name(m['model']) for m in partial_matches[:3]]
                    suggestion_text += f" {' or '.join(model_names)}?"
            
            suggestions.append({
                "type": "clarification",
                "text": suggestion_text,
                "options": partial_matches[:3],
                "confidence_threshold": 0.6
            })
        
        # Always provide general suggestions for very low confidence
        if confidence < 0.4:
            if language == "th":
                suggestions.append({
                    "type": "examples",
                    "text": "ลองถามแบบนี้: 'แสดงคนเดิน', 'แสดงคนวิ่ง', 'แสดงตัวละคร' หรือ 'แสดงคนยืน'",
                    "examples": [
                        {"text": "แสดงคนเดิน", "model": "Walking.fbx"},
                        {"text": "แสดงคนวิ่ง", "model": "Running.fbx"},
                        {"text": "แสดงตัวละคร", "model": "Man.fbx"},
                        {"text": "แสดงคนยืน", "model": "Idle.fbx"}
                    ]
                })
            else:
                suggestions.append({
                    "type": "examples",
                    "text": "Try asking: 'show walking', 'show running', 'show character', or 'show standing'",
                    "examples": [
                        {"text": "show walking", "model": "Walking.fbx"},
                        {"text": "show running", "model": "Running.fbx"},
                        {"text": "show character", "model": "Man.fbx"},
                        {"text": "show standing", "model": "Idle.fbx"}
                    ]
                })
        
        return suggestions

    def _get_thai_model_name(self, model: str) -> str:
        """Get Thai name for model"""
        thai_names = {
            "Walking.fbx": "คนเดิน",
            "Running.fbx": "คนวิ่ง", 
            "Man.fbx": "ตัวละคร",
            "Idle.fbx": "คนยืน",
            "Man_Rig.fbx": "โมเดลแอนิเมชัน"
        }
        return thai_names.get(model, model)

    def _get_english_model_name(self, model: str) -> str:
        """Get English name for model"""
        english_names = {
            "Walking.fbx": "walking person",
            "Running.fbx": "running person",
            "Man.fbx": "character",
            "Idle.fbx": "standing person", 
            "Man_Rig.fbx": "rigged character"
        }
        return english_names.get(model, model)

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
            
            result = model_selector.analyze_question(question, language)
            
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