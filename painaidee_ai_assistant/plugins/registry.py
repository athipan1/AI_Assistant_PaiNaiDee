"""
Plugin registry for managing and discovering plugins
"""

import logging
from typing import Dict, List, Optional, Type
from pathlib import Path

from .base import PluginInterface, PluginConfig, PluginStatus

logger = logging.getLogger(__name__)


class PluginRegistry:
    """Registry for managing plugin discovery and registration"""
    
    def __init__(self):
        self._plugins: Dict[str, Type[PluginInterface]] = {}
        self._configs: Dict[str, PluginConfig] = {}
        self._instances: Dict[str, PluginInterface] = {}
        
    def register_plugin(self, plugin_class: Type[PluginInterface], config: PluginConfig) -> None:
        """Register a plugin class with its configuration"""
        plugin_name = config.name
        if plugin_name in self._plugins:
            logger.warning(f"Plugin {plugin_name} is already registered. Overriding...")
            
        self._plugins[plugin_name] = plugin_class
        self._configs[plugin_name] = config
        logger.info(f"Registered plugin: {plugin_name}")
        
    def unregister_plugin(self, plugin_name: str) -> bool:
        """Unregister a plugin"""
        if plugin_name not in self._plugins:
            return False
            
        # Clean up instance if exists
        if plugin_name in self._instances:
            instance = self._instances[plugin_name]
            try:
                # Run cleanup asynchronously if needed
                import asyncio
                asyncio.create_task(instance.cleanup())
            except Exception as e:
                logger.error(f"Error cleaning up plugin {plugin_name}: {e}")
            del self._instances[plugin_name]
            
        del self._plugins[plugin_name]
        del self._configs[plugin_name]
        logger.info(f"Unregistered plugin: {plugin_name}")
        return True
        
    def get_plugin_class(self, plugin_name: str) -> Optional[Type[PluginInterface]]:
        """Get plugin class by name"""
        return self._plugins.get(plugin_name)
        
    def get_plugin_config(self, plugin_name: str) -> Optional[PluginConfig]:
        """Get plugin configuration by name"""
        return self._configs.get(plugin_name)
        
    def get_plugin_instance(self, plugin_name: str) -> Optional[PluginInterface]:
        """Get plugin instance by name"""
        return self._instances.get(plugin_name)
        
    def create_plugin_instance(self, plugin_name: str) -> Optional[PluginInterface]:
        """Create and cache plugin instance"""
        plugin_class = self.get_plugin_class(plugin_name)
        config = self.get_plugin_config(plugin_name)
        
        if not plugin_class or not config:
            logger.error(f"Plugin {plugin_name} not found in registry")
            return None
            
        if plugin_name in self._instances:
            return self._instances[plugin_name]
            
        try:
            instance = plugin_class(config)
            self._instances[plugin_name] = instance
            logger.info(f"Created instance for plugin: {plugin_name}")
            return instance
        except Exception as e:
            logger.error(f"Failed to create instance for plugin {plugin_name}: {e}")
            return None
            
    def list_plugins(self) -> List[str]:
        """List all registered plugin names"""
        return list(self._plugins.keys())
        
    def list_enabled_plugins(self) -> List[str]:
        """List enabled plugin names"""
        return [name for name, config in self._configs.items() if config.enabled]
        
    def list_plugins_by_intent(self, intent: str) -> List[str]:
        """List plugins that support the given intent"""
        matching_plugins = []
        for name, config in self._configs.items():
            if config.enabled:
                # Create temporary instance to check intent support
                plugin_class = self._plugins[name]
                temp_instance = plugin_class(config)
                if temp_instance.supports_intent(intent):
                    matching_plugins.append(name)
        return matching_plugins
        
    def update_plugin_config(self, plugin_name: str, config_updates: Dict) -> bool:
        """Update plugin configuration"""
        if plugin_name not in self._configs:
            return False
            
        config = self._configs[plugin_name]
        for key, value in config_updates.items():
            if hasattr(config, key):
                setattr(config, key, value)
                
        # If instance exists, we might need to recreate it
        if plugin_name in self._instances:
            logger.info(f"Configuration updated for {plugin_name}. Instance will be recreated on next use.")
            
        return True
        
    def enable_plugin(self, plugin_name: str) -> bool:
        """Enable a plugin"""
        return self.update_plugin_config(plugin_name, {"enabled": True})
        
    def disable_plugin(self, plugin_name: str) -> bool:
        """Disable a plugin"""
        success = self.update_plugin_config(plugin_name, {"enabled": False})
        
        # Also cleanup instance if exists
        if plugin_name in self._instances:
            instance = self._instances[plugin_name]
            try:
                import asyncio
                asyncio.create_task(instance.cleanup())
            except Exception as e:
                logger.error(f"Error cleaning up disabled plugin {plugin_name}: {e}")
            del self._instances[plugin_name]
            
        return success
        
    def get_registry_stats(self) -> Dict:
        """Get registry statistics"""
        total_plugins = len(self._plugins)
        enabled_plugins = len(self.list_enabled_plugins())
        active_instances = len(self._instances)
        
        plugin_details = []
        for name in self._plugins:
            config = self._configs[name]
            instance = self._instances.get(name)
            
            plugin_info = {
                "name": name,
                "enabled": config.enabled,
                "has_instance": instance is not None,
                "status": instance.status.value if instance else "not_instantiated",
                "intents": config.intents,
                "version": config.version
            }
            
            if instance:
                plugin_info.update(instance.get_stats())
                
            plugin_details.append(plugin_info)
            
        return {
            "total_plugins": total_plugins,
            "enabled_plugins": enabled_plugins,
            "active_instances": active_instances,
            "plugins": plugin_details
        }


# Global registry instance
_registry = None

def get_registry() -> PluginRegistry:
    """Get the global plugin registry"""
    global _registry
    if _registry is None:
        _registry = PluginRegistry()
    return _registry