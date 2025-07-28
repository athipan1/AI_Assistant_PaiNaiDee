"""
Performance API routes for model caching and optimization
"""

from fastapi import APIRouter, Request, HTTPException, Query
from fastapi.responses import FileResponse
from typing import Optional
from pathlib import Path
import os
from models.cache_manager import model_cache, get_performance_config

router = APIRouter()

@router.get("/performance/config")
async def get_client_performance_config(
    request: Request,
    connection: str = Query("auto", description="Connection speed: auto, fast, slow, 2g, 3g, 4g, 5g, wifi"),
    lod: str = Query("auto", description="Force specific LOD: auto, high, medium, low")
):
    """
    Get performance configuration recommendations for the client
    """
    try:
        user_agent = request.headers.get("user-agent", "")
        
        config = get_performance_config(user_agent, connection)
        
        if lod != "auto":
            config['recommended_lod'] = lod
            config['lod_description'] = model_cache.lod_configs.get(lod, {}).get('description', 'Custom LOD')
        
        return {
            "config": config,
            "cache_stats": model_cache.get_cache_stats(),
            "status": "success"
        }
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error getting performance config: {str(e)}")

@router.get("/performance/models/{model_name}")
async def get_optimized_model(
    model_name: str,
    request: Request,
    lod: str = Query("auto", description="LOD level: auto, high, medium, low"),
    connection: str = Query("auto", description="Connection speed hint")
):
    """
    Get optimized/cached version of a model based on client capabilities
    """
    try:
        # Get original model path  
        models_dir = Path(__file__).parent.parent.parent / "assets" / "models" / "Fbx"
        original_model_path = models_dir / model_name
        
        if not original_model_path.exists():
            raise HTTPException(status_code=404, detail=f"Model {model_name} not found")
        
        user_agent = request.headers.get("user-agent", "")
        
        # Get cached/optimized version
        cached_info = model_cache.get_cached_model(
            str(original_model_path), 
            lod, 
            user_agent
        )
        
        if cached_info:
            return FileResponse(
                cached_info['cached_path'],
                media_type='application/octet-stream',
                filename=f"{model_name.replace('.fbx', '')}_{cached_info['lod_level']}.fbx",
                headers={
                    "X-LOD-Level": cached_info['lod_level'],
                    "X-Cache-Hit": str(cached_info['cache_hit']),
                    "X-Compression-Ratio": str(cached_info['compression_ratio']),
                    "X-File-Size": str(cached_info['file_size'])
                }
            )
        else:
            # Fallback to original file
            return FileResponse(
                str(original_model_path),
                media_type='application/octet-stream',
                filename=model_name,
                headers={
                    "X-LOD-Level": "original",
                    "X-Cache-Hit": "false"
                }
            )
            
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error serving optimized model: {str(e)}")

@router.post("/performance/cache/{model_name}")
async def cache_model_with_lod(
    model_name: str,
    lod_level: str = Query("high", description="LOD level to cache: high, medium, low")
):
    """
    Pre-cache a model with specific LOD level
    """
    try:
        models_dir = Path(__file__).parent.parent.parent / "assets" / "models" / "Fbx"
        model_path = models_dir / model_name
        
        if not model_path.exists():
            raise HTTPException(status_code=404, detail=f"Model {model_name} not found")
        
        if lod_level not in ['high', 'medium', 'low']:
            raise HTTPException(status_code=400, detail="Invalid LOD level")
        
        cached_path = model_cache.cache_model(str(model_path), lod_level)
        
        if cached_path:
            return {
                "message": f"Model {model_name} cached with {lod_level} LOD",
                "cached_path": cached_path,
                "lod_level": lod_level,
                "status": "success"
            }
        else:
            raise HTTPException(status_code=500, detail="Failed to cache model")
            
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error caching model: {str(e)}")

@router.get("/performance/cache/stats")
async def get_cache_statistics():
    """
    Get detailed cache performance statistics
    """
    try:
        stats = model_cache.get_cache_stats()
        
        return {
            "cache_stats": stats,
            "lod_configs": model_cache.lod_configs,
            "cache_directory": str(model_cache.cache_dir),
            "max_cache_size_mb": round(model_cache.max_cache_size / (1024 * 1024), 2),
            "status": "success"
        }
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error getting cache stats: {str(e)}")

@router.delete("/performance/cache")
async def clear_cache(
    older_than_days: int = Query(0, description="Clear cache older than X days (0 = clear all)")
):
    """
    Clear model cache
    """
    try:
        files_removed = model_cache.clear_cache(older_than_days)
        
        return {
            "message": f"Cache cleared successfully",
            "files_removed": files_removed,
            "older_than_days": older_than_days,
            "status": "success"
        }
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error clearing cache: {str(e)}")

@router.get("/performance/benchmark")
async def run_performance_benchmark(
    request: Request,
    model_name: str = Query("Man.fbx", description="Model to benchmark"),
    iterations: int = Query(5, description="Number of iterations")
):
    """
    Run performance benchmark for model loading
    """
    try:
        import time
        
        models_dir = Path(__file__).parent.parent.parent / "assets" / "models" / "Fbx"
        model_path = models_dir / model_name
        
        if not model_path.exists():
            raise HTTPException(status_code=404, detail=f"Model {model_name} not found")
        
        user_agent = request.headers.get("user-agent", "")
        results = {}
        
        # Benchmark different LOD levels
        for lod_level in ['high', 'medium', 'low']:
            times = []
            
            for i in range(iterations):
                start_time = time.time()
                
                # Get cached model (this will create cache if not exists)
                cached_info = model_cache.get_cached_model(str(model_path), lod_level, user_agent)
                
                end_time = time.time()
                times.append(end_time - start_time)
            
            results[lod_level] = {
                'average_time': sum(times) / len(times),
                'min_time': min(times),
                'max_time': max(times),
                'file_size': cached_info['file_size'] if cached_info else 0,
                'compression_ratio': cached_info['compression_ratio'] if cached_info else 1.0
            }
        
        return {
            "benchmark_results": results,
            "model_name": model_name,
            "iterations": iterations,
            "user_agent": user_agent,
            "status": "success"
        }
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error running benchmark: {str(e)}")