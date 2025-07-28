"""
Performance optimization module for 3D model caching and LOD management
Handles model caching, level-of-detail selection, and performance monitoring
"""

import os
import json
import hashlib
import time
from pathlib import Path
from typing import Dict, Any, Optional, List
from dataclasses import dataclass, asdict
from datetime import datetime, timedelta

@dataclass
class CacheMetadata:
    """Metadata for cached models"""
    original_file: str
    cache_level: str  # 'high', 'medium', 'low'
    file_size: int
    created_at: datetime
    last_accessed: datetime
    access_count: int
    compression_ratio: float
    
class ModelCache:
    """
    Model caching system with Level of Detail (LOD) support
    Automatically creates different quality versions based on device capabilities
    """
    
    def __init__(self, cache_dir: str = "cache/models", max_cache_size: int = 1024 * 1024 * 500):  # 500MB default
        self.cache_dir = Path(cache_dir)
        self.cache_dir.mkdir(parents=True, exist_ok=True)
        self.max_cache_size = max_cache_size
        self.metadata_file = self.cache_dir / "cache_metadata.json"
        self.metadata = self._load_metadata()
        
        # LOD configurations
        self.lod_configs = {
            'high': {
                'max_file_size': 2 * 1024 * 1024,  # 2MB
                'compression_level': 0.9,
                'description': 'High quality for desktop/high-speed connections'
            },
            'medium': {
                'max_file_size': 1 * 1024 * 1024,  # 1MB  
                'compression_level': 0.7,
                'description': 'Medium quality for tablets/mobile'
            },
            'low': {
                'max_file_size': 512 * 1024,  # 512KB
                'compression_level': 0.5,
                'description': 'Low quality for slow connections/older devices'
            }
        }
    
    def _load_metadata(self) -> Dict[str, Dict[str, Any]]:
        """Load cache metadata from disk"""
        if self.metadata_file.exists():
            try:
                with open(self.metadata_file, 'r') as f:
                    data = json.load(f)
                    # Convert datetime strings back to datetime objects
                    for cache_key, meta in data.items():
                        meta['created_at'] = datetime.fromisoformat(meta['created_at'])
                        meta['last_accessed'] = datetime.fromisoformat(meta['last_accessed'])
                    return data
            except Exception as e:
                print(f"Error loading cache metadata: {e}")
        return {}
    
    def _save_metadata(self):
        """Save cache metadata to disk"""
        try:
            # Convert datetime objects to strings for JSON serialization
            serializable_data = {}
            for cache_key, meta in self.metadata.items():
                serializable_data[cache_key] = {
                    **meta,
                    'created_at': meta['created_at'].isoformat(),
                    'last_accessed': meta['last_accessed'].isoformat()
                }
            
            with open(self.metadata_file, 'w') as f:
                json.dump(serializable_data, f, indent=2)
        except Exception as e:
            print(f"Error saving cache metadata: {e}")
    
    def _generate_cache_key(self, model_path: str, lod_level: str) -> str:
        """Generate unique cache key for model + LOD combination"""
        content = f"{model_path}:{lod_level}"
        return hashlib.md5(content.encode()).hexdigest()
    
    def get_optimal_lod(self, user_agent: str = "", connection_speed: str = "auto", screen_size: str = "auto") -> str:
        """
        Determine optimal LOD level based on client capabilities
        """
        # Simple heuristics - can be enhanced with more sophisticated detection
        
        # Check user agent for device type
        user_agent_lower = user_agent.lower()
        is_mobile = any(device in user_agent_lower for device in ['mobile', 'android', 'iphone', 'ipad'])
        is_tablet = 'tablet' in user_agent_lower or 'ipad' in user_agent_lower
        
        # Default LOD selection logic
        if connection_speed == "slow" or "2g" in connection_speed:
            return "low"
        elif connection_speed == "fast" or "5g" in connection_speed or "wifi" in connection_speed:
            return "high"
        elif is_mobile:
            return "medium"
        elif is_tablet:
            return "medium"
        else:
            return "high"  # Desktop default
    
    def cache_model(self, model_path: str, lod_level: str = "high") -> Optional[str]:
        """
        Cache a model file with specified LOD level
        Returns path to cached file or None if caching failed
        """
        if not os.path.exists(model_path):
            return None
            
        cache_key = self._generate_cache_key(model_path, lod_level)
        cached_file = self.cache_dir / f"{cache_key}_{lod_level}.fbx"
        
        # Check if already cached and valid
        if cached_file.exists() and cache_key in self.metadata:
            self._update_access_stats(cache_key)
            return str(cached_file)
        
        try:
            # For this demo, we'll simulate LOD processing
            # In a real implementation, you'd use FBX/glTF processing libraries
            original_size = os.path.getsize(model_path)
            
            # Simulate compression based on LOD level
            compression_ratio = self.lod_configs[lod_level]['compression_level']
            
            # Copy file (in real implementation, this would be actual compression/optimization)
            import shutil
            shutil.copy2(model_path, cached_file)
            
            # Create metadata
            now = datetime.now()
            self.metadata[cache_key] = {
                'original_file': model_path,
                'cache_level': lod_level,
                'file_size': os.path.getsize(cached_file),
                'created_at': now,
                'last_accessed': now,
                'access_count': 1,
                'compression_ratio': compression_ratio
            }
            
            self._save_metadata()
            self._cleanup_old_cache()
            
            return str(cached_file)
            
        except Exception as e:
            print(f"Error caching model {model_path}: {e}")
            return None
    
    def get_cached_model(self, model_path: str, lod_level: str = "auto", user_agent: str = "") -> Optional[Dict[str, Any]]:
        """
        Get cached model with optimal LOD level
        """
        if lod_level == "auto":
            lod_level = self.get_optimal_lod(user_agent)
        
        cache_key = self._generate_cache_key(model_path, lod_level)
        cached_file = self.cache_dir / f"{cache_key}_{lod_level}.fbx"
        
        # Check if cached version exists
        if cached_file.exists() and cache_key in self.metadata:
            self._update_access_stats(cache_key)
            meta = self.metadata[cache_key]
            
            return {
                'cached_path': str(cached_file),
                'lod_level': lod_level,
                'file_size': meta['file_size'],
                'compression_ratio': meta['compression_ratio'],
                'cache_hit': True,
                'created_at': meta['created_at'].isoformat(),
                'access_count': meta['access_count']
            }
        
        # Cache miss - create cached version
        cached_path = self.cache_model(model_path, lod_level)
        if cached_path:
            return self.get_cached_model(model_path, lod_level, user_agent)
        
        return None
    
    def _update_access_stats(self, cache_key: str):
        """Update access statistics for cached model"""
        if cache_key in self.metadata:
            self.metadata[cache_key]['last_accessed'] = datetime.now()
            self.metadata[cache_key]['access_count'] += 1
    
    def _cleanup_old_cache(self):
        """Clean up old cached files when cache size exceeds limit"""
        try:
            # Calculate total cache size
            total_size = sum(
                os.path.getsize(self.cache_dir / f"{key}_{meta['cache_level']}.fbx")
                for key, meta in self.metadata.items()
                if (self.cache_dir / f"{key}_{meta['cache_level']}.fbx").exists()
            )
            
            if total_size > self.max_cache_size:
                # Sort by last accessed time (oldest first)
                sorted_items = sorted(
                    self.metadata.items(),
                    key=lambda x: x[1]['last_accessed']
                )
                
                # Remove oldest files until under size limit
                for cache_key, meta in sorted_items:
                    if total_size <= self.max_cache_size * 0.8:  # Keep 20% buffer
                        break
                    
                    cached_file = self.cache_dir / f"{cache_key}_{meta['cache_level']}.fbx"
                    if cached_file.exists():
                        file_size = cached_file.stat().st_size
                        cached_file.unlink()
                        total_size -= file_size
                        del self.metadata[cache_key]
                
                self._save_metadata()
                
        except Exception as e:
            print(f"Error during cache cleanup: {e}")
    
    def get_cache_stats(self) -> Dict[str, Any]:
        """Get cache performance statistics"""
        total_files = len(self.metadata)
        total_size = 0
        total_accesses = 0
        lod_distribution = {'high': 0, 'medium': 0, 'low': 0}
        
        for meta in self.metadata.values():
            total_size += meta['file_size']
            total_accesses += meta['access_count']
            lod_distribution[meta['cache_level']] += 1
        
        return {
            'total_cached_files': total_files,
            'total_cache_size': total_size,
            'total_cache_size_mb': round(total_size / (1024 * 1024), 2),
            'total_accesses': total_accesses,
            'average_accesses_per_file': round(total_accesses / max(total_files, 1), 2),
            'lod_distribution': lod_distribution,
            'cache_utilization': round((total_size / self.max_cache_size) * 100, 2),
            'available_lod_levels': list(self.lod_configs.keys())
        }
    
    def clear_cache(self, older_than_days: int = 0):
        """Clear cache files older than specified days"""
        cutoff_date = datetime.now() - timedelta(days=older_than_days)
        
        files_removed = 0
        for cache_key, meta in list(self.metadata.items()):
            if meta['last_accessed'] < cutoff_date:
                cached_file = self.cache_dir / f"{cache_key}_{meta['cache_level']}.fbx"
                if cached_file.exists():
                    cached_file.unlink()
                    files_removed += 1
                del self.metadata[cache_key]
        
        self._save_metadata()
        return files_removed

# Global cache instance
model_cache = ModelCache()

def get_performance_config(user_agent: str = "", connection: str = "auto") -> Dict[str, Any]:
    """
    Get recommended performance configuration for client
    """
    lod_level = model_cache.get_optimal_lod(user_agent, connection)
    
    config = {
        'recommended_lod': lod_level,
        'lod_description': model_cache.lod_configs[lod_level]['description'],
        'max_file_size': model_cache.lod_configs[lod_level]['max_file_size'],
        'preload_models': lod_level == 'high',  # Only preload on fast connections
        'use_compression': True,
        'cache_enabled': True,
        'available_levels': list(model_cache.lod_configs.keys())
    }
    
    return config