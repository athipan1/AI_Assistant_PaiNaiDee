"""
AI Orchestrator Module
Intelligent coordination and routing system for PaiNaiDee AI Assistant
Routes user queries to appropriate AI modules based on intent and language
"""

import asyncio
import logging
from typing import Optional, Dict, Any, List, Tuple
from enum import Enum
import re
import time
from dataclasses import dataclass

# Import AI modules
from ai.llms.openthaigpt_integration import OpenThaiGPTLLM, create_openthaigpt_llm
from ai.llms.openai_wrapper import OpenAILLM, create_openai_llm

# Import existing agents
try:
    from agents.emotion_analysis import EmotionAnalysisAgent
    from agents.greeting_agent import GreetingAgent
    from agents.search_agent import SearchAgent
    AGENTS_AVAILABLE = True
except ImportError as e:
    logging.warning(f"Could not import agents: {e}")
    AGENTS_AVAILABLE = False

logger = logging.getLogger(__name__)

class IntentType(Enum):
    """Types of user intents"""
    GREETING = "greeting"
    QUESTION = "question"
    RECOMMENDATION = "recommendation"
    EMOTION = "emotion"
    SEARCH = "search"
    CHAT = "chat"
    UNKNOWN = "unknown"

class LanguageType(Enum):
    """Supported languages"""
    THAI = "th"
    ENGLISH = "en"
    AUTO = "auto"

@dataclass
class AIResponse:
    """Standardized response from AI modules"""
    content: str
    intent_type: IntentType
    language: LanguageType
    model_used: str
    confidence: float
    response_time: float
    metadata: Optional[Dict[str, Any]] = None

class IntentClassifier:
    """Classify user intents from input text"""
    
    def __init__(self):
        # Thai intent patterns
        self.thai_patterns = {
            IntentType.GREETING: [
                r'สวัสดี', r'หวัดดี', r'ดีครับ', r'ดีค่ะ', r'ยินดีที่ได้รู้จัก',
                r'hello.*thai', r'hi.*thai'
            ],
            IntentType.RECOMMENDATION: [
                r'แนะนำ', r'ช่วยแนะนำ', r'อยากไป', r'ที่ไหนดี', r'ทริป',
                r'สถานที่', r'ท่องเที่ยว', r'recommend', r'suggest'
            ],
            IntentType.EMOTION: [
                r'รู้สึก', r'อารมณ์', r'เศร้า', r'ดีใจ', r'เสียใจ', r'กังวล',
                r'excited', r'happy', r'sad', r'worried'
            ],
            IntentType.SEARCH: [
                r'ค้นหา', r'หา', r'ข้อมูล', r'รายละเอียด', r'search', r'find',
                r'what.*about', r'tell.*about'
            ],
            IntentType.QUESTION: [
                r'อะไร', r'ยังไง', r'ทำไม', r'เมื่อไหร่', r'ที่ไหน', r'ใคร',
                r'what', r'how', r'why', r'when', r'where', r'who', r'\?'
            ]
        }
        
        # English intent patterns
        self.english_patterns = {
            IntentType.GREETING: [
                r'\bhello\b', r'\bhi\b', r'\bhey\b', r'good morning', r'good afternoon',
                r'nice to meet', r'pleased to meet'
            ],
            IntentType.RECOMMENDATION: [
                r'recommend', r'suggest', r'advise', r'best place', r'where to go',
                r'trip', r'travel', r'visit', r'tour'
            ],
            IntentType.EMOTION: [
                r'feel', r'emotion', r'mood', r'happy', r'sad', r'excited',
                r'worried', r'anxious', r'depressed'
            ],
            IntentType.SEARCH: [
                r'search', r'find', r'look for', r'information about', r'details about',
                r'tell me about', r'what.*about'
            ],
            IntentType.QUESTION: [
                r'what', r'how', r'why', r'when', r'where', r'who', r'which',
                r'\?', r'can you', r'could you', r'would you'
            ]
        }
    
    def classify_intent(self, text: str, language: LanguageType = LanguageType.AUTO) -> Tuple[IntentType, float]:
        """
        Classify the intent of user input
        
        Args:
            text: User input text
            language: Language hint
            
        Returns:
            Tuple of (intent_type, confidence_score)
        """
        text_lower = text.lower()
        
        # Detect language if auto
        if language == LanguageType.AUTO:
            language = self._detect_language(text)
        
        # Choose appropriate patterns
        patterns = self.thai_patterns if language == LanguageType.THAI else self.english_patterns
        
        # Score each intent type
        intent_scores = {}
        for intent_type, pattern_list in patterns.items():
            score = 0
            for pattern in pattern_list:
                matches = len(re.findall(pattern, text_lower))
                score += matches
            
            if score > 0:
                intent_scores[intent_type] = score / len(text.split())  # Normalize by text length
        
        # Return highest scoring intent or UNKNOWN
        if intent_scores:
            best_intent = max(intent_scores.items(), key=lambda x: x[1])
            return best_intent[0], min(best_intent[1], 1.0)  # Cap confidence at 1.0
        
        return IntentType.UNKNOWN, 0.0
    
    def _detect_language(self, text: str) -> LanguageType:
        """Detect if text is Thai or English"""
        thai_chars = sum(1 for char in text if '\u0e00' <= char <= '\u0e7f')
        return LanguageType.THAI if thai_chars > len(text) * 0.3 else LanguageType.ENGLISH

