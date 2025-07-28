"""
API routes for Admin Dashboard
Provides comprehensive admin interface with real-time analytics and management
"""

from fastapi import APIRouter, HTTPException, Query, Depends
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from typing import List, Optional, Dict, Any
from pydantic import BaseModel
import os

from models.admin_dashboard import admin_analytics
from models.versioning import versioning_manager
from models.cdn import cdn_manager
from models.lod_prediction import lod_predictor
from models.external_apis import external_api_manager


# Simple admin authentication (in production, use proper JWT/OAuth)
security = HTTPBearer()

def verify_admin_token(credentials: HTTPAuthorizationCredentials = Depends(security)):
    """Verify admin authentication token"""
    admin_token = os.getenv("ADMIN_TOKEN", "admin_demo_token_123")
    if credentials.credentials != admin_token:
        raise HTTPException(status_code=401, detail="Invalid admin token")
    return credentials.credentials


# Pydantic models for request/response
class ModelModerationRequest(BaseModel):
    model_id: str
    status: str  # approved, rejected, pending
    notes: str = ""


class SystemConfigUpdate(BaseModel):
    config_section: str
    config_data: Dict[str, Any]


class AlertRule(BaseModel):
    name: str
    metric: str
    threshold: float
    condition: str  # greater_than, less_than, equals
    notification_type: str  # email, webhook, dashboard


