#!/usr/bin/env python3
"""
Comprehensive 3D Model-AI Integration Verification Tests
Tests the complete pipeline: User Input → AI Analysis → 3D Model Selection → Animation Synchronization
"""

import asyncio
import json
import time
import logging
import requests
from typing import Dict, List, Any, Optional
from datetime import datetime
import sys
import os

# Setup logging for integration testing
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('integration_tests.log'),
        logging.StreamHandler(sys.stdout)
    ]
)
logger = logging.getLogger(__name__)

class ModelIntegrationVerifier:
    """Comprehensive 3D Model-AI Integration Verification System"""
    
    def __init__(self, base_url: str = "http://localhost:8000"):
        self.base_url = base_url
        self.test_results = []
        self.error_log = []
        
    def log_test_result(self, test_name: str, success: bool, details: Dict[str, Any]):
        """Log test result with timestamp and details"""
        result = {
            "test_name": test_name,
            "success": success,
            "timestamp": datetime.now().isoformat(),
            "details": details
        }
        self.test_results.append(result)
        
        if success:
            logger.info(f"✅ {test_name}: PASSED")
        else:
            logger.error(f"❌ {test_name}: FAILED - {details.get('error', 'Unknown error')}")
            self.error_log.append(result)
    
    def test_api_health_check(self) -> bool:
        """Verify basic API connectivity and health"""
        try:
            response = requests.get(f"{self.base_url}/health", timeout=10)
            health_data = response.json()
            
            required_features = [
                "3d_viewer", "ai_selection", "model_serving", 
                "emotion_analysis", "3d_gesture_recognition"
            ]
            
            missing_features = [
                feature for feature in required_features 
                if not health_data.get("features", {}).get(feature, False)
            ]
            
            success = response.status_code == 200 and len(missing_features) == 0
            
            self.log_test_result("API Health Check", success, {
                "status_code": response.status_code,
                "features_available": health_data.get("features", {}),
                "missing_features": missing_features,
                "models_available": health_data.get("models_available", 0)
            })
            
            return success
            
        except Exception as e:
            self.log_test_result("API Health Check", False, {"error": str(e)})
            return False
    
    def test_3d_model_availability(self) -> bool:
        """Verify all required 3D models are available and accessible"""
        try:
            response = requests.get(f"{self.base_url}/ai/models", timeout=10)
            models_data = response.json()
            
            required_models = ["Man.fbx", "Idle.fbx", "Walking.fbx", "Running.fbx", "Man_Rig.fbx"]
            available_models = [model["name"] for model in models_data.get("models", [])]
            
            missing_models = [model for model in required_models if model not in available_models]
            
            # Test individual model accessibility
            model_accessibility = {}
            for model_name in available_models:
                try:
                    model_response = requests.get(f"{self.base_url}/models/{model_name}", timeout=5, stream=True)
                    model_accessibility[model_name] = model_response.status_code == 200
                    model_response.close()  # Close stream to avoid downloading full file
                except:
                    model_accessibility[model_name] = False
            
            success = len(missing_models) == 0 and all(model_accessibility.values())
            
            self.log_test_result("3D Model Availability", success, {
                "available_models": available_models,
                "missing_models": missing_models,
                "model_accessibility": model_accessibility,
                "total_models": len(available_models)
            })
            
            return success
            
        except Exception as e:
            self.log_test_result("3D Model Availability", False, {"error": str(e)})
            return False
    
    def test_ai_model_selection_integration(self) -> bool:
        """Test AI model selection with various user inputs"""
        test_cases = [
            {
                "query": "Show me a walking person",
                "expected_model": "Walking.fbx",
                "description": "Basic walking animation request"
            },
            {
                "query": "I want to see someone running",
                "expected_model": "Running.fbx", 
                "description": "Running animation request"
            },
            {
                "query": "Display a character in idle pose",
                "expected_model": "Idle.fbx",
                "description": "Idle/static pose request"
            },
            {
                "query": "Show me a basic human figure",
                "expected_model": "Man.fbx",
                "description": "Basic character model request"
            }
        ]
        
        results = []
        
        for test_case in test_cases:
            try:
                response = requests.post(
                    f"{self.base_url}/ai/select_model",
                    json={"question": test_case["query"], "language": "en"},
                    timeout=15
                )
                
                if response.status_code != 200:
                    results.append({
                        "test_case": test_case,
                        "success": False,
                        "error": f"HTTP {response.status_code}"
                    })
                    continue
                
                data = response.json()
                selected_model = data.get("model_selection", {}).get("selected_model")
                confidence = data.get("model_selection", {}).get("confidence", 0)
                
                # Check if correct model was selected (allow flexibility for AI decisions)
                model_correct = selected_model == test_case["expected_model"]
                confidence_good = confidence > 0.2  # Reasonable confidence threshold
                
                results.append({
                    "test_case": test_case,
                    "success": model_correct and confidence_good,
                    "selected_model": selected_model,
                    "expected_model": test_case["expected_model"],
                    "confidence": confidence,
                    "response_time": response.elapsed.total_seconds()
                })
                
            except Exception as e:
                results.append({
                    "test_case": test_case,
                    "success": False,
                    "error": str(e)
                })
        
        success_count = sum(1 for r in results if r["success"])
        overall_success = success_count >= len(test_cases) * 0.75  # 75% success rate
        
        self.log_test_result("AI Model Selection Integration", overall_success, {
            "test_cases": len(test_cases),
            "successful": success_count,
            "success_rate": success_count / len(test_cases),
            "results": results
        })
        
        return overall_success
    
    def test_emotion_integration(self) -> bool:
        """Test emotion analysis integration with 3D model selection"""
        test_cases = [
            {
                "query": "I'm excited to see walking animations!",
                "expected_emotion": "excited",
                "description": "Positive emotion with walking request"
            },
            {
                "query": "I'm worried about running alone",
                "expected_emotion": "worried", 
                "description": "Negative emotion with running context"
            },
            {
                "query": "Show me a calm standing pose",
                "expected_emotion": "calm",
                "description": "Peaceful emotion request"
            }
        ]
        
        results = []
        
        for test_case in test_cases:
            try:
                response = requests.post(
                    f"{self.base_url}/ai/select_model_with_emotion",
                    json={"question": test_case["query"], "analyze_emotion": True},
                    timeout=15
                )
                
                if response.status_code != 200:
                    results.append({
                        "test_case": test_case,
                        "success": False,
                        "error": f"HTTP {response.status_code}"
                    })
                    continue
                
                data = response.json()
                emotion_analysis = data.get("emotion_analysis", {})
                detected_emotion = emotion_analysis.get("primary_emotion")
                gesture_suggested = emotion_analysis.get("suggested_gesture")
                
                # Check if emotion was detected and gesture was suggested
                emotion_detected = detected_emotion is not None
                gesture_available = gesture_suggested is not None
                
                results.append({
                    "test_case": test_case,
                    "success": emotion_detected and gesture_available,
                    "detected_emotion": detected_emotion,
                    "suggested_gesture": gesture_suggested,
                    "emotion_analysis": emotion_analysis
                })
                
            except Exception as e:
                results.append({
                    "test_case": test_case,
                    "success": False,
                    "error": str(e)
                })
        
        success_count = sum(1 for r in results if r["success"])
        overall_success = success_count >= len(test_cases) * 0.66  # 66% success rate for emotion integration
        
        self.log_test_result("Emotion-3D Integration", overall_success, {
            "test_cases": len(test_cases),
            "successful": success_count,
            "results": results
        })
        
        return overall_success
    
    def test_multimodal_action_plans(self) -> bool:
        """Test multimodal action plan generation for 3D interaction"""
        test_scenarios = [
            {
                "intent": "suggest_place",
                "parameters": {"place_name": "Walking Trail"},
                "description": "Tourism suggestion with 3D interaction"
            },
            {
                "intent": "greet_user", 
                "parameters": {},
                "description": "User greeting with gesture"
            },
            {
                "intent": "confirm_action",
                "parameters": {"action": "show_walking_demo"},
                "description": "Action confirmation with animation"
            }
        ]
        
        results = []
        
        for scenario in test_scenarios:
            try:
                response = requests.post(
                    f"{self.base_url}/action/generate_plan",
                    json={
                        "intent": scenario["intent"],
                        "parameters": scenario["parameters"]
                    },
                    timeout=10
                )
                
                if response.status_code != 200:
                    results.append({
                        "scenario": scenario,
                        "success": False,
                        "error": f"HTTP {response.status_code}"
                    })
                    continue
                
                data = response.json()
                
                # Check if action plan contains required components
                has_speech = len(data.get("speech_actions", [])) > 0
                has_gesture = len(data.get("gesture_actions", [])) > 0
                has_ui = len(data.get("ui_actions", [])) > 0
                has_execution_order = "execution_order" in data
                
                success = has_speech and has_gesture and has_execution_order
                
                results.append({
                    "scenario": scenario,
                    "success": success,
                    "action_plan": data,
                    "components": {
                        "speech": has_speech,
                        "gesture": has_gesture, 
                        "ui": has_ui,
                        "execution_order": has_execution_order
                    }
                })
                
            except Exception as e:
                results.append({
                    "scenario": scenario,
                    "success": False,
                    "error": str(e)
                })
        
        success_count = sum(1 for r in results if r["success"])
        overall_success = success_count >= len(test_scenarios) * 0.66
        
        self.log_test_result("Multimodal Action Plans", overall_success, {
            "scenarios": len(test_scenarios),
            "successful": success_count,
            "results": results
        })
        
        return overall_success
    
    def test_synchronization_timing(self) -> bool:
        """Test response timing for real-time synchronization"""
        timing_tests = []
        
        for i in range(5):  # Run multiple timing tests
            start_time = time.time()
            
            try:
                response = requests.post(
                    f"{self.base_url}/ai/select_model",
                    json={"question": f"Show walking animation test {i}", "language": "en"},
                    timeout=10
                )
                
                end_time = time.time()
                response_time = end_time - start_time
                
                timing_tests.append({
                    "test_number": i + 1,
                    "response_time": response_time,
                    "status_code": response.status_code,
                    "success": response.status_code == 200 and response_time < 2.0  # 2 second threshold
                })
                
            except Exception as e:
                timing_tests.append({
                    "test_number": i + 1,
                    "response_time": None,
                    "error": str(e),
                    "success": False
                })
        
        successful_tests = [t for t in timing_tests if t["success"]]
        avg_response_time = sum(t["response_time"] for t in successful_tests) / len(successful_tests) if successful_tests else 0
        
        # Success if average response time < 1.5 seconds and at least 80% tests pass
        overall_success = len(successful_tests) >= len(timing_tests) * 0.8 and avg_response_time < 1.5
        
        self.log_test_result("Synchronization Timing", overall_success, {
            "total_tests": len(timing_tests),
            "successful_tests": len(successful_tests),
            "average_response_time": avg_response_time,
            "timing_details": timing_tests
        })
        
        return overall_success
    
    def test_error_handling(self) -> bool:
        """Test error handling and recovery mechanisms"""
        error_test_cases = [
            {
                "endpoint": "/ai/select_model",
                "payload": {},  # Missing required fields
                "expected_status": 200,  # The API returns 200 with error message
                "description": "Missing required fields"
            },
            {
                "endpoint": "/models/NonExistent.fbx",
                "method": "GET",
                "expected_status": 404,
                "description": "Non-existent model request"
            },
            {
                "endpoint": "/ai/select_model",
                "payload": {"question": "", "language": "en"},  # Empty question
                "expected_status": 200,  # Should handle gracefully
                "description": "Empty query handling"
            }
        ]
        
        results = []
        
        for test_case in error_test_cases:
            try:
                if test_case.get("method", "POST") == "GET":
                    response = requests.get(f"{self.base_url}{test_case['endpoint']}", timeout=10)
                else:
                    response = requests.post(
                        f"{self.base_url}{test_case['endpoint']}", 
                        json=test_case.get("payload", {}),
                        timeout=10
                    )
                
                expected_status = test_case["expected_status"]
                actual_status = response.status_code
                
                # For error cases, we expect specific status codes
                # For valid cases, we check if they're handled gracefully
                if expected_status >= 400:
                    success = actual_status == expected_status
                else:
                    success = 200 <= actual_status < 300
                
                results.append({
                    "test_case": test_case,
                    "success": success,
                    "expected_status": expected_status,
                    "actual_status": actual_status,
                    "response_data": response.json() if response.headers.get("content-type", "").startswith("application/json") else None
                })
                
            except Exception as e:
                results.append({
                    "test_case": test_case,
                    "success": False,
                    "error": str(e)
                })
        
        success_count = sum(1 for r in results if r["success"])
        overall_success = success_count >= len(error_test_cases) * 0.8
        
        self.log_test_result("Error Handling", overall_success, {
            "test_cases": len(error_test_cases),
            "successful": success_count,
            "results": results
        })
        
        return overall_success
    
    def run_comprehensive_verification(self) -> Dict[str, Any]:
        """Run complete integration verification suite"""
        logger.info("🔍 Starting Comprehensive 3D-AI Integration Verification")
        logger.info("=" * 80)
        
        test_suite = [
            ("API Health Check", self.test_api_health_check),
            ("3D Model Availability", self.test_3d_model_availability),
            ("AI Model Selection Integration", self.test_ai_model_selection_integration),
            ("Emotion Integration", self.test_emotion_integration),
            ("Multimodal Action Plans", self.test_multimodal_action_plans),
            ("Synchronization Timing", self.test_synchronization_timing),
            ("Error Handling", self.test_error_handling)
        ]
        
        overall_results = {"passed": 0, "failed": 0, "total": len(test_suite)}
        
        for test_name, test_function in test_suite:
            logger.info(f"\n🧪 Running: {test_name}")
            try:
                success = test_function()
                if success:
                    overall_results["passed"] += 1
                else:
                    overall_results["failed"] += 1
            except Exception as e:
                logger.error(f"💥 Test {test_name} crashed: {e}")
                overall_results["failed"] += 1
                self.log_test_result(test_name, False, {"error": f"Test crashed: {str(e)}"})
        
        # Calculate final score
        success_rate = overall_results["passed"] / overall_results["total"]
        overall_success = success_rate >= 0.8  # 80% pass rate required
        
        logger.info("\n" + "=" * 80)
        logger.info("📊 INTEGRATION VERIFICATION RESULTS")
        logger.info("=" * 80)
        logger.info(f"✅ Tests Passed: {overall_results['passed']}/{overall_results['total']}")
        logger.info(f"❌ Tests Failed: {overall_results['failed']}/{overall_results['total']}")
        logger.info(f"📈 Success Rate: {success_rate:.1%}")
        
        if overall_success:
            logger.info("🎉 INTEGRATION VERIFICATION: PASSED")
            logger.info("✅ 3D Model-AI integration is working seamlessly")
        else:
            logger.error("❌ INTEGRATION VERIFICATION: FAILED") 
            logger.error("🔧 Integration issues need to be addressed")
            logger.error("\nError Summary:")
            for error in self.error_log:
                logger.error(f"  - {error['test_name']}: {error['details'].get('error', 'See details')}")
        
        return {
            "overall_success": overall_success,
            "success_rate": success_rate,
            "results": overall_results,
            "detailed_results": self.test_results,
            "errors": self.error_log,
            "timestamp": datetime.now().isoformat()
        }

def main():
    """Run the comprehensive integration verification"""
    verifier = ModelIntegrationVerifier()
    results = verifier.run_comprehensive_verification()
    
    # Save results to file
    with open('integration_verification_results.json', 'w') as f:
        json.dump(results, f, indent=2)
    
    logger.info(f"\n📁 Detailed results saved to: integration_verification_results.json")
    logger.info(f"📁 Test logs saved to: integration_tests.log")
    
    # Exit with appropriate code
    sys.exit(0 if results["overall_success"] else 1)

if __name__ == "__main__":
    main()