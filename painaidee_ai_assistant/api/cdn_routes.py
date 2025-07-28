"""
API routes for CDN Management and Edge Distribution
Provides RESTful endpoints for CDN operations and global content delivery
"""

from fastapi import APIRouter, HTTPException, UploadFile, File, Form, Query
from typing import List, Optional, Dict, Any
from pydantic import BaseModel
import os
import tempfile

from models.cdn import cdn_manager


# Pydantic models for request/response
class CDNUploadRequest(BaseModel):
    asset_id: Optional[str] = None


class CDNAssetResponse(BaseModel):
    asset_id: str
    size: int
    content_type: str
    uploaded_at: str
    access_count: int
    cdn_locations: int


class OptimalURLResponse(BaseModel):
    primary_url: str
    fallback_urls: List[str]
    optimal_edge: Dict[str, str]
    cache_control: str
    content_hash: str


def create_cdn_routes(app):
    """Add CDN routes to FastAPI app"""
    
    @app.post("/api/cdn/upload")
    async def upload_to_cdn(
        asset_id: Optional[str] = Form(None),
        model_file: UploadFile = File(...)
    ):
        """Upload 3D model to CDN edge locations"""
        try:
            # Save uploaded file temporarily
            with tempfile.NamedTemporaryFile(delete=False, suffix=f"_{model_file.filename}") as temp_file:
                content = await model_file.read()
                temp_file.write(content)
                temp_path = temp_file.name
            
            try:
                # Upload to CDN
                result = await cdn_manager.upload_asset(temp_path, asset_id)
                
                return {
                    "message": "Asset uploaded to CDN successfully",
                    "upload_result": result,
                    "status": "success"
                }
                
            finally:
                # Clean up temp file
                os.unlink(temp_path)
                
        except FileNotFoundError as e:
            raise HTTPException(status_code=404, detail=str(e))
        except ValueError as e:
            raise HTTPException(status_code=400, detail=str(e))
        except Exception as e:
            raise HTTPException(status_code=500, detail=str(e))
    
    @app.get("/api/cdn/url/{asset_id}")
    async def get_optimal_url(
        asset_id: str,
        client_region: Optional[str] = Query(None, description="Client region (e.g., 'North America')"),
        client_ip: Optional[str] = Query(None, description="Client IP address")
    ):
        """Get optimal CDN URL for asset based on client location"""
        try:
            url_info = cdn_manager.get_optimal_url(asset_id, client_region, client_ip)
            
            return {
                "asset_id": asset_id,
                "url_info": OptimalURLResponse(
                    primary_url=url_info["primary_url"],
                    fallback_urls=url_info["fallback_urls"],
                    optimal_edge=url_info["optimal_edge"],
                    cache_control=url_info["cache_control"],
                    content_hash=url_info["content_hash"]
                ),
                "status": "success"
            }
            
        except ValueError as e:
            raise HTTPException(status_code=404, detail=str(e))
        except Exception as e:
            raise HTTPException(status_code=500, detail=str(e))
    
    @app.get("/api/cdn/assets")
    async def list_cdn_assets():
        """List all assets stored in CDN"""
        try:
            assets = []
            for asset_id, asset in cdn_manager.assets.items():
                assets.append(CDNAssetResponse(
                    asset_id=asset_id,
                    size=asset.size,
                    content_type=asset.content_type,
                    uploaded_at=asset.uploaded_at,
                    access_count=asset.access_count,
                    cdn_locations=len(asset.cdn_urls)
                ))
            
            return {
                "assets": assets,
                "count": len(assets),
                "total_size": sum(asset.size for asset in assets),
                "status": "success"
            }
            
        except Exception as e:
            raise HTTPException(status_code=500, detail=str(e))
    
    @app.get("/api/cdn/assets/{asset_id}")
    async def get_cdn_asset_info(asset_id: str):
        """Get detailed information about a CDN asset"""
        try:
            if asset_id not in cdn_manager.assets:
                raise HTTPException(status_code=404, detail="Asset not found")
            
            asset = cdn_manager.assets[asset_id]
            
            return {
                "asset": {
                    "asset_id": asset_id,
                    "original_path": asset.original_path,
                    "cdn_urls": asset.cdn_urls,
                    "content_hash": asset.content_hash,
                    "content_type": asset.content_type,
                    "size": asset.size,
                    "cache_control": asset.cache_control,
                    "uploaded_at": asset.uploaded_at,
                    "last_accessed": asset.last_accessed,
                    "access_count": asset.access_count
                },
                "status": "success"
            }
            
        except HTTPException:
            raise
        except Exception as e:
            raise HTTPException(status_code=500, detail=str(e))
    
    @app.get("/api/cdn/health")
    async def check_edge_health():
        """Perform health check on all CDN edge locations"""
        try:
            health_results = await cdn_manager.health_check_edges()
            
            return {
                "health_check": health_results,
                "status": "success"
            }
            
        except Exception as e:
            raise HTTPException(status_code=500, detail=str(e))
    
    @app.get("/api/cdn/edges")
    async def get_edge_status():
        """Get current status of all CDN edge locations"""
        try:
            edge_status = cdn_manager.get_edge_status()
            
            return {
                "edge_status": edge_status,
                "status": "success"
            }
            
        except Exception as e:
            raise HTTPException(status_code=500, detail=str(e))
    
    @app.post("/api/cdn/purge")
    async def purge_cdn_cache(asset_id: Optional[str] = None):
        """Purge CDN cache for specific asset or all assets"""
        try:
            purge_result = await cdn_manager.purge_cache(asset_id)
            
            return {
                "message": f"Cache purged successfully for {'all assets' if not asset_id else asset_id}",
                "purge_result": purge_result,
                "status": "success"
            }
            
        except ValueError as e:
            raise HTTPException(status_code=404, detail=str(e))
        except Exception as e:
            raise HTTPException(status_code=500, detail=str(e))
    
    @app.get("/api/cdn/analytics")
    async def get_cdn_analytics(
        asset_id: Optional[str] = Query(None, description="Specific asset ID"),
        days: int = Query(7, description="Number of days for analytics")
    ):
        """Get CDN analytics and usage statistics"""
        try:
            analytics = cdn_manager.get_analytics(asset_id, days)
            
            return {
                "analytics": analytics,
                "status": "success"
            }
            
        except ValueError as e:
            raise HTTPException(status_code=404, detail=str(e))
        except Exception as e:
            raise HTTPException(status_code=500, detail=str(e))
    
    @app.get("/api/cdn/config")
    async def get_cdn_config():
        """Get current CDN configuration"""
        try:
            return {
                "config": cdn_manager.config,
                "edge_count": len(cdn_manager.edge_locations),
                "healthy_edges": len([e for e in cdn_manager.edge_locations if e.is_healthy]),
                "total_assets": len(cdn_manager.assets),
                "status": "success"
            }
            
        except Exception as e:
            raise HTTPException(status_code=500, detail=str(e))
    
    @app.post("/api/cdn/config/update")
    async def update_cdn_config(config_update: Dict[str, Any]):
        """Update CDN configuration"""
        try:
            # Update configuration
            cdn_manager.config.update(config_update)
            
            # Save updated configuration
            with open(cdn_manager.config_file, 'w') as f:
                import json
                json.dump(cdn_manager.config, f, indent=2)
            
            return {
                "message": "CDN configuration updated successfully",
                "updated_config": cdn_manager.config,
                "status": "success"
            }
            
        except Exception as e:
            raise HTTPException(status_code=500, detail=str(e))
    
    @app.get("/api/cdn/performance")
    async def get_cdn_performance():
        """Get CDN performance metrics"""
        try:
            # Calculate performance metrics
            total_requests = sum(asset.access_count for asset in cdn_manager.assets.values())
            avg_edge_latency = None
            
            healthy_edges = [e for e in cdn_manager.edge_locations if e.is_healthy and e.latency_ms]
            if healthy_edges:
                avg_edge_latency = sum(e.latency_ms for e in healthy_edges) / len(healthy_edges)
            
            performance = {
                "timestamp": cdn_manager.health_check_interval,
                "total_requests": total_requests,
                "total_assets": len(cdn_manager.assets),
                "healthy_edges": len([e for e in cdn_manager.edge_locations if e.is_healthy]),
                "total_edges": len(cdn_manager.edge_locations),
                "average_edge_latency_ms": avg_edge_latency,
                "cache_hit_ratio": 0.95,  # Simulated - would be from CDN provider APIs
                "bandwidth_saved_gb": sum(asset.size for asset in cdn_manager.assets.values()) / (1024**3) * 0.7,
                "edge_performance": [
                    {
                        "edge_id": edge.id,
                        "name": edge.name,
                        "region": edge.region,
                        "healthy": edge.is_healthy,
                        "latency_ms": edge.latency_ms,
                        "priority": edge.priority
                    }
                    for edge in cdn_manager.edge_locations
                ]
            }
            
            return {
                "performance": performance,
                "status": "success"
            }
            
        except Exception as e:
            raise HTTPException(status_code=500, detail=str(e))