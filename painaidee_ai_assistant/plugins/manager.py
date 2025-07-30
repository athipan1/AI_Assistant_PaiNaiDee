"""
Plugin manager for orchestrating multiple plugins and intent resolution
"""

import asyncio
import logging
from typing import Dict, List, Any, Optional
from datetime import datetime

from .base import PluginInterface, PluginResponse
from .registry import get_registry

logger = logging.getLogger(__name__)


class IntentClassifier:
    """Simple intent classifier for plugin selection"""
    
    def __init__(self):
        # Define intent patterns and their associated keywords
        self.intent_patterns = {
            "attractions": ["attraction", "place", "visit", "tourist", "sightseeing", "landmark", "temple", "wat", "สถานที่", "ท่องเที่ยว"],
            "reviews": ["review", "rating", "opinion", "feedback", "comment", "tripadvisor", "google", "รีวิว", "ความคิดเห็น"],
            "news": ["news", "event", "happening", "update", "current", "latest", "ข่าว", "เหตุการณ์"],
            "cultural": ["history", "culture", "heritage", "traditional", "museum", "art", "วัฒนธรรม", "ประวัติศาสตร์"],
            "location": ["province", "city", "area", "region", "district", "จังหวัด", "เมือง", "พื้นที่"],
            "food": ["food", "restaurant", "eat", "dining", "cuisine", "อาหาร", "ร้านอาหาร"],
            "accommodation": ["hotel", "resort", "stay", "accommodation", "โรงแรม", "ที่พัก"],
            "transportation": ["transport", "travel", "bus", "train", "flight", "การเดินทาง", "ขนส่ง"]
        }
        
    def classify_intent(self, text: str) -> List[str]:
        """Classify user input text to determine intent categories"""
        text_lower = text.lower()
        detected_intents = []
        
        for intent, keywords in self.intent_patterns.items():
            for keyword in keywords:
                if keyword.lower() in text_lower:
                    if intent not in detected_intents:
                        detected_intents.append(intent)
                    break
                    
        # If no specific intent detected, default to attractions (most common tourism query)
        if not detected_intents:
            detected_intents = ["attractions"]
            
        return detected_intents
        
    def extract_parameters(self, text: str, intents: List[str]) -> Dict[str, Any]:
        """Extract parameters from user input based on detected intents"""
        params = {}
        text_lower = text.lower()
        
        # Common location extraction
        thai_provinces = [
            "bangkok", "กรุงเทพ", "chiangmai", "เชียงใหม่", "phuket", "ภูเก็ต", 
            "pattaya", "พัทยา", "ayutthaya", "อยุธยา", "sukhothai", "สุโขทัย",
            "krabi", "กระบี่", "koh samui", "เกาะสมุย", "hua hin", "หัวหิน"
        ]
        
        for province in thai_provinces:
            if province in text_lower:
                params["province"] = province.title()
                params["location"] = province.title()
                break
                
        # Language detection
        if any(char for char in text if ord(char) > 127):  # Simple Thai character detection
            params["lang"] = "th"
        else:
            params["lang"] = "en"
            
        # Extract specific terms based on intent
        if "cultural" in intents:
            wat_keywords = ["wat", "temple", "วัด"]
            for keyword in wat_keywords:
                if keyword in text_lower:
                    # Try to extract temple name (simplified)
                    words = text.split()
                    for i, word in enumerate(words):
                        if keyword.lower() in word.lower() and i < len(words) - 1:
                            temple_name = f"{word} {words[i+1]}"
                            params["wat_name"] = temple_name
                            break
                            
        # Add more parameter extraction logic as needed
        params["query"] = text
        
        return params


