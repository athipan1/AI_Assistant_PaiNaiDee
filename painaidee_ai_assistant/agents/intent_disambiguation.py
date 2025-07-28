"""
Intent Disambiguation Engine for 3D Model Selection
Resolves ambiguous user input and classifies intent using offline NLP techniques
"""

import re
import json
from typing import Dict, List, Any, Optional, Tuple
from dataclasses import dataclass
from enum import Enum
import logging

logger = logging.getLogger(__name__)

class ModelStyle(Enum):
    """Model style classifications"""
    REALISTIC = "realistic"
    STYLIZED = "stylized"
    NEUTRAL = "neutral"

class ModelPurpose(Enum):
    """Model purpose classifications"""
    ANIMATION = "animation"
    STATIC = "static"
    RIGGED = "rigged"
    DISPLAY = "display"

class ModelMotion(Enum):
    """Model motion classifications"""
    IDLE = "idle"
    WALKING = "walking"
    RUNNING = "running"
    CUSTOM = "custom"
    NONE = "none"

@dataclass
class Intent:
    """Structured intent representation"""
    style: ModelStyle
    purpose: ModelPurpose
    motion: ModelMotion
    confidence: float
    reasoning: str
    ambiguities: List[str]
    suggestions: List[str]

class IntentDisambiguationEngine:
    """
    Advanced intent classification engine that resolves ambiguous queries
    and provides structured intent information for model selection
    """
    
    def __init__(self):
        self.style_patterns = {
            ModelStyle.REALISTIC: {
                "keywords": ["realistic", "real", "lifelike", "photorealistic", "human-like", "natural"],
                "weight": 1.0
            },
            ModelStyle.STYLIZED: {
                "keywords": ["stylized", "cartoon", "anime", "artistic", "abstract", "simplified"],
                "weight": 1.0
            },
            ModelStyle.NEUTRAL: {
                "keywords": ["basic", "simple", "standard", "default", "generic"],
                "weight": 0.7
            }
        }
        
        self.purpose_patterns = {
            ModelPurpose.ANIMATION: {
                "keywords": ["animation", "animate", "animated", "move", "movement", "motion"],
                "weight": 1.0
            },
            ModelPurpose.STATIC: {
                "keywords": ["static", "still", "pose", "standing", "display", "show"],
                "weight": 0.8
            },
            ModelPurpose.RIGGED: {
                "keywords": ["rig", "rigged", "skeleton", "bones", "custom", "customize"],
                "weight": 1.0
            },
            ModelPurpose.DISPLAY: {
                "keywords": ["display", "view", "look", "see", "present", "demo"],
                "weight": 0.6
            }
        }
        
        self.motion_patterns = {
            ModelMotion.IDLE: {
                "keywords": ["idle", "standing", "still", "waiting", "neutral", "rest"],
                "weight": 1.0
            },
            ModelMotion.WALKING: {
                "keywords": ["walk", "walking", "step", "stroll", "move", "moving"],
                "weight": 1.0
            },
            ModelMotion.RUNNING: {
                "keywords": ["run", "running", "fast", "sprint", "jog", "jogging"],
                "weight": 1.0
            },
            ModelMotion.CUSTOM: {
                "keywords": ["custom", "specific", "particular", "special"],
                "weight": 0.8
            },
            ModelMotion.NONE: {
                "keywords": ["none", "no motion", "static"],
                "weight": 0.5
            }
        }
        
        # Context clues for disambiguation
        self.context_clues = {
            "game_development": ["game", "gaming", "unity", "unreal", "development"],
            "visualization": ["visualize", "visualization", "render", "presentation"],
            "education": ["education", "teaching", "learning", "tutorial"],
            "animation": ["animation", "film", "movie", "video"],
            "character_design": ["character", "design", "concept", "prototype"]
        }
        
        # Common ambiguous phrases and their resolutions
        self.ambiguity_patterns = {
            "person": {
                "clarifications": ["Do you want a realistic or stylized person?", 
                                 "Should the person be animated or static?"],
                "default_intent": {
                    "style": ModelStyle.NEUTRAL,
                    "purpose": ModelPurpose.DISPLAY,
                    "motion": ModelMotion.IDLE
                }
            },
            "character": {
                "clarifications": ["What style of character do you prefer?",
                                 "Do you need the character to be animated?"],
                "default_intent": {
                    "style": ModelStyle.NEUTRAL,
                    "purpose": ModelPurpose.DISPLAY,
                    "motion": ModelMotion.IDLE
                }
            },
            "model": {
                "clarifications": ["What type of model are you looking for?",
                                 "Do you need animation capabilities?"],
                "default_intent": {
                    "style": ModelStyle.NEUTRAL,
                    "purpose": ModelPurpose.DISPLAY,
                    "motion": ModelMotion.NONE
                }
            },
            "show": {
                "clarifications": ["What would you like to see?",
                                 "What type of model interests you?"],
                "default_intent": {
                    "style": ModelStyle.NEUTRAL,
                    "purpose": ModelPurpose.DISPLAY,
                    "motion": ModelMotion.IDLE
                }
            }
        }
    
    def classify_intent(self, query: str, context: Optional[Dict[str, Any]] = None) -> Intent:
        """
        Main entry point for intent classification
        
        Args:
            query: User input query
            context: Optional context information (session data, user preferences, etc.)
            
        Returns:
            Intent: Structured intent classification
        """
        query_lower = query.lower().strip()
        
        # Detect ambiguities first
        ambiguities = self._detect_ambiguities(query_lower)
        
        # Classify each dimension
        style_result = self._classify_style(query_lower, context)
        purpose_result = self._classify_purpose(query_lower, context)
        motion_result = self._classify_motion(query_lower, context)
        
        # Calculate overall confidence
        confidence = self._calculate_confidence(style_result, purpose_result, motion_result, ambiguities)
        
        # Generate reasoning
        reasoning = self._generate_reasoning(query, style_result, purpose_result, motion_result)
        
        # Generate suggestions for ambiguous cases
        suggestions = self._generate_suggestions(query_lower, ambiguities, confidence)
        
        return Intent(
            style=style_result["classification"],
            purpose=purpose_result["classification"],
            motion=motion_result["classification"],
            confidence=confidence,
            reasoning=reasoning,
            ambiguities=ambiguities,
            suggestions=suggestions
        )
    
    def _classify_style(self, query: str, context: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
        """Classify model style preference"""
        scores = {}
        
        for style, pattern in self.style_patterns.items():
            score = 0
            matched_keywords = []
            
            for keyword in pattern["keywords"]:
                if keyword in query:
                    score += pattern["weight"]
                    matched_keywords.append(keyword)
            
            if score > 0:
                scores[style] = {
                    "score": score,
                    "keywords": matched_keywords
                }
        
        # Default to neutral if no specific style mentioned
        if not scores:
            return {
                "classification": ModelStyle.NEUTRAL,
                "confidence": 0.3,
                "matched_keywords": []
            }
        
        best_style = max(scores, key=lambda k: scores[k]["score"])
        return {
            "classification": best_style,
            "confidence": min(scores[best_style]["score"] / len(query.split()), 1.0),
            "matched_keywords": scores[best_style]["keywords"]
        }
    
    def _classify_purpose(self, query: str, context: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
        """Classify model purpose"""
        scores = {}
        
        for purpose, pattern in self.purpose_patterns.items():
            score = 0
            matched_keywords = []
            
            for keyword in pattern["keywords"]:
                if keyword in query:
                    score += pattern["weight"]
                    matched_keywords.append(keyword)
            
            if score > 0:
                scores[purpose] = {
                    "score": score,
                    "keywords": matched_keywords
                }
        
        # Default to display if no specific purpose mentioned
        if not scores:
            return {
                "classification": ModelPurpose.DISPLAY,
                "confidence": 0.4,
                "matched_keywords": []
            }
        
        best_purpose = max(scores, key=lambda k: scores[k]["score"])
        return {
            "classification": best_purpose,
            "confidence": min(scores[best_purpose]["score"] / len(query.split()), 1.0),
            "matched_keywords": scores[best_purpose]["keywords"]
        }
    
    def _classify_motion(self, query: str, context: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
        """Classify motion requirement"""
        scores = {}
        
        for motion, pattern in self.motion_patterns.items():
            score = 0
            matched_keywords = []
            
            for keyword in pattern["keywords"]:
                if keyword in query:
                    score += pattern["weight"]
                    matched_keywords.append(keyword)
            
            if score > 0:
                scores[motion] = {
                    "score": score,
                    "keywords": matched_keywords
                }
        
        # Default to idle if no specific motion mentioned
        if not scores:
            return {
                "classification": ModelMotion.IDLE,
                "confidence": 0.3,
                "matched_keywords": []
            }
        
        best_motion = max(scores, key=lambda k: scores[k]["score"])
        return {
            "classification": best_motion,
            "confidence": min(scores[best_motion]["score"] / len(query.split()), 1.0),
            "matched_keywords": scores[best_motion]["keywords"]
        }
    
    def _detect_ambiguities(self, query: str) -> List[str]:
        """Detect ambiguous terms in the query"""
        ambiguities = []
        
        for ambiguous_term, info in self.ambiguity_patterns.items():
            if ambiguous_term in query:
                # Check if there are enough context clues to resolve the ambiguity
                has_context = False
                context_count = 0
                
                for pattern_list in [self.style_patterns, self.purpose_patterns, self.motion_patterns]:
                    for pattern_info in pattern_list.values():
                        for keyword in pattern_info["keywords"]:
                            if keyword in query and keyword != ambiguous_term:
                                context_count += 1
                                has_context = True
                
                # Only consider it ambiguous if there are very few context clues
                if context_count < 2:
                    ambiguities.append(ambiguous_term)
        
        return ambiguities
    
    def _calculate_confidence(self, style_result: Dict, purpose_result: Dict, 
                            motion_result: Dict, ambiguities: List[str]) -> float:
        """Calculate overall confidence score"""
        # Base confidence from individual classifications
        base_confidence = (
            style_result["confidence"] + 
            purpose_result["confidence"] + 
            motion_result["confidence"]
        ) / 3
        
        # Reduce confidence for ambiguities
        ambiguity_penalty = len(ambiguities) * 0.15
        
        # Boost confidence if multiple dimensions are well-defined
        well_defined_count = sum(1 for result in [style_result, purpose_result, motion_result] 
                               if result["confidence"] > 0.7)
        confidence_boost = well_defined_count * 0.1
        
        final_confidence = max(0.1, min(1.0, base_confidence - ambiguity_penalty + confidence_boost))
        return final_confidence
    
    def _generate_reasoning(self, original_query: str, style_result: Dict, 
                          purpose_result: Dict, motion_result: Dict) -> str:
        """Generate human-readable reasoning for the classification"""
        reasoning_parts = []
        
        if style_result["matched_keywords"]:
            reasoning_parts.append(f"Style: {style_result['classification'].value} (matched: {', '.join(style_result['matched_keywords'])})")
        
        if purpose_result["matched_keywords"]:
            reasoning_parts.append(f"Purpose: {purpose_result['classification'].value} (matched: {', '.join(purpose_result['matched_keywords'])})")
        
        if motion_result["matched_keywords"]:
            reasoning_parts.append(f"Motion: {motion_result['classification'].value} (matched: {', '.join(motion_result['matched_keywords'])})")
        
        if not reasoning_parts:
            return f"Used default classifications for query: '{original_query}'"
        
        return "; ".join(reasoning_parts)
    
    def _generate_suggestions(self, query: str, ambiguities: List[str], confidence: float) -> List[str]:
        """Generate suggestions for disambiguation"""
        suggestions = []
        
        # Add clarification questions for ambiguous terms
        for ambiguity in ambiguities:
            if ambiguity in self.ambiguity_patterns:
                suggestions.extend(self.ambiguity_patterns[ambiguity]["clarifications"])
        
        # Add general suggestions for low confidence
        if confidence < 0.5:
            suggestions.extend([
                "Try being more specific about the style (realistic/stylized)",
                "Specify if you need animation or static display",
                "Mention the intended use case (game, visualization, etc.)"
            ])
        
        return suggestions
    
    def resolve_ambiguity(self, original_intent: Intent, clarification: str) -> Intent:
        """
        Resolve ambiguity with additional user clarification
        
        Args:
            original_intent: The original ambiguous intent
            clarification: Additional user input to resolve ambiguity
            
        Returns:
            Intent: Updated intent with resolved ambiguity
        """
        # Combine original query context with clarification
        combined_query = f"{clarification}"
        
        # Re-classify with the additional information
        new_intent = self.classify_intent(combined_query)
        
        # Merge with original intent, giving priority to new information
        merged_intent = Intent(
            style=new_intent.style if new_intent.confidence > 0.5 else original_intent.style,
            purpose=new_intent.purpose if new_intent.confidence > 0.5 else original_intent.purpose,
            motion=new_intent.motion if new_intent.confidence > 0.5 else original_intent.motion,
            confidence=max(original_intent.confidence, new_intent.confidence),
            reasoning=f"Original: {original_intent.reasoning}; Clarified: {new_intent.reasoning}",
            ambiguities=[],  # Resolved
            suggestions=[]
        )
        
        return merged_intent

# Global instance
intent_engine = IntentDisambiguationEngine()

def test_intent_disambiguation():
    """Test the intent disambiguation engine"""
    engine = IntentDisambiguationEngine()
    
    test_queries = [
        "Show me a person",
        "I need a realistic walking character",
        "Display a stylized animation",
        "Can you show me a rigged model for my game?",
        "I want to see someone running",
        "Show me an idle pose",
        "I need a character for visualization",
        "Display a basic human figure",
        "Show me something animated",
        "I want a model"
    ]
    
    print("Testing Intent Disambiguation Engine:")
    print("=" * 60)
    
    for query in test_queries:
        intent = engine.classify_intent(query)
        print(f"Query: '{query}'")
        print(f"Style: {intent.style.value}")
        print(f"Purpose: {intent.purpose.value}")
        print(f"Motion: {intent.motion.value}")
        print(f"Confidence: {intent.confidence:.2f}")
        print(f"Reasoning: {intent.reasoning}")
        if intent.ambiguities:
            print(f"Ambiguities: {intent.ambiguities}")
        if intent.suggestions:
            print(f"Suggestions: {intent.suggestions}")
        print("-" * 40)

if __name__ == "__main__":
    test_intent_disambiguation()