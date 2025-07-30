"""
Admin routes for plugin management
Additional admin endpoints for comprehensive plugin management
"""

from fastapi import APIRouter, HTTPException
from typing import Dict, Any, List

from plugins.registry import get_registry
from plugins.manager import get_manager

# Create admin router
admin_router = APIRouter(prefix="/admin/plugins", tags=["Plugin Admin"])

@admin_router.get("/")
async def admin_plugin_dashboard():
    """Admin dashboard for plugin management"""
    try:
        registry = get_registry()
        manager = get_manager()
        
        stats = registry.get_registry_stats()
        manager_stats = manager.get_manager_stats()
        
        return {
            "title": "PaiNaiDee Plugin Administration",
            "system_overview": {
                "total_plugins": stats["total_plugins"],
                "enabled_plugins": stats["enabled_plugins"],
                "active_instances": stats["active_instances"],
                "system_status": "operational"
            },
            "available_actions": {
                "add_plugin": "/admin/plugins/add",
                "list_plugins": "/admin/plugins/list",
                "manage_plugin": "/admin/plugins/{plugin_name}",
                "disable_plugin": "/admin/plugins/{plugin_name}/disable",
                "enable_plugin": "/admin/plugins/{plugin_name}/enable"
            },
            "plugin_statistics": stats,
            "manager_info": manager_stats
        }
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@admin_router.get("/list")
async def admin_list_plugins():
    """
    List all plugins with detailed admin information
    Equivalent to: /admin/plugins/list
    """
    try:
        registry = get_registry()
        stats = registry.get_registry_stats()
        
        # Add admin-specific information
        for plugin in stats["plugins"]:
            plugin["admin_actions"] = {
                "disable": f"/admin/plugins/{plugin['name']}/disable",
                "enable": f"/admin/plugins/{plugin['name']}/enable",
                "configure": f"/admin/plugins/{plugin['name']}/config",
                "status": f"/admin/plugins/{plugin['name']}/status"
            }
        
        return {
            "plugins": stats["plugins"],
            "summary": {
                "total": stats["total_plugins"],
                "enabled": stats["enabled_plugins"],
                "active": stats["active_instances"],
                "available_intents": list(set(
                    intent for plugin in stats["plugins"] 
                    for intent in plugin.get("intents", [])
                ))
            }
        }
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@admin_router.post("/add")
async def admin_add_plugin():
    """
    Add a new plugin (placeholder for future extensibility)
    Equivalent to: /admin/plugins/add
    """
    return {
        "message": "Plugin addition interface",
        "status": "not_implemented",
        "note": "In the current implementation, plugins are registered at startup. Future versions will support dynamic plugin loading.",
        "supported_plugins": [
            {
                "name": "tripadvisor",
                "description": "TripAdvisor/Google Reviews integration",
                "status": "available"
            },
            {
                "name": "thai_news", 
                "description": "Thai news sources integration",
                "status": "available"
            },
            {
                "name": "cultural_sites",
                "description": "Department of Fine Arts integration", 
                "status": "available"
            }
        ],
        "future_plugins": [
            {
                "name": "youtube_travel",
                "description": "YouTube Travel content integration",
                "status": "planned"
            },
            {
                "name": "tiktok_travel",
                "description": "TikTok Travel content integration", 
                "status": "planned"
            },
            {
                "name": "tat_official",
                "description": "Tourism Authority of Thailand official data",
                "status": "planned"
            }
        ]
    }


@admin_router.get("/{plugin_name}")
async def admin_get_plugin_details(plugin_name: str):
    """Get detailed plugin information for admin purposes"""
    try:
        registry = get_registry()
        config = registry.get_plugin_config(plugin_name)
        instance = registry.get_plugin_instance(plugin_name)
        
        if not config:
            raise HTTPException(status_code=404, detail=f"Plugin '{plugin_name}' not found")
        
        plugin_details = {
            "name": plugin_name,
            "configuration": {
                "description": config.description,
                "version": config.version,
                "enabled": config.enabled,
                "timeout": config.timeout,
                "cache_ttl": config.cache_ttl,
                "rate_limit": config.rate_limit,
                "intents": config.intents,
                "base_url": config.base_url,
                "headers": config.headers
            },
            "runtime_status": {
                "has_instance": instance is not None,
                "status": instance.status.value if instance else "not_instantiated"
            },
            "admin_actions": {
                "enable": f"/admin/plugins/{plugin_name}/enable",
                "disable": f"/admin/plugins/{plugin_name}/disable", 
                "configure": f"/admin/plugins/{plugin_name}/config",
                "test": f"/plugin/execute"
            }
        }
        
        if instance:
            plugin_details["statistics"] = instance.get_stats()
            
        return plugin_details
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@admin_router.delete("/{plugin_name}")
async def admin_remove_plugin(plugin_name: str):
    """Remove a plugin from the registry"""
    try:
        registry = get_registry()
        success = registry.unregister_plugin(plugin_name)
        
        if not success:
            raise HTTPException(status_code=404, detail=f"Plugin '{plugin_name}' not found")
        
        return {
            "success": True,
            "plugin_name": plugin_name,
            "message": f"Plugin '{plugin_name}' removed successfully",
            "warning": "Plugin has been unregistered. Restart server to reload default plugins."
        }
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


def create_admin_plugin_routes() -> APIRouter:
    """Factory function to create admin plugin routes"""
    return admin_router