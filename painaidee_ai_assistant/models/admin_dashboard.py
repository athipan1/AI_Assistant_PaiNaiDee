"""
Admin Dashboard System
Provides comprehensive admin interface with real-time analytics and management tools
"""

import os
import json
import time
from typing import Dict, List, Optional, Any
from dataclasses import dataclass, asdict
from datetime import datetime, timedelta
from pathlib import Path
from collections import defaultdict, deque
import asyncio
import threading


@dataclass
class SystemMetrics:
    """Real-time system performance metrics"""
    timestamp: str
    cpu_usage: float
    memory_usage: float
    disk_usage: float
    active_sessions: int
    total_requests: int
    error_rate: float
    avg_response_time: float


@dataclass
class ModelUsageStats:
    """Usage statistics for 3D models"""
    model_name: str
    total_views: int
    total_downloads: int
    avg_load_time: float
    user_ratings: List[float]
    peak_concurrent_users: int
    bandwidth_used: int
    lod_distribution: Dict[int, int]  # LOD level -> usage count
    last_accessed: str


@dataclass
class SearchTrend:
    """Search trend analysis"""
    query: str
    search_count: int
    success_rate: float
    avg_results: float
    peak_times: List[str]
    user_demographics: Dict[str, int]


@dataclass
class CacheMetrics:
    """Cache performance metrics"""
    cache_type: str  # cdn, model, search, etc.
    hit_ratio: float
    miss_ratio: float
    total_requests: int
    avg_latency: float
    storage_size: int
    eviction_count: int


