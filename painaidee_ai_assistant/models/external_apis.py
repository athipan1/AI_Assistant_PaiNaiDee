"""
External API Integration for 3D Model Platforms
Integrates with Sketchfab, Open3D, and other platforms for real-time gallery enrichment
"""

import os
import json
import aiohttp
import asyncio
from typing import Dict, List, Optional, Any, Union
from dataclasses import dataclass, asdict
from datetime import datetime, timedelta
from pathlib import Path
import hashlib
import tempfile
from urllib.parse import urljoin, quote


@dataclass
class ExternalModel:
    """Represents a 3D model from external platforms"""
    platform: str  # sketchfab, open3d, etc.
    external_id: str
    name: str
    description: str
    author: str
    thumbnail_url: str
    download_url: str
    view_url: str
    file_format: str
    file_size: Optional[int] = None
    license: str = "unknown"
    tags: List[str] = None
    categories: List[str] = None
    rating: Optional[float] = None
    download_count: int = 0
    is_free: bool = True
    created_at: Optional[str] = None
    updated_at: Optional[str] = None


@dataclass
class SearchFilter:
    """Search filters for external model discovery"""
    query: str = ""
    categories: List[str] = None
    file_formats: List[str] = None
    licenses: List[str] = None
    max_file_size: Optional[int] = None
    min_rating: Optional[float] = None
    free_only: bool = True
    sort_by: str = "relevance"  # relevance, popularity, date, rating
    limit: int = 20


class SketchfabConnector:
    """Connector for Sketchfab API"""
    
    def __init__(self, api_token: str = None):
        self.api_token = api_token or os.getenv("SKETCHFAB_API_TOKEN")
        self.base_url = "https://api.sketchfab.com/v3"
        self.headers = {
            "Authorization": f"Token {self.api_token}" if self.api_token else None,
            "User-Agent": "PaiNaiDee-3D-Platform/1.0"
        }
    
    async def search_models(self, search_filter: SearchFilter) -> List[ExternalModel]:
        """Search for models on Sketchfab"""
        if not self.api_token:
            print("Warning: No Sketchfab API token provided")
            return []
        
        try:
            params = {
                "q": search_filter.query,
                "count": min(search_filter.limit, 100),
                "sort_by": self._map_sort_field(search_filter.sort_by)
            }
            
            if search_filter.categories:
                params["categories"] = ",".join(search_filter.categories)
            
            if search_filter.free_only:
                params["downloadable"] = "true"
            
            async with aiohttp.ClientSession() as session:
                async with session.get(
                    f"{self.base_url}/models",
                    headers=self.headers,
                    params=params
                ) as response:
                    if response.status == 200:
                        data = await response.json()
                        return self._parse_sketchfab_models(data.get("results", []))
                    else:
                        print(f"Sketchfab API error: {response.status}")
                        return []
                        
        except Exception as e:
            print(f"Error searching Sketchfab: {e}")
            return []
    
    def _map_sort_field(self, sort_by: str) -> str:
        """Map generic sort field to Sketchfab specific field"""
        mapping = {
            "relevance": "relevance",
            "popularity": "viewCount",
            "date": "publishedAt",
            "rating": "likeCount"
        }
        return mapping.get(sort_by, "relevance")
    
    def _parse_sketchfab_models(self, models_data: List[Dict]) -> List[ExternalModel]:
        """Parse Sketchfab API response into ExternalModel objects"""
        models = []
        
        for model_data in models_data:
            try:
                # Extract thumbnail URL
                thumbnails = model_data.get("thumbnails", {}).get("images", [])
                thumbnail_url = thumbnails[0]["url"] if thumbnails else ""
                
                # Check if downloadable
                download_url = ""
                is_downloadable = model_data.get("isDownloadable", False)
                if is_downloadable and "archives" in model_data:
                    archives = model_data["archives"]
                    if archives:
                        download_url = archives[0].get("url", "")
                
                model = ExternalModel(
                    platform="sketchfab",
                    external_id=model_data["uid"],
                    name=model_data.get("name", "Untitled"),
                    description=model_data.get("description", ""),
                    author=model_data.get("user", {}).get("displayName", "Unknown"),
                    thumbnail_url=thumbnail_url,
                    download_url=download_url,
                    view_url=f"https://sketchfab.com/3d-models/{model_data['uid']}",
                    file_format="unknown",
                    license=model_data.get("license", {}).get("label", "unknown"),
                    tags=model_data.get("tags", []),
                    categories=[cat["name"] for cat in model_data.get("categories", [])],
                    rating=model_data.get("likeCount", 0) / 100.0,  # Normalize to 0-1
                    download_count=model_data.get("downloadCount", 0),
                    is_free=is_downloadable,
                    created_at=model_data.get("publishedAt"),
                    updated_at=model_data.get("updatedAt")
                )
                
                models.append(model)
                
            except Exception as e:
                print(f"Error parsing Sketchfab model: {e}")
                continue
        
        return models
    
    async def get_model_details(self, model_id: str) -> Optional[ExternalModel]:
        """Get detailed information about a specific model"""
        if not self.api_token:
            return None
        
        try:
            async with aiohttp.ClientSession() as session:
                async with session.get(
                    f"{self.base_url}/models/{model_id}",
                    headers=self.headers
                ) as response:
                    if response.status == 200:
                        data = await response.json()
                        models = self._parse_sketchfab_models([data])
                        return models[0] if models else None
                    
        except Exception as e:
            print(f"Error getting Sketchfab model details: {e}")
        
        return None


