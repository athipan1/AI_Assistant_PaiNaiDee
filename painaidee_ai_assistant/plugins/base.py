"""
Base classes and interfaces for the plugin system
"""

import asyncio
import logging
from abc import ABC, abstractmethod
from datetime import datetime
from typing import Dict, Any, List, Optional, Union
from enum import Enum

from pydantic import BaseModel, Field

logger = logging.getLogger(__name__)


class PluginStatus(str, Enum):
    """Plugin status enumeration"""
    ACTIVE = "active"
    INACTIVE = "inactive"
    ERROR = "error"
    LOADING = "loading"
    DISABLED = "disabled"


class PluginConfig(BaseModel):
    """Configuration for a plugin"""
    name: str = Field(..., description="Plugin name")
    description: str = Field(..., description="Plugin description")
    version: str = Field("1.0.0", description="Plugin version")
    enabled: bool = Field(True, description="Whether plugin is enabled")
    timeout: int = Field(30, description="Request timeout in seconds")
    cache_ttl: int = Field(300, description="Cache TTL in seconds")
    rate_limit: int = Field(60, description="Requests per minute")
    api_key: Optional[str] = Field(None, description="API key if required")
    base_url: Optional[str] = Field(None, description="Base URL for API")
    headers: Dict[str, str] = Field(default_factory=dict, description="Default headers")
    parameters: Dict[str, Any] = Field(default_factory=dict, description="Default parameters")
    intents: List[str] = Field(default_factory=list, description="Supported intent keywords")
    schema: Dict[str, Any] = Field(default_factory=dict, description="Response data schema")
    

class PluginResponse(BaseModel):
    """Standardized plugin response format"""
    plugin_name: str = Field(..., description="Name of the plugin that generated this response")
    success: bool = Field(..., description="Whether the plugin call was successful")
    data: List[Dict[str, Any]] = Field(default_factory=list, description="Response data")
    metadata: Dict[str, Any] = Field(default_factory=dict, description="Additional metadata")
    error: Optional[str] = Field(None, description="Error message if failed")
    timestamp: datetime = Field(default_factory=datetime.now, description="Response timestamp")
    cache_hit: bool = Field(False, description="Whether response came from cache")
    execution_time_ms: Optional[float] = Field(None, description="Plugin execution time in milliseconds")


class PluginInterface(ABC):
    """Abstract base class for all plugins"""
    
    def __init__(self, config: PluginConfig):
        self.config = config
        self.status = PluginStatus.INACTIVE
        self.last_error: Optional[str] = None
        self.request_count = 0
        self.error_count = 0
        self.cache: Dict[str, Any] = {}
        self.cache_timestamps: Dict[str, datetime] = {}
        
    @property
    def name(self) -> str:
        """Get plugin name"""
        return self.config.name
        
    @property
    def is_enabled(self) -> bool:
        """Check if plugin is enabled"""
        return self.config.enabled and self.status != PluginStatus.ERROR
        
    @abstractmethod
    async def initialize(self) -> bool:
        """Initialize the plugin. Return True if successful."""
        pass
        
    @abstractmethod
    async def execute(self, intent: str, parameters: Dict[str, Any]) -> PluginResponse:
        """Execute plugin with given intent and parameters"""
        pass
        
    @abstractmethod
    async def health_check(self) -> bool:
        """Check plugin health. Return True if healthy."""
        pass
        
    async def cleanup(self) -> None:
        """Cleanup plugin resources"""
        self.cache.clear()
        self.cache_timestamps.clear()
        self.status = PluginStatus.INACTIVE
        
    def supports_intent(self, intent: str) -> bool:
        """Check if plugin supports the given intent"""
        if not self.config.intents:
            return True  # If no specific intents configured, support all
        return any(keyword.lower() in intent.lower() for keyword in self.config.intents)
        
    def _get_cache_key(self, intent: str, parameters: Dict[str, Any]) -> str:
        """Generate cache key for request"""
        # Simple cache key generation - could be improved with hash
        params_str = "_".join(f"{k}:{v}" for k, v in sorted(parameters.items()))
        return f"{intent}_{params_str}"
        
    def _is_cache_valid(self, cache_key: str) -> bool:
        """Check if cached response is still valid"""
        if cache_key not in self.cache_timestamps:
            return False
        age = (datetime.now() - self.cache_timestamps[cache_key]).total_seconds()
        return age < self.config.cache_ttl
        
    def _get_cached_response(self, cache_key: str) -> Optional[PluginResponse]:
        """Get cached response if valid"""
        if cache_key in self.cache and self._is_cache_valid(cache_key):
            cached_data = self.cache[cache_key]
            cached_data.cache_hit = True
            return cached_data
        return None
        
    def _cache_response(self, cache_key: str, response: PluginResponse) -> None:
        """Cache plugin response"""
        self.cache[cache_key] = response
        self.cache_timestamps[cache_key] = datetime.now()
        
    async def execute_with_cache(self, intent: str, parameters: Dict[str, Any]) -> PluginResponse:
        """Execute plugin with caching support"""
        if not self.is_enabled:
            return PluginResponse(
                plugin_name=self.name,
                success=False,
                error=f"Plugin {self.name} is not enabled or in error state"
            )
            
        cache_key = self._get_cache_key(intent, parameters)
        
        # Check cache first
        cached_response = self._get_cached_response(cache_key)
        if cached_response:
            logger.debug(f"Plugin {self.name}: Cache hit for {cache_key}")
            return cached_response
            
        # Execute plugin
        start_time = datetime.now()
        try:
            self.request_count += 1
            response = await asyncio.wait_for(
                self.execute(intent, parameters),
                timeout=self.config.timeout
            )
            execution_time = (datetime.now() - start_time).total_seconds() * 1000
            response.execution_time_ms = execution_time
            
            # Cache successful responses
            if response.success:
                self._cache_response(cache_key, response)
                
            self.status = PluginStatus.ACTIVE
            return response
            
        except asyncio.TimeoutError:
            self.error_count += 1
            error_msg = f"Plugin {self.name} timed out after {self.config.timeout}s"
            logger.error(error_msg)
            self.last_error = error_msg
            return PluginResponse(
                plugin_name=self.name,
                success=False,
                error=error_msg
            )
            
        except Exception as e:
            self.error_count += 1
            error_msg = f"Plugin {self.name} error: {str(e)}"
            logger.error(error_msg, exc_info=True)
            self.last_error = error_msg
            self.status = PluginStatus.ERROR
            return PluginResponse(
                plugin_name=self.name,
                success=False,
                error=error_msg
            )
            
    def get_stats(self) -> Dict[str, Any]:
        """Get plugin statistics"""
        return {
            "name": self.name,
            "status": self.status.value,
            "enabled": self.config.enabled,
            "request_count": self.request_count,
            "error_count": self.error_count,
            "error_rate": self.error_count / max(1, self.request_count),
            "last_error": self.last_error,
            "cache_size": len(self.cache),
            "supported_intents": self.config.intents,
            "config": {
                "timeout": self.config.timeout,
                "cache_ttl": self.config.cache_ttl,
                "rate_limit": self.config.rate_limit
            }
        }