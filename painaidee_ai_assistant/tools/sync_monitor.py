#!/usr/bin/env python3
"""
Real-time 3D Model-AI Synchronization Monitor
Monitors and logs the synchronization between AI responses and 3D model animations
"""

import asyncio
import json
import time
import logging
import requests
import websockets
from typing import Dict, List, Any, Optional
from datetime import datetime, timedelta
import threading
from collections import deque
import statistics

logger = logging.getLogger(__name__)

class SynchronizationMonitor:
    """Real-time synchronization monitoring for AI-3D integration"""
    
    def __init__(self, base_url: str = "http://localhost:8000"):
        self.base_url = base_url
        self.monitoring = False
        self.sync_events = deque(maxlen=1000)  # Keep last 1000 events
        self.performance_metrics = {
            "response_times": deque(maxlen=100),
            "sync_delays": deque(maxlen=100),
            "error_count": 0,
            "total_requests": 0
        }
        
    def log_sync_event(self, event_type: str, timestamp: float, details: Dict[str, Any]):
        """Log a synchronization event with timestamp"""
        event = {
            "type": event_type,
            "timestamp": timestamp,
            "datetime": datetime.fromtimestamp(timestamp).isoformat(),
            "details": details
        }
        self.sync_events.append(event)
        
    def measure_ai_response_time(self, query: str) -> Dict[str, Any]:
        """Measure AI response time and extract timing data"""
        start_time = time.time()
        
        try:
            response = requests.post(
                f"{self.base_url}/ai/select_model",
                json={"question": query, "language": "en"},
                timeout=10
            )
            
            end_time = time.time()
            response_time = end_time - start_time
            
            self.performance_metrics["total_requests"] += 1
            self.performance_metrics["response_times"].append(response_time)
            
            if response.status_code == 200:
                data = response.json()
                model_selected = data.get("model_selection", {}).get("selected_model")
                confidence = data.get("model_selection", {}).get("confidence", 0)
                
                result = {
                    "success": True,
                    "response_time": response_time,
                    "model_selected": model_selected,
                    "confidence": confidence,
                    "ai_analysis_time": response_time,  # Full AI processing time
                    "timestamp": start_time
                }
                
                self.log_sync_event("ai_response", start_time, result)
                return result
            else:
                self.performance_metrics["error_count"] += 1
                result = {
                    "success": False,
                    "response_time": response_time,
                    "error": f"HTTP {response.status_code}",
                    "timestamp": start_time
                }
                self.log_sync_event("ai_error", start_time, result)
                return result
                
        except Exception as e:
            end_time = time.time()
            response_time = end_time - start_time
            self.performance_metrics["error_count"] += 1
            
            result = {
                "success": False,
                "response_time": response_time,
                "error": str(e),
                "timestamp": start_time
            }
            self.log_sync_event("ai_error", start_time, result)
            return result
    
    def simulate_3d_model_load_time(self, model_name: str) -> Dict[str, Any]:
        """Simulate and measure 3D model loading time"""
        start_time = time.time()
        
        try:
            # Check if model is accessible
            response = requests.get(f"{self.base_url}/models/{model_name}", timeout=5, stream=True)
            response.close()  # Close stream to avoid downloading full file
            
            # Simulate realistic 3D model loading times based on model size
            model_load_times = {
                "Man.fbx": 0.3,      # Small model
                "Idle.fbx": 0.8,     # Medium model with animation
                "Walking.fbx": 0.7,  # Medium animation model
                "Running.fbx": 0.7,  # Medium animation model  
                "Man_Rig.fbx": 0.6   # Rigged model
            }
            
            estimated_load_time = model_load_times.get(model_name, 0.5)
            
            # Simulate the loading delay
            time.sleep(estimated_load_time)
            
            end_time = time.time()
            actual_load_time = end_time - start_time
            
            if response.status_code == 200:
                result = {
                    "success": True,
                    "model_name": model_name,
                    "load_time": actual_load_time,
                    "estimated_time": estimated_load_time,
                    "accessible": True,
                    "timestamp": start_time
                }
                self.log_sync_event("model_loaded", start_time, result)
                return result
            else:
                result = {
                    "success": False,
                    "model_name": model_name,
                    "load_time": actual_load_time,
                    "error": f"Model not accessible: HTTP {response.status_code}",
                    "timestamp": start_time
                }
                self.log_sync_event("model_error", start_time, result)
                return result
                
        except Exception as e:
            end_time = time.time()
            actual_load_time = end_time - start_time
            
            result = {
                "success": False,
                "model_name": model_name,
                "load_time": actual_load_time,
                "error": str(e),
                "timestamp": start_time
            }
            self.log_sync_event("model_error", start_time, result)
            return result
    
    def test_end_to_end_synchronization(self, query: str) -> Dict[str, Any]:
        """Test complete end-to-end synchronization from query to 3D model display"""
        logger.info(f"🔄 Testing E2E sync for: '{query}'")
        
        # Step 1: Measure AI response
        ai_result = self.measure_ai_response_time(query)
        
        if not ai_result["success"]:
            return {
                "success": False,
                "stage": "ai_processing",
                "error": ai_result["error"],
                "total_time": ai_result["response_time"]
            }
        
        # Step 2: Measure 3D model loading
        model_name = ai_result["model_selected"]
        model_result = self.simulate_3d_model_load_time(model_name)
        
        # Calculate synchronization metrics
        total_time = ai_result["response_time"] + model_result["load_time"]
        sync_delay = model_result["load_time"]  # Time between AI response and model ready
        
        self.performance_metrics["sync_delays"].append(sync_delay)
        
        # Determine if synchronization is acceptable
        # Good synchronization: total time < 2 seconds, no stage > 1.5 seconds
        sync_acceptable = (
            total_time < 2.0 and 
            ai_result["response_time"] < 1.5 and 
            model_result["load_time"] < 1.5
        )
        
        result = {
            "success": ai_result["success"] and model_result["success"],
            "sync_acceptable": sync_acceptable,
            "query": query,
            "ai_response_time": ai_result["response_time"],
            "model_load_time": model_result["load_time"],
            "total_time": total_time,
            "sync_delay": sync_delay,
            "model_selected": model_name,
            "confidence": ai_result["confidence"],
            "timestamp": ai_result["timestamp"]
        }
        
        self.log_sync_event("e2e_sync_test", ai_result["timestamp"], result)
        
        if sync_acceptable:
            logger.info(f"✅ Sync OK: {total_time:.2f}s total (AI: {ai_result['response_time']:.2f}s, 3D: {model_result['load_time']:.2f}s)")
        else:
            logger.warning(f"⚠️ Sync slow: {total_time:.2f}s total (AI: {ai_result['response_time']:.2f}s, 3D: {model_result['load_time']:.2f}s)")
        
        return result
    
    def run_continuous_monitoring(self, duration_minutes: int = 5, interval_seconds: int = 10):
        """Run continuous synchronization monitoring"""
        logger.info(f"🎯 Starting continuous monitoring for {duration_minutes} minutes")
        logger.info(f"📊 Testing every {interval_seconds} seconds")
        
        self.monitoring = True
        start_time = time.time()
        end_time = start_time + (duration_minutes * 60)
        
        test_queries = [
            "Show me a walking person",
            "Display running animation", 
            "I want to see someone standing",
            "Show basic character model",
            "Demonstrate idle pose"
        ]
        
        query_index = 0
        test_count = 0
        successful_tests = 0
        
        try:
            while time.time() < end_time and self.monitoring:
                query = test_queries[query_index % len(test_queries)]
                query_index += 1
                test_count += 1
                
                logger.info(f"\n📈 Test {test_count}: {query}")
                
                result = self.test_end_to_end_synchronization(query)
                
                if result["success"] and result["sync_acceptable"]:
                    successful_tests += 1
                
                # Wait for next test
                time.sleep(interval_seconds)
            
        except KeyboardInterrupt:
            logger.info("\n⏹️ Monitoring stopped by user")
        
        self.monitoring = False
        
        # Generate monitoring report
        success_rate = successful_tests / test_count if test_count > 0 else 0
        
        logger.info(f"\n📊 MONITORING REPORT ({duration_minutes} minutes)")
        logger.info("=" * 50)
        logger.info(f"Total tests: {test_count}")
        logger.info(f"Successful syncs: {successful_tests}")
        logger.info(f"Success rate: {success_rate:.1%}")
        
        return {
            "duration_minutes": duration_minutes,
            "total_tests": test_count,
            "successful_tests": successful_tests,
            "success_rate": success_rate,
            "monitoring_events": list(self.sync_events)
        }
    
    def get_performance_statistics(self) -> Dict[str, Any]:
        """Get current performance statistics"""
        response_times = list(self.performance_metrics["response_times"])
        sync_delays = list(self.performance_metrics["sync_delays"])
        
        stats = {
            "total_requests": self.performance_metrics["total_requests"],
            "error_count": self.performance_metrics["error_count"],
            "error_rate": self.performance_metrics["error_count"] / max(1, self.performance_metrics["total_requests"]),
            "response_times": {
                "count": len(response_times),
                "average": statistics.mean(response_times) if response_times else 0,
                "median": statistics.median(response_times) if response_times else 0,
                "min": min(response_times) if response_times else 0,
                "max": max(response_times) if response_times else 0
            },
            "sync_delays": {
                "count": len(sync_delays),
                "average": statistics.mean(sync_delays) if sync_delays else 0,
                "median": statistics.median(sync_delays) if sync_delays else 0,
                "min": min(sync_delays) if sync_delays else 0,
                "max": max(sync_delays) if sync_delays else 0
            }
        }
        
        return stats
    
    def export_monitoring_data(self, filename: str = None):
        """Export monitoring data to JSON file"""
        if filename is None:
            filename = f"sync_monitoring_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
        
        data = {
            "timestamp": datetime.now().isoformat(),
            "performance_statistics": self.get_performance_statistics(),
            "sync_events": list(self.sync_events),
            "monitoring_active": self.monitoring
        }
        
        with open(filename, 'w') as f:
            json.dump(data, f, indent=2)
        
        logger.info(f"📁 Monitoring data exported to: {filename}")
        return filename