class AdminAnalyticsEngine:
    """Core analytics engine for admin dashboard"""
    
    def __init__(self, data_dir: str = "analytics_data"):
        self.data_dir = Path(data_dir)
        self.data_dir.mkdir(exist_ok=True)
        
        # Real-time metrics storage
        self.system_metrics: deque = deque(maxlen=1440)  # 24 hours at 1-minute intervals
        self.model_usage: Dict[str, ModelUsageStats] = {}
        self.search_trends: Dict[str, SearchTrend] = {}
        self.cache_metrics: Dict[str, CacheMetrics] = {}
        
        # User analytics
        self.active_sessions: Dict[str, Dict] = {}
        self.user_behavior: Dict[str, List] = defaultdict(list)
        
        # Performance tracking
        self.request_logs: deque = deque(maxlen=10000)
        self.error_logs: deque = deque(maxlen=1000)
        
        # Background monitoring
        self._monitoring_active = False
        self._monitoring_thread = None
        
        self._load_persistent_data()
        self._start_monitoring()
    
    def _load_persistent_data(self):
        """Load persistent analytics data"""
        try:
            # Load model usage stats
            usage_file = self.data_dir / "model_usage.json"
            if usage_file.exists():
                with open(usage_file, 'r') as f:
                    data = json.load(f)
                    self.model_usage = {k: ModelUsageStats(**v) for k, v in data.items()}
            
            # Load search trends
            trends_file = self.data_dir / "search_trends.json"
            if trends_file.exists():
                with open(trends_file, 'r') as f:
                    data = json.load(f)
                    self.search_trends = {k: SearchTrend(**v) for k, v in data.items()}
            
            # Load cache metrics
            cache_file = self.data_dir / "cache_metrics.json"
            if cache_file.exists():
                with open(cache_file, 'r') as f:
                    data = json.load(f)
                    self.cache_metrics = {k: CacheMetrics(**v) for k, v in data.items()}
                    
        except Exception as e:
            print(f"Error loading analytics data: {e}")
    
    def _save_persistent_data(self):
        """Save persistent analytics data"""
        try:
            # Save model usage stats
            with open(self.data_dir / "model_usage.json", 'w') as f:
                data = {k: asdict(v) for k, v in self.model_usage.items()}
                json.dump(data, f, indent=2)
            
            # Save search trends
            with open(self.data_dir / "search_trends.json", 'w') as f:
                data = {k: asdict(v) for k, v in self.search_trends.items()}
                json.dump(data, f, indent=2)
            
            # Save cache metrics
            with open(self.data_dir / "cache_metrics.json", 'w') as f:
                data = {k: asdict(v) for k, v in self.cache_metrics.items()}
                json.dump(data, f, indent=2)
                
        except Exception as e:
            print(f"Error saving analytics data: {e}")
    
    def _start_monitoring(self):
        """Start background monitoring thread"""
        if self._monitoring_active:
            return
        
        self._monitoring_active = True
        
        def monitoring_loop():
            while self._monitoring_active:
                try:
                    self._collect_system_metrics()
                    time.sleep(60)  # Collect metrics every minute
                except Exception as e:
                    print(f"Error in monitoring loop: {e}")
                    time.sleep(60)
        
        self._monitoring_thread = threading.Thread(target=monitoring_loop, daemon=True)
        self._monitoring_thread.start()
    
    def _collect_system_metrics(self):
        """Collect current system metrics"""
        try:
            import psutil
            
            metrics = SystemMetrics(
                timestamp=datetime.now().isoformat(),
                cpu_usage=psutil.cpu_percent(),
                memory_usage=psutil.virtual_memory().percent,
                disk_usage=psutil.disk_usage('/').percent,
                active_sessions=len(self.active_sessions),
                total_requests=len(self.request_logs),
                error_rate=self._calculate_error_rate(),
                avg_response_time=self._calculate_avg_response_time()
            )
            
            self.system_metrics.append(metrics)
            
        except ImportError:
            print("psutil not available - using mock system metrics")
            # Mock metrics for demonstration
            metrics = SystemMetrics(
                timestamp=datetime.now().isoformat(),
                cpu_usage=25.0,
                memory_usage=45.0,
                disk_usage=60.0,
                active_sessions=len(self.active_sessions),
                total_requests=len(self.request_logs),
                error_rate=self._calculate_error_rate(),
                avg_response_time=self._calculate_avg_response_time()
            )
            self.system_metrics.append(metrics)
    
    def _calculate_error_rate(self) -> float:
        """Calculate current error rate"""
        if not self.request_logs:
            return 0.0
        
        recent_requests = [log for log in self.request_logs 
                          if (datetime.now() - datetime.fromisoformat(log['timestamp'])).seconds < 3600]
        
        if not recent_requests:
            return 0.0
        
        error_count = sum(1 for log in recent_requests if log.get('status_code', 200) >= 400)
        return (error_count / len(recent_requests)) * 100
    
    def _calculate_avg_response_time(self) -> float:
        """Calculate average response time"""
        if not self.request_logs:
            return 0.0
        
        recent_requests = [log for log in self.request_logs 
                          if (datetime.now() - datetime.fromisoformat(log['timestamp'])).seconds < 3600]
        
        if not recent_requests:
            return 0.0
        
        response_times = [log.get('response_time', 0) for log in recent_requests]
        return sum(response_times) / len(response_times)
    
    def track_model_usage(self, model_name: str, action: str, **kwargs):
        """Track model usage events"""
        if model_name not in self.model_usage:
            self.model_usage[model_name] = ModelUsageStats(
                model_name=model_name,
                total_views=0,
                total_downloads=0,
                avg_load_time=0.0,
                user_ratings=[],
                peak_concurrent_users=0,
                bandwidth_used=0,
                lod_distribution={},
                last_accessed=datetime.now().isoformat()
            )
        
        stats = self.model_usage[model_name]
        stats.last_accessed = datetime.now().isoformat()
        
        if action == "view":
            stats.total_views += 1
        elif action == "download":
            stats.total_downloads += 1
            stats.bandwidth_used += kwargs.get('file_size', 0)
        elif action == "rating":
            rating = kwargs.get('rating', 0)
            if 0 <= rating <= 5:
                stats.user_ratings.append(rating)
        elif action == "lod_selection":
            lod_level = kwargs.get('lod_level', 0)
            stats.lod_distribution[lod_level] = stats.lod_distribution.get(lod_level, 0) + 1
        
        # Update load time
        if 'load_time' in kwargs:
            current_avg = stats.avg_load_time
            total_views = stats.total_views
            new_time = kwargs['load_time']
            stats.avg_load_time = ((current_avg * (total_views - 1)) + new_time) / total_views
    
    def track_search_trend(self, query: str, results_count: int, success: bool):
        """Track search trends and patterns"""
        query_lower = query.lower().strip()
        
        if query_lower not in self.search_trends:
            self.search_trends[query_lower] = SearchTrend(
                query=query_lower,
                search_count=0,
                success_rate=0.0,
                avg_results=0.0,
                peak_times=[],
                user_demographics={}
            )
        
        trend = self.search_trends[query_lower]
        trend.search_count += 1
        
        # Update success rate
        current_success_count = trend.success_rate * (trend.search_count - 1) / 100
        if success:
            current_success_count += 1
        trend.success_rate = (current_success_count / trend.search_count) * 100
        
        # Update average results
        current_total_results = trend.avg_results * (trend.search_count - 1)
        trend.avg_results = (current_total_results + results_count) / trend.search_count
        
        # Track peak times
        current_hour = datetime.now().hour
        if len(trend.peak_times) < 24:
            trend.peak_times.extend([0] * (24 - len(trend.peak_times)))
        trend.peak_times[current_hour] += 1
    
    def update_cache_metrics(self, cache_type: str, hit: bool, latency: float):
        """Update cache performance metrics"""
        if cache_type not in self.cache_metrics:
            self.cache_metrics[cache_type] = CacheMetrics(
                cache_type=cache_type,
                hit_ratio=0.0,
                miss_ratio=0.0,
                total_requests=0,
                avg_latency=0.0,
                storage_size=0,
                eviction_count=0
            )
        
        metrics = self.cache_metrics[cache_type]
        metrics.total_requests += 1
        
        # Update hit/miss ratios
        current_hits = metrics.hit_ratio * (metrics.total_requests - 1) / 100
        if hit:
            current_hits += 1
        
        metrics.hit_ratio = (current_hits / metrics.total_requests) * 100
        metrics.miss_ratio = 100 - metrics.hit_ratio
        
        # Update average latency
        current_total_latency = metrics.avg_latency * (metrics.total_requests - 1)
        metrics.avg_latency = (current_total_latency + latency) / metrics.total_requests
    
    def log_request(self, method: str, endpoint: str, status_code: int, 
                   response_time: float, user_id: str = None):
        """Log API request for analytics"""
        log_entry = {
            "timestamp": datetime.now().isoformat(),
            "method": method,
            "endpoint": endpoint,
            "status_code": status_code,
            "response_time": response_time,
            "user_id": user_id
        }
        
        self.request_logs.append(log_entry)
        
        # Track errors separately
        if status_code >= 400:
            self.error_logs.append(log_entry)
    
    def start_user_session(self, user_id: str, session_data: Dict[str, Any]):
        """Start tracking a user session"""
        session_id = f"{user_id}_{int(time.time())}"
        self.active_sessions[session_id] = {
            "user_id": user_id,
            "start_time": datetime.now().isoformat(),
            "session_data": session_data,
            "activity_count": 0,
            "models_viewed": [],
            "searches_performed": []
        }
        return session_id
    
    def end_user_session(self, session_id: str):
        """End a user session and save analytics"""
        if session_id in self.active_sessions:
            session = self.active_sessions[session_id]
            session["end_time"] = datetime.now().isoformat()
            
            # Save to user behavior history
            user_id = session["user_id"]
            self.user_behavior[user_id].append(session)
            
            # Keep only recent behavior (last 100 sessions per user)
            if len(self.user_behavior[user_id]) > 100:
                self.user_behavior[user_id] = self.user_behavior[user_id][-100:]
            
            del self.active_sessions[session_id]
    
    def get_dashboard_overview(self) -> Dict[str, Any]:
        """Get comprehensive dashboard overview"""
        current_time = datetime.now()
        
        # Recent system metrics
        recent_metrics = list(self.system_metrics)[-60:]  # Last hour
        
        # Top models by usage
        top_models = sorted(
            self.model_usage.values(),
            key=lambda x: x.total_views + x.total_downloads,
            reverse=True
        )[:10]
        
        # Popular searches
        popular_searches = sorted(
            self.search_trends.values(),
            key=lambda x: x.search_count,
            reverse=True
        )[:10]
        
        return {
            "timestamp": current_time.isoformat(),
            "system_health": {
                "status": "healthy" if recent_metrics and recent_metrics[-1].cpu_usage < 80 else "warning",
                "uptime_hours": len(self.system_metrics),
                "active_sessions": len(self.active_sessions),
                "total_users": len(self.user_behavior),
                "requests_last_hour": len([log for log in self.request_logs 
                                         if (current_time - datetime.fromisoformat(log['timestamp'])).seconds < 3600])
            },
            "performance_metrics": {
                "avg_cpu_usage": sum(m.cpu_usage for m in recent_metrics) / len(recent_metrics) if recent_metrics else 0,
                "avg_memory_usage": sum(m.memory_usage for m in recent_metrics) / len(recent_metrics) if recent_metrics else 0,
                "current_error_rate": recent_metrics[-1].error_rate if recent_metrics else 0,
                "avg_response_time": recent_metrics[-1].avg_response_time if recent_metrics else 0
            },
            "content_stats": {
                "total_models": len(self.model_usage),
                "total_views": sum(stats.total_views for stats in self.model_usage.values()),
                "total_downloads": sum(stats.total_downloads for stats in self.model_usage.values()),
                "bandwidth_used_gb": sum(stats.bandwidth_used for stats in self.model_usage.values()) / (1024**3)
            },
            "top_models": [
                {
                    "name": model.model_name,
                    "views": model.total_views,
                    "downloads": model.total_downloads,
                    "avg_rating": sum(model.user_ratings) / len(model.user_ratings) if model.user_ratings else 0,
                    "last_accessed": model.last_accessed
                }
                for model in top_models
            ],
            "search_insights": {
                "total_searches": sum(trend.search_count for trend in self.search_trends.values()),
                "avg_success_rate": sum(trend.success_rate for trend in self.search_trends.values()) / len(self.search_trends) if self.search_trends else 0,
                "popular_queries": [
                    {
                        "query": trend.query,
                        "count": trend.search_count,
                        "success_rate": trend.success_rate
                    }
                    for trend in popular_searches
                ]
            },
            "cache_performance": {
                cache_type: {
                    "hit_ratio": metrics.hit_ratio,
                    "avg_latency": metrics.avg_latency,
                    "total_requests": metrics.total_requests
                }
                for cache_type, metrics in self.cache_metrics.items()
            }
        }
    
    def get_detailed_analytics(self, time_range: str = "24h") -> Dict[str, Any]:
        """Get detailed analytics for specified time range"""
        # Parse time range
        if time_range == "1h":
            cutoff = datetime.now() - timedelta(hours=1)
            metrics_slice = list(self.system_metrics)[-60:]
        elif time_range == "24h":
            cutoff = datetime.now() - timedelta(hours=24)
            metrics_slice = list(self.system_metrics)[-1440:]
        elif time_range == "7d":
            cutoff = datetime.now() - timedelta(days=7)
            metrics_slice = list(self.system_metrics)[-10080:]
        else:
            cutoff = datetime.now() - timedelta(hours=24)
            metrics_slice = list(self.system_metrics)[-1440:]
        
        return {
            "time_range": time_range,
            "system_metrics_timeline": [
                {
                    "timestamp": m.timestamp,
                    "cpu_usage": m.cpu_usage,
                    "memory_usage": m.memory_usage,
                    "active_sessions": m.active_sessions,
                    "response_time": m.avg_response_time
                }
                for m in metrics_slice
            ],
            "model_analytics": {
                model_name: {
                    "total_views": stats.total_views,
                    "total_downloads": stats.total_downloads,
                    "avg_load_time": stats.avg_load_time,
                    "avg_rating": sum(stats.user_ratings) / len(stats.user_ratings) if stats.user_ratings else 0,
                    "lod_distribution": stats.lod_distribution,
                    "bandwidth_used": stats.bandwidth_used
                }
                for model_name, stats in self.model_usage.items()
            },
            "user_behavior_patterns": self._analyze_user_patterns(cutoff),
            "error_analysis": self._analyze_errors(cutoff),
            "performance_trends": self._analyze_performance_trends(metrics_slice)
        }
    
    def _analyze_user_patterns(self, cutoff: datetime) -> Dict[str, Any]:
        """Analyze user behavior patterns"""
        patterns = {
            "avg_session_duration": 0,
            "peak_hours": [0] * 24,
            "device_distribution": defaultdict(int),
            "most_viewed_models": defaultdict(int),
            "user_retention": 0
        }
        
        session_durations = []
        for user_sessions in self.user_behavior.values():
            for session in user_sessions:
                # Skip if outside time range
                session_start = datetime.fromisoformat(session["start_time"])
                if session_start < cutoff:
                    continue
                
                # Calculate session duration
                if "end_time" in session:
                    end_time = datetime.fromisoformat(session["end_time"])
                    duration = (end_time - session_start).total_seconds() / 60  # minutes
                    session_durations.append(duration)
                
                # Track peak hours
                patterns["peak_hours"][session_start.hour] += 1
                
                # Device distribution
                device_type = session.get("session_data", {}).get("device_type", "unknown")
                patterns["device_distribution"][device_type] += 1
                
                # Most viewed models
                for model in session.get("models_viewed", []):
                    patterns["most_viewed_models"][model] += 1
        
        if session_durations:
            patterns["avg_session_duration"] = sum(session_durations) / len(session_durations)
        
        return patterns
    
    def _analyze_errors(self, cutoff: datetime) -> Dict[str, Any]:
        """Analyze error patterns"""
        recent_errors = [
            log for log in self.error_logs
            if datetime.fromisoformat(log['timestamp']) >= cutoff
        ]
        
        error_analysis = {
            "total_errors": len(recent_errors),
            "error_by_status": defaultdict(int),
            "error_by_endpoint": defaultdict(int),
            "error_timeline": []
        }
        
        for error in recent_errors:
            error_analysis["error_by_status"][error["status_code"]] += 1
            error_analysis["error_by_endpoint"][error["endpoint"]] += 1
        
        return error_analysis
    
    def _analyze_performance_trends(self, metrics: List[SystemMetrics]) -> Dict[str, Any]:
        """Analyze performance trends"""
        if not metrics:
            return {}
        
        cpu_values = [m.cpu_usage for m in metrics]
        memory_values = [m.memory_usage for m in metrics]
        response_times = [m.avg_response_time for m in metrics]
        
        return {
            "cpu_trend": {
                "min": min(cpu_values),
                "max": max(cpu_values),
                "avg": sum(cpu_values) / len(cpu_values),
                "trend": "increasing" if cpu_values[-1] > cpu_values[0] else "decreasing"
            },
            "memory_trend": {
                "min": min(memory_values),
                "max": max(memory_values),
                "avg": sum(memory_values) / len(memory_values),
                "trend": "increasing" if memory_values[-1] > memory_values[0] else "decreasing"
            },
            "response_time_trend": {
                "min": min(response_times),
                "max": max(response_times),
                "avg": sum(response_times) / len(response_times),
                "trend": "increasing" if response_times[-1] > response_times[0] else "decreasing"
            }
        }
    
    def cleanup_old_data(self, days_to_keep: int = 30):
        """Clean up old analytics data"""
        cutoff = datetime.now() - timedelta(days=days_to_keep)
        
        # Clean user behavior data
        for user_id in list(self.user_behavior.keys()):
            sessions = self.user_behavior[user_id]
            recent_sessions = [
                session for session in sessions
                if datetime.fromisoformat(session["start_time"]) >= cutoff
            ]
            if recent_sessions:
                self.user_behavior[user_id] = recent_sessions
            else:
                del self.user_behavior[user_id]
        
        self._save_persistent_data()


# Initialize global analytics engine
admin_analytics = AdminAnalyticsEngine()