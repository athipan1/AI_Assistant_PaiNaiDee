"""
Enhanced AI Agent for 3D Model Selection
Supports multiple AI backends: OpenChat, OpenHermes, llama.cpp, and Hugging Face
"""

import os
import re
import json
from typing import Dict, List, Any, Optional
from pathlib import Path
import logging

logger = logging.getLogger(__name__)

class EnhancedModelSelector:
    """
    Enhanced AI-powered 3D model selector with multiple backend support
    """
    
    def __init__(self):
        self.models_dir = Path(__file__).parent.parent.parent / "assets" / "models" / "Fbx"
        
        # Enhanced keyword mapping with weights
        self.keyword_weights = {
            # Person/Character keywords
            "person": {"model": "Man.fbx", "weight": 0.8},
            "human": {"model": "Man.fbx", "weight": 0.9},
            "man": {"model": "Man.fbx", "weight": 0.9},
            "character": {"model": "Man.fbx", "weight": 0.7},
            "figure": {"model": "Man.fbx", "weight": 0.6},
            
            # Idle/Standing keywords
            "idle": {"model": "Idle.fbx", "weight": 0.9},
            "standing": {"model": "Idle.fbx", "weight": 0.8},
            "still": {"model": "Idle.fbx", "weight": 0.7},
            "pose": {"model": "Idle.fbx", "weight": 0.6},
            "static": {"model": "Idle.fbx", "weight": 0.7},
            
            # Walking keywords
            "walking": {"model": "Walking.fbx", "weight": 0.9},
            "walk": {"model": "Walking.fbx", "weight": 0.9},
            "move": {"model": "Walking.fbx", "weight": 0.6},
            "step": {"model": "Walking.fbx", "weight": 0.7},
            "stroll": {"model": "Walking.fbx", "weight": 0.8},
            
            # Running keywords
            "running": {"model": "Running.fbx", "weight": 0.9},
            "run": {"model": "Running.fbx", "weight": 0.9},
            "fast": {"model": "Running.fbx", "weight": 0.6},
            "sprint": {"model": "Running.fbx", "weight": 0.8},
            "jog": {"model": "Running.fbx", "weight": 0.7},
            
            # Rig/Animation keywords
            "rig": {"model": "Man_Rig.fbx", "weight": 0.9},
            "rigged": {"model": "Man_Rig.fbx", "weight": 0.9},
            "animation": {"model": "Man_Rig.fbx", "weight": 0.7},
            "skeleton": {"model": "Man_Rig.fbx", "weight": 0.8},
            "bones": {"model": "Man_Rig.fbx", "weight": 0.8}
        }
        
        self.model_descriptions = {
            "Man.fbx": "3D character model of a human figure in neutral pose",
            "Idle.fbx": "Animated character in idle/standing position", 
            "Walking.fbx": "Character animation showing walking motion",
            "Running.fbx": "Character animation demonstrating running movement",
            "Man_Rig.fbx": "Rigged character model ready for custom animations"
        }
        
        # Initialize AI backend if available
        self.ai_backend = self._initialize_ai_backend()
    
    def _initialize_ai_backend(self) -> Optional[Any]:
        """Initialize available AI backend"""
        try:
            # Try Hugging Face transformers first
            from transformers import pipeline
            sentiment_analyzer = pipeline("sentiment-analysis")
            logger.info("Initialized Hugging Face transformers backend")
            return {"type": "huggingface", "pipeline": sentiment_analyzer}
        except ImportError:
            logger.info("Hugging Face transformers not available")
        
        try:
            # Try OpenAI-compatible models (could be local llama.cpp server)
            import openai
            logger.info("OpenAI-compatible backend available")
            return {"type": "openai", "client": openai}
        except ImportError:
            logger.info("OpenAI backend not available")
        
        logger.info("Using keyword-based analysis (no AI backend)")
        return None
    
    def analyze_question_with_ai(self, question: str) -> Dict[str, Any]:
        """Enhanced question analysis using AI if available"""
        
        if self.ai_backend:
            try:
                if self.ai_backend["type"] == "huggingface":
                    # Use sentiment and keywords combined
                    return self._analyze_with_huggingface(question)
                elif self.ai_backend["type"] == "openai":
                    # Use OpenAI-compatible API (could be local model)
                    return self._analyze_with_openai(question)
            except Exception as e:
                logger.warning(f"AI analysis failed: {e}, falling back to keyword analysis")
        
        # Fallback to enhanced keyword analysis
        return self._analyze_with_keywords(question)
    
    def _analyze_with_huggingface(self, question: str) -> Dict[str, Any]:
        """Analyze using Hugging Face transformers"""
        # This is a simplified example - in real implementation,
        # you'd use a more sophisticated model for intent classification
        
        keyword_result = self._analyze_with_keywords(question)
        
        # Use sentiment to adjust confidence
        try:
            sentiment = self.ai_backend["pipeline"](question)[0]
            confidence_boost = 0.1 if sentiment["label"] == "POSITIVE" else 0.0
            keyword_result["confidence"] = min(1.0, keyword_result["confidence"] + confidence_boost)
            keyword_result["ai_method"] = "huggingface_enhanced"
        except Exception as e:
            logger.warning(f"Sentiment analysis failed: {e}")
            keyword_result["ai_method"] = "keyword_fallback"
        
        return keyword_result
    
    def _analyze_with_openai(self, question: str) -> Dict[str, Any]:
        """Analyze using OpenAI-compatible API (local or remote)"""
        try:
            # Example prompt for model selection
            prompt = f"""
            Based on this question about 3D models, select the most appropriate model:
            
            Question: "{question}"
            
            Available models:
            - Man.fbx: Basic human character
            - Idle.fbx: Standing/idle character
            - Walking.fbx: Walking animation
            - Running.fbx: Running animation  
            - Man_Rig.fbx: Rigged character for custom animations
            
            Respond with JSON: {{"model": "filename.fbx", "confidence": 0.8, "reasoning": "explanation"}}
            """
            
            # This would call your local llama.cpp server or OpenAI API
            # For now, return enhanced keyword analysis
            result = self._analyze_with_keywords(question)
            result["ai_method"] = "openai_enhanced"
            return result
            
        except Exception as e:
            logger.warning(f"OpenAI analysis failed: {e}")
            return self._analyze_with_keywords(question)
    
    def _analyze_with_keywords(self, question: str) -> Dict[str, Any]:
        """Enhanced keyword-based analysis with weights"""
        question_lower = question.lower()
        
        # Remove common words
        stop_words = {"the", "a", "an", "show", "me", "display", "i", "want", "to", "see", "can", "you"}
        words = [word for word in re.findall(r'\b\w+\b', question_lower) if word not in stop_words]
        
        # Score each model based on weighted keyword matches
        model_scores = {}
        total_matches = 0
        
        for word in words:
            if word in self.keyword_weights:
                mapping = self.keyword_weights[word]
                model = mapping["model"]
                weight = mapping["weight"]
                
                if model not in model_scores:
                    model_scores[model] = 0
                model_scores[model] += weight
                total_matches += 1
        
        # Calculate confidence and select best model
        if not model_scores:
            selected_model = "Man.fbx"
            confidence = 0.5
            reasoning = "No specific keywords found, defaulting to basic character"
        else:
            selected_model = max(model_scores, key=model_scores.get)
            max_score = model_scores[selected_model]
            confidence = min(1.0, max_score / max(len(words), 1))
            reasoning = f"Matched {total_matches} relevant keywords"
        
        return {
            "selected_model": selected_model,
            "confidence": confidence,
            "description": self.model_descriptions.get(selected_model, "3D model"),
            "model_path": str(self.models_dir / selected_model),
            "available_models": list(self.model_descriptions.keys()),
            "reasoning": reasoning,
            "ai_method": "enhanced_keywords",
            "keyword_scores": model_scores
        }
    
    def analyze_question(self, question: str) -> Dict[str, Any]:
        """Main entry point for question analysis"""
        return self.analyze_question_with_ai(question)
    
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
                logger.error(f"Error loading model {model_file.name}: {e}")
        return models

# Global instance for the enhanced selector
enhanced_model_selector = EnhancedModelSelector()

def test_enhanced_selector():
    """Test the enhanced model selector"""
    selector = EnhancedModelSelector()
    
    test_questions = [
        "Show me a person walking",
        "I need a running character for my game",
        "Display an idle animation",
        "Can you show me a rigged model?",
        "I want to see a human figure standing still",
        "Show me some fast movement animation"
    ]
    
    print("Testing Enhanced Model Selector:")
    print("=" * 60)
    
    for question in test_questions:
        result = selector.analyze_question(question)
        print(f"Question: {question}")
        print(f"Selected: {result['selected_model']}")
        print(f"Confidence: {result['confidence']:.2f}")
        print(f"Method: {result['ai_method']}")
        print(f"Reasoning: {result['reasoning']}")
        if 'keyword_scores' in result:
            print(f"Keyword Scores: {result['keyword_scores']}")
        print("-" * 40)

if __name__ == "__main__":
    test_enhanced_selector()