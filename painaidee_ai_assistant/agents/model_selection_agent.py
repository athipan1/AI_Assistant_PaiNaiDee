"""
Enhanced AI Agent for 3D Model Selection
Integrates Intent Disambiguation, Semantic Search, and Personalization layers
"""

import os
import re
import json
from typing import Dict, List, Any, Optional
from pathlib import Path
import logging

# Import the three AI layers
try:
    from .intent_disambiguation import intent_engine, Intent, ModelStyle, ModelPurpose, ModelMotion
    from .semantic_search import semantic_search_engine, SearchResult
    from .personalization import personalization_engine, Recommendation
except ImportError:
    # Handle direct execution
    import sys
    import os
    sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
    from intent_disambiguation import intent_engine, Intent, ModelStyle, ModelPurpose, ModelMotion
    from semantic_search import semantic_search_engine, SearchResult
    from personalization import personalization_engine, Recommendation

logger = logging.getLogger(__name__)

class IntegratedModelSelector:
    """
    Integrated AI-powered 3D model selector that combines:
    1. Intent Disambiguation Engine
    2. Semantic Search Engine  
    3. Personalization Layer
    """
    
    def __init__(self):
        self.models_dir = Path(__file__).parent.parent.parent / "assets" / "models" / "Fbx"
        
        # Enhanced model descriptions with additional metadata
        self.model_descriptions = {
            "Man.fbx": "3D character model of a human figure in neutral pose",
            "Idle.fbx": "Animated character in idle/standing position", 
            "Walking.fbx": "Character animation showing walking motion",
            "Running.fbx": "Character animation demonstrating running movement",
            "Man_Rig.fbx": "Rigged character model ready for custom animations"
        }
        
        # Map models to their characteristics for intent matching
        self.model_characteristics = {
            "Man.fbx": {
                "style": ModelStyle.NEUTRAL,
                "purpose": ModelPurpose.DISPLAY,
                "motion": ModelMotion.NONE
            },
            "Idle.fbx": {
                "style": ModelStyle.NEUTRAL,
                "purpose": ModelPurpose.STATIC,
                "motion": ModelMotion.IDLE
            },
            "Walking.fbx": {
                "style": ModelStyle.NEUTRAL,
                "purpose": ModelPurpose.ANIMATION,
                "motion": ModelMotion.WALKING
            },
            "Running.fbx": {
                "style": ModelStyle.NEUTRAL,
                "purpose": ModelPurpose.ANIMATION,
                "motion": ModelMotion.RUNNING
            },
            "Man_Rig.fbx": {
                "style": ModelStyle.NEUTRAL,
                "purpose": ModelPurpose.RIGGED,
                "motion": ModelMotion.CUSTOM
            }
        }
    
    def analyze_question_comprehensive(self, question: str, session_id: Optional[str] = None, 
                                     user_id: Optional[str] = None) -> Dict[str, Any]:
        """
        Comprehensive question analysis using all three AI layers
        
        Args:
            question: User input query
            session_id: Current session ID (optional)
            user_id: User ID for personalization (optional)
            
        Returns:
            Complete analysis with model recommendation and reasoning
        """
        
        # Step 1: Intent Disambiguation
        intent = intent_engine.classify_intent(question)
        
        # Step 2: Semantic Search
        available_models = list(self.model_descriptions.keys())
        semantic_results = semantic_search_engine.search(question, top_k=len(available_models))
        
        # Step 3: Personalization (if session provided)
        personalized_recommendations = []
        if session_id:
            personalized_recommendations = personalization_engine.get_recommendations(
                session_id, question, available_models, top_k=len(available_models)
            )
        
        # Step 4: Integrate all results
        integrated_result = self._integrate_results(
            question, intent, semantic_results, personalized_recommendations
        )
        
        # Step 5: Record interaction for future personalization
        if session_id and integrated_result.get("selected_model"):
            personalization_engine.record_interaction(
                session_id=session_id,
                query=question,
                selected_model=integrated_result["selected_model"],
                intent_style=intent.style.value,
                intent_purpose=intent.purpose.value,
                intent_motion=intent.motion.value,
                confidence=integrated_result["confidence"]
            )
        
        return integrated_result
    
    def _integrate_results(self, question: str, intent: Intent, 
                          semantic_results: List[SearchResult],
                          personalized_recommendations: List[Recommendation]) -> Dict[str, Any]:
        """Integrate results from all three AI layers"""
        
        # Calculate composite scores for each model
        model_scores = {}
        reasoning_components = {}
        
        available_models = list(self.model_descriptions.keys())
        
        for model in available_models:
            score_components = {
                "intent_match": 0.0,
                "semantic_similarity": 0.0,
                "personalization": 0.0
            }
            
            reasoning_parts = []
            
            # 1. Intent matching score
            model_char = self.model_characteristics.get(model, {})
            intent_score = self._calculate_intent_match(intent, model_char)
            score_components["intent_match"] = intent_score
            if intent_score > 0.5:
                reasoning_parts.append(f"Intent match: {intent_score:.2f}")
            
            # 2. Semantic similarity score
            semantic_score = 0.0
            for result in semantic_results:
                if result.model_name == model:
                    semantic_score = result.similarity_score
                    reasoning_parts.append(f"Semantic similarity: {semantic_score:.2f}")
                    break
            score_components["semantic_similarity"] = semantic_score
            
            # 3. Personalization score
            personalization_score = 0.0
            for rec in personalized_recommendations:
                if rec.model_name == model:
                    personalization_score = rec.personalization_score
                    reasoning_parts.append(f"Personalization: {personalization_score:.2f}")
                    break
            score_components["personalization"] = personalization_score
            
            # Calculate weighted composite score
            weights = {
                "intent_match": 0.4,
                "semantic_similarity": 0.4,
                "personalization": 0.2 if personalized_recommendations else 0.0
            }
            
            # Adjust weights if no personalization
            if not personalized_recommendations:
                weights["intent_match"] = 0.5
                weights["semantic_similarity"] = 0.5
            
            composite_score = sum(
                score_components[component] * weights[component]
                for component in weights
            )
            
            model_scores[model] = composite_score
            reasoning_components[model] = {
                "components": score_components,
                "reasoning": "; ".join(reasoning_parts) if reasoning_parts else "Default selection"
            }
        
        # Select best model
        selected_model = max(model_scores, key=model_scores.get)
        confidence = model_scores[selected_model]
        
        # Generate comprehensive reasoning
        comprehensive_reasoning = self._generate_comprehensive_reasoning(
            question, intent, selected_model, reasoning_components[selected_model]
        )
        
        # Prepare result
        result = {
            "selected_model": selected_model,
            "confidence": confidence,
            "description": self.model_descriptions.get(selected_model, "3D model"),
            "model_path": str(self.models_dir / selected_model),
            "available_models": available_models,
            
            # AI Analysis Details
            "intent_analysis": {
                "style": intent.style.value,
                "purpose": intent.purpose.value,
                "motion": intent.motion.value,
                "confidence": intent.confidence,
                "reasoning": intent.reasoning,
                "ambiguities": intent.ambiguities,
                "suggestions": intent.suggestions
            },
            
            "semantic_analysis": [
                {
                    "model": result.model_name,
                    "similarity": result.similarity_score,
                    "reasoning": result.semantic_reasoning,
                    "matched_concepts": result.matched_concepts
                }
                for result in semantic_results[:3]  # Top 3 semantic results
            ],
            
            "personalization_analysis": [
                {
                    "model": rec.model_name,
                    "score": rec.personalization_score,
                    "type": rec.recommendation_type,
                    "reasoning": rec.reasoning
                }
                for rec in personalized_recommendations[:3]  # Top 3 personalized recommendations
            ] if personalized_recommendations else [],
            
            "comprehensive_reasoning": comprehensive_reasoning,
            "all_model_scores": model_scores,
            "ai_method": "integrated_ai_layers"
        }
        
        return result
    
    def _calculate_intent_match(self, intent: Intent, model_characteristics: Dict) -> float:
        """Calculate how well a model matches the user's intent"""
        if not model_characteristics:
            return 0.3  # Default score for unknown models
        
        matches = 0
        total_checks = 0
        
        # Style matching
        if intent.style == model_characteristics.get("style"):
            matches += 1
        total_checks += 1
        
        # Purpose matching
        if intent.purpose == model_characteristics.get("purpose"):
            matches += 1
        total_checks += 1
        
        # Motion matching
        if intent.motion == model_characteristics.get("motion"):
            matches += 1
        total_checks += 1
        
        # Calculate match ratio with confidence weighting
        match_ratio = matches / total_checks if total_checks > 0 else 0
        return match_ratio * intent.confidence
    
    def _generate_comprehensive_reasoning(self, question: str, intent: Intent, 
                                        selected_model: str, score_components: Dict) -> str:
        """Generate human-readable comprehensive reasoning"""
        reasoning_parts = []
        
        # Intent summary
        reasoning_parts.append(
            f"Intent: {intent.style.value} style, {intent.purpose.value} purpose, "
            f"{intent.motion.value} motion (confidence: {intent.confidence:.2f})"
        )
        
        # Model selection reasoning
        reasoning_parts.append(f"Selected '{selected_model}' based on: {score_components['reasoning']}")
        
        # Ambiguity handling
        if intent.ambiguities:
            reasoning_parts.append(f"Note: Detected ambiguities in '{', '.join(intent.ambiguities)}'")
        
        return "; ".join(reasoning_parts)
    
    def start_user_session(self, user_id: Optional[str] = None) -> str:
        """Start a new user session for personalization"""
        return personalization_engine.start_session(user_id)
    
    def update_user_feedback(self, session_id: str, interaction_index: int, feedback: str) -> None:
        """Update user preferences based on feedback"""
        personalization_engine.update_preferences_from_feedback(session_id, interaction_index, feedback)
    
    def get_session_summary(self, session_id: str) -> Dict[str, Any]:
        """Get summary of user session"""
        return personalization_engine.get_session_summary(session_id)
    
    def explain_recommendation(self, question: str, session_id: Optional[str] = None) -> Dict[str, Any]:
        """Provide detailed explanation of how the recommendation was made"""
        result = self.analyze_question_comprehensive(question, session_id)
        
        # Add detailed explanations from each layer
        explanation = {
            "question": question,
            "final_recommendation": {
                "model": result["selected_model"],
                "confidence": result["confidence"],
                "reasoning": result["comprehensive_reasoning"]
            },
            "layer_analysis": {
                "intent_disambiguation": {
                    "detected_intent": result["intent_analysis"],
                    "explanation": "Analyzed query to understand user's style preference, purpose, and motion requirements"
                },
                "semantic_search": {
                    "results": result["semantic_analysis"],
                    "explanation": "Used embeddings to find models with semantic similarity to the query"
                },
                "personalization": {
                    "recommendations": result["personalization_analysis"],
                    "explanation": "Applied user preferences and session context for personalized suggestions"
                } if result["personalization_analysis"] else {
                    "recommendations": [],
                    "explanation": "No personalization data available (new session)"
                }
            },
            "integration_details": {
                "all_scores": result["all_model_scores"],
                "method": "Weighted combination of intent matching, semantic similarity, and personalization"
            }
        }
        
        return explanation
    
    # Legacy compatibility methods
    def analyze_question(self, question: str) -> Dict[str, Any]:
        """Legacy compatibility method"""
        return self.analyze_question_comprehensive(question)
    
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
            "interactions": ["rotate", "zoom", "pan", "click_info"],
            "characteristics": self.model_characteristics.get(model_name, {})
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


