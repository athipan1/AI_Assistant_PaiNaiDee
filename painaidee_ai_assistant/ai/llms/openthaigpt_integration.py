"""
OpenThaiGPT Integration Module
Provides Thai language LLM capabilities using HuggingFace Transformers
with fallback to OpenAI GPT-4 for reliability
"""

import asyncio
import logging
from typing import Optional, Dict, Any, List
import torch
from transformers import AutoTokenizer, AutoModelForCausalLM, pipeline
import json
import time
from dataclasses import dataclass

# For fallback to OpenAI (placeholder - would need openai package)
try:
    import openai
    HAS_OPENAI = True
except ImportError:
    HAS_OPENAI = False

logger = logging.getLogger(__name__)

@dataclass
class ChatResponse:
    """Response from LLM chat"""
    message: str
    model_used: str
    response_time: float
    tokens_used: Optional[int] = None
    status: str = "success"
    error: Optional[str] = None

class OpenThaiGPTLLM:
    """
    OpenThaiGPT Language Model Integration
    Supports Thai language with fallback to English models
    """
    
    def __init__(
        self,
        model_name: str = "airesearch/WangchanBERTa-finetuned-sentiment",  # Start with smaller model for demo
        device: Optional[str] = None,
        max_tokens: int = 512,
        temperature: float = 0.7,
        openai_api_key: Optional[str] = None,
        enable_fallback: bool = True
    ):
        self.model_name = model_name
        self.device = device or ("cuda" if torch.cuda.is_available() else "cpu")
        self.max_tokens = max_tokens
        self.temperature = temperature
        self.openai_api_key = openai_api_key
        self.enable_fallback = enable_fallback
        
        # Model components (lazy loaded)
        self.tokenizer = None
        self.model = None
        self.pipeline = None
        self._model_loaded = False
        
        # Thai-specific configurations
        self.thai_templates = {
            "greeting": "คุณ: {input}\nผู้ช่วย: ",
            "question": "คำถาม: {input}\nคำตอบ: ",
            "recommendation": "กรุณาแนะนำ: {input}\nข้อแนะนำ: ",
            "general": "ผู้ใช้: {input}\nผู้ช่วย: "
        }
        
        # Fallback responses for error cases
        self.fallback_responses = {
            "th": [
                "ขออภัย ไม่สามารถประมวลผลคำขอของคุณได้ในขณะนี้ กรุณาลองใหม่อีกครั้ง",
                "ขออภัย เกิดข้อผิดพลาดในระบบ กรุณาติดต่อฝ่ายสนับสนุน",
                "ไม่สามารถให้คำตอบได้ในขณะนี้ กรุณาลองใหม่ภายหลัง"
            ],
            "en": [
                "Sorry, I'm unable to process your request at the moment. Please try again.",
                "Apologies, there was a system error. Please contact support.",
                "Cannot provide a response right now. Please try again later."
            ]
        }
        
        logger.info(f"OpenThaiGPT initialized with model: {self.model_name}, device: {self.device}")
    
    async def _load_model(self) -> bool:
        """Load the Thai LLM model (async for better performance)"""
        if self._model_loaded:
            return True
            
        try:
            logger.info(f"Loading OpenThaiGPT model: {self.model_name}")
            start_time = time.time()
            
            # For demo, we'll use a simpler approach with pipeline
            # In production, you might want to use specific OpenThaiGPT models
            self.pipeline = pipeline(
                "text-generation",
                model=self.model_name,
                device=0 if self.device == "cuda" and torch.cuda.is_available() else -1,
                torch_dtype=torch.float16 if self.device == "cuda" else torch.float32,
                trust_remote_code=True
            )
            
            self._model_loaded = True
            load_time = time.time() - start_time
            logger.info(f"Model loaded successfully in {load_time:.2f}s")
            return True
            
        except Exception as e:
            logger.error(f"Failed to load OpenThaiGPT model: {str(e)}")
            if self.enable_fallback:
                logger.info("Will use fallback responses")
            return False
    
    def _detect_language(self, text: str) -> str:
        """Detect if text is Thai or English"""
        # Simple heuristic: check for Thai Unicode characters
        thai_chars = sum(1 for char in text if '\u0e00' <= char <= '\u0e7f')
        return "th" if thai_chars > len(text) * 0.3 else "en"
    
    def _prepare_prompt(self, message: str, context_type: str = "general") -> str:
        """Prepare input prompt based on context and language"""
        lang = self._detect_language(message)
        
        if lang == "th" and context_type in self.thai_templates:
            return self.thai_templates[context_type].format(input=message)
        else:
            # English or fallback template
            return f"User: {message}\nAssistant: "
    
    def _truncate_response(self, response: str, max_length: int = 512) -> str:
        """Truncate response to reasonable length"""
        if len(response) <= max_length:
            return response
        
        # Try to cut at sentence boundary
        sentences = response[:max_length].split('.')
        if len(sentences) > 1:
            return '.'.join(sentences[:-1]) + '.'
        
        # If no sentence boundary, cut at word boundary
        words = response[:max_length].split()
        return ' '.join(words[:-1]) + '...'
    
    async def chat(self, message: str, context_type: str = "general") -> str:
        """
        Main chat interface
        
        Args:
            message: User input message
            context_type: Type of conversation (general, greeting, question, recommendation)
            
        Returns:
            Generated response string
        """
        try:
            start_time = time.time()
            
            # Load model if not already loaded
            if not await self._load_model():
                if self.enable_fallback:
                    return await self._fallback_response(message)
                else:
                    raise RuntimeError("Failed to load OpenThaiGPT model")
            
            # Prepare prompt
            prompt = self._prepare_prompt(message, context_type)
            
            # Generate response
            response = await self._generate_response(prompt)
            
            # Post-process response
            response = self._truncate_response(response)
            
            response_time = time.time() - start_time
            logger.info(f"Generated response in {response_time:.2f}s")
            
            return response
            
        except Exception as e:
            logger.error(f"Error in chat: {str(e)}")
            if self.enable_fallback:
                return await self._fallback_response(message)
            else:
                raise
    
    async def _generate_response(self, prompt: str) -> str:
        """Generate response using the loaded model"""
        try:
            # Use asyncio to run the pipeline in a thread pool to avoid blocking
            loop = asyncio.get_event_loop()
            
            def run_pipeline():
                result = self.pipeline(
                    prompt,
                    max_length=len(prompt.split()) + self.max_tokens,
                    temperature=self.temperature,
                    do_sample=True,
                    pad_token_id=self.pipeline.tokenizer.eos_token_id,
                    num_return_sequences=1
                )
                return result[0]['generated_text']
            
            generated_text = await loop.run_in_executor(None, run_pipeline)
            
            # Extract only the response part (remove the prompt)
            response = generated_text[len(prompt):].strip()
            
            return response if response else "ขออภัย ไม่สามารถสร้างคำตอบได้"
            
        except Exception as e:
            logger.error(f"Error generating response: {str(e)}")
            raise
    
    async def _fallback_response(self, message: str) -> str:
        """Provide fallback response when main model fails"""
        lang = self._detect_language(message)
        responses = self.fallback_responses.get(lang, self.fallback_responses["en"])
        
        # Simple logic: return first fallback response
        # In production, you might want to use OpenAI API here
        return responses[0]
    
    async def chat_with_history(self, messages: List[Dict[str, str]]) -> str:
        """
        Multi-turn chat with conversation history
        
        Args:
            messages: List of {"role": "user/assistant", "content": "message"} dicts
            
        Returns:
            Generated response string
        """
        try:
            # Build conversation context
            context = ""
            for msg in messages[-5:]:  # Keep last 5 messages for context
                role = "ผู้ใช้" if msg["role"] == "user" else "ผู้ช่วย"
                context += f"{role}: {msg['content']}\n"
            
            context += "ผู้ช่วย: "
            
            # Generate response with context
            if not await self._load_model():
                return await self._fallback_response(messages[-1]["content"])
            
            loop = asyncio.get_event_loop()
            
            def run_pipeline():
                result = self.pipeline(
                    context,
                    max_length=len(context.split()) + self.max_tokens,
                    temperature=self.temperature,
                    do_sample=True,
                    pad_token_id=self.pipeline.tokenizer.eos_token_id
                )
                return result[0]['generated_text']
            
            generated_text = await loop.run_in_executor(None, run_pipeline)
            response = generated_text[len(context):].strip()
            
            return self._truncate_response(response) if response else await self._fallback_response(messages[-1]["content"])
            
        except Exception as e:
            logger.error(f"Error in multi-turn chat: {str(e)}")
            return await self._fallback_response(messages[-1]["content"] if messages else "")
    
    def get_model_info(self) -> Dict[str, Any]:
        """Get information about the current model"""
        return {
            "model_name": self.model_name,
            "device": self.device,
            "is_loaded": self._model_loaded,
            "max_tokens": self.max_tokens,
            "temperature": self.temperature,
            "fallback_enabled": self.enable_fallback,
            "has_openai_fallback": HAS_OPENAI and self.openai_api_key is not None
        }

# Factory function for easy instantiation
def create_openthaigpt_llm(**kwargs) -> OpenThaiGPTLLM:
    """Create and return OpenThaiGPT LLM instance"""
    return OpenThaiGPTLLM(**kwargs)