class AIOrchestrator:
    """
    Main AI Orchestrator class
    Coordinates between different AI modules and agents
    """
    
    def __init__(
        self,
        enable_thai_llm: bool = True,
        enable_openai_fallback: bool = True,
        default_language: LanguageType = LanguageType.AUTO
    ):
        self.enable_thai_llm = enable_thai_llm
        self.enable_openai_fallback = enable_openai_fallback
        self.default_language = default_language
        
        # Initialize components
        self.intent_classifier = IntentClassifier()
        
        # LLM instances (lazy loaded)
        self.thai_llm: Optional[OpenThaiGPTLLM] = None
        self.openai_llm: Optional[OpenAILLM] = None
        
        # Existing agents (lazy loaded)
        self.emotion_agent = None
        self.greeting_agent = None
        self.search_agent = None
        
        logger.info(f"AI Orchestrator initialized (Thai LLM: {enable_thai_llm}, OpenAI fallback: {enable_openai_fallback})")
    
    def _get_thai_llm(self) -> OpenThaiGPTLLM:
        """Get or create Thai LLM instance"""
        if self.thai_llm is None:
            self.thai_llm = create_openthaigpt_llm(
                enable_fallback=self.enable_openai_fallback
            )
        return self.thai_llm
    
    def _get_openai_llm(self) -> OpenAILLM:
        """Get or create OpenAI LLM instance"""
        if self.openai_llm is None:
            self.openai_llm = create_openai_llm()
        return self.openai_llm
    
    def _get_emotion_agent(self):
        """Get or create emotion analysis agent"""
        if self.emotion_agent is None and AGENTS_AVAILABLE:
            try:
                from agents.emotion_analysis import EmotionAnalysisAgent
                self.emotion_agent = EmotionAnalysisAgent()
            except Exception as e:
                logger.warning(f"Could not load emotion agent: {e}")
        return self.emotion_agent
    
    def _get_greeting_agent(self):
        """Get or create greeting agent"""
        if self.greeting_agent is None and AGENTS_AVAILABLE:
            try:
                from agents.greeting_agent import GreetingAgent
                self.greeting_agent = GreetingAgent()
            except Exception as e:
                logger.warning(f"Could not load greeting agent: {e}")
        return self.greeting_agent
    
    def _get_search_agent(self):
        """Get or create search agent"""
        if self.search_agent is None and AGENTS_AVAILABLE:
            try:
                from agents.search_agent import SearchAgent
                self.search_agent = SearchAgent()
            except Exception as e:
                logger.warning(f"Could not load search agent: {e}")
        return self.search_agent
    
    async def handle_input(
        self,
        user_input: str,
        lang: str = "auto",
        source: str = "web",
        context: Optional[Dict[str, Any]] = None
    ) -> AIResponse:
        """
        Main entry point for handling user input
        
        Args:
            user_input: User's message/query
            lang: Language preference ("th", "en", "auto")
            source: Source of the request (e.g., "3D-assistant", "web", "mobile")
            context: Additional context information
            
        Returns:
            AIResponse with generated content and metadata
        """
        start_time = time.time()
        
        try:
            # Convert language string to enum
            language = LanguageType.THAI if lang == "th" else LanguageType.ENGLISH if lang == "en" else LanguageType.AUTO
            
            # Classify user intent
            intent_type, confidence = self.intent_classifier.classify_intent(user_input, language)
            
            # Detect actual language if auto
            if language == LanguageType.AUTO:
                language = self.intent_classifier._detect_language(user_input)
            
            logger.info(f"Intent: {intent_type.value}, Language: {language.value}, Confidence: {confidence:.2f}")
            
            # Route to appropriate handler
            response_content = await self._route_to_handler(
                user_input, intent_type, language, context or {}
            )
            
            # Determine which model was used
            model_used = self._get_model_used(intent_type, language)
            
            response_time = time.time() - start_time
            
            return AIResponse(
                content=response_content,
                intent_type=intent_type,
                language=language,
                model_used=model_used,
                confidence=confidence,
                response_time=response_time,
                metadata={
                    "source": source,
                    "context": context,
                    "processing_time": response_time
                }
            )
            
        except Exception as e:
            logger.error(f"Error in handle_input: {str(e)}")
            response_time = time.time() - start_time
            
            # Return fallback response
            fallback_content = self._get_fallback_response(lang)
            
            return AIResponse(
                content=fallback_content,
                intent_type=IntentType.UNKNOWN,
                language=LanguageType.THAI if lang == "th" else LanguageType.ENGLISH,
                model_used="fallback",
                confidence=0.0,
                response_time=response_time,
                metadata={"error": str(e)}
            )
    
    async def _route_to_handler(
        self,
        user_input: str,
        intent_type: IntentType,
        language: LanguageType,
        context: Dict[str, Any]
    ) -> str:
        """Route user input to appropriate handler based on intent"""
        
        try:
            if intent_type == IntentType.GREETING:
                return await self._handle_greeting(user_input, language, context)
            
            elif intent_type == IntentType.EMOTION:
                return await self._handle_emotion(user_input, language, context)
            
            elif intent_type == IntentType.SEARCH:
                return await self._handle_search(user_input, language, context)
            
            elif intent_type == IntentType.RECOMMENDATION:
                return await self._handle_recommendation(user_input, language, context)
            
            elif intent_type == IntentType.QUESTION or intent_type == IntentType.CHAT:
                return await self._handle_question(user_input, language, context)
            
            else:  # UNKNOWN
                return await self._handle_general_chat(user_input, language, context)
                
        except Exception as e:
            logger.error(f"Error in routing: {str(e)}")
            return await self._handle_general_chat(user_input, language, context)
    
    async def _handle_greeting(self, user_input: str, language: LanguageType, context: Dict) -> str:
        """Handle greeting intents"""
        greeting_agent = self._get_greeting_agent()
        if greeting_agent:
            try:
                lang_str = "th" if language == LanguageType.THAI else "en"
                return await greeting_agent.generate_greeting(language=lang_str)
            except Exception as e:
                logger.warning(f"Greeting agent failed: {e}")
        
        # Fallback to LLM
        return await self._handle_with_llm(user_input, language, "greeting")
    
    async def _handle_emotion(self, user_input: str, language: LanguageType, context: Dict) -> str:
        """Handle emotion analysis intents"""
        emotion_agent = self._get_emotion_agent()
        if emotion_agent:
            try:
                # Use existing emotion analysis
                analysis = await emotion_agent.analyze_emotion_and_generate_response(user_input)
                return analysis.get("response", "")
            except Exception as e:
                logger.warning(f"Emotion agent failed: {e}")
        
        # Fallback to LLM with emotion context
        return await self._handle_with_llm(user_input, language, "emotion")
    
    async def _handle_search(self, user_input: str, language: LanguageType, context: Dict) -> str:
        """Handle search intents"""
        search_agent = self._get_search_agent()
        if search_agent:
            try:
                lang_str = "th" if language == LanguageType.THAI else "en"
                
                # Extract place name from input (simple approach)
                place_name = self._extract_place_name(user_input)
                if place_name:
                    search_result = await search_agent.search_place_info(place_name, lang_str)
                    return search_result.get("description", "")
            except Exception as e:
                logger.warning(f"Search agent failed: {e}")
        
        # Fallback to LLM
        return await self._handle_with_llm(user_input, language, "search")
    
    async def _handle_recommendation(self, user_input: str, language: LanguageType, context: Dict) -> str:
        """Handle recommendation intents"""
        # For recommendations, we can use existing trip recommendation logic
        # For now, use LLM with recommendation context
        return await self._handle_with_llm(user_input, language, "recommendation")
    
    async def _handle_question(self, user_input: str, language: LanguageType, context: Dict) -> str:
        """Handle question intents"""
        return await self._handle_with_llm(user_input, language, "question")
    
    async def _handle_general_chat(self, user_input: str, language: LanguageType, context: Dict) -> str:
        """Handle general chat intents"""
        return await self._handle_with_llm(user_input, language, "general")
    
    async def _handle_with_llm(self, user_input: str, language: LanguageType, context_type: str) -> str:
        """Handle input using appropriate LLM"""
        try:
            # Choose LLM based on language and availability
            if language == LanguageType.THAI and self.enable_thai_llm:
                llm = self._get_thai_llm()
                return await llm.chat(user_input, context_type)
            else:
                # Use OpenAI or fallback
                llm = self._get_openai_llm()
                return await llm.chat(user_input, context_type)
                
        except Exception as e:
            logger.error(f"LLM handling failed: {e}")
            return self._get_fallback_response("th" if language == LanguageType.THAI else "en")
    
    def _extract_place_name(self, text: str) -> Optional[str]:
        """Simple extraction of place names from text"""
        # This is a simplified approach - in production you'd use NER
        common_places = ["bangkok", "chiang mai", "phuket", "pattaya", "krabi", "กรุงเทพ", "เชียงใหม่", "ภูเก็ต"]
        text_lower = text.lower()
        
        for place in common_places:
            if place in text_lower:
                return place
        
        # If no known place found, return the whole input for search
        return text
    
    def _get_model_used(self, intent_type: IntentType, language: LanguageType) -> str:
        """Determine which model was used for response"""
        if intent_type == IntentType.GREETING and AGENTS_AVAILABLE:
            return "greeting_agent"
        elif intent_type == IntentType.EMOTION and AGENTS_AVAILABLE:
            return "emotion_agent"
        elif intent_type == IntentType.SEARCH and AGENTS_AVAILABLE:
            return "search_agent"
        elif language == LanguageType.THAI and self.enable_thai_llm:
            return "openthaigpt"
        else:
            return "openai_fallback"
    
    def _get_fallback_response(self, lang: str) -> str:
        """Get fallback response when all else fails"""
        if lang == "th":
            return "ขออภัย ไม่สามารถประมวลผลคำขอของคุณได้ในขณะนี้ กรุณาลองใหม่อีกครั้งครับ"
        else:
            return "Sorry, I'm unable to process your request at the moment. Please try again."
    
    def get_status(self) -> Dict[str, Any]:
        """Get orchestrator status and component information"""
        return {
            "thai_llm_enabled": self.enable_thai_llm,
            "openai_fallback_enabled": self.enable_openai_fallback,
            "agents_available": AGENTS_AVAILABLE,
            "components": {
                "thai_llm": self.thai_llm.get_model_info() if self.thai_llm else None,
                "openai_llm": self.openai_llm.get_model_info() if self.openai_llm else None,
                "emotion_agent": self.emotion_agent is not None,
                "greeting_agent": self.greeting_agent is not None,
                "search_agent": self.search_agent is not None
            }
        }

# Factory function for easy instantiation
def create_ai_orchestrator(**kwargs) -> AIOrchestrator:
    """Create and return AI Orchestrator instance"""
    return AIOrchestrator(**kwargs)

# Singleton instance for global access
_orchestrator_instance: Optional[AIOrchestrator] = None

def get_ai_orchestrator() -> AIOrchestrator:
    """Get or create global orchestrator instance"""
    global _orchestrator_instance
    if _orchestrator_instance is None:
        _orchestrator_instance = create_ai_orchestrator()
    return _orchestrator_instance