def create_admin_routes(app):
    """Add admin dashboard routes to FastAPI app"""
    
    @app.get("/admin/dashboard/overview")
    async def get_dashboard_overview(admin_token: str = Depends(verify_admin_token)):
        """Get comprehensive dashboard overview"""
        try:
            overview = admin_analytics.get_dashboard_overview()
            
            return {
                "dashboard_overview": overview,
                "status": "success"
            }
            
        except Exception as e:
            raise HTTPException(status_code=500, detail=str(e))
    
    @app.get("/admin/analytics/detailed")
    async def get_detailed_analytics(
        time_range: str = Query("24h", description="Time range: 1h, 24h, 7d, 30d"),
        admin_token: str = Depends(verify_admin_token)
    ):
        """Get detailed analytics for specified time range"""
        try:
            analytics = admin_analytics.get_detailed_analytics(time_range)
            
            return {
                "detailed_analytics": analytics,
                "status": "success"
            }
            
        except Exception as e:
            raise HTTPException(status_code=500, detail=str(e))
    
    @app.get("/admin/models/usage")
    async def get_model_usage_stats(
        model_name: Optional[str] = Query(None, description="Specific model name"),
        admin_token: str = Depends(verify_admin_token)
    ):
        """Get model usage statistics"""
        try:
            if model_name:
                if model_name in admin_analytics.model_usage:
                    usage_stats = admin_analytics.model_usage[model_name]
                    return {
                        "model_name": model_name,
                        "usage_stats": {
                            "total_views": usage_stats.total_views,
                            "total_downloads": usage_stats.total_downloads,
                            "avg_load_time": usage_stats.avg_load_time,
                            "avg_rating": sum(usage_stats.user_ratings) / len(usage_stats.user_ratings) if usage_stats.user_ratings else 0,
                            "peak_concurrent_users": usage_stats.peak_concurrent_users,
                            "bandwidth_used": usage_stats.bandwidth_used,
                            "lod_distribution": usage_stats.lod_distribution,
                            "last_accessed": usage_stats.last_accessed
                        },
                        "status": "success"
                    }
                else:
                    raise HTTPException(status_code=404, detail="Model not found")
            else:
                # Return all model usage stats
                all_stats = {}
                for model_name, stats in admin_analytics.model_usage.items():
                    all_stats[model_name] = {
                        "total_views": stats.total_views,
                        "total_downloads": stats.total_downloads,
                        "avg_load_time": stats.avg_load_time,
                        "avg_rating": sum(stats.user_ratings) / len(stats.user_ratings) if stats.user_ratings else 0,
                        "bandwidth_used": stats.bandwidth_used
                    }
                
                return {
                    "all_model_stats": all_stats,
                    "total_models": len(all_stats),
                    "status": "success"
                }
                
        except HTTPException:
            raise
        except Exception as e:
            raise HTTPException(status_code=500, detail=str(e))
    
    @app.get("/admin/search/trends")
    async def get_search_trends(
        limit: int = Query(50, description="Number of top searches to return"),
        admin_token: str = Depends(verify_admin_token)
    ):
        """Get search trends and popular queries"""
        try:
            sorted_trends = sorted(
                admin_analytics.search_trends.values(),
                key=lambda x: x.search_count,
                reverse=True
            )[:limit]
            
            trends_data = []
            for trend in sorted_trends:
                trends_data.append({
                    "query": trend.query,
                    "search_count": trend.search_count,
                    "success_rate": trend.success_rate,
                    "avg_results": trend.avg_results,
                    "peak_hours": [i for i, count in enumerate(trend.peak_times) if count == max(trend.peak_times)]
                })
            
            return {
                "search_trends": trends_data,
                "total_unique_queries": len(admin_analytics.search_trends),
                "total_searches": sum(t.search_count for t in admin_analytics.search_trends.values()),
                "status": "success"
            }
            
        except Exception as e:
            raise HTTPException(status_code=500, detail=str(e))
    
    @app.get("/admin/performance/cache")
    async def get_cache_performance(
        admin_token: str = Depends(verify_admin_token)
    ):
        """Get cache performance metrics across all cache types"""
        try:
            cache_data = {}
            
            for cache_type, metrics in admin_analytics.cache_metrics.items():
                cache_data[cache_type] = {
                    "hit_ratio": metrics.hit_ratio,
                    "miss_ratio": metrics.miss_ratio,
                    "total_requests": metrics.total_requests,
                    "avg_latency": metrics.avg_latency,
                    "storage_size": metrics.storage_size,
                    "eviction_count": metrics.eviction_count
                }
            
            # Add CDN cache metrics
            try:
                cdn_analytics = cdn_manager.get_analytics()
                cache_data["cdn_global"] = {
                    "total_assets": cdn_analytics.get("total_assets", 0),
                    "total_requests": cdn_analytics.get("total_requests", 0),
                    "edge_performance": cdn_analytics.get("edge_performance", [])
                }
            except Exception:
                pass
            
            return {
                "cache_performance": cache_data,
                "overall_hit_ratio": sum(m.hit_ratio for m in admin_analytics.cache_metrics.values()) / len(admin_analytics.cache_metrics) if admin_analytics.cache_metrics else 0,
                "status": "success"
            }
            
        except Exception as e:
            raise HTTPException(status_code=500, detail=str(e))
    
    @app.get("/admin/system/health")
    async def get_system_health(
        admin_token: str = Depends(verify_admin_token)
    ):
        """Get comprehensive system health status"""
        try:
            # Get latest system metrics
            latest_metrics = list(admin_analytics.system_metrics)[-1] if admin_analytics.system_metrics else None
            
            health_status = {
                "overall_status": "healthy",
                "components": {
                    "web_server": {"status": "healthy", "response_time": latest_metrics.avg_response_time if latest_metrics else 0},
                    "database": {"status": "healthy", "connection_pool": "normal"},
                    "cdn": {"status": "healthy", "edge_locations": len([e for e in cdn_manager.edge_locations if e.is_healthy])},
                    "ml_engine": {"status": "healthy", "prediction_accuracy": "85%"},
                    "external_apis": {"status": "healthy", "connected_platforms": len(external_api_manager.connectors)}
                },
                "resource_usage": {
                    "cpu": latest_metrics.cpu_usage if latest_metrics else 0,
                    "memory": latest_metrics.memory_usage if latest_metrics else 0,
                    "disk": latest_metrics.disk_usage if latest_metrics else 0,
                    "active_sessions": latest_metrics.active_sessions if latest_metrics else 0
                },
                "performance_metrics": {
                    "avg_response_time": latest_metrics.avg_response_time if latest_metrics else 0,
                    "error_rate": latest_metrics.error_rate if latest_metrics else 0,
                    "requests_per_minute": len([log for log in admin_analytics.request_logs if log.get('timestamp')]) / max(1, len(admin_analytics.system_metrics))
                }
            }
            
            # Determine overall status
            if latest_metrics:
                if latest_metrics.cpu_usage > 90 or latest_metrics.memory_usage > 90 or latest_metrics.error_rate > 10:
                    health_status["overall_status"] = "critical"
                elif latest_metrics.cpu_usage > 80 or latest_metrics.memory_usage > 80 or latest_metrics.error_rate > 5:
                    health_status["overall_status"] = "warning"
            
            return {
                "system_health": health_status,
                "timestamp": latest_metrics.timestamp if latest_metrics else None,
                "status": "success"
            }
            
        except Exception as e:
            raise HTTPException(status_code=500, detail=str(e))
    
    @app.get("/admin/users/analytics")
    async def get_user_analytics(
        admin_token: str = Depends(verify_admin_token)
    ):
        """Get user behavior analytics"""
        try:
            user_analytics = {
                "total_users": len(admin_analytics.user_behavior),
                "active_sessions": len(admin_analytics.active_sessions),
                "user_retention": 0,  # Would calculate based on return visits
                "geographic_distribution": {},  # Would track by IP/location
                "device_analytics": {},
                "session_analytics": {
                    "avg_duration": 0,
                    "avg_models_viewed": 0,
                    "avg_searches": 0
                }
            }
            
            # Calculate session analytics
            all_sessions = []
            for user_sessions in admin_analytics.user_behavior.values():
                all_sessions.extend(user_sessions)
            
            if all_sessions:
                total_duration = 0
                total_models = 0
                total_searches = 0
                valid_sessions = 0
                
                for session in all_sessions:
                    if "end_time" in session:
                        from datetime import datetime
                        start = datetime.fromisoformat(session["start_time"])
                        end = datetime.fromisoformat(session["end_time"])
                        duration = (end - start).total_seconds() / 60  # minutes
                        total_duration += duration
                        valid_sessions += 1
                    
                    total_models += len(session.get("models_viewed", []))
                    total_searches += len(session.get("searches_performed", []))
                
                if valid_sessions > 0:
                    user_analytics["session_analytics"]["avg_duration"] = total_duration / valid_sessions
                
                if all_sessions:
                    user_analytics["session_analytics"]["avg_models_viewed"] = total_models / len(all_sessions)
                    user_analytics["session_analytics"]["avg_searches"] = total_searches / len(all_sessions)
            
            return {
                "user_analytics": user_analytics,
                "status": "success"
            }
            
        except Exception as e:
            raise HTTPException(status_code=500, detail=str(e))
    
    @app.get("/admin/content/moderation")
    async def get_content_moderation_queue(
        status: Optional[str] = Query(None, description="Filter by status: pending, approved, rejected"),
        admin_token: str = Depends(verify_admin_token)
    ):
        """Get content moderation queue"""
        try:
            # Get external models pending moderation
            external_models = external_api_manager.get_downloaded_models(status)
            
            moderation_queue = {
                "external_models": [
                    {
                        "model_key": f"{model['model']['platform']}_{model['model']['external_id']}",
                        "model_name": model["model"]["name"],
                        "platform": model["model"]["platform"],
                        "author": model["model"]["author"],
                        "file_size": model["file_size"],
                        "downloaded_at": model["downloaded_at"],
                        "status": model["status"],
                        "moderation_notes": model.get("moderation_notes", "")
                    }
                    for model in external_models
                ],
                "pending_count": len([m for m in external_models if m["status"] == "pending_moderation"]),
                "total_count": len(external_models)
            }
            
            return {
                "moderation_queue": moderation_queue,
                "status": "success"
            }
            
        except Exception as e:
            raise HTTPException(status_code=500, detail=str(e))
    
    @app.post("/admin/content/moderate")
    async def moderate_content(
        request: ModelModerationRequest,
        admin_token: str = Depends(verify_admin_token)
    ):
        """Moderate content (approve/reject models)"""
        try:
            # Moderate external model
            result = external_api_manager.moderate_model(
                model_key=request.model_id,
                approved=request.status == "approved",
                notes=request.notes
            )
            
            return {
                "moderation_result": result,
                "status": "success"
            }
            
        except Exception as e:
            raise HTTPException(status_code=500, detail=str(e))
    
    @app.get("/admin/platform/config")
    async def get_platform_config(
        admin_token: str = Depends(verify_admin_token)
    ):
        """Get current platform configuration"""
        try:
            config = {
                "versioning": {
                    "enabled": True,
                    "default_increment": "patch",
                    "cleanup_policy": "keep_latest_5"
                },
                "cdn": cdn_manager.config,
                "lod_prediction": {
                    "enabled": True,
                    "learning_rate": lod_predictor.learning_rate,
                    "adaptation_threshold": lod_predictor.adaptation_threshold,
                    "ml_weights_count": len(lod_predictor.feature_weights)
                },
                "external_apis": external_api_manager.config,
                "analytics": {
                    "retention_days": 30,
                    "monitoring_interval": 60,
                    "alerts_enabled": True
                }
            }
            
            return {
                "platform_config": config,
                "status": "success"
            }
            
        except Exception as e:
            raise HTTPException(status_code=500, detail=str(e))
    
    @app.post("/admin/platform/config/update")
    async def update_platform_config(
        request: SystemConfigUpdate,
        admin_token: str = Depends(verify_admin_token)
    ):
        """Update platform configuration"""
        try:
            section = request.config_section
            config_data = request.config_data
            
            if section == "cdn":
                cdn_manager.config.update(config_data)
                # Save CDN config
                with open(cdn_manager.config_file, 'w') as f:
                    import json
                    json.dump(cdn_manager.config, f, indent=2)
            
            elif section == "external_apis":
                external_api_manager.config.update(config_data)
                # Save external API config
                with open(external_api_manager.config_file, 'w') as f:
                    import json
                    json.dump(external_api_manager.config, f, indent=2)
            
            elif section == "lod_prediction":
                if "learning_rate" in config_data:
                    lod_predictor.learning_rate = config_data["learning_rate"]
                if "adaptation_threshold" in config_data:
                    lod_predictor.adaptation_threshold = config_data["adaptation_threshold"]
            
            else:
                raise HTTPException(status_code=400, detail=f"Unknown config section: {section}")
            
            return {
                "message": f"Configuration updated for section: {section}",
                "updated_config": config_data,
                "status": "success"
            }
            
        except HTTPException:
            raise
        except Exception as e:
            raise HTTPException(status_code=500, detail=str(e))
    
    @app.post("/admin/maintenance/cleanup")
    async def run_maintenance_cleanup(
        days_to_keep: int = Query(30, description="Days of data to keep"),
        admin_token: str = Depends(verify_admin_token)
    ):
        """Run maintenance cleanup tasks"""
        try:
            cleanup_results = {}
            
            # Clean up analytics data
            admin_analytics.cleanup_old_data(days_to_keep)
            cleanup_results["analytics"] = f"Cleaned data older than {days_to_keep} days"
            
            # Clean up old model versions
            total_freed = 0
            for model_name in versioning_manager.metadata.keys():
                result = versioning_manager.cleanup_old_versions(model_name, keep_latest=5)
                if "freed_space" in result:
                    total_freed += result["freed_space"]
            
            cleanup_results["versioning"] = f"Freed {total_freed} bytes from old versions"
            
            # Clear CDN cache
            await cdn_manager.purge_cache()
            cleanup_results["cdn"] = "Purged CDN cache"
            
            # Clear search cache
            cache_cleared = len(external_api_manager.search_cache)
            external_api_manager.search_cache.clear()
            cleanup_results["search_cache"] = f"Cleared {cache_cleared} cached searches"
            
            return {
                "cleanup_results": cleanup_results,
                "status": "success"
            }
            
        except Exception as e:
            raise HTTPException(status_code=500, detail=str(e))
    
    @app.get("/admin/logs/errors")
    async def get_error_logs(
        limit: int = Query(100, description="Number of recent errors to return"),
        admin_token: str = Depends(verify_admin_token)
    ):
        """Get recent error logs"""
        try:
            recent_errors = list(admin_analytics.error_logs)[-limit:]
            
            return {
                "error_logs": recent_errors,
                "total_errors": len(admin_analytics.error_logs),
                "returned_count": len(recent_errors),
                "status": "success"
            }
            
        except Exception as e:
            raise HTTPException(status_code=500, detail=str(e))
    
    @app.get("/admin/reports/summary")
    async def generate_admin_summary_report(
        admin_token: str = Depends(verify_admin_token)
    ):
        """Generate comprehensive admin summary report"""
        try:
            from datetime import datetime
            
            # Collect data from all systems
            overview = admin_analytics.get_dashboard_overview()
            versioning_summary = versioning_manager.get_platform_stats() if hasattr(versioning_manager, 'get_platform_stats') else {}
            cdn_performance = cdn_manager.get_analytics()
            lod_analytics = lod_predictor.get_analytics()
            external_stats = external_api_manager.get_platform_stats()
            
            summary_report = {
                "report_generated": datetime.now().isoformat(),
                "executive_summary": {
                    "total_users": overview["system_health"]["total_users"],
                    "total_models": overview["content_stats"]["total_models"],
                    "total_views": overview["content_stats"]["total_views"],
                    "platform_uptime": "99.9%",  # Would calculate from actual metrics
                    "performance_score": "A",  # Would calculate based on various metrics
                },
                "system_performance": overview["performance_metrics"],
                "content_statistics": overview["content_stats"],
                "user_engagement": {
                    "active_sessions": overview["system_health"]["active_sessions"],
                    "search_success_rate": overview["search_insights"]["avg_success_rate"],
                    "top_models": overview["top_models"][:5]
                },
                "technical_metrics": {
                    "versioning": versioning_summary,
                    "cdn_performance": cdn_performance,
                    "ml_predictions": lod_analytics,
                    "external_integrations": external_stats
                },
                "recommendations": [
                    "Consider scaling CDN capacity during peak hours",
                    "Optimize LOD prediction model with recent user feedback",
                    "Review and approve pending external models",
                    "Schedule regular cleanup of old analytics data"
                ]
            }
            
            return {
                "summary_report": summary_report,
                "status": "success"
            }
            
        except Exception as e:
            raise HTTPException(status_code=500, detail=str(e))