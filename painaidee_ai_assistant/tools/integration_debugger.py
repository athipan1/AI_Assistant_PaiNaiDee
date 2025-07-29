#!/usr/bin/env python3
"""
3D-AI Integration Debugging and Error Handling System
Provides comprehensive debugging tools and error recovery mechanisms
"""

import json
import logging
import time
import traceback
import requests
from typing import Dict, List, Any, Optional, Tuple
from datetime import datetime
from pathlib import Path
import sys
import os

class IntegrationDebugger:
    """Comprehensive debugging system for 3D-AI integration"""
    
    def __init__(self, base_url: str = "http://localhost:8000", log_file: str = "integration_debug.log"):
        self.base_url = base_url
        self.log_file = log_file
        self.error_history = []
        self.debug_sessions = []
        
        # Setup detailed logging
        self.setup_logging()
        
    def setup_logging(self):
        """Setup comprehensive logging system"""
        logging.basicConfig(
            level=logging.DEBUG,
            format='%(asctime)s - %(name)s - %(levelname)s - %(funcName)s:%(lineno)d - %(message)s',
            handlers=[
                logging.FileHandler(self.log_file),
                logging.StreamHandler(sys.stdout)
            ]
        )
        self.logger = logging.getLogger(__name__)
        
    def log_error(self, error_type: str, error_details: Dict[str, Any], context: Dict[str, Any] = None):
        """Log detailed error information"""
        error_entry = {
            "timestamp": datetime.now().isoformat(),
            "error_type": error_type,
            "error_details": error_details,
            "context": context or {},
            "stack_trace": traceback.format_stack()
        }
        
        self.error_history.append(error_entry)
        self.logger.error(f"INTEGRATION ERROR [{error_type}]: {error_details}")
        
        if context:
            self.logger.debug(f"Error context: {json.dumps(context, indent=2)}")
    
    def diagnose_api_connectivity(self) -> Dict[str, Any]:
        """Diagnose API connectivity and endpoint availability"""
        self.logger.info("🔍 Diagnosing API connectivity...")
        
        endpoints_to_test = [
            ("/health", "GET", "System health check"),
            ("/ai/models", "GET", "3D models listing"),
            ("/ai/select_model", "POST", "AI model selection"),
            ("/emotion/analyze_emotion", "POST", "Emotion analysis"),
            ("/action/generate_plan", "POST", "Action plan generation")
        ]
        
        connectivity_results = {}
        
        for endpoint, method, description in endpoints_to_test:
            try:
                if method == "GET":
                    response = requests.get(f"{self.base_url}{endpoint}", timeout=10)
                else:
                    # Use minimal valid payload for POST requests
                    test_payloads = {
                        "/ai/select_model": {"question": "test", "language": "en"},
                        "/emotion/analyze_emotion": {"text": "test", "language": "en"},
                        "/action/generate_plan": {"intent": "greet_user", "parameters": {}}
                    }
                    payload = test_payloads.get(endpoint, {})
                    response = requests.post(f"{self.base_url}{endpoint}", json=payload, timeout=10)
                
                connectivity_results[endpoint] = {
                    "status": "accessible",
                    "status_code": response.status_code,
                    "response_time": response.elapsed.total_seconds(),
                    "description": description,
                    "response_size": len(response.content) if response.content else 0
                }
                
                self.logger.info(f"✅ {endpoint}: {response.status_code} ({response.elapsed.total_seconds():.2f}s)")
                
            except requests.exceptions.Timeout:
                connectivity_results[endpoint] = {
                    "status": "timeout",
                    "error": "Request timed out",
                    "description": description
                }
                self.logger.error(f"⏰ {endpoint}: Timeout")
                
            except requests.exceptions.ConnectionError:
                connectivity_results[endpoint] = {
                    "status": "connection_error",
                    "error": "Cannot connect to server",
                    "description": description
                }
                self.logger.error(f"🔌 {endpoint}: Connection error")
                
            except Exception as e:
                connectivity_results[endpoint] = {
                    "status": "error",
                    "error": str(e),
                    "description": description
                }
                self.logger.error(f"❌ {endpoint}: {str(e)}")
        
        return connectivity_results
    
    def diagnose_3d_model_issues(self) -> Dict[str, Any]:
        """Diagnose 3D model availability and accessibility issues"""
        self.logger.info("🎭 Diagnosing 3D model issues...")
        
        model_diagnosis = {}
        
        try:
            # Get list of available models
            response = requests.get(f"{self.base_url}/ai/models", timeout=10)
            
            if response.status_code != 200:
                self.log_error("MODEL_LIST_ERROR", {
                    "status_code": response.status_code,
                    "response": response.text
                })
                return {"error": "Cannot retrieve model list"}
            
            models_data = response.json()
            models = models_data.get("models", [])
            
            self.logger.info(f"Found {len(models)} models to test")
            
            for model in models:
                model_name = model["name"]
                model_path = model["path"]
                
                self.logger.debug(f"Testing model: {model_name}")
                
                # Test model file accessibility
                try:
                    model_response = requests.get(f"{self.base_url}/models/{model_name}", timeout=5, stream=True)
                    
                    model_diagnosis[model_name] = {
                        "accessible": model_response.status_code == 200,
                        "status_code": model_response.status_code,
                        "file_path": model_path,
                        "size_bytes": model.get("size", "unknown"),
                        "format": model.get("format", "unknown"),
                        "characteristics": model.get("characteristics", {})
                    }
                    model_response.close()  # Close stream to avoid downloading full file
                    
                    # Test if file exists on filesystem
                    if os.path.exists(model_path):
                        file_size = os.path.getsize(model_path)
                        model_diagnosis[model_name]["file_exists"] = True
                        model_diagnosis[model_name]["actual_size"] = file_size
                        
                        # Check if size matches
                        expected_size = model.get("size", 0)
                        if expected_size and abs(file_size - expected_size) > 1024:  # Allow 1KB difference
                            model_diagnosis[model_name]["size_mismatch"] = True
                            self.logger.warning(f"⚠️ {model_name}: Size mismatch (expected: {expected_size}, actual: {file_size})")
                    else:
                        model_diagnosis[model_name]["file_exists"] = False
                        self.logger.error(f"❌ {model_name}: File not found at {model_path}")
                    
                except Exception as e:
                    model_diagnosis[model_name] = {
                        "accessible": False,
                        "error": str(e),
                        "file_path": model_path
                    }
                    self.logger.error(f"❌ {model_name}: Access error - {str(e)}")
            
        except Exception as e:
            self.log_error("MODEL_DIAGNOSIS_ERROR", {"error": str(e)})
            return {"error": f"Model diagnosis failed: {str(e)}"}
        
        return model_diagnosis
    
    def diagnose_ai_selection_issues(self) -> Dict[str, Any]:
        """Diagnose AI model selection logic issues"""
        self.logger.info("🧠 Diagnosing AI selection issues...")
        
        # Test various types of queries to identify selection issues
        test_queries = [
            {"query": "Show me a walking person", "expected_keywords": ["walking", "person"]},
            {"query": "Display running animation", "expected_keywords": ["running", "animation"]},
            {"query": "", "test_type": "empty_query"},
            {"query": "xyzabc123", "test_type": "gibberish_query"},
            {"query": "Show me something very specific that probably doesn't exist", "test_type": "no_match_query"}
        ]
        
        selection_diagnosis = {}
        
        for test in test_queries:
            query = test["query"]
            test_type = test.get("test_type", "normal")
            
            try:
                self.logger.debug(f"Testing query: '{query}'")
                
                response = requests.post(
                    f"{self.base_url}/ai/select_model",
                    json={"question": query, "language": "en"},
                    timeout=15
                )
                
                if response.status_code != 200:
                    selection_diagnosis[query] = {
                        "success": False,
                        "error": f"HTTP {response.status_code}",
                        "test_type": test_type
                    }
                    continue
                
                data = response.json()
                model_selection = data.get("model_selection", {})
                ai_analysis = data.get("ai_analysis", {})
                
                # Analyze the response quality
                analysis = {
                    "success": True,
                    "test_type": test_type,
                    "selected_model": model_selection.get("selected_model"),
                    "confidence": model_selection.get("confidence", 0),
                    "response_time": response.elapsed.total_seconds(),
                    "reasoning_provided": bool(model_selection.get("reasoning")),
                    "ai_analysis_present": bool(ai_analysis),
                    "response_quality": "unknown"
                }
                
                # Evaluate response quality based on test type
                if test_type == "normal":
                    confidence = analysis["confidence"]
                    if confidence > 0.5:
                        analysis["response_quality"] = "good"
                    elif confidence > 0.2:
                        analysis["response_quality"] = "acceptable"
                    else:
                        analysis["response_quality"] = "poor"
                        
                elif test_type == "empty_query":
                    # Should handle gracefully
                    analysis["response_quality"] = "good" if analysis["selected_model"] else "poor"
                    
                elif test_type in ["gibberish_query", "no_match_query"]:
                    # Should have low confidence or fallback
                    analysis["response_quality"] = "good" if confidence < 0.3 else "poor"
                
                selection_diagnosis[query] = analysis
                
                self.logger.info(f"📊 '{query}' -> {analysis['selected_model']} (confidence: {confidence:.2f})")
                
            except Exception as e:
                selection_diagnosis[query] = {
                    "success": False,
                    "error": str(e),
                    "test_type": test_type
                }
                self.log_error("AI_SELECTION_ERROR", {"query": query, "error": str(e)})
        
        return selection_diagnosis
    
    def diagnose_synchronization_issues(self) -> Dict[str, Any]:
        """Diagnose synchronization timing issues"""
        self.logger.info("⏱️ Diagnosing synchronization issues...")
        
        sync_tests = []
        
        # Test response times for different scenarios
        for i in range(3):
            test_query = f"Show walking animation test {i+1}"
            
            # Measure AI response time
            ai_start = time.time()
            try:
                response = requests.post(
                    f"{self.base_url}/ai/select_model",
                    json={"question": test_query, "language": "en"},
                    timeout=10
                )
                ai_end = time.time()
                ai_time = ai_end - ai_start
                
                if response.status_code == 200:
                    data = response.json()
                    selected_model = data.get("model_selection", {}).get("selected_model")
                    
                    # Simulate 3D model loading time
                    model_start = time.time()
                    model_response = requests.get(f"{self.base_url}/models/{selected_model}", timeout=5, stream=True)
                    model_end = time.time()
                    model_time = model_end - model_start
                    model_response.close()  # Close stream to avoid downloading full file
                    
                    total_time = ai_time + model_time
                    
                    sync_test = {
                        "test_number": i + 1,
                        "query": test_query,
                        "ai_response_time": ai_time,
                        "model_access_time": model_time,
                        "total_time": total_time,
                        "selected_model": selected_model,
                        "sync_acceptable": total_time < 2.0,
                        "issues": []
                    }
                    
                    # Identify potential issues
                    if ai_time > 1.5:
                        sync_test["issues"].append("AI response too slow")
                    if model_time > 1.0:
                        sync_test["issues"].append("Model access too slow")
                    if total_time > 3.0:
                        sync_test["issues"].append("Total time unacceptable")
                    
                    sync_tests.append(sync_test)
                    
                else:
                    sync_tests.append({
                        "test_number": i + 1,
                        "query": test_query,
                        "error": f"AI request failed: HTTP {response.status_code}",
                        "sync_acceptable": False
                    })
                    
            except Exception as e:
                sync_tests.append({
                    "test_number": i + 1,
                    "query": test_query,
                    "error": str(e),
                    "sync_acceptable": False
                })
        
        # Calculate overall synchronization health
        successful_tests = [t for t in sync_tests if t.get("sync_acceptable", False)]
        avg_ai_time = sum(t["ai_response_time"] for t in successful_tests) / len(successful_tests) if successful_tests else 0
        avg_total_time = sum(t["total_time"] for t in successful_tests) / len(successful_tests) if successful_tests else 0
        
        return {
            "sync_tests": sync_tests,
            "summary": {
                "total_tests": len(sync_tests),
                "successful_tests": len(successful_tests),
                "success_rate": len(successful_tests) / len(sync_tests) if sync_tests else 0,
                "average_ai_time": avg_ai_time,
                "average_total_time": avg_total_time,
                "sync_health": "good" if len(successful_tests) >= 2 and avg_total_time < 2.0 else "poor"
            }
        }
    
    def run_comprehensive_diagnosis(self) -> Dict[str, Any]:
        """Run complete diagnostic suite"""
        self.logger.info("🏥 Starting Comprehensive Integration Diagnosis")
        self.logger.info("=" * 80)
        
        diagnosis_start = time.time()
        
        diagnosis_results = {
            "timestamp": datetime.now().isoformat(),
            "diagnostics": {},
            "overall_health": "unknown",
            "critical_issues": [],
            "recommendations": []
        }
        
        # Run individual diagnostic modules
        diagnostic_modules = [
            ("API Connectivity", self.diagnose_api_connectivity),
            ("3D Model Issues", self.diagnose_3d_model_issues),
            ("AI Selection Issues", self.diagnose_ai_selection_issues),
            ("Synchronization Issues", self.diagnose_synchronization_issues)
        ]
        
        for module_name, diagnostic_function in diagnostic_modules:
            self.logger.info(f"\n🔧 Running {module_name} diagnosis...")
            
            try:
                module_results = diagnostic_function()
                diagnosis_results["diagnostics"][module_name] = module_results
                
                # Check for critical issues
                self._analyze_module_for_critical_issues(module_name, module_results, diagnosis_results)
                
            except Exception as e:
                self.logger.error(f"❌ {module_name} diagnosis failed: {str(e)}")
                diagnosis_results["diagnostics"][module_name] = {"error": str(e)}
                diagnosis_results["critical_issues"].append(f"{module_name} diagnosis failed: {str(e)}")
        
        # Determine overall health
        critical_count = len(diagnosis_results["critical_issues"])
        if critical_count == 0:
            diagnosis_results["overall_health"] = "excellent"
        elif critical_count <= 2:
            diagnosis_results["overall_health"] = "good"
        elif critical_count <= 4:
            diagnosis_results["overall_health"] = "fair"
        else:
            diagnosis_results["overall_health"] = "poor"
        
        # Generate recommendations
        self._generate_recommendations(diagnosis_results)
        
        diagnosis_time = time.time() - diagnosis_start
        
        self.logger.info(f"\n" + "=" * 80)
        self.logger.info(f"🏥 DIAGNOSIS COMPLETE ({diagnosis_time:.1f}s)")
        self.logger.info("=" * 80)
        self.logger.info(f"Overall Health: {diagnosis_results['overall_health'].upper()}")
        self.logger.info(f"Critical Issues: {critical_count}")
        
        if diagnosis_results["critical_issues"]:
            self.logger.error("🚨 CRITICAL ISSUES FOUND:")
            for issue in diagnosis_results["critical_issues"]:
                self.logger.error(f"  - {issue}")
        
        if diagnosis_results["recommendations"]:
            self.logger.info("💡 RECOMMENDATIONS:")
            for rec in diagnosis_results["recommendations"]:
                self.logger.info(f"  - {rec}")
        
        return diagnosis_results
    
    def _analyze_module_for_critical_issues(self, module_name: str, results: Dict[str, Any], diagnosis_results: Dict[str, Any]):
        """Analyze diagnostic module results for critical issues"""
        if module_name == "API Connectivity":
            for endpoint, result in results.items():
                if result.get("status") == "connection_error":
                    diagnosis_results["critical_issues"].append(f"Cannot connect to {endpoint}")
                elif result.get("status") == "timeout":
                    diagnosis_results["critical_issues"].append(f"Timeout accessing {endpoint}")
        
        elif module_name == "3D Model Issues":
            for model_name, result in results.items():
                if not result.get("accessible", False):
                    diagnosis_results["critical_issues"].append(f"3D model {model_name} not accessible")
                if not result.get("file_exists", True):
                    diagnosis_results["critical_issues"].append(f"3D model file {model_name} missing from filesystem")
        
        elif module_name == "AI Selection Issues":
            poor_responses = [q for q, r in results.items() if r.get("response_quality") == "poor"]
            if len(poor_responses) > 1:
                diagnosis_results["critical_issues"].append("AI selection quality is consistently poor")
        
        elif module_name == "Synchronization Issues":
            summary = results.get("summary", {})
            if summary.get("sync_health") == "poor":
                diagnosis_results["critical_issues"].append("Synchronization performance is poor")
    
    def _generate_recommendations(self, diagnosis_results: Dict[str, Any]):
        """Generate actionable recommendations based on diagnosis"""
        recommendations = []
        
        # Analyze issues and suggest fixes
        issues = diagnosis_results["critical_issues"]
        
        if any("connect" in issue.lower() for issue in issues):
            recommendations.append("Check if the FastAPI server is running on the correct port")
            recommendations.append("Verify network connectivity and firewall settings")
        
        if any("model" in issue.lower() and "accessible" in issue.lower() for issue in issues):
            recommendations.append("Check 3D model file paths and permissions")
            recommendations.append("Verify model files exist in the assets/models/Fbx directory")
        
        if any("timeout" in issue.lower() for issue in issues):
            recommendations.append("Increase timeout values or optimize server performance")
            recommendations.append("Check server resource usage (CPU, memory)")
        
        if any("ai selection" in issue.lower() for issue in issues):
            recommendations.append("Review AI model selection algorithms and confidence thresholds")
            recommendations.append("Update semantic search embeddings or model mappings")
        
        if any("synchronization" in issue.lower() for issue in issues):
            recommendations.append("Optimize AI response times by caching frequently used models")
            recommendations.append("Implement preloading for popular 3D models")
        
        diagnosis_results["recommendations"] = recommendations

def main():
    """Run the integration debugger"""
    import argparse
    
    parser = argparse.ArgumentParser(description="3D-AI Integration Debugger")
    parser.add_argument("--module", choices=["api", "models", "ai", "sync", "all"], 
                       default="all", help="Diagnostic module to run")
    parser.add_argument("--output", type=str, help="Output file for results")
    
    args = parser.parse_args()
    
    debugger = IntegrationDebugger()
    
    if args.module == "all":
        results = debugger.run_comprehensive_diagnosis()
    else:
        module_map = {
            "api": debugger.diagnose_api_connectivity,
            "models": debugger.diagnose_3d_model_issues,
            "ai": debugger.diagnose_ai_selection_issues,
            "sync": debugger.diagnose_synchronization_issues
        }
        results = module_map[args.module]()
    
    if args.output:
        with open(args.output, 'w') as f:
            json.dump(results, f, indent=2)
        print(f"Results saved to {args.output}")
    else:
        print(json.dumps(results, indent=2))

if __name__ == "__main__":
    main()