class PluginManager:
    """Main plugin manager that orchestrates plugin execution"""
    
    def __init__(self):
        self.registry = get_registry()
        self.intent_classifier = IntentClassifier()
        self.initialized_plugins = set()
        
    async def initialize_plugin(self, plugin_name: str) -> bool:
        """Initialize a specific plugin"""
        if plugin_name in self.initialized_plugins:
            return True
            
        instance = self.registry.get_plugin_instance(plugin_name)
        if not instance:
            instance = self.registry.create_plugin_instance(plugin_name)
            
        if not instance:
            return False
            
        try:
            success = await instance.initialize()
            if success:
                self.initialized_plugins.add(plugin_name)
                logger.info(f"Successfully initialized plugin: {plugin_name}")
            else:
                logger.error(f"Failed to initialize plugin: {plugin_name}")
            return success
        except Exception as e:
            logger.error(f"Error initializing plugin {plugin_name}: {e}")
            return False
            
    async def initialize_all_plugins(self) -> Dict[str, bool]:
        """Initialize all enabled plugins"""
        enabled_plugins = self.registry.list_enabled_plugins()
        results = {}
        
        for plugin_name in enabled_plugins:
            results[plugin_name] = await self.initialize_plugin(plugin_name)
            
        return results
        
    async def query_plugins(self, user_input: str, max_plugins: int = 3) -> List[PluginResponse]:
        """Query plugins based on user input with intent classification"""
        # Classify intent and extract parameters
        intents = self.intent_classifier.classify_intent(user_input)
        parameters = self.intent_classifier.extract_parameters(user_input, intents)
        
        logger.info(f"Detected intents: {intents}, Parameters: {parameters}")
        
        # Find plugins that support these intents
        suitable_plugins = set()
        for intent in intents:
            matching_plugins = self.registry.list_plugins_by_intent(intent)
            suitable_plugins.update(matching_plugins)
            
        # Limit number of plugins to avoid overwhelming response
        suitable_plugins = list(suitable_plugins)[:max_plugins]
        
        if not suitable_plugins:
            logger.warning(f"No plugins found for intents: {intents}")
            return []
            
        # Execute plugins concurrently
        tasks = []
        for plugin_name in suitable_plugins:
            instance = self.registry.get_plugin_instance(plugin_name)
            if not instance:
                instance = self.registry.create_plugin_instance(plugin_name)
                
            if instance and plugin_name not in self.initialized_plugins:
                await self.initialize_plugin(plugin_name)
                
            if instance and instance.is_enabled:
                # Choose the most relevant intent for this plugin
                plugin_intent = self._choose_best_intent_for_plugin(instance, intents)
                task = instance.execute_with_cache(plugin_intent, parameters)
                tasks.append(task)
                
        if not tasks:
            return []
            
        # Execute all plugin tasks concurrently
        try:
            responses = await asyncio.gather(*tasks, return_exceptions=True)
            
            # Filter out exceptions and return valid responses
            valid_responses = []
            for response in responses:
                if isinstance(response, PluginResponse):
                    valid_responses.append(response)
                elif isinstance(response, Exception):
                    logger.error(f"Plugin execution error: {response}")
                    
            return valid_responses
            
        except Exception as e:
            logger.error(f"Error executing plugins: {e}")
            return []
            
    def _choose_best_intent_for_plugin(self, plugin: PluginInterface, intents: List[str]) -> str:
        """Choose the best intent for a specific plugin"""
        # Find the first intent that this plugin supports
        for intent in intents:
            if plugin.supports_intent(intent):
                return intent
        # If no specific match, return the first intent
        return intents[0] if intents else "general"
        
    async def query_specific_plugin(self, plugin_name: str, intent: str, parameters: Dict[str, Any]) -> Optional[PluginResponse]:
        """Query a specific plugin directly"""
        instance = self.registry.get_plugin_instance(plugin_name)
        if not instance:
            instance = self.registry.create_plugin_instance(plugin_name)
            
        if not instance:
            return None
            
        if plugin_name not in self.initialized_plugins:
            success = await self.initialize_plugin(plugin_name)
            if not success:
                return None
                
        if not instance.is_enabled:
            return PluginResponse(
                plugin_name=plugin_name,
                success=False,
                error=f"Plugin {plugin_name} is not enabled"
            )
            
        return await instance.execute_with_cache(intent, parameters)
        
    async def health_check_all(self) -> Dict[str, bool]:
        """Health check all plugins"""
        results = {}
        enabled_plugins = self.registry.list_enabled_plugins()
        
        for plugin_name in enabled_plugins:
            instance = self.registry.get_plugin_instance(plugin_name)
            if instance:
                try:
                    results[plugin_name] = await instance.health_check()
                except Exception as e:
                    logger.error(f"Health check failed for {plugin_name}: {e}")
                    results[plugin_name] = False
            else:
                results[plugin_name] = False
                
        return results
        
    def get_manager_stats(self) -> Dict[str, Any]:
        """Get comprehensive manager statistics"""
        registry_stats = self.registry.get_registry_stats()
        
        return {
            "registry": registry_stats,
            "initialized_plugins": list(self.initialized_plugins),
            "intent_patterns": self.intent_classifier.intent_patterns,
            "manager_status": "active"
        }


# Global manager instance
_manager = None

def get_manager() -> PluginManager:
    """Get the global plugin manager"""
    global _manager
    if _manager is None:
        _manager = PluginManager()
    return _manager