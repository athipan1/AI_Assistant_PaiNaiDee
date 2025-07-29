"""
Advanced AI Models Integration
Supports llama.cpp, OpenChat, OpenHermes, and other advanced models
"""

import os
import json
import logging
import asyncio
from typing import Dict, List, Optional, Any, Union
from dataclasses import dataclass
from enum import Enum
from pathlib import Path
import torch
from transformers import AutoTokenizer, AutoModelForCausalLM, pipeline

logger = logging.getLogger(__name__)

class ModelType(Enum):
    """Supported advanced AI model types"""
    LLAMA_CPP = "llama_cpp"
    OPENCHAT = "openchat"
    OPENHERMES = "openhermes"
    BERT_EMOTION = "bert_emotion"  # Existing BERT models
    CUSTOM = "custom"

class ModelCapability(Enum):
    """AI model capabilities"""
    CONVERSATION = "conversation"
    QUESTION_ANSWERING = "question_answering"
    EMOTION_ANALYSIS = "emotion_analysis"
    TEXT_GENERATION = "text_generation"
    TOURISM_ADVICE = "tourism_advice"
    THAI_LANGUAGE = "thai_language"

@dataclass
class ModelConfig:
    """Configuration for an AI model"""
    name: str
    model_type: ModelType
    model_path: str
    capabilities: List[ModelCapability]
    language_support: List[str]
    max_tokens: int = 2048
    temperature: float = 0.7
    is_local: bool = True
    requires_gpu: bool = False
    load_in_8bit: bool = False
    priority: int = 1  # Higher number = higher priority

@dataclass
class AIResponse:
    """Response from an AI model"""
    text: str
    model_used: str
    confidence: float
    capabilities_used: List[ModelCapability]
    processing_time: float
    metadata: Dict[str, Any]

class LlamaCppModel:
    """Wrapper for llama.cpp models"""
    
    def __init__(self, config: ModelConfig):
        self.config = config
        self.model = None
        self._loaded = False
        
    async def load(self):
        """Load the llama.cpp model"""
        if self._loaded:
            return
            
        try:
            # Try to import llama-cpp-python
            from llama_cpp import Llama
            
            logger.info(f"Loading llama.cpp model: {self.config.name}")
            self.model = Llama(
                model_path=self.config.model_path,
                n_ctx=self.config.max_tokens,
                n_gpu_layers=-1 if self.config.requires_gpu and torch.cuda.is_available() else 0,
                verbose=False
            )
            self._loaded = True
            logger.info(f"Successfully loaded llama.cpp model: {self.config.name}")
            
        except ImportError:
            logger.error("llama-cpp-python not installed. Install with: pip install llama-cpp-python")
            raise
        except Exception as e:
            logger.error(f"Failed to load llama.cpp model {self.config.name}: {e}")
            raise
    
    async def generate(self, prompt: str, max_tokens: int = None, temperature: float = None) -> str:
        """Generate text using the llama.cpp model"""
        if not self._loaded:
            await self.load()
            
        max_tokens = max_tokens or self.config.max_tokens
        temperature = temperature or self.config.temperature
        
        try:
            result = self.model(
                prompt,
                max_tokens=max_tokens,
                temperature=temperature,
                echo=False
            )
            return result['choices'][0]['text'].strip()
        except Exception as e:
            logger.error(f"Error generating text with llama.cpp: {e}")
            raise

