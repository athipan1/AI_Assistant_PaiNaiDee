"""
Emotion Analysis Module Wrapper
Provides standardized interface to existing emotion analysis agent
"""

import logging
from typing import Dict, Any, Optional
import asyncio

logger = logging.getLogger(__name__)

class EmotionModule:
    """
    Wrapper for existing emotion analysis functionality
    """
    
    def __init__(self):
        self.agent = None
        self._load_agent()
    
    def _load_agent(self):
        """Load the existing emotion analysis agent"""
        try:
            from agents.emotion_analysis import EmotionAnalysisAgent
            self.agent = EmotionAnalysisAgent()
            logger.info("Emotion analysis agent loaded successfully")
        except Exception as e:
            logger.warning(f"Could not load emotion analysis agent: {e}")
            self.agent = None
    
    async def analyze(self, text: str, language: str = "auto") -> Dict[str, Any]:
        """
        Analyze emotion in text
        
        Args:
            text: Input text to analyze
            language: Language hint ("th", "en", "auto")
            
        Returns:
            Dictionary with emotion analysis results
        """
        if self.agent is None:
            return self._fallback_analysis(text, language)
        
        try:
            # Use existing emotion analysis agent
            result = await self.agent.analyze_emotion_and_generate_response(text)
            
            # Standardize the response format
            return {
                "emotion": result.get("emotion", "neutral"),
                "confidence": result.get("confidence", 0.5),
                "response": result.get("response", ""),
                "gesture": result.get("gesture", "neutral_idle"),
                "language": language,
                "status": "success"
            }
            
        except Exception as e:
            logger.error(f"Error in emotion analysis: {str(e)}")
            return self._fallback_analysis(text, language)
    
    def _fallback_analysis(self, text: str, language: str) -> Dict[str, Any]:
        """Provide fallback emotion analysis"""
        # Simple keyword-based emotion detection
        text_lower = text.lower()
        
        if any(word in text_lower for word in ["happy", "joy", "excited", "ดีใจ", "มีความสุข"]):
            emotion = "happy"
            gesture = "excited_jump"
        elif any(word in text_lower for word in ["sad", "sorry", "เศร้า", "เสียใจ"]):
            emotion = "sad"
            gesture = "reassuring_gesture"
        elif any(word in text_lower for word in ["angry", "mad", "โกรธ", "หงุดหงิด"]):
            emotion = "frustrated"
            gesture = "calm_standing"
        elif any(word in text_lower for word in ["worried", "anxious", "กังวล", "เป็นห่วง"]):
            emotion = "worried"
            gesture = "thoughtful_pose"
        else:
            emotion = "neutral"
            gesture = "neutral_idle"
        
        response = self._generate_emotion_response(emotion, language)
        
        return {
            "emotion": emotion,
            "confidence": 0.6,  # Moderate confidence for fallback
            "response": response,
            "gesture": gesture,
            "language": language,
            "status": "fallback"
        }
    
    def _generate_emotion_response(self, emotion: str, language: str) -> str:
        """Generate appropriate response based on detected emotion"""
        responses = {
            "th": {
                "happy": "ดีใจที่เห็นคุณมีความสุขนะครับ! มีอะไรให้ช่วยเหลือไหมครับ?",
                "sad": "เข้าใจความรู้สึกของคุณครับ หวังว่าจะดีขึ้นนะครับ",
                "frustrated": "ขออภัยที่ทำให้คุณรู้สึกหงุดหงิดนะครับ ผมจะพยายามช่วยให้ดีที่สุด",
                "worried": "ไม่ต้องกังวลมากนะครับ ผมพร้อมช่วยเหลือคุณครับ",
                "neutral": "มีอะไรให้ช่วยเหลือไหมครับ?"
            },
            "en": {
                "happy": "I'm glad to see you're happy! How can I help you today?",
                "sad": "I understand how you're feeling. I hope things get better for you.",
                "frustrated": "I'm sorry you're feeling frustrated. I'll do my best to help.",
                "worried": "Don't worry too much. I'm here to help you.",
                "neutral": "How can I assist you today?"
            }
        }
        
        lang_responses = responses.get(language, responses["en"])
        return lang_responses.get(emotion, lang_responses["neutral"])

def create_emotion_module() -> EmotionModule:
    """Create and return emotion module instance"""
    return EmotionModule()