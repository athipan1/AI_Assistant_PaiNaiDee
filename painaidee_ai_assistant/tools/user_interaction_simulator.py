#!/usr/bin/env python3
"""
User Interaction Simulation for 3D-AI Integration Testing
Simulates real-world user interactions and validates 3D model responses
"""

import asyncio
import json
import time
import logging
import requests
from typing import Dict, List, Any, Optional
from datetime import datetime
import random

logger = logging.getLogger(__name__)

class UserInteractionSimulator:
    """Simulates realistic user interactions with the 3D-AI system"""
    
    def __init__(self, base_url: str = "http://localhost:8000"):
        self.base_url = base_url
        self.interaction_history = []
        self.session_data = {}
        
        # Setup logging
        logging.basicConfig(
            level=logging.INFO,
            format='%(asctime)s - %(levelname)s - %(message)s'
        )
        
    def log_interaction(self, user_input: str, ai_response: Dict[str, Any], success: bool, details: Dict[str, Any]):
        """Log user interaction with detailed analysis"""
        interaction = {
            "timestamp": datetime.now().isoformat(),
            "user_input": user_input,
            "ai_response": ai_response,
            "success": success,
            "details": details
        }
        self.interaction_history.append(interaction)
        
    def simulate_tourist_scenarios(self) -> List[Dict[str, Any]]:
        """Simulate realistic tourist interaction scenarios"""
        tourist_scenarios = [
            {
                "context": "First-time visitor looking for activities",
                "queries": [
                    "What can I do in Thailand?",
                    "Show me some walking tours",
                    "I want to see traditional Thai dancing"
                ],
                "expected_emotions": ["curious", "excited", "interested"],
                "scenario_type": "exploration"
            },
            {
                "context": "Family vacation planning",
                "queries": [
                    "Are there family-friendly activities?",
                    "Show me something for kids",
                    "I'm worried about safety for children"
                ],
                "expected_emotions": ["concerned", "hopeful", "worried"],
                "scenario_type": "family_planning"
            },
            {
                "context": "Adventure seeker",
                "queries": [
                    "I want extreme sports!",
                    "Show me running and hiking activities",
                    "What's the most exciting thing to do?"
                ],
                "expected_emotions": ["excited", "adventurous", "energetic"],
                "scenario_type": "adventure"
            },
            {
                "context": "Cultural enthusiast",
                "queries": [
                    "Tell me about Thai culture",
                    "Show me traditional ceremonies",
                    "I want to learn about local customs"
                ],
                "expected_emotions": ["curious", "respectful", "interested"],
                "scenario_type": "cultural"
            },
            {
                "context": "Tired traveler seeking relaxation",
                "queries": [
                    "I'm exhausted and need to rest",
                    "Show me calm, peaceful places",
                    "What are some quiet activities?"
                ],
                "expected_emotions": ["tired", "calm", "peaceful"],
                "scenario_type": "relaxation"
            }
        ]
        
        simulation_results = []
        
        for scenario in tourist_scenarios:
            logger.info(f"🎭 Simulating scenario: {scenario['context']}")
            
            scenario_results = {
                "scenario": scenario,
                "interactions": [],
                "overall_success": True,
                "emotional_consistency": True,
                "model_relevance": True
            }
            
            for i, query in enumerate(scenario["queries"]):
                logger.info(f"  👤 User: {query}")
                
                # Test AI model selection
                interaction_result = self.test_single_interaction(
                    query, 
                    expected_emotion=scenario["expected_emotions"][i] if i < len(scenario["expected_emotions"]) else None,
                    context=scenario["scenario_type"]
                )
                
                scenario_results["interactions"].append(interaction_result)
                
                if not interaction_result["success"]:
                    scenario_results["overall_success"] = False
                
                if not interaction_result.get("emotion_appropriate", True):
                    scenario_results["emotional_consistency"] = False
                
                if not interaction_result.get("model_relevant", True):
                    scenario_results["model_relevance"] = False
                
                # Add slight delay between interactions
                time.sleep(0.5)
            
            simulation_results.append(scenario_results)
            logger.info(f"  ✅ Scenario complete: Success={scenario_results['overall_success']}")
        
        return simulation_results
    
    def test_single_interaction(self, user_input: str, expected_emotion: str = None, context: str = None) -> Dict[str, Any]:
        """Test a single user interaction with comprehensive analysis"""
        start_time = time.time()
        
        try:
            # Test AI model selection with emotion analysis
            response = requests.post(
                f"{self.base_url}/ai/select_model_with_emotion",
                json={
                    "question": user_input,
                    "analyze_emotion": True,
                    "language": "en"
                },
                timeout=15
            )
            
            end_time = time.time()
            response_time = end_time - start_time
            
            if response.status_code != 200:
                result = {
                    "success": False,
                    "user_input": user_input,
                    "error": f"HTTP {response.status_code}",
                    "response_time": response_time
                }
                self.log_interaction(user_input, {}, False, result)
                return result
            
            data = response.json()
            
            # Extract response components
            model_selection = data.get("model_selection", {})
            emotion_analysis = data.get("emotion_analysis", {})
            
            selected_model = model_selection.get("selected_model")
            confidence = model_selection.get("confidence", 0)
            detected_emotion = emotion_analysis.get("primary_emotion")
            suggested_gesture = emotion_analysis.get("suggested_gesture")
            
            # Analyze response quality
            analysis = {
                "success": True,
                "user_input": user_input,
                "selected_model": selected_model,
                "confidence": confidence,
                "detected_emotion": detected_emotion,
                "expected_emotion": expected_emotion,
                "suggested_gesture": suggested_gesture,
                "response_time": response_time,
                "context": context
            }
            
            # Check if emotion detection is appropriate
            if expected_emotion and detected_emotion:
                # Allow related emotions (e.g., "excited" and "adventurous")
                emotion_families = {
                    "positive": ["excited", "happy", "curious", "interested", "adventurous", "energetic"],
                    "negative": ["worried", "concerned", "tired", "anxious"],
                    "neutral": ["calm", "peaceful", "respectful", "hopeful"]
                }
                
                expected_family = None
                detected_family = None
                
                for family, emotions in emotion_families.items():
                    if expected_emotion in emotions:
                        expected_family = family
                    if detected_emotion in emotions:
                        detected_family = family
                
                analysis["emotion_appropriate"] = expected_family == detected_family
            else:
                analysis["emotion_appropriate"] = True
            
            # Check if model selection is relevant to context
            model_relevance = self._check_model_relevance(selected_model, user_input, context)
            analysis["model_relevant"] = model_relevance
            
            # Check if gesture is appropriate
            gesture_appropriate = suggested_gesture is not None
            analysis["gesture_appropriate"] = gesture_appropriate
            
            # Overall success criteria
            analysis["success"] = (
                confidence > 0.2 and  # Reasonable confidence
                analysis["emotion_appropriate"] and
                analysis["model_relevant"] and
                analysis["gesture_appropriate"]
            )
            
            self.log_interaction(user_input, data, analysis["success"], analysis)
            
            logger.info(f"    🤖 AI: {selected_model} (confidence: {confidence:.2f})")
            if detected_emotion:
                logger.info(f"    😊 Emotion: {detected_emotion} → {suggested_gesture}")
            
            return analysis
            
        except Exception as e:
            end_time = time.time()
            response_time = end_time - start_time
            
            result = {
                "success": False,
                "user_input": user_input,
                "error": str(e),
                "response_time": response_time
            }
            
            self.log_interaction(user_input, {}, False, result)
            logger.error(f"    ❌ Error: {str(e)}")
            return result
    
    def _check_model_relevance(self, selected_model: str, user_input: str, context: str) -> bool:
        """Check if selected model is relevant to user input and context"""
        if not selected_model:
            return False
        
        # Define model relevance rules
        relevance_rules = {
            "Walking.fbx": ["walk", "walking", "tour", "explore", "stroll", "hike"],
            "Running.fbx": ["run", "running", "exercise", "sport", "fast", "quick", "extreme"],
            "Idle.fbx": ["stand", "idle", "wait", "calm", "peaceful", "rest", "quiet"],
            "Man.fbx": ["person", "human", "character", "basic", "simple"],
            "Man_Rig.fbx": ["animation", "custom", "rigged", "complex", "demonstrate"]
        }
        
        # Context-based relevance
        context_preferences = {
            "adventure": ["Running.fbx", "Walking.fbx"],
            "relaxation": ["Idle.fbx", "Man.fbx"],
            "cultural": ["Man_Rig.fbx", "Idle.fbx"],
            "family_planning": ["Walking.fbx", "Idle.fbx"],
            "exploration": ["Walking.fbx", "Man_Rig.fbx"]
        }
        
        # Check keyword relevance
        keywords = relevance_rules.get(selected_model, [])
        keyword_match = any(keyword in user_input.lower() for keyword in keywords)
        
        # Check context relevance
        context_models = context_preferences.get(context, [])
        context_match = selected_model in context_models or not context
        
        return keyword_match or context_match
    
    def simulate_edge_cases(self) -> List[Dict[str, Any]]:
        """Simulate edge cases and challenging scenarios"""
        edge_cases = [
            {
                "description": "Ambiguous query",
                "query": "Show me something",
                "expected_behavior": "should_select_default_or_ask_clarification"
            },
            {
                "description": "Non-English mixed query",
                "query": "Show me สวยๆ walking ดีๆ",
                "expected_behavior": "should_handle_mixed_language"
            },
            {
                "description": "Very long query",
                "query": "I want to see a very detailed and specific walking animation that shows someone moving through a beautiful landscape with mountains and trees and rivers and all kinds of wonderful scenery",
                "expected_behavior": "should_extract_key_concepts"
            },
            {
                "description": "Nonsensical query",
                "query": "Purple monkey dishwasher running elephant",
                "expected_behavior": "should_handle_gracefully"
            },
            {
                "description": "Empty query",
                "query": "",
                "expected_behavior": "should_return_error_or_default"
            },
            {
                "description": "Technical query",
                "query": "Show me the FBX model with the highest polygon count",
                "expected_behavior": "should_understand_technical_terms"
            }
        ]
        
        results = []
        
        for case in edge_cases:
            logger.info(f"🔧 Testing edge case: {case['description']}")
            result = self.test_single_interaction(case["query"])
            
            # Analyze if the system handled the edge case appropriately
            handled_appropriately = True
            
            if case["expected_behavior"] == "should_return_error_or_default":
                handled_appropriately = not result["success"] or result.get("selected_model") == "Man.fbx"
            elif case["expected_behavior"] == "should_handle_gracefully":
                handled_appropriately = result["success"] and result.get("confidence", 0) < 0.5
            elif case["expected_behavior"] == "should_extract_key_concepts":
                handled_appropriately = result["success"] and "Walking.fbx" in str(result.get("selected_model", ""))
            
            result["edge_case"] = case
            result["handled_appropriately"] = handled_appropriately
            results.append(result)
            
            logger.info(f"  {'✅' if handled_appropriately else '❌'} Edge case handled appropriately: {handled_appropriately}")
        
        return results
    
    def run_comprehensive_user_simulation(self) -> Dict[str, Any]:
        """Run comprehensive user interaction simulation"""
        logger.info("👥 Starting Comprehensive User Interaction Simulation")
        logger.info("=" * 80)
        
        simulation_start = time.time()
        
        # Run tourist scenarios
        logger.info("\n🏖️ Simulating Tourist Scenarios...")
        tourist_results = self.simulate_tourist_scenarios()
        
        # Run edge cases
        logger.info("\n🔧 Simulating Edge Cases...")
        edge_case_results = self.simulate_edge_cases()
        
        simulation_end = time.time()
        total_time = simulation_end - simulation_start
        
        # Analyze overall results
        tourist_success_count = sum(1 for r in tourist_results if r["overall_success"])
        edge_case_success_count = sum(1 for r in edge_case_results if r["handled_appropriately"])
        
        total_interactions = len(self.interaction_history)
        successful_interactions = sum(1 for i in self.interaction_history if i["success"])
        
        overall_results = {
            "simulation_time": total_time,
            "total_interactions": total_interactions,
            "successful_interactions": successful_interactions,
            "success_rate": successful_interactions / total_interactions if total_interactions > 0 else 0,
            "tourist_scenarios": {
                "total": len(tourist_results),
                "successful": tourist_success_count,
                "success_rate": tourist_success_count / len(tourist_results) if tourist_results else 0,
                "results": tourist_results
            },
            "edge_cases": {
                "total": len(edge_case_results),
                "handled_appropriately": edge_case_success_count,
                "success_rate": edge_case_success_count / len(edge_case_results) if edge_case_results else 0,
                "results": edge_case_results
            },
            "interaction_history": self.interaction_history,
            "timestamp": datetime.now().isoformat()
        }
        
        # Calculate overall simulation success
        overall_success = (
            overall_results["success_rate"] >= 0.8 and
            overall_results["tourist_scenarios"]["success_rate"] >= 0.7 and
            overall_results["edge_cases"]["success_rate"] >= 0.6
        )
        
        overall_results["simulation_success"] = overall_success
        
        # Print summary
        logger.info("\n" + "=" * 80)
        logger.info("📊 USER INTERACTION SIMULATION RESULTS")
        logger.info("=" * 80)
        logger.info(f"Total interactions: {total_interactions}")
        logger.info(f"Successful interactions: {successful_interactions}/{total_interactions} ({overall_results['success_rate']:.1%})")
        logger.info(f"Tourist scenarios: {tourist_success_count}/{len(tourist_results)} successful ({overall_results['tourist_scenarios']['success_rate']:.1%})")
        logger.info(f"Edge cases handled: {edge_case_success_count}/{len(edge_case_results)} ({overall_results['edge_cases']['success_rate']:.1%})")
        logger.info(f"Simulation time: {total_time:.1f} seconds")
        
        if overall_success:
            logger.info("🎉 SIMULATION PASSED: User interactions work seamlessly!")
        else:
            logger.warning("⚠️ SIMULATION ISSUES: Some user interactions need improvement")
        
        return overall_results

def main():
    """Run user interaction simulation"""
    import argparse
    
    parser = argparse.ArgumentParser(description="User Interaction Simulator for 3D-AI Integration")
    parser.add_argument("--scenarios", choices=["tourist", "edge", "all"], default="all", 
                       help="Which scenarios to run")
    parser.add_argument("--output", type=str, help="Output file for results")
    
    args = parser.parse_args()
    
    simulator = UserInteractionSimulator()
    
    if args.scenarios == "tourist":
        results = simulator.simulate_tourist_scenarios()
    elif args.scenarios == "edge":
        results = simulator.simulate_edge_cases()
    else:
        results = simulator.run_comprehensive_user_simulation()
    
    if args.output:
        with open(args.output, 'w') as f:
            json.dump(results, f, indent=2)
        logger.info(f"📁 Results saved to {args.output}")
    else:
        print(json.dumps(results, indent=2))

if __name__ == "__main__":
    main()