class OpenChatModel:
    """Wrapper for OpenChat models"""
    
    def __init__(self, config: ModelConfig):
        self.config = config
        self.tokenizer = None
        self.model = None
        self.pipeline = None
        self._loaded = False
        
    async def load(self):
        """Load the OpenChat model"""
        if self._loaded:
            return
            
        try:
            logger.info(f"Loading OpenChat model: {self.config.name}")
            
            # Load OpenChat model (typically openchat/openchat-3.5-1210)
            model_name = self.config.model_path
            
            self.tokenizer = AutoTokenizer.from_pretrained(model_name)
            self.model = AutoModelForCausalLM.from_pretrained(
                model_name,
                torch_dtype=torch.float16 if torch.cuda.is_available() else torch.float32,
                device_map="auto" if torch.cuda.is_available() else None,
                load_in_8bit=self.config.load_in_8bit
            )
            
            self.pipeline = pipeline(
                "text-generation",
                model=self.model,
                tokenizer=self.tokenizer,
                device=0 if torch.cuda.is_available() else -1
            )
            
            self._loaded = True
            logger.info(f"Successfully loaded OpenChat model: {self.config.name}")
            
        except Exception as e:
            logger.error(f"Failed to load OpenChat model {self.config.name}: {e}")
            raise
    
    async def generate(self, prompt: str, max_tokens: int = None, temperature: float = None) -> str:
        """Generate text using the OpenChat model"""
        if not self._loaded:
            await self.load()
            
        max_tokens = max_tokens or self.config.max_tokens
        temperature = temperature or self.config.temperature
        
        try:
            # Format prompt for OpenChat
            formatted_prompt = f"GPT4 Correct User: {prompt}<|end_of_turn|>GPT4 Correct Assistant:"
            
            result = self.pipeline(
                formatted_prompt,
                max_new_tokens=max_tokens,
                temperature=temperature,
                do_sample=True,
                pad_token_id=self.tokenizer.eos_token_id
            )
            
            generated_text = result[0]['generated_text']
            # Extract just the assistant's response
            if "GPT4 Correct Assistant:" in generated_text:
                response = generated_text.split("GPT4 Correct Assistant:")[-1].strip()
            else:
                response = generated_text.strip()
                
            return response
            
        except Exception as e:
            logger.error(f"Error generating text with OpenChat: {e}")
            raise

class OpenHermesModel:
    """Wrapper for OpenHermes models"""
    
    def __init__(self, config: ModelConfig):
        self.config = config
        self.tokenizer = None
        self.model = None
        self.pipeline = None
        self._loaded = False
        
    async def load(self):
        """Load the OpenHermes model"""
        if self._loaded:
            return
            
        try:
            logger.info(f"Loading OpenHermes model: {self.config.name}")
            
            # Load OpenHermes model (typically NousResearch/Nous-Hermes-2-Mixtral-8x7B-DPO)
            model_name = self.config.model_path
            
            self.tokenizer = AutoTokenizer.from_pretrained(model_name)
            self.model = AutoModelForCausalLM.from_pretrained(
                model_name,
                torch_dtype=torch.float16 if torch.cuda.is_available() else torch.float32,
                device_map="auto" if torch.cuda.is_available() else None,
                load_in_8bit=self.config.load_in_8bit
            )
            
            self.pipeline = pipeline(
                "text-generation",
                model=self.model,
                tokenizer=self.tokenizer,
                device=0 if torch.cuda.is_available() else -1
            )
            
            self._loaded = True
            logger.info(f"Successfully loaded OpenHermes model: {self.config.name}")
            
        except Exception as e:
            logger.error(f"Failed to load OpenHermes model {self.config.name}: {e}")
            raise
    
    async def generate(self, prompt: str, max_tokens: int = None, temperature: float = None) -> str:
        """Generate text using the OpenHermes model"""
        if not self._loaded:
            await self.load()
            
        max_tokens = max_tokens or self.config.max_tokens
        temperature = temperature or self.config.temperature
        
        try:
            # Format prompt for OpenHermes
            formatted_prompt = f"<|im_start|>user\n{prompt}<|im_end|>\n<|im_start|>assistant\n"
            
            result = self.pipeline(
                formatted_prompt,
                max_new_tokens=max_tokens,
                temperature=temperature,
                do_sample=True,
                pad_token_id=self.tokenizer.eos_token_id
            )
            
            generated_text = result[0]['generated_text']
            # Extract just the assistant's response
            if "<|im_start|>assistant\n" in generated_text:
                response = generated_text.split("<|im_start|>assistant\n")[-1].strip()
                # Remove end token if present
                if "<|im_end|>" in response:
                    response = response.split("<|im_end|>")[0].strip()
            else:
                response = generated_text.strip()
                
            return response
            
        except Exception as e:
            logger.error(f"Error generating text with OpenHermes: {e}")
            raise