def main():
    """Run synchronization monitoring"""
    import argparse
    
    parser = argparse.ArgumentParser(description="3D-AI Synchronization Monitor")
    parser.add_argument("--duration", type=int, default=5, help="Monitoring duration in minutes")
    parser.add_argument("--interval", type=int, default=10, help="Test interval in seconds")
    parser.add_argument("--single-test", action="store_true", help="Run single synchronization test")
    parser.add_argument("--query", type=str, default="Show me a walking person", help="Query for single test")
    
    args = parser.parse_args()
    
    # Setup logging
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(levelname)s - %(message)s'
    )
    
    monitor = SynchronizationMonitor()
    
    if args.single_test:
        logger.info(f"🧪 Running single synchronization test")
        result = monitor.test_end_to_end_synchronization(args.query)
        print(json.dumps(result, indent=2))
    else:
        logger.info(f"🔄 Starting continuous monitoring")
        results = monitor.run_continuous_monitoring(args.duration, args.interval)
        
        # Export results
        filename = monitor.export_monitoring_data()
        
        # Print summary
        stats = monitor.get_performance_statistics()
        logger.info(f"\n📈 FINAL STATISTICS")
        logger.info(f"Average response time: {stats['response_times']['average']:.2f}s")
        logger.info(f"Average sync delay: {stats['sync_delays']['average']:.2f}s")
        logger.info(f"Error rate: {stats['error_rate']:.1%}")

if __name__ == "__main__":
    main()