class Open3DConnector:
    """Connector for Open3D model repository"""
    
    def __init__(self):
        self.base_url = "https://open3d.org/api/v1"
        self.headers = {
            "User-Agent": "PaiNaiDee-3D-Platform/1.0"
        }
    
    async def search_models(self, search_filter: SearchFilter) -> List[ExternalModel]:
        """Search for models in Open3D repository"""
        # Note: This is a simplified implementation
        # In practice, Open3D might not have a public API or might require different authentication
        
        try:
            # Simulate Open3D search results
            sample_models = [
                {
                    "id": "open3d_bunny",
                    "name": "Stanford Bunny",
                    "description": "Classic 3D test model - Stanford Bunny mesh",
                    "author": "Stanford Graphics Lab",
                    "file_format": "ply",
                    "file_size": 1048576,
                    "tags": ["test", "classic", "mesh", "bunny"],
                    "license": "academic"
                },
                {
                    "id": "open3d_teapot",
                    "name": "Utah Teapot",
                    "description": "Classic Utah teapot reference model",
                    "author": "Martin Newell",
                    "file_format": "obj",
                    "file_size": 524288,
                    "tags": ["test", "classic", "teapot"],
                    "license": "public_domain"
                }
            ]
            
            models = []
            for model_data in sample_models:
                if search_filter.query.lower() in model_data["name"].lower():
                    model = ExternalModel(
                        platform="open3d",
                        external_id=model_data["id"],
                        name=model_data["name"],
                        description=model_data["description"],
                        author=model_data["author"],
                        thumbnail_url=f"https://open3d.org/thumbnails/{model_data['id']}.jpg",
                        download_url=f"https://open3d.org/models/{model_data['id']}.{model_data['file_format']}",
                        view_url=f"https://open3d.org/models/{model_data['id']}",
                        file_format=model_data["file_format"],
                        file_size=model_data["file_size"],
                        license=model_data["license"],
                        tags=model_data["tags"],
                        is_free=True,
                        rating=0.9  # High quality reference models
                    )
                    models.append(model)
            
            return models[:search_filter.limit]
            
        except Exception as e:
            print(f"Error searching Open3D: {e}")
            return []


