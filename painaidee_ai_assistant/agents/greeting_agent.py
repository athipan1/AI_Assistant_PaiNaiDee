"""
Greeting Agent
Handles Thai-style greeting generation using Falcon-7B-Instruct
"""

import asyncio
import logging
from typing import Optional
from transformers import AutoTokenizer, AutoModelForCausalLM
import torch

logger = logging.getLogger(__name__)

class GreetingAgent:
    def __init__(self):
        self.model_name = "tiiuae/falcon-7b-instruct"
        self.tokenizer = None
        self.model = None
        self.device = "cuda" if torch.cuda.is_available() else "cpu"
        self._model_loaded = False
        
        # Thai greeting templates for fallback
        self.thai_greetings = {
            "en": [
                "Sawasdee! Welcome to Thailand, the Land of Smiles! 🇹🇭",
                "Hello and welcome! May your journey in Thailand be filled with wonderful memories!",
                "Greetings, traveler! Thailand awaits you with open arms and warm hospitality!",
                "Welcome to the amazing Kingdom of Thailand! Get ready for an incredible adventure!"
            ],
            "th": [
                "สวัสดีค่ะ! ยินดีต้อนรับสู่ประเทศไทย แดนแห่งรอยยิ้ม! 🇹🇭",
                "สวัสดีครับ! ขอให้การเดินทางในประเทศไทยเป็นความทรงจำที่ดีนะครับ!",
                "ยินดีต้อนรับค่ะ! ประเทศไทยรอต้อนรับด้วยความอบอุ่นและไมตรีจิต!",
                "ขอต้อนรับสู่ราชอาณาจักรไทยที่สวยงาม! เตรียมพร้อมสำหรับการผจญภัยที่น่าทึ่ง!"
            ]
        }
    
    async def _load_model(self):
        """Load the Falcon-7B model (lazy loading)"""
        if self._model_loaded:
            return
            
        try:
            logger.info(f"Loading model {self.model_name}...")
            
            # For demo purposes, we'll use a smaller model or mock the response
            # In production, you would load the actual Falcon-7B model
            # self.tokenizer = AutoTokenizer.from_pretrained(self.model_name)
            # self.model = AutoModelForCausalLM.from_pretrained(
            #     self.model_name,
            #     torch_dtype=torch.float16,
            #     device_map="auto",
            #     trust_remote_code=True
            # )
            
            # For now, we'll simulate model loading
            await asyncio.sleep(0.1)  # Simulate loading time
            self._model_loaded = True
            logger.info("Model loaded successfully (mock)")
            
        except Exception as e:
            logger.warning(f"Failed to load model: {e}. Using fallback responses.")
            self._model_loaded = False
    
    async def generate_greeting(self, name: Optional[str] = None, language: str = "en") -> str:
        """
        Generate a personalized Thai-style greeting
        
        Args:
            name: Optional user name
            language: Language preference ("en" or "th")
        
        Returns:
            Generated greeting string
        """
        try:
            await self._load_model()
            
            if self._model_loaded and self.model is not None:
                # Use the actual model for generation
                greeting = await self._generate_with_model(name, language)
            else:
                # Use fallback templates
                greeting = self._generate_fallback_greeting(name, language)
            
            return greeting
            
        except Exception as e:
            logger.error(f"Error generating greeting: {e}")
            return self._generate_fallback_greeting(name, language)
    
    async def _generate_with_model(self, name: Optional[str], language: str) -> str:
        """Generate greeting using the actual model"""
        try:
            # Construct prompt
            if language == "th":
                if name:
                    prompt = f"สร้างคำทักทายแบบไทย ๆ สำหรับนักท่องเที่ยวชื่อ {name} ที่มาเที่ยวประเทศไทย:"
                else:
                    prompt = "สร้างคำทักทายแบบไทย ๆ สำหรับนักท่องเที่ยวที่มาเที่ยวประเทศไทย:"
            else:
                if name:
                    prompt = f"Generate a warm Thai-style greeting for a tourist named {name} visiting Thailand:"
                else:
                    prompt = "Generate a warm Thai-style greeting for a tourist visiting Thailand:"
            
            # For demo purposes, return a mock response
            # In production, you would use:
            # inputs = self.tokenizer(prompt, return_tensors="pt").to(self.device)
            # outputs = self.model.generate(**inputs, max_length=150, temperature=0.7)
            # response = self.tokenizer.decode(outputs[0], skip_special_tokens=True)
            
            # Mock response based on prompt
            if name:
                if language == "th":
                    return f"สวัสดีค่ะคุณ {name}! ยินดีต้อนรับสู่ประเทศไทย แดนแห่งรอยยิ้ม! หวังว่าคุณจะได้สัมผัสกับวัฒนธรรม อาหาร และความงดงามของเมืองไทยอย่างเต็มที่นะคะ 🇹🇭✨"
                else:
                    return f"Sawasdee {name}! Welcome to Thailand, the Land of Smiles! 🇹🇭 May your journey be filled with amazing discoveries of our rich culture, delicious cuisine, and breathtaking landscapes. Enjoy every moment of your Thai adventure!"
            else:
                return self._generate_fallback_greeting(name, language)
                
        except Exception as e:
            logger.error(f"Model generation failed: {e}")
            return self._generate_fallback_greeting(name, language)
    
    def _generate_fallback_greeting(self, name: Optional[str], language: str) -> str:
        """Generate fallback greeting using templates"""
        import random
        
        greetings = self.thai_greetings.get(language, self.thai_greetings["en"])
        base_greeting = random.choice(greetings)
        
        if name:
            if language == "th":
                return f"สวัสดีค่ะคุณ {name}! {base_greeting}"
            else:
                return f"Hello {name}! {base_greeting}"
        
        return base_greeting