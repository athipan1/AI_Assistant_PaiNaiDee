"""
Plugin system for PaiNaiDee AI Assistant
Provides extensible external API integration for real-time information retrieval
"""

from .base import PluginInterface, PluginConfig, PluginResponse
from .registry import PluginRegistry
from .manager import PluginManager

__all__ = [
    'PluginInterface',
    'PluginConfig', 
    'PluginResponse',
    'PluginRegistry',
    'PluginManager'
]