class AdvancedAIManager:
    """Manager for advanced AI models with intelligent routing"""
    
    def __init__(self, config_path: Optional[str] = None):
        self.models: Dict[str, Union[LlamaCppModel, OpenChatModel, OpenHermesModel]] = {}
        self.model_configs: Dict[str, ModelConfig] = {}
        self.config_path = config_path or "config/ai_models.json"
        self.default_models = self._get_default_models()
        
    def _get_default_models(self) -> Dict[str, ModelConfig]:
        """Get default model configurations"""
        return {
            "llama-2-7b-chat": ModelConfig(
                name="llama-2-7b-chat",
                model_type=ModelType.LLAMA_CPP,
                model_path="models/llama-2-7b-chat.gguf",
                capabilities=[
                    ModelCapability.CONVERSATION,
                    ModelCapability.QUESTION_ANSWERING,
                    ModelCapability.TEXT_GENERATION,
                    ModelCapability.TOURISM_ADVICE
                ],
                language_support=["en", "th"],
                max_tokens=2048,
                temperature=0.7,
                priority=2,
                requires_gpu=False
            ),
            "openchat-3.5": ModelConfig(
                name="openchat-3.5",
                model_type=ModelType.OPENCHAT,
                model_path="openchat/openchat-3.5-1210",
                capabilities=[
                    ModelCapability.CONVERSATION,
                    ModelCapability.QUESTION_ANSWERING,
                    ModelCapability.TEXT_GENERATION
                ],
                language_support=["en", "th"],
                max_tokens=4096,
                temperature=0.7,
                priority=3,
                requires_gpu=True,
                load_in_8bit=True
            ),
            "openhermes-2.5": ModelConfig(
                name="openhermes-2.5",
                model_type=ModelType.OPENHERMES,
                model_path="NousResearch/Nous-Hermes-2-Mixtral-8x7B-DPO",
                capabilities=[
                    ModelCapability.CONVERSATION,
                    ModelCapability.QUESTION_ANSWERING,
                    ModelCapability.TEXT_GENERATION,
                    ModelCapability.TOURISM_ADVICE
                ],
                language_support=["en", "th"],
                max_tokens=4096,
                temperature=0.7,
                priority=4,
                requires_gpu=True,
                load_in_8bit=True
            )
        }
    
    async def initialize(self):
        """Initialize the AI manager and load configurations"""
        logger.info("Initializing Advanced AI Manager...")
        
        # Load configuration from file if exists
        if os.path.exists(self.config_path):
            try:
                with open(self.config_path, 'r') as f:
                    config_data = json.load(f)
                    for name, config in config_data.items():
                        # Convert string values to enums
                        if isinstance(config.get("model_type"), str):
                            config["model_type"] = ModelType(config["model_type"])
                        
                        if isinstance(config.get("capabilities"), list):
                            capabilities = []
                            for cap in config["capabilities"]:
                                if isinstance(cap, str):
                                    capabilities.append(ModelCapability(cap))
                                else:
                                    capabilities.append(cap)
                            config["capabilities"] = capabilities
                        
                        self.model_configs[name] = ModelConfig(**config)
            except Exception as e:
                logger.warning(f"Failed to load AI config from {self.config_path}: {e}")
        
        # Use default models if no config loaded
        if not self.model_configs:
            self.model_configs = self.default_models
            logger.info("Using default AI model configurations")
        
        # Initialize available models (lazy loading)
        for name, config in self.model_configs.items():
            if self._is_model_available(config):
                logger.info(f"Model {name} is available for loading")
            else:
                logger.warning(f"Model {name} is not available (missing files or dependencies)")
    
    def _is_model_available(self, config: ModelConfig) -> bool:
        """Check if a model is available for loading"""
        try:
            if config.model_type == ModelType.LLAMA_CPP:
                # Check if model file exists and llama-cpp-python is available
                try:
                    import llama_cpp
                    return os.path.exists(config.model_path)
                except ImportError:
                    return False
            elif config.model_type in [ModelType.OPENCHAT, ModelType.OPENHERMES]:
                # For HuggingFace models, we'll try to load on demand
                return True
            return False
        except Exception:
            return False
    
    async def get_model(self, model_name: str):
        """Get or load a specific model"""
        if model_name in self.models:
            return self.models[model_name]
        
        if model_name not in self.model_configs:
            raise ValueError(f"Model {model_name} not configured")
        
        config = self.model_configs[model_name]
        
        # Create model instance based on type
        if config.model_type == ModelType.LLAMA_CPP:
            model = LlamaCppModel(config)
        elif config.model_type == ModelType.OPENCHAT:
            model = OpenChatModel(config)
        elif config.model_type == ModelType.OPENHERMES:
            model = OpenHermesModel(config)
        else:
            raise ValueError(f"Unsupported model type: {config.model_type}")
        
        # Load the model
        await model.load()
        self.models[model_name] = model
        
        return model
    
    def select_best_model(self, 
                         capability: ModelCapability,
                         language: str = "en",
                         prefer_local: bool = True) -> Optional[str]:
        """Select the best model for a given capability and language"""
        
        suitable_models = []
        
        for name, config in self.model_configs.items():
            # Check capability support
            if capability not in config.capabilities:
                continue
            
            # Check language support
            if language not in config.language_support:
                continue
            
            # Check availability
            if not self._is_model_available(config):
                continue
            
            # Check local preference
            if prefer_local and not config.is_local:
                continue
            
            suitable_models.append((name, config.priority))
        
        if not suitable_models:
            logger.warning(f"No suitable model found for capability {capability} and language {language}")
            return None
        
        # Return model with highest priority
        best_model = max(suitable_models, key=lambda x: x[1])
        return best_model[0]
    
    async def generate_response(self,
                              prompt: str,
                              capability: ModelCapability = ModelCapability.CONVERSATION,
                              language: str = "en",
                              model_name: Optional[str] = None,
                              max_tokens: Optional[int] = None,
                              temperature: Optional[float] = None) -> AIResponse:
        """Generate a response using the most appropriate AI model"""
        
        start_time = asyncio.get_event_loop().time()
        
        # Select model if not specified
        if not model_name:
            model_name = self.select_best_model(capability, language)
            if not model_name:
                raise ValueError(f"No suitable model available for capability {capability}")
        
        # Get the model
        model = await self.get_model(model_name)
        config = self.model_configs[model_name]
        
        # Generate response
        try:
            response_text = await model.generate(prompt, max_tokens, temperature)
            processing_time = asyncio.get_event_loop().time() - start_time
            
            return AIResponse(
                text=response_text,
                model_used=model_name,
                confidence=0.8,  # Could be improved with actual confidence scoring
                capabilities_used=[capability],
                processing_time=processing_time,
                metadata={
                    "model_type": config.model_type.value,
                    "language": language,
                    "prompt_length": len(prompt),
                    "response_length": len(response_text)
                }
            )
            
        except Exception as e:
            logger.error(f"Error generating response with model {model_name}: {e}")
            raise
    
    def get_available_models(self) -> List[Dict[str, Any]]:
        """Get list of available models with their capabilities"""
        models = []
        for name, config in self.model_configs.items():
            models.append({
                "name": name,
                "type": config.model_type.value if hasattr(config.model_type, 'value') else str(config.model_type),
                "capabilities": [cap.value if hasattr(cap, 'value') else str(cap) for cap in config.capabilities],
                "languages": config.language_support,
                "is_local": config.is_local,
                "priority": config.priority,
                "available": self._is_model_available(config)
            })
        return models

# Global instance
ai_manager = AdvancedAIManager()

async def initialize_advanced_ai():
    """Initialize the advanced AI system"""
    await ai_manager.initialize()

def get_ai_manager() -> AdvancedAIManager:
    """Get the global AI manager instance"""
    return ai_manager