class ExternalAPIManager:
    """Manages integration with multiple external 3D model platforms"""
    
    def __init__(self, config_file: str = "external_apis.json"):
        self.config_file = Path(config_file)
        self.config = self._load_config()
        
        # Initialize connectors
        self.connectors = {
            "sketchfab": SketchfabConnector(self.config.get("sketchfab", {}).get("api_token")),
            "open3d": Open3DConnector()
        }
        
        # Cache for search results
        self.search_cache = {}
        self.cache_ttl = 3600  # 1 hour
        
        # Downloaded models tracking
        self.downloaded_models = self._load_downloaded_models()
    
    def _load_config(self) -> Dict[str, Any]:
        """Load external API configuration"""
        default_config = {
            "enabled_platforms": ["sketchfab", "open3d"],
            "search_timeout": 30,
            "download_timeout": 300,
            "max_file_size": 50 * 1024 * 1024,  # 50MB
            "auto_import": False,
            "moderation_required": True,
            "sketchfab": {
                "api_token": os.getenv("SKETCHFAB_API_TOKEN"),
                "rate_limit": 60  # requests per hour
            },
            "open3d": {
                "enabled": True
            }
        }
        
        if self.config_file.exists():
            try:
                with open(self.config_file, 'r') as f:
                    loaded_config = json.load(f)
                    default_config.update(loaded_config)
            except Exception as e:
                print(f"Error loading external API config: {e}")
        
        return default_config
    
    def _load_downloaded_models(self) -> Dict[str, Dict]:
        """Load metadata of previously downloaded models"""
        downloaded_file = Path("downloaded_models.json")
        if downloaded_file.exists():
            try:
                with open(downloaded_file, 'r') as f:
                    return json.load(f)
            except Exception as e:
                print(f"Error loading downloaded models: {e}")
        return {}
    
    def _save_downloaded_models(self):
        """Save downloaded models metadata"""
        try:
            with open("downloaded_models.json", 'w') as f:
                json.dump(self.downloaded_models, f, indent=2)
        except Exception as e:
            print(f"Error saving downloaded models: {e}")
    
    async def search_all_platforms(self, search_filter: SearchFilter) -> Dict[str, List[ExternalModel]]:
        """Search across all enabled platforms"""
        results = {}
        
        # Check cache first
        cache_key = self._generate_cache_key(search_filter)
        if cache_key in self.search_cache:
            cache_entry = self.search_cache[cache_key]
            if datetime.now().timestamp() - cache_entry["timestamp"] < self.cache_ttl:
                return cache_entry["results"]
        
        # Search each enabled platform
        search_tasks = []
        enabled_platforms = self.config.get("enabled_platforms", [])
        
        for platform in enabled_platforms:
            if platform in self.connectors:
                task = self._search_platform(platform, search_filter)
                search_tasks.append((platform, task))
        
        # Execute searches concurrently
        for platform, task in search_tasks:
            try:
                models = await asyncio.wait_for(task, timeout=self.config["search_timeout"])
                results[platform] = models
            except asyncio.TimeoutError:
                print(f"Search timeout for platform: {platform}")
                results[platform] = []
            except Exception as e:
                print(f"Error searching platform {platform}: {e}")
                results[platform] = []
        
        # Cache results
        self.search_cache[cache_key] = {
            "results": results,
            "timestamp": datetime.now().timestamp()
        }
        
        return results
    
    async def _search_platform(self, platform: str, search_filter: SearchFilter) -> List[ExternalModel]:
        """Search a specific platform"""
        connector = self.connectors.get(platform)
        if connector:
            return await connector.search_models(search_filter)
        return []
    
    def _generate_cache_key(self, search_filter: SearchFilter) -> str:
        """Generate cache key for search filter"""
        filter_dict = asdict(search_filter)
        filter_str = json.dumps(filter_dict, sort_keys=True)
        return hashlib.md5(filter_str.encode()).hexdigest()
    
    async def get_unified_search_results(self, search_filter: SearchFilter) -> List[ExternalModel]:
        """Get unified search results from all platforms, sorted by relevance"""
        platform_results = await self.search_all_platforms(search_filter)
        
        # Combine and rank results
        all_models = []
        for platform, models in platform_results.items():
            all_models.extend(models)
        
        # Sort by relevance score (combination of rating, download count, etc.)
        def relevance_score(model: ExternalModel) -> float:
            score = 0.0
            
            # Query relevance (simple keyword matching)
            query_lower = search_filter.query.lower()
            if query_lower in model.name.lower():
                score += 2.0
            if query_lower in model.description.lower():
                score += 1.0
            if any(query_lower in tag.lower() for tag in (model.tags or [])):
                score += 1.5
            
            # Platform quality bonus
            platform_bonus = {"sketchfab": 1.0, "open3d": 1.5}
            score += platform_bonus.get(model.platform, 0.5)
            
            # Rating and popularity
            if model.rating:
                score += model.rating * 2.0
            
            if model.download_count > 100:
                score += 1.0
            
            # Free models bonus
            if model.is_free:
                score += 0.5
            
            return score
        
        sorted_models = sorted(all_models, key=relevance_score, reverse=True)
        return sorted_models[:search_filter.limit]
    
    async def download_model(self, model: ExternalModel, local_path: str = None) -> Dict[str, Any]:
        """Download a model from external platform"""
        if not model.download_url or not model.is_free:
            return {
                "status": "error",
                "message": "Model is not available for download"
            }
        
        if model.file_size and model.file_size > self.config["max_file_size"]:
            return {
                "status": "error",
                "message": f"Model too large: {model.file_size} bytes"
            }
        
        try:
            # Generate local path if not provided
            if not local_path:
                safe_name = "".join(c for c in model.name if c.isalnum() or c in (' ', '-', '_'))
                local_path = f"downloads/{model.platform}_{model.external_id}_{safe_name}.{model.file_format}"
            
            # Create directory if needed
            Path(local_path).parent.mkdir(parents=True, exist_ok=True)
            
            # Download file
            async with aiohttp.ClientSession() as session:
                async with session.get(
                    model.download_url,
                    timeout=aiohttp.ClientTimeout(total=self.config["download_timeout"])
                ) as response:
                    if response.status == 200:
                        with open(local_path, 'wb') as f:
                            async for chunk in response.content.iter_chunked(8192):
                                f.write(chunk)
                        
                        # Verify file size
                        actual_size = os.path.getsize(local_path)
                        
                        # Record download
                        download_record = {
                            "model": asdict(model),
                            "local_path": local_path,
                            "downloaded_at": datetime.now().isoformat(),
                            "file_size": actual_size,
                            "status": "pending_moderation" if self.config["moderation_required"] else "approved"
                        }
                        
                        self.downloaded_models[f"{model.platform}_{model.external_id}"] = download_record
                        self._save_downloaded_models()
                        
                        return {
                            "status": "success",
                            "message": "Model downloaded successfully",
                            "local_path": local_path,
                            "file_size": actual_size,
                            "moderation_required": self.config["moderation_required"]
                        }
                    else:
                        return {
                            "status": "error",
                            "message": f"Download failed: HTTP {response.status}"
                        }
            
        except Exception as e:
            return {
                "status": "error",
                "message": f"Download error: {str(e)}"
            }
    
    def get_downloaded_models(self, status: str = None) -> List[Dict[str, Any]]:
        """Get list of downloaded models, optionally filtered by status"""
        models = list(self.downloaded_models.values())
        
        if status:
            models = [m for m in models if m.get("status") == status]
        
        return models
    
    def moderate_model(self, model_key: str, approved: bool, notes: str = "") -> Dict[str, Any]:
        """Moderate a downloaded model (approve/reject)"""
        if model_key not in self.downloaded_models:
            return {
                "status": "error",
                "message": "Model not found"
            }
        
        model_record = self.downloaded_models[model_key]
        model_record["status"] = "approved" if approved else "rejected"
        model_record["moderation_notes"] = notes
        model_record["moderated_at"] = datetime.now().isoformat()
        
        self._save_downloaded_models()
        
        return {
            "status": "success",
            "message": f"Model {'approved' if approved else 'rejected'}",
            "model_status": model_record["status"]
        }
    
    def get_platform_stats(self) -> Dict[str, Any]:
        """Get statistics about external platform integration"""
        stats = {
            "enabled_platforms": self.config.get("enabled_platforms", []),
            "total_downloaded": len(self.downloaded_models),
            "pending_moderation": len([m for m in self.downloaded_models.values() 
                                     if m.get("status") == "pending_moderation"]),
            "approved_models": len([m for m in self.downloaded_models.values() 
                                  if m.get("status") == "approved"]),
            "rejected_models": len([m for m in self.downloaded_models.values() 
                                  if m.get("status") == "rejected"]),
            "cache_entries": len(self.search_cache),
            "platforms": {}
        }
        
        # Platform-specific stats
        for platform in self.config.get("enabled_platforms", []):
            platform_models = [m for m in self.downloaded_models.values() 
                             if m.get("model", {}).get("platform") == platform]
            stats["platforms"][platform] = {
                "downloaded_count": len(platform_models),
                "connector_available": platform in self.connectors
            }
        
        return stats


# Initialize global external API manager
external_api_manager = ExternalAPIManager()