"""
Edge CDN Support for Global 3D Model Distribution
Provides CDN integration for low-latency, global delivery of 3D assets
"""

import os
import json
import time
import hashlib
import requests
from typing import Dict, List, Optional, Any
from dataclasses import dataclass, asdict
from pathlib import Path
from datetime import datetime, timedelta
import asyncio
import aiohttp


@dataclass
class CDNEdgeLocation:
    """Represents a CDN edge location"""
    id: str
    name: str
    region: str
    endpoint: str
    priority: int
    latency_ms: Optional[float] = None
    is_healthy: bool = True
    last_health_check: Optional[str] = None


@dataclass
class CDNAsset:
    """Represents an asset stored in CDN"""
    asset_id: str
    original_path: str
    cdn_urls: Dict[str, str]  # edge_location_id -> URL
    content_hash: str
    content_type: str
    size: int
    cache_control: str
    uploaded_at: str
    last_accessed: Optional[str] = None
    access_count: int = 0


class CDNManager:
    """Manages CDN distribution and edge routing for 3D models"""
    
    def __init__(self, config_file: str = "cdn_config.json"):
        self.config_file = Path(config_file)
        self.config = self._load_config()
        self.edge_locations = self._load_edge_locations()
        self.assets = self._load_assets()
        self.health_check_interval = 300  # 5 minutes
        
    def _load_config(self) -> Dict[str, Any]:
        """Load CDN configuration"""
        default_config = {
            "enabled": True,
            "primary_provider": "cloudflare",
            "fallback_provider": "aws_cloudfront",
            "cache_ttl": 86400,  # 24 hours
            "max_file_size": 100 * 1024 * 1024,  # 100MB
            "allowed_types": ["fbx", "gltf", "glb", "obj", "dae"],
            "compression": {
                "enabled": True,
                "gzip": True,
                "brotli": True
            },
            "purge_on_update": True,
            "monitoring": {
                "enabled": True,
                "alert_threshold_ms": 1000
            }
        }
        
        if self.config_file.exists():
            try:
                with open(self.config_file, 'r') as f:
                    loaded_config = json.load(f)
                    default_config.update(loaded_config)
            except Exception as e:
                print(f"Error loading CDN config: {e}")
        
        return default_config
    
    def _load_edge_locations(self) -> List[CDNEdgeLocation]:
        """Load and initialize edge locations"""
        return [
            CDNEdgeLocation(
                id="us-east-1",
                name="US East (Virginia)",
                region="North America",
                endpoint="https://us-east-1.cdn.painaidee.com",
                priority=1
            ),
            CDNEdgeLocation(
                id="us-west-1",
                name="US West (California)",
                region="North America",
                endpoint="https://us-west-1.cdn.painaidee.com",
                priority=2
            ),
            CDNEdgeLocation(
                id="eu-west-1",
                name="Europe (Ireland)",
                region="Europe",
                endpoint="https://eu-west-1.cdn.painaidee.com",
                priority=1
            ),
            CDNEdgeLocation(
                id="ap-southeast-1",
                name="Asia Pacific (Singapore)",
                region="Asia",
                endpoint="https://ap-southeast-1.cdn.painaidee.com",
                priority=1
            ),
            CDNEdgeLocation(
                id="ap-southeast-2", 
                name="Asia Pacific (Sydney)",
                region="Oceania",
                endpoint="https://ap-southeast-2.cdn.painaidee.com",
                priority=2
            )
        ]
    
    def _load_assets(self) -> Dict[str, CDNAsset]:
        """Load CDN asset metadata"""
        assets_file = Path("cdn_assets.json")
        if assets_file.exists():
            try:
                with open(assets_file, 'r') as f:
                    data = json.load(f)
                    return {k: CDNAsset(**v) for k, v in data.items()}
            except Exception as e:
                print(f"Error loading CDN assets: {e}")
        return {}
    
    def _save_assets(self):
        """Save CDN asset metadata"""
        try:
            with open("cdn_assets.json", 'w') as f:
                serializable_assets = {k: asdict(v) for k, v in self.assets.items()}
                json.dump(serializable_assets, f, indent=2)
        except Exception as e:
            print(f"Error saving CDN assets: {e}")
    
    def _calculate_file_hash(self, file_path: str) -> str:
        """Calculate content hash for cache validation"""
        sha256_hash = hashlib.sha256()
        with open(file_path, "rb") as f:
            for chunk in iter(lambda: f.read(4096), b""):
                sha256_hash.update(chunk)
        return sha256_hash.hexdigest()
    
    def _get_content_type(self, file_path: str) -> str:
        """Determine content type from file extension"""
        ext = Path(file_path).suffix.lower()
        content_types = {
            '.fbx': 'model/fbx',
            '.gltf': 'model/gltf+json',
            '.glb': 'model/gltf-binary',
            '.obj': 'model/obj',
            '.dae': 'model/vnd.collada+xml',
            '.mtl': 'text/plain',
            '.jpg': 'image/jpeg',
            '.jpeg': 'image/jpeg',
            '.png': 'image/png',
            '.webp': 'image/webp'
        }
        return content_types.get(ext, 'application/octet-stream')
    
    async def upload_asset(self, file_path: str, asset_id: str = None) -> Dict[str, Any]:
        """Upload asset to CDN edge locations"""
        if not os.path.exists(file_path):
            raise FileNotFoundError(f"File not found: {file_path}")
        
        file_size = os.path.getsize(file_path)
        if file_size > self.config["max_file_size"]:
            raise ValueError(f"File too large: {file_size} bytes")
        
        if asset_id is None:
            asset_id = Path(file_path).stem
        
        content_hash = self._calculate_file_hash(file_path)
        content_type = self._get_content_type(file_path)
        
        # Check if asset already exists with same content
        if asset_id in self.assets and self.assets[asset_id].content_hash == content_hash:
            return {
                "status": "exists",
                "message": "Asset already exists with same content",
                "asset_id": asset_id,
                "cdn_urls": self.assets[asset_id].cdn_urls
            }
        
        # Upload to edge locations
        cdn_urls = {}
        upload_results = {}
        
        for edge in self.edge_locations:
            if not edge.is_healthy:
                continue
            
            try:
                # Simulate CDN upload (in real implementation, use actual CDN APIs)
                url = f"{edge.endpoint}/assets/{asset_id}"
                cdn_urls[edge.id] = url
                upload_results[edge.id] = {"status": "success", "url": url}
                
            except Exception as e:
                upload_results[edge.id] = {"status": "error", "error": str(e)}
        
        if not cdn_urls:
            raise Exception("Failed to upload to any edge location")
        
        # Create asset record
        cdn_asset = CDNAsset(
            asset_id=asset_id,
            original_path=file_path,
            cdn_urls=cdn_urls,
            content_hash=content_hash,
            content_type=content_type,
            size=file_size,
            cache_control=f"public, max-age={self.config['cache_ttl']}",
            uploaded_at=datetime.now().isoformat()
        )
        
        self.assets[asset_id] = cdn_asset
        self._save_assets()
        
        return {
            "status": "uploaded",
            "message": "Asset uploaded successfully",
            "asset_id": asset_id,
            "cdn_urls": cdn_urls,
            "upload_results": upload_results,
            "content_hash": content_hash
        }
    
    def get_optimal_url(self, asset_id: str, client_region: str = None, 
                       client_ip: str = None) -> Dict[str, Any]:
        """Get optimal CDN URL based on client location and edge health"""
        if asset_id not in self.assets:
            raise ValueError(f"Asset not found: {asset_id}")
        
        asset = self.assets[asset_id]
        
        # Update access statistics
        asset.last_accessed = datetime.now().isoformat()
        asset.access_count += 1
        self._save_assets()
        
        # Determine optimal edge location
        optimal_edge = self._select_optimal_edge(client_region, client_ip)
        
        # Get URL from optimal edge
        if optimal_edge.id in asset.cdn_urls:
            primary_url = asset.cdn_urls[optimal_edge.id]
        else:
            # Fallback to first available URL
            primary_url = next(iter(asset.cdn_urls.values()))
        
        # Provide fallback URLs
        fallback_urls = [url for edge_id, url in asset.cdn_urls.items() 
                        if edge_id != optimal_edge.id]
        
        return {
            "primary_url": primary_url,
            "fallback_urls": fallback_urls,
            "optimal_edge": {
                "id": optimal_edge.id,
                "name": optimal_edge.name,
                "region": optimal_edge.region
            },
            "cache_control": asset.cache_control,
            "content_hash": asset.content_hash,
            "last_modified": asset.uploaded_at
        }
    
    def _select_optimal_edge(self, client_region: str = None, 
                           client_ip: str = None) -> CDNEdgeLocation:
        """Select optimal edge location based on client and edge health"""
        healthy_edges = [edge for edge in self.edge_locations if edge.is_healthy]
        
        if not healthy_edges:
            # Return first edge as fallback
            return self.edge_locations[0]
        
        # If client region is specified, prefer edges in same region
        if client_region:
            region_edges = [edge for edge in healthy_edges 
                          if edge.region.lower() == client_region.lower()]
            if region_edges:
                # Sort by priority and latency
                return min(region_edges, key=lambda e: (e.priority, e.latency_ms or 0))
        
        # Default: select by priority and latency
        return min(healthy_edges, key=lambda e: (e.priority, e.latency_ms or 0))
    
    async def health_check_edges(self) -> Dict[str, Any]:
        """Perform health check on all edge locations"""
        health_results = {}
        
        async with aiohttp.ClientSession() as session:
            tasks = []
            for edge in self.edge_locations:
                task = self._check_edge_health(session, edge)
                tasks.append(task)
            
            results = await asyncio.gather(*tasks, return_exceptions=True)
            
            for edge, result in zip(self.edge_locations, results):
                if isinstance(result, Exception):
                    health_results[edge.id] = {
                        "healthy": False,
                        "error": str(result),
                        "latency_ms": None
                    }
                    edge.is_healthy = False
                else:
                    health_results[edge.id] = result
                    edge.is_healthy = result["healthy"]
                    edge.latency_ms = result["latency_ms"]
                
                edge.last_health_check = datetime.now().isoformat()
        
        return {
            "timestamp": datetime.now().isoformat(),
            "results": health_results,
            "healthy_edges": len([r for r in health_results.values() if r["healthy"]]),
            "total_edges": len(self.edge_locations)
        }
    
    async def _check_edge_health(self, session: aiohttp.ClientSession, 
                                edge: CDNEdgeLocation) -> Dict[str, Any]:
        """Check health of a single edge location"""
        try:
            start_time = time.time()
            
            # Perform health check (ping endpoint)
            health_url = f"{edge.endpoint}/health"
            
            async with session.get(health_url, timeout=5) as response:
                latency_ms = (time.time() - start_time) * 1000
                
                if response.status == 200:
                    return {
                        "healthy": True,
                        "latency_ms": latency_ms,
                        "status_code": response.status
                    }
                else:
                    return {
                        "healthy": False,
                        "latency_ms": latency_ms,
                        "status_code": response.status
                    }
                    
        except Exception as e:
            return {
                "healthy": False,
                "latency_ms": None,
                "error": str(e)
            }
    
    async def purge_cache(self, asset_id: str = None) -> Dict[str, Any]:
        """Purge CDN cache for specific asset or all assets"""
        purge_results = {}
        
        if asset_id:
            if asset_id not in self.assets:
                raise ValueError(f"Asset not found: {asset_id}")
            assets_to_purge = [asset_id]
        else:
            assets_to_purge = list(self.assets.keys())
        
        for edge in self.edge_locations:
            if not edge.is_healthy:
                continue
            
            try:
                # Simulate cache purge (use actual CDN APIs in production)
                purged_urls = []
                for aid in assets_to_purge:
                    if aid in self.assets and edge.id in self.assets[aid].cdn_urls:
                        purged_urls.append(self.assets[aid].cdn_urls[edge.id])
                
                purge_results[edge.id] = {
                    "status": "success",
                    "purged_urls": purged_urls,
                    "count": len(purged_urls)
                }
                
            except Exception as e:
                purge_results[edge.id] = {
                    "status": "error",
                    "error": str(e)
                }
        
        return {
            "timestamp": datetime.now().isoformat(),
            "asset_id": asset_id,
            "purge_results": purge_results,
            "total_purged": sum(r.get("count", 0) for r in purge_results.values())
        }
    
    def get_analytics(self, asset_id: str = None, 
                     days: int = 7) -> Dict[str, Any]:
        """Get CDN analytics and usage statistics"""
        analytics = {
            "period": f"Last {days} days",
            "timestamp": datetime.now().isoformat(),
            "total_assets": len(self.assets),
            "total_storage": sum(asset.size for asset in self.assets.values()),
            "total_requests": sum(asset.access_count for asset in self.assets.values()),
            "edge_locations": len(self.edge_locations),
            "healthy_edges": len([e for e in self.edge_locations if e.is_healthy])
        }
        
        if asset_id:
            if asset_id not in self.assets:
                raise ValueError(f"Asset not found: {asset_id}")
            
            asset = self.assets[asset_id]
            analytics["asset"] = {
                "id": asset_id,
                "size": asset.size,
                "access_count": asset.access_count,
                "last_accessed": asset.last_accessed,
                "cdn_locations": len(asset.cdn_urls),
                "content_type": asset.content_type
            }
        else:
            # Top assets by access count
            sorted_assets = sorted(self.assets.items(), 
                                 key=lambda x: x[1].access_count, reverse=True)
            analytics["top_assets"] = [
                {
                    "asset_id": aid,
                    "access_count": asset.access_count,
                    "size": asset.size
                }
                for aid, asset in sorted_assets[:10]
            ]
        
        return analytics
    
    def get_edge_status(self) -> Dict[str, Any]:
        """Get current status of all edge locations"""
        return {
            "timestamp": datetime.now().isoformat(),
            "edges": [
                {
                    "id": edge.id,
                    "name": edge.name,
                    "region": edge.region,
                    "endpoint": edge.endpoint,
                    "healthy": edge.is_healthy,
                    "latency_ms": edge.latency_ms,
                    "priority": edge.priority,
                    "last_check": edge.last_health_check
                }
                for edge in self.edge_locations
            ]
        }


# Initialize global CDN manager
cdn_manager = CDNManager()