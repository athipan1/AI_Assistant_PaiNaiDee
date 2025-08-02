"""
OpenAI Wrapper Module
Provides integration with OpenAI GPT models for fallback and English language support
"""

import asyncio
import logging
from typing import Optional, Dict, Any, List
import time

logger = logging.getLogger(__name__)

class OpenAILLM:
    """
    OpenAI GPT Integration wrapper
    Provides fallback for OpenThaiGPT when needed
    """
    
    def __init__(
        self,
        api_key: Optional[str] = None,
        model_name: str = "gpt-3.5-turbo",
        max_tokens: int = 512,
        temperature: float = 0.7
    ):
        self.api_key = api_key
        self.model_name = model_name
        self.max_tokens = max_tokens
        self.temperature = temperature
        
        # Fallback responses when OpenAI is not available
        self.fallback_responses = {
            "en": [
                "I'm a Thai tourism assistant. How can I help you explore Thailand?",
                "Welcome to Thailand! I can help you with travel recommendations.",
                "Hello! I'm here to assist with your Thai travel experience."
            ],
            "th": [
                "สวัสดีครับ! ผมเป็นผู้ช่วยท่องเที่ยวไทย จะช่วยอะไรได้บ้างครับ?",
                "ยินดีต้อนรับสู่ประเทศไทย! ผมสามารถช่วยแนะนำการท่องเที่ยวได้ครับ",
                "สวัสดีค่ะ! ดิฉันพร้อมช่วยเหลือเรื่องการเดินทางในประเทศไทย"
            ]
        }
        
        logger.info(f"OpenAI wrapper initialized (fallback mode)")
    
    def _detect_language(self, text: str) -> str:
        """Detect if text is Thai or English"""
        thai_chars = sum(1 for char in text if '\u0e00' <= char <= '\u0e7f')
        return "th" if thai_chars > len(text) * 0.3 else "en"
    
    async def chat(self, message: str, context_type: str = "general") -> str:
        """
        Chat interface with OpenAI (or fallback)
        
        Args:
            message: User input message
            context_type: Type of conversation
            
        Returns:
            Generated response string
        """
        try:
            # For now, return smart fallback responses
            # In production, this would call OpenAI API
            lang = self._detect_language(message)
            responses = self.fallback_responses.get(lang, self.fallback_responses["en"])
            
            # Simple context-aware response selection
            if "hello" in message.lower() or "สวัสดี" in message:
                return responses[0]
            elif "recommend" in message.lower() or "แนะนำ" in message:
                return responses[1]
            else:
                return responses[2]
                
        except Exception as e:
            logger.error(f"Error in OpenAI chat: {str(e)}")
            return "Sorry, I'm having trouble responding right now."
    
    async def chat_with_history(self, messages: List[Dict[str, str]]) -> str:
        """Multi-turn chat with OpenAI"""
        if messages:
            return await self.chat(messages[-1]["content"])
        return await self.chat("Hello")
    
    def get_model_info(self) -> Dict[str, Any]:
        """Get model information"""
        return {
            "model_name": self.model_name,
            "provider": "openai",
            "is_fallback": True,
            "max_tokens": self.max_tokens,
            "temperature": self.temperature
        }

def create_openai_llm(**kwargs) -> OpenAILLM:
    """Create and return OpenAI LLM instance"""
    return OpenAILLM(**kwargs)