# Global instance for the integrated selector
integrated_model_selector = IntegratedModelSelector()

def test_integrated_selector():
    """Test the integrated model selector with all three AI layers"""
    selector = IntegratedModelSelector()
    
    # Start a test session
    session_id = selector.start_user_session("test_user")
    print(f"Started test session: {session_id}")
    print("=" * 80)
    
    test_questions = [
        "Show me a person walking",
        "I need a running character for my game",
        "Display an idle animation",
        "Can you show me a rigged model?",
        "I want to see a human figure standing still",
        "Show me some fast movement animation",
        "I need something for character customization",
        "Show me walking again"  # Test personalization learning
    ]
    
    print("Testing Integrated Model Selector (All AI Layers):")
    print("=" * 80)
    
    for i, question in enumerate(test_questions):
        print(f"\nQuery {i+1}: '{question}'")
        print("-" * 60)
        
        # Get comprehensive analysis
        result = selector.analyze_question_comprehensive(question, session_id)
        
        print(f"Selected Model: {result['selected_model']}")
        print(f"Overall Confidence: {result['confidence']:.3f}")
        print(f"Comprehensive Reasoning: {result['comprehensive_reasoning']}")
        
        # Show layer-by-layer analysis
        print("\nLayer Analysis:")
        intent = result['intent_analysis']
        print(f"  Intent: {intent['style']}/{intent['purpose']}/{intent['motion']} (conf: {intent['confidence']:.2f})")
        
        if result['semantic_analysis']:
            semantic_top = result['semantic_analysis'][0]
            print(f"  Semantic: {semantic_top['model']} (sim: {semantic_top['similarity']:.2f})")
        
        if result['personalization_analysis']:
            personal_top = result['personalization_analysis'][0]
            print(f"  Personal: {personal_top['model']} (score: {personal_top['score']:.2f}, type: {personal_top['type']})")
        
        # Show ambiguities and suggestions
        if intent['ambiguities']:
            print(f"  Ambiguities: {intent['ambiguities']}")
        if intent['suggestions']:
            print(f"  Suggestions: {intent['suggestions'][:2]}")  # First 2 suggestions
        
        print("-" * 60)
    
    # Show session summary
    print(f"\nSession Summary:")
    summary = selector.get_session_summary(session_id)
    print(f"Interactions: {summary['interactions_count']}")
    print(f"Model Usage: {summary['model_usage']}")
    print(f"Session Theme: {summary['session_theme']}")
    
    # Test explanation feature
    print(f"\nDetailed Explanation for Last Query:")
    explanation = selector.explain_recommendation(test_questions[-1], session_id)
    print(f"Final Model: {explanation['final_recommendation']['model']}")
    print(f"Integration Method: {explanation['integration_details']['method']}")
    print(f"All Model Scores: {explanation['integration_details']['all_scores']}")

if __name__ == "__main__":
    test_integrated_selector()