"""
Plugin API routes for PaiNaiDee AI Assistant
Provides endpoints for plugin management and execution
"""

import asyncio
import logging
from typing import Dict, Any, List, Optional
from datetime import datetime

from fastapi import APIRouter, HTTPException, BackgroundTasks, Query, Path
from pydantic import BaseModel, Field

from plugins.manager import get_manager
from plugins.registry import get_registry
from plugins.external.tripadvisor_plugin import create_tripadvisor_plugin
from plugins.external.thai_news_plugin import create_thai_news_plugin
from plugins.external.cultural_sites_plugin import create_cultural_sites_plugin

logger = logging.getLogger(__name__)

# Initialize router
router = APIRouter(prefix="/plugin", tags=["Plugin System"])

# Request/Response models
class PluginQueryRequest(BaseModel):
    """Request model for plugin queries"""
    question: str = Field(..., description="User's question or query")
    max_plugins: int = Field(3, description="Maximum number of plugins to query")
    language: str = Field("en", description="Response language (en/th)")
    include_metadata: bool = Field(True, description="Include plugin metadata in response")

class PluginQueryResponse(BaseModel):
    """Response model for plugin queries"""
    success: bool
    results: List[Dict[str, Any]]
    metadata: Dict[str, Any]
    execution_time_ms: float
    plugins_used: List[str]

class DirectPluginRequest(BaseModel):
    """Request model for direct plugin execution"""
    plugin_name: str = Field(..., description="Name of the plugin to execute")
    intent: str = Field(..., description="Intent or action for the plugin")
    parameters: Dict[str, Any] = Field(default_factory=dict, description="Parameters for the plugin")

class PluginConfigUpdate(BaseModel):
    """Model for updating plugin configuration"""
    enabled: Optional[bool] = Field(None, description="Enable/disable plugin")
    timeout: Optional[int] = Field(None, description="Request timeout in seconds")
    cache_ttl: Optional[int] = Field(None, description="Cache TTL in seconds")
    rate_limit: Optional[int] = Field(None, description="Rate limit per minute")

class PluginRegistration(BaseModel):
    """Model for registering new plugins"""
    name: str = Field(..., description="Plugin name")
    description: str = Field(..., description="Plugin description")
    version: str = Field("1.0.0", description="Plugin version")
    enabled: bool = Field(True, description="Whether plugin should be enabled")
    timeout: int = Field(30, description="Request timeout in seconds")
    cache_ttl: int = Field(300, description="Cache TTL in seconds")
    intents: List[str] = Field(default_factory=list, description="Supported intents")
    base_url: Optional[str] = Field(None, description="Base URL for external API")
    api_key: Optional[str] = Field(None, description="API key if required")


# Plugin execution endpoints
@router.post("/query", response_model=PluginQueryResponse)
async def query_plugins(request: PluginQueryRequest):
    """
    Query multiple plugins based on user input with intent classification
    
    This is the main endpoint for getting real-time information from external sources.
    """
    start_time = datetime.now()
    
    try:
        manager = get_manager()
        
        # Query plugins with intent classification
        responses = await manager.query_plugins(
            user_input=request.question,
            max_plugins=request.max_plugins
        )
        
        # Process responses
        results = []
        plugins_used = []
        
        for response in responses:
            if response.success:
                result = {
                    "plugin": response.plugin_name,
                    "data": response.data,
                    "timestamp": response.timestamp.isoformat(),
                    "cache_hit": response.cache_hit
                }
                
                if request.include_metadata:
                    result["metadata"] = response.metadata
                    
                results.append(result)
                plugins_used.append(response.plugin_name)
            else:
                logger.warning(f"Plugin {response.plugin_name} failed: {response.error}")
        
        execution_time = (datetime.now() - start_time).total_seconds() * 1000
        
        return PluginQueryResponse(
            success=True,
            results=results,
            metadata={
                "total_plugins_queried": len(responses),
                "successful_plugins": len(results),
                "language": request.language,
                "intent_classification": "automatic"
            },
            execution_time_ms=execution_time,
            plugins_used=plugins_used
        )
        
    except Exception as e:
        logger.error(f"Plugin query error: {e}")
        raise HTTPException(status_code=500, detail=f"Plugin query failed: {str(e)}")


