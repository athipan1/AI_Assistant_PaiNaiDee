"""
Enhanced Model Selection Agent
Integrates existing 3D model selection with advanced AI capabilities
"""

import logging
from typing import Dict, List, Any, Optional
from agents.advanced_ai_models import ai_manager, ModelCapability, get_ai_manager
from agents.model_selection_agent import integrated_model_selector

logger = logging.getLogger(__name__)

class EnhancedModelSelector:
    """
    Enhanced model selector that combines 3D model selection with advanced AI
    """
    
    def __init__(self):
        self.ai_manager = get_ai_manager()
        self.model_selector = integrated_model_selector
        
    async def analyze_question_with_ai(self, 
                                     question: str, 
                                     session_id: Optional[str] = None,
                                     use_advanced_ai: bool = True,
                                     language: str = "en") -> Dict[str, Any]:
        """
        Enhanced question analysis using both 3D model selection and advanced AI
        """
        
        # Start with existing 3D model selection
        base_result = self.model_selector.analyze_question_comprehensive(question, session_id)
        
        if not use_advanced_ai:
            return base_result
        
        try:
            # Use advanced AI to enhance the analysis
            enhanced_analysis = await self._enhance_with_advanced_ai(question, base_result, language)
            
            # Merge results
            enhanced_result = {
                **base_result,
                "enhanced_analysis": enhanced_analysis,
                "ai_enhancement_used": True
            }
            
            return enhanced_result
            
        except Exception as e:
            logger.warning(f"Advanced AI enhancement failed: {e}")
            # Return base result if advanced AI fails
            base_result["ai_enhancement_used"] = False
            base_result["ai_enhancement_error"] = str(e)
            return base_result
    
    async def _enhance_with_advanced_ai(self, 
                                      question: str, 
                                      base_result: Dict[str, Any],
                                      language: str) -> Dict[str, Any]:
        """Use advanced AI to enhance the model selection analysis"""
        
        # Create context for advanced AI
        context_prompt = f"""
        User Question: {question}
        
        Current 3D Model Selection:
        - Selected Model: {base_result.get('selected_model', 'unknown')}
        - Confidence: {base_result.get('confidence', 0)}
        - Description: {base_result.get('description', '')}
        
        Please provide:
        1. An improved explanation of why this 3D model is suitable
        2. Additional context about tourism applications
        3. Suggestions for how to present this model to the user
        4. Any cultural considerations for Thai tourism context
        
        Respond in a helpful, informative manner.
        """
        
        # Get AI enhancement
        ai_response = await self.ai_manager.generate_response(
            prompt=context_prompt,
            capability=ModelCapability.TOURISM_ADVICE,
            language=language
        )
        
        return {
            "ai_explanation": ai_response.text,
            "model_used": ai_response.model_used,
            "processing_time": ai_response.processing_time,
            "confidence": ai_response.confidence
        }
    
    async def get_tourism_advice(self, 
                               question: str,
                               location: Optional[str] = None,
                               preferences: Optional[Dict[str, Any]] = None,
                               language: str = "en") -> Dict[str, Any]:
        """
        Get tourism advice using advanced AI models
        """
        
        try:
            # Analyze question for 3D model selection first
            model_result = await self.analyze_question_with_ai(question, use_advanced_ai=False)
            
            # Build tourism-specific prompt
            prompt_parts = [
                f"Tourism Question: {question}"
            ]
            
            if location:
                prompt_parts.append(f"Location: {location}")
            
            if preferences:
                pref_text = ", ".join([f"{k}: {v}" for k, v in preferences.items()])
                prompt_parts.append(f"User Preferences: {pref_text}")
            
            # Add 3D model context
            if model_result.get("selected_model"):
                prompt_parts.append(f"Relevant 3D Model: {model_result['selected_model']} - {model_result.get('description', '')}")
            
            prompt_parts.append("""
            Please provide comprehensive tourism advice that:
            1. Answers the user's question thoroughly
            2. Considers Thai cultural context and customs
            3. Provides practical, actionable recommendations
            4. Includes safety and cultural sensitivity tips
            5. Suggests specific activities, places, or experiences
            
            Be helpful, friendly, and culturally aware in your response.
            """)
            
            full_prompt = "\n".join(prompt_parts)
            
            # Get AI response
            ai_response = await self.ai_manager.generate_response(
                prompt=full_prompt,
                capability=ModelCapability.TOURISM_ADVICE,
                language=language
            )
            
            return {
                "advice": ai_response.text,
                "related_3d_model": model_result.get("selected_model"),
                "model_description": model_result.get("description"),
                "ai_model_used": ai_response.model_used,
                "processing_time": ai_response.processing_time,
                "confidence": ai_response.confidence,
                "location_context": location,
                "language": language
            }
            
        except Exception as e:
            logger.error(f"Error in tourism advice: {e}")
            raise
    
    async def conversational_response(self,
                                    message: str,
                                    conversation_history: Optional[List[Dict[str, str]]] = None,
                                    language: str = "en") -> Dict[str, Any]:
        """
        Generate conversational response with potential 3D model recommendations
        """
        
        try:
            # Analyze for 3D model relevance
            model_analysis = await self.analyze_question_with_ai(message, use_advanced_ai=False)
            
            # Build conversation context
            context_parts = []
            
            if conversation_history:
                # Add recent conversation history
                for item in conversation_history[-3:]:  # Last 3 exchanges
                    if item.get("role") == "user":
                        context_parts.append(f"User: {item.get('content', '')}")
                    elif item.get("role") == "assistant":
                        context_parts.append(f"Assistant: {item.get('content', '')}")
            
            # Add current message
            context_parts.append(f"User: {message}")
            
            # Add 3D model context if relevant
            if model_analysis.get("confidence", 0) > 0.5:
                context_parts.append(f"[Available 3D Model: {model_analysis.get('selected_model')} - {model_analysis.get('description', '')}]")
            
            # Add conversation instruction
            context_parts.append("""
            Assistant: Please provide a helpful, natural response that:
            1. Addresses the user's message directly
            2. Maintains a friendly, conversational tone
            3. Provides useful information if needed
            4. Suggests the 3D model if it's relevant to the conversation
            5. Considers Thai cultural context if discussing tourism
            
            Keep the response natural and engaging.
            """)
            
            full_prompt = "\n".join(context_parts)
            
            # Generate conversational response
            ai_response = await self.ai_manager.generate_response(
                prompt=full_prompt,
                capability=ModelCapability.CONVERSATION,
                language=language
            )
            
            return {
                "response": ai_response.text,
                "suggested_3d_model": model_analysis.get("selected_model") if model_analysis.get("confidence", 0) > 0.5 else None,
                "model_description": model_analysis.get("description") if model_analysis.get("confidence", 0) > 0.5 else None,
                "ai_model_used": ai_response.model_used,
                "processing_time": ai_response.processing_time,
                "confidence": ai_response.confidence,
                "language": language
            }
            
        except Exception as e:
            logger.error(f"Error in conversational response: {e}")
            raise
    
    async def get_available_ai_models(self) -> Dict[str, Any]:
        """Get information about available AI models"""
        
        try:
            advanced_models = self.ai_manager.get_available_models()
            threed_models = self.model_selector.list_available_models()
            
            return {
                "advanced_ai_models": advanced_models,
                "threed_models": threed_models,
                "total_advanced_models": len(advanced_models),
                "total_3d_models": len(threed_models),
                "available_advanced_models": sum(1 for m in advanced_models if m.get("available", False)),
                "capabilities": [cap.value for cap in ModelCapability]
            }
            
        except Exception as e:
            logger.error(f"Error getting available models: {e}")
            raise

# Global enhanced selector instance
enhanced_selector = EnhancedModelSelector()

def get_enhanced_selector() -> EnhancedModelSelector:
    """Get the global enhanced selector instance"""
    return enhanced_selector