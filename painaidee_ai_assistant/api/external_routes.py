"""
API routes for External Platform Integration
Provides RESTful endpoints for discovering and importing models from external platforms
"""

from fastapi import APIRouter, HTTPException, Query, Form
from typing import List, Optional, Dict, Any
from pydantic import BaseModel

from models.external_apis import external_api_manager, SearchFilter, ExternalModel


# Pydantic models for request/response
class SearchRequest(BaseModel):
    query: str = ""
    categories: Optional[List[str]] = None
    file_formats: Optional[List[str]] = None
    licenses: Optional[List[str]] = None
    max_file_size: Optional[int] = None
    min_rating: Optional[float] = None
    free_only: bool = True
    sort_by: str = "relevance"
    limit: int = 20


class DownloadRequest(BaseModel):
    platform: str
    external_id: str
    local_path: Optional[str] = None


class ModerationRequest(BaseModel):
    model_key: str
    approved: bool
    notes: str = ""


def create_external_api_routes(app):
    """Add external API integration routes to FastAPI app"""
    
    @app.post("/api/external/search")
    async def search_external_models(request: SearchRequest):
        """Search for models across all external platforms"""
        try:
            search_filter = SearchFilter(
                query=request.query,
                categories=request.categories,
                file_formats=request.file_formats,
                licenses=request.licenses,
                max_file_size=request.max_file_size,
                min_rating=request.min_rating,
                free_only=request.free_only,
                sort_by=request.sort_by,
                limit=request.limit
            )
            
            # Get unified search results
            models = await external_api_manager.get_unified_search_results(search_filter)
            
            return {
                "query": request.query,
                "total_results": len(models),
                "models": [
                    {
                        "platform": model.platform,
                        "external_id": model.external_id,
                        "name": model.name,
                        "description": model.description,
                        "author": model.author,
                        "thumbnail_url": model.thumbnail_url,
                        "view_url": model.view_url,
                        "file_format": model.file_format,
                        "file_size": model.file_size,
                        "license": model.license,
                        "tags": model.tags or [],
                        "categories": model.categories or [],
                        "rating": model.rating,
                        "download_count": model.download_count,
                        "is_free": model.is_free,
                        "created_at": model.created_at
                    }
                    for model in models
                ],
                "status": "success"
            }
            
        except Exception as e:
            raise HTTPException(status_code=500, detail=str(e))
    
    @app.get("/api/external/search/platforms")
    async def search_by_platforms(
        query: str = Query("", description="Search query"),
        platforms: List[str] = Query([], description="Specific platforms to search"),
        limit: int = Query(20, description="Maximum results per platform")
    ):
        """Search models on specific platforms separately"""
        try:
            search_filter = SearchFilter(query=query, limit=limit)
            
            if platforms:
                # Override enabled platforms temporarily
                original_platforms = external_api_manager.config["enabled_platforms"]
                external_api_manager.config["enabled_platforms"] = platforms
            
            try:
                platform_results = await external_api_manager.search_all_platforms(search_filter)
            finally:
                # Restore original platforms
                if platforms:
                    external_api_manager.config["enabled_platforms"] = original_platforms
            
            return {
                "query": query,
                "platform_results": {
                    platform: [
                        {
                            "platform": model.platform,
                            "external_id": model.external_id,
                            "name": model.name,
                            "description": model.description,
                            "thumbnail_url": model.thumbnail_url,
                            "rating": model.rating,
                            "is_free": model.is_free
                        }
                        for model in models
                    ]
                    for platform, models in platform_results.items()
                },
                "total_by_platform": {
                    platform: len(models) for platform, models in platform_results.items()
                },
                "status": "success"
            }
            
        except Exception as e:
            raise HTTPException(status_code=500, detail=str(e))
    
    @app.get("/api/external/model/{platform}/{external_id}")
    async def get_external_model_details(platform: str, external_id: str):
        """Get detailed information about a specific external model"""
        try:
            connector = external_api_manager.connectors.get(platform)
            if not connector:
                raise HTTPException(status_code=404, detail=f"Platform {platform} not supported")
            
            model = await connector.get_model_details(external_id)
            if not model:
                raise HTTPException(status_code=404, detail="Model not found")
            
            return {
                "model": {
                    "platform": model.platform,
                    "external_id": model.external_id,
                    "name": model.name,
                    "description": model.description,
                    "author": model.author,
                    "thumbnail_url": model.thumbnail_url,
                    "download_url": model.download_url,
                    "view_url": model.view_url,
                    "file_format": model.file_format,
                    "file_size": model.file_size,
                    "license": model.license,
                    "tags": model.tags or [],
                    "categories": model.categories or [],
                    "rating": model.rating,
                    "download_count": model.download_count,
                    "is_free": model.is_free,
                    "created_at": model.created_at,
                    "updated_at": model.updated_at
                },
                "status": "success"
            }
            
        except HTTPException:
            raise
        except Exception as e:
            raise HTTPException(status_code=500, detail=str(e))
    
    @app.post("/api/external/download")
    async def download_external_model(request: DownloadRequest):
        """Download a model from an external platform"""
        try:
            # First get the model details
            connector = external_api_manager.connectors.get(request.platform)
            if not connector:
                raise HTTPException(status_code=404, detail=f"Platform {request.platform} not supported")
            
            model = await connector.get_model_details(request.external_id)
            if not model:
                raise HTTPException(status_code=404, detail="Model not found")
            
            # Download the model
            result = await external_api_manager.download_model(model, request.local_path)
            
            return {
                "download_result": result,
                "model_info": {
                    "name": model.name,
                    "platform": model.platform,
                    "external_id": model.external_id,
                    "file_format": model.file_format
                },
                "status": "success"
            }
            
        except HTTPException:
            raise
        except Exception as e:
            raise HTTPException(status_code=500, detail=str(e))
    
    @app.get("/api/external/downloads")
    async def list_downloaded_models(
        status: Optional[str] = Query(None, description="Filter by status: pending_moderation, approved, rejected")
    ):
        """List all downloaded models"""
        try:
            models = external_api_manager.get_downloaded_models(status)
            
            return {
                "downloaded_models": models,
                "count": len(models),
                "filter_status": status,
                "status": "success"
            }
            
        except Exception as e:
            raise HTTPException(status_code=500, detail=str(e))
    
    @app.post("/api/external/moderate")
    async def moderate_downloaded_model(request: ModerationRequest):
        """Moderate a downloaded model (approve or reject)"""
        try:
            result = external_api_manager.moderate_model(
                model_key=request.model_key,
                approved=request.approved,
                notes=request.notes
            )
            
            return result
            
        except Exception as e:
            raise HTTPException(status_code=500, detail=str(e))
    
    @app.get("/api/external/platforms")
    async def get_platform_info():
        """Get information about supported external platforms"""
        try:
            return {
                "platforms": {
                    "sketchfab": {
                        "name": "Sketchfab",
                        "description": "Community platform for 3D models",
                        "supported_formats": ["fbx", "obj", "dae", "3ds", "blend"],
                        "requires_auth": True,
                        "free_models_available": True,
                        "api_status": "available" if external_api_manager.connectors["sketchfab"].api_token else "no_token"
                    },
                    "open3d": {
                        "name": "Open3D",
                        "description": "Academic and research 3D models",
                        "supported_formats": ["ply", "obj", "off"],
                        "requires_auth": False,
                        "free_models_available": True,
                        "api_status": "available"
                    }
                },
                "enabled_platforms": external_api_manager.config.get("enabled_platforms", []),
                "status": "success"
            }
            
        except Exception as e:
            raise HTTPException(status_code=500, detail=str(e))
    
    @app.get("/api/external/stats")
    async def get_external_integration_stats():
        """Get statistics about external platform integration"""
        try:
            stats = external_api_manager.get_platform_stats()
            
            return {
                "integration_stats": stats,
                "status": "success"
            }
            
        except Exception as e:
            raise HTTPException(status_code=500, detail=str(e))
    
    @app.post("/api/external/config/update")
    async def update_external_config(config_update: Dict[str, Any]):
        """Update external API configuration"""
        try:
            # Update configuration
            external_api_manager.config.update(config_update)
            
            # Save updated configuration
            with open(external_api_manager.config_file, 'w') as f:
                import json
                json.dump(external_api_manager.config, f, indent=2)
            
            return {
                "message": "External API configuration updated successfully",
                "updated_config": external_api_manager.config,
                "status": "success"
            }
            
        except Exception as e:
            raise HTTPException(status_code=500, detail=str(e))
    
    @app.delete("/api/external/cache/clear")
    async def clear_search_cache():
        """Clear external platform search cache"""
        try:
            cache_size = len(external_api_manager.search_cache)
            external_api_manager.search_cache.clear()
            
            return {
                "message": f"Cleared {cache_size} cached search results",
                "status": "success"
            }
            
        except Exception as e:
            raise HTTPException(status_code=500, detail=str(e))
    
    @app.get("/api/external/trending")
    async def get_trending_models():
        """Get trending models from external platforms"""
        try:
            # Search for trending/popular models
            trending_filter = SearchFilter(
                query="",
                sort_by="popularity",
                limit=20,
                free_only=True
            )
            
            models = await external_api_manager.get_unified_search_results(trending_filter)
            
            return {
                "trending_models": [
                    {
                        "platform": model.platform,
                        "external_id": model.external_id,
                        "name": model.name,
                        "author": model.author,
                        "thumbnail_url": model.thumbnail_url,
                        "rating": model.rating,
                        "download_count": model.download_count,
                        "tags": model.tags or []
                    }
                    for model in models
                ],
                "count": len(models),
                "status": "success"
            }
            
        except Exception as e:
            raise HTTPException(status_code=500, detail=str(e))
    
    @app.get("/api/external/categories")
    async def get_popular_categories():
        """Get popular categories from external platforms"""
        try:
            # This would normally aggregate from actual API calls
            # For now, return common categories
            categories = {
                "sketchfab": [
                    "Architecture", "Characters", "Animals", "Vehicles", 
                    "Furniture", "Nature", "Weapons", "Buildings", 
                    "Electronics", "Food & Drink"
                ],
                "open3d": [
                    "Academic", "Research", "Benchmarks", "Test Models",
                    "Point Clouds", "Meshes", "Surfaces"
                ]
            }
            
            return {
                "categories_by_platform": categories,
                "all_categories": list(set([cat for cats in categories.values() for cat in cats])),
                "status": "success"
            }
            
        except Exception as e:
            raise HTTPException(status_code=500, detail=str(e))