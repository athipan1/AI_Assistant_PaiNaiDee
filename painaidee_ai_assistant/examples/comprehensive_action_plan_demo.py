"""
Comprehensive Example: Extending the Multimodal Action Plan System

This example demonstrates how to:
1. Add new intents for different scenarios
2. Create custom action templates
3. Register new composite actions
4. Use the system for various tourism and assistance use cases
"""

import asyncio
import requests
import json
from typing import Dict, Any

# Base URL for the API (adjust if running on different host/port)
BASE_URL = "http://localhost:8000"

def register_new_intent_and_templates():
    """Example: Register new intent for restaurant recommendation"""
    
    print("🔧 Registering new restaurant recommendation intent...")
    
    # First, register custom templates
    
    # 1. Custom speech template for restaurant suggestions
    restaurant_speech_template = {
        "text": "แนะนำร้าน{restaurant_name}ครับ อาหาร{cuisine_type}อร่อยมากเลย",
        "language": "th", 
        "style": "enthusiastic",
        "duration_ms": None,
        "voice_params": {"tone": "excited"}
    }
    
    # 2. Custom gesture for food recommendation (excited pointing)
    food_gesture_template = {
        "animation": "point",
        "model_name": "Man_Rig.fbx", 
        "duration_ms": 2500,
        "intensity": 1.2,
        "loop": False,
        "facial_expression": "delighted"
    }
    
    # 3. Custom UI template for restaurant info
    restaurant_ui_template = {
        "component_type": "info_panel",
        "content": {
            "title": "ข้อมูลร้านอาหาร",
            "fields": ["name", "cuisine", "rating", "price_range", "hours", "phone"]
        },
        "position": "sidebar",
        "duration_ms": None,
        "interaction_enabled": True
    }
    
    # Register the templates
    templates_to_register = [
        ("speech", "restaurant_suggestion", restaurant_speech_template),
        ("gesture", "excited_food_point", food_gesture_template), 
        ("ui", "restaurant_info", restaurant_ui_template)
    ]
    
    for category, name, template in templates_to_register:
        response = requests.post(
            f"{BASE_URL}/action/register_template",
            json={
                "category": category,
                "name": name, 
                "template": template,
                "description": f"Custom {category} template for restaurant recommendations"
            }
        )
        
        if response.status_code == 200:
            print(f"✓ Registered {category} template: {name}")
        else:
            print(f"✗ Failed to register {category} template: {name} - {response.text}")
    
    # Now register the intent mapping
    restaurant_intent_mapping = {
        "speech_templates": ["restaurant_suggestion"],
        "gesture_templates": ["excited_food_point"],
        "scene_templates": ["focus_map_pin", "zoom_to_location"], 
        "ui_templates": ["place_photo", "action_buttons", "restaurant_info"],
        "parameters": {
            "restaurant_name": "{restaurant_name}",
            "cuisine_type": "{cuisine_type}",
            "coordinates": "{coordinates}",
            "photo_url": "{photo_url}"
        },
        "execution_order": ["speech", "gesture", "scene", "ui"]
    }
    
    response = requests.post(
        f"{BASE_URL}/action/register_intent",
        json={
            "intent": "suggest_restaurant",
            "mapping": restaurant_intent_mapping,
            "description": "Recommend a restaurant with cuisine info and location"
        }
    )
    
    if response.status_code == 200:
        print("✓ Registered new intent: suggest_restaurant")
        return True
    else:
        print(f"✗ Failed to register intent: {response.text}")
        return False

def demonstrate_restaurant_recommendation():
    """Demonstrate the new restaurant recommendation feature"""
    
    print("\n🍽️ Testing restaurant recommendation...")
    
    # Test the new intent
    restaurant_plan_data = {
        "intent": "suggest_restaurant",
        "parameters": {
            "restaurant_name": "ร้านส้มตำป้าบุญ",
            "cuisine_type": "อาหารอีสาน", 
            "coordinates": "13.7563,100.5018",
            "photo_url": "https://example.com/som-tam-restaurant.jpg"
        },
        "confidence": 0.95
    }
    
    response = requests.post(
        f"{BASE_URL}/action/generate_plan",
        json=restaurant_plan_data
    )
    
    if response.status_code == 200:
        plan = response.json()
        print("✓ Restaurant recommendation plan generated:")
        print(f"  - Speech: {plan['speech_actions'][0]['text']}")
        print(f"  - Gesture: {plan['gesture_actions'][0]['animation']}")
        print(f"  - Scene actions: {len(plan['scene_actions'])}")
        print(f"  - UI components: {len(plan['ui_actions'])}")
        return plan
    else:
        print(f"✗ Failed to generate restaurant plan: {response.text}")
        return None