@router.post("/execute")
async def execute_plugin_directly(request: DirectPluginRequest):
    """
    Execute a specific plugin directly with custom parameters
    """
    try:
        manager = get_manager()
        
        response = await manager.query_specific_plugin(
            plugin_name=request.plugin_name,
            intent=request.intent,
            parameters=request.parameters
        )
        
        if not response:
            raise HTTPException(
                status_code=404, 
                detail=f"Plugin '{request.plugin_name}' not found or not available"
            )
        
        return {
            "success": response.success,
            "plugin_name": response.plugin_name,
            "data": response.data,
            "metadata": response.metadata,
            "error": response.error,
            "execution_time_ms": response.execution_time_ms,
            "cache_hit": response.cache_hit
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Direct plugin execution error: {e}")
        raise HTTPException(status_code=500, detail=str(e))


# Specific plugin endpoints as requested
@router.get("/get_latest_attractions")
async def get_latest_attractions(
    province: str = Query(..., description="Province name (e.g., ChiangMai)"),
    language: str = Query("en", description="Response language (en/th)")
):
    """
    Get latest tourist attractions for a specific province
    """
    try:
        manager = get_manager()
        
        # Query TripAdvisor plugin specifically
        response = await manager.query_specific_plugin(
            plugin_name="tripadvisor",
            intent="attractions",
            parameters={
                "province": province,
                "lang": language
            }
        )
        
        if not response or not response.success:
            raise HTTPException(
                status_code=503, 
                detail=f"TripAdvisor plugin unavailable: {response.error if response else 'Plugin not found'}"
            )
        
        return {
            "province": province,
            "language": language,
            "attractions": response.data,
            "metadata": response.metadata,
            "source": "TripAdvisor API"
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Get attractions error: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/get_event_news")
async def get_event_news(
    lang: str = Query("th", description="Language (th/en)"),
    category: str = Query("travel", description="News category")
):
    """
    Get latest event and travel-related news
    """
    try:
        manager = get_manager()
        
        # Query Thai News plugin specifically
        response = await manager.query_specific_plugin(
            plugin_name="thai_news",
            intent="news",
            parameters={
                "lang": lang,
                "category": category
            }
        )
        
        if not response or not response.success:
            raise HTTPException(
                status_code=503, 
                detail=f"Thai News plugin unavailable: {response.error if response else 'Plugin not found'}"
            )
        
        return {
            "language": lang,
            "category": category,
            "news": response.data,
            "metadata": response.metadata,
            "source": "Thai News Sources"
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Get event news error: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/get_temple_info")
async def get_temple_info(
    wat_name: str = Query(..., description="Temple name (e.g., WatPhraKaew)"),
    language: str = Query("en", description="Response language (en/th)")
):
    """
    Get temple and cultural site information from Department of Fine Arts
    """
    try:
        manager = get_manager()
        
        # Query Cultural Sites plugin specifically
        response = await manager.query_specific_plugin(
            plugin_name="cultural_sites",
            intent="cultural",
            parameters={
                "wat_name": wat_name,
                "lang": language
            }
        )
        
        if not response or not response.success:
            raise HTTPException(
                status_code=503, 
                detail=f"Cultural Sites plugin unavailable: {response.error if response else 'Plugin not found'}"
            )
        
        return {
            "wat_name": wat_name,
            "language": language,
            "temple_info": response.data,
            "metadata": response.metadata,
            "source": "Department of Fine Arts"
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Get temple info error: {e}")
        raise HTTPException(status_code=500, detail=str(e))


# Plugin management endpoints
@router.get("/list")
async def list_plugins():
    """
    List all registered plugins with their status
    """
    try:
        registry = get_registry()
        stats = registry.get_registry_stats()
        
        return {
            "total_plugins": stats["total_plugins"],
            "enabled_plugins": stats["enabled_plugins"],
            "active_instances": stats["active_instances"],
            "plugins": stats["plugins"]
        }
        
    except Exception as e:
        logger.error(f"List plugins error: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/status/{plugin_name}")
async def get_plugin_status(plugin_name: str = Path(..., description="Plugin name")):
    """
    Get detailed status of a specific plugin
    """
    try:
        registry = get_registry()
        instance = registry.get_plugin_instance(plugin_name)
        config = registry.get_plugin_config(plugin_name)
        
        if not config:
            raise HTTPException(status_code=404, detail=f"Plugin '{plugin_name}' not found")
        
        status = {
            "name": plugin_name,
            "enabled": config.enabled,
            "has_instance": instance is not None,
            "config": {
                "timeout": config.timeout,
                "cache_ttl": config.cache_ttl,
                "rate_limit": config.rate_limit,
                "intents": config.intents
            }
        }
        
        if instance:
            status.update(instance.get_stats())
            
        return status
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Get plugin status error: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/health")
async def health_check_plugins():
    """
    Perform health check on all plugins
    """
    try:
        manager = get_manager()
        health_results = await manager.health_check_all()
        
        return {
            "timestamp": datetime.now().isoformat(),
            "overall_status": "healthy" if all(health_results.values()) else "degraded",
            "plugin_health": health_results
        }
        
    except Exception as e:
        logger.error(f"Plugin health check error: {e}")
        raise HTTPException(status_code=500, detail=str(e))


# Admin endpoints for plugin management
@router.put("/admin/{plugin_name}/config")
async def update_plugin_config(
    plugin_name: str = Path(..., description="Plugin name"),
    config: PluginConfigUpdate = None
):
    """
    Update plugin configuration
    """
    try:
        registry = get_registry()
        
        if not registry.get_plugin_config(plugin_name):
            raise HTTPException(status_code=404, detail=f"Plugin '{plugin_name}' not found")
        
        # Build update dict from non-None values
        updates = {}
        if config.enabled is not None:
            updates["enabled"] = config.enabled
        if config.timeout is not None:
            updates["timeout"] = config.timeout
        if config.cache_ttl is not None:
            updates["cache_ttl"] = config.cache_ttl
        if config.rate_limit is not None:
            updates["rate_limit"] = config.rate_limit
        
        success = registry.update_plugin_config(plugin_name, updates)
        
        if not success:
            raise HTTPException(status_code=400, detail="Failed to update plugin configuration")
        
        return {
            "success": True,
            "plugin_name": plugin_name,
            "updates_applied": updates,
            "message": "Plugin configuration updated successfully"
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Update plugin config error: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/admin/{plugin_name}/enable")
async def enable_plugin(plugin_name: str = Path(..., description="Plugin name")):
    """
    Enable a plugin
    """
    try:
        registry = get_registry()
        success = registry.enable_plugin(plugin_name)
        
        if not success:
            raise HTTPException(status_code=404, detail=f"Plugin '{plugin_name}' not found")
        
        return {
            "success": True,
            "plugin_name": plugin_name,
            "message": f"Plugin '{plugin_name}' enabled successfully"
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Enable plugin error: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/admin/{plugin_name}/disable")
async def disable_plugin(plugin_name: str = Path(..., description="Plugin name")):
    """
    Disable a plugin
    """
    try:
        registry = get_registry()
        success = registry.disable_plugin(plugin_name)
        
        if not success:
            raise HTTPException(status_code=404, detail=f"Plugin '{plugin_name}' not found")
        
        return {
            "success": True,
            "plugin_name": plugin_name,
            "message": f"Plugin '{plugin_name}' disabled successfully"
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Disable plugin error: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/admin/stats")
async def get_admin_stats():
    """
    Get comprehensive plugin system statistics for admin dashboard
    """
    try:
        manager = get_manager()
        stats = manager.get_manager_stats()
        
        return {
            "timestamp": datetime.now().isoformat(),
            "system_status": "operational",
            "statistics": stats
        }
        
    except Exception as e:
        logger.error(f"Get admin stats error: {e}")
        raise HTTPException(status_code=500, detail=str(e))


# Initialize plugins function to be called on startup
async def initialize_default_plugins():
    """Initialize the default plugins"""
    try:
        registry = get_registry()
        
        # Register default plugins
        plugins_to_register = [
            create_tripadvisor_plugin(),
            create_thai_news_plugin(),
            create_cultural_sites_plugin()
        ]
        
        for plugin in plugins_to_register:
            registry.register_plugin(type(plugin), plugin.config)
            logger.info(f"Registered plugin: {plugin.name}")
        
        # Initialize plugin manager
        manager = get_manager()
        init_results = await manager.initialize_all_plugins()
        
        logger.info(f"Plugin initialization results: {init_results}")
        
        return init_results
        
    except Exception as e:
        logger.error(f"Failed to initialize default plugins: {e}")
        raise


def create_plugin_routes() -> APIRouter:
    """Factory function to create plugin routes"""
    return router