def demonstrate_quick_actions():
    """Demonstrate natural language to action plan conversion"""
    
    print("\n🗣️ Testing natural language processing...")
    
    test_inputs = [
        {
            "input": "สวัสดีครับ ยินดีต้อนรับ",
            "expected": "greet_user"
        },
        {
            "input": "แนะนำวัดพระแก้วหน่อย",
            "expected": "suggest_place"
        },
        {
            "input": "ไปพิพิธภัณฑ์กันเถอะ",
            "expected": "suggest_cultural_place"
        },
        {
            "input": "โอเค เข้าใจแล้ว",
            "expected": "confirm_action"
        }
    ]
    
    for test_case in test_inputs:
        response = requests.post(
            f"{BASE_URL}/action/quick_action",
            json={
                "user_input": test_case["input"],
                "language": "th"
            }
        )
        
        if response.status_code == 200:
            result = response.json()
            recognized_intent = result["intent"]
            confidence = result["confidence"]
            
            status = "✓" if recognized_intent == test_case["expected"] else "⚠️"
            print(f"{status} '{test_case['input']}' → {recognized_intent} (confidence: {confidence:.2f})")
        else:
            print(f"✗ Failed to process: '{test_case['input']}'")

def demonstrate_execution_modes():
    """Demonstrate different execution modes"""
    
    print("\n⚡ Testing execution modes...")
    
    plan_data = {
        "intent": "greet_user",
        "parameters": {},
        "confidence": 1.0
    }
    
    # Test preview mode
    response = requests.post(
        f"{BASE_URL}/action/execute_plan",
        json={
            "plan": plan_data,
            "execution_mode": "preview"
        }
    )
    
    if response.status_code == 200:
        result = response.json()
        print(f"✓ Preview mode: {result['status']}")
        print(f"  - Execution ID: {result['execution_id']}")
        print(f"  - Speech outputs: {len(result['outputs'].get('speech', []))}")
        print(f"  - Gesture outputs: {len(result['outputs'].get('gesture', []))}")
    
    # Test immediate execution
    response = requests.post(
        f"{BASE_URL}/action/execute_plan",
        json={
            "plan": plan_data,
            "execution_mode": "immediate"
        }
    )
    
    if response.status_code == 200:
        result = response.json()
        print(f"✓ Immediate execution: {result['status']}")
        print(f"  - Execution ID: {result['execution_id']}")
        print(f"  - Started at: {result['started_at']}")

def demonstrate_complex_scenario():
    """Demonstrate a complex multi-step tourism scenario"""
    
    print("\n🎭 Testing complex tourism scenario...")
    
    # Scenario: User arrives in Bangkok, wants cultural recommendations
    scenario_steps = [
        {
            "description": "Greet tourist",
            "plan": {
                "intent": "greet_user",
                "parameters": {},
                "confidence": 1.0
            }
        },
        {
            "description": "Suggest cultural place",
            "plan": {
                "intent": "suggest_cultural_place", 
                "parameters": {
                    "place_name": "พิพิธภัณฑ์พระราชวังใหญ่",
                    "coordinates": "13.7503,100.4914",
                    "photo_url": "https://example.com/grand-palace-museum.jpg"
                },
                "confidence": 0.9
            }
        },
        {
            "description": "Confirm user interest",
            "plan": {
                "intent": "confirm_action",
                "parameters": {},
                "confidence": 1.0
            }
        }
    ]
    
    execution_results = []
    
    for i, step in enumerate(scenario_steps, 1):
        print(f"\n  Step {i}: {step['description']}")
        
        response = requests.post(
            f"{BASE_URL}/action/execute_plan",
            json={
                "plan": step["plan"],
                "execution_mode": "immediate"
            }
        )
        
        if response.status_code == 200:
            result = response.json()
            execution_results.append(result)
            print(f"    ✓ Executed successfully (ID: {result['execution_id']})")
            
            # Show key outputs
            outputs = result.get('outputs', {})
            if 'speech' in outputs and outputs['speech']:
                speech_text = outputs['speech'][0]['text']
                print(f"    💬 Speech: {speech_text}")
            if 'gesture' in outputs and outputs['gesture']:
                gesture_anim = outputs['gesture'][0]['animation']
                print(f"    🤲 Gesture: {gesture_anim}")
        else:
            print(f"    ✗ Failed: {response.text}")
    
    return execution_results

def show_system_capabilities():
    """Display current system capabilities"""
    
    print("\n📊 System Capabilities Overview...")
    
    # Check health
    response = requests.get(f"{BASE_URL}/health")
    if response.status_code == 200:
        health = response.json()
        print("✓ System Status: Healthy")
        print(f"  - Available models: {health['models_available']}")
        
        features = health.get('features', {})
        enabled_features = [name for name, enabled in features.items() if enabled]
        print(f"  - Enabled features: {len(enabled_features)}")
        for feature in enabled_features:
            print(f"    • {feature}")
    
    # Check available intents
    response = requests.get(f"{BASE_URL}/action/available_intents")
    if response.status_code == 200:
        intents_data = response.json()
        intents = intents_data['intents']
        print(f"\n📝 Available Intents ({intents_data['total_count']}):")
        
        for intent, info in intents.items():
            print(f"  • {intent}: {info['description']}")
            if info['parameters']:
                print(f"    Parameters: {', '.join(info['parameters'])}")
            print(f"    Actions: {', '.join(info['actions'])}")
    
    # Check execution history
    response = requests.get(f"{BASE_URL}/action/execution_history")
    if response.status_code == 200:
        history_data = response.json()
        history = history_data['history']
        print(f"\n📈 Recent Executions ({len(history)}):")
        
        for execution in history[-5:]:  # Show last 5
            print(f"  • {execution['intent']} - {execution['status']} "
                  f"({execution.get('execution_time_ms', 0)}ms)")

def demonstrate_extensibility():
    """Show how easy it is to extend the system"""
    
    print("\n🔧 Demonstrating System Extensibility...")
    
    # Example: Add a new intent for hotel recommendations
    hotel_intent_mapping = {
        "composite_template": "suggest_place_full",  # Reuse existing composite
        "parameters": {
            "place_name": "{hotel_name}",
            "location_coordinates": "{coordinates}",
            "photo_url": "{photo_url}",
            "price_range": "{price_range}",
            "rating": "{rating}"
        },
        "execution_order": ["speech", "gesture", "scene", "ui"]
    }
    
    # Register the new intent
    response = requests.post(
        f"{BASE_URL}/action/register_intent",
        json={
            "intent": "suggest_hotel",
            "mapping": hotel_intent_mapping,
            "description": "Recommend a hotel with pricing and rating info"
        }
    )
    
    if response.status_code == 200:
        print("✓ Added new intent: suggest_hotel")
        
        # Test the new intent immediately
        test_plan_data = {
            "intent": "suggest_hotel",
            "parameters": {
                "hotel_name": "โรงแรมมันดาริน โอเรียนเต็ล",
                "coordinates": "13.7275,100.5154",
                "photo_url": "https://example.com/mandarin-oriental.jpg",
                "price_range": "หรู",
                "rating": "5 ดาว"
            },
            "confidence": 0.95
        }
        
        response = requests.post(
            f"{BASE_URL}/action/generate_plan",
            json=test_plan_data
        )
        
        if response.status_code == 200:
            plan = response.json()
            print("✓ Hotel recommendation plan generated successfully")
            print(f"  - Intent: {plan['intent']}")
            print(f"  - Actions: {len(plan['speech_actions'])} speech, "
                  f"{len(plan['gesture_actions'])} gesture, "
                  f"{len(plan['scene_actions'])} scene, "
                  f"{len(plan['ui_actions'])} UI")
        else:
            print(f"✗ Failed to generate hotel plan: {response.text}")
    else:
        print(f"✗ Failed to register hotel intent: {response.text}")

async def main():
    """Main demonstration script"""
    
    print("🎯 Multimodal Action Plan System - Comprehensive Demo")
    print("=" * 60)
    
    # Check if server is running
    try:
        response = requests.get(f"{BASE_URL}/health", timeout=5)
        if response.status_code != 200:
            print("❌ Server is not responding correctly")
            return
    except requests.exceptions.RequestException:
        print("❌ Cannot connect to server. Make sure it's running on http://localhost:8000")
        return
    
    print("✅ Connected to PaiNaiDee AI Assistant server\n")
    
    # Show current system capabilities
    show_system_capabilities()
    
    # Demonstrate basic functionality
    demonstrate_quick_actions()
    demonstrate_execution_modes()
    
    # Demonstrate extensibility
    demonstrate_extensibility()
    
    # Register and test new restaurant feature
    if register_new_intent_and_templates():
        demonstrate_restaurant_recommendation()
    
    # Run complex scenario
    demonstrate_complex_scenario()
    
    print("\n" + "=" * 60)
    print("🎉 Demo completed! The system successfully demonstrated:")
    print("  ✓ Modular action plan generation")
    print("  ✓ Multimodal output coordination (speech, gesture, scene, UI)")
    print("  ✓ Natural language intent recognition")
    print("  ✓ Easy extensibility with new intents and actions")
    print("  ✓ Thai language support")
    print("  ✓ Tourism-specific use cases")
    print("  ✓ Composable and reusable action templates")
    
    print("\n📚 Key Usage Examples:")
    print("  • Tourist place suggestions with full presentation")
    print("  • Cultural site recommendations with information panels")
    print("  • Restaurant suggestions with cuisine details")
    print("  • Hotel recommendations with pricing and ratings")
    print("  • Interactive greetings and confirmations")
    
    print(f"\n🔗 Access the API documentation at: {BASE_URL}/docs")

if __name__ == "__main__":
    asyncio.run(main())