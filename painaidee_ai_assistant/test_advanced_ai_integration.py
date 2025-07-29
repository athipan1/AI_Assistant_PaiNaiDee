#!/usr/bin/env python3
"""
Test script for Advanced AI Models Integration
Tests the new llama.cpp, OpenChat, and OpenHermes integration
"""

import asyncio
import json
import logging
import time
from pathlib import Path
import sys
import os

# Add the painaidee_ai_assistant directory to the path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

async def test_advanced_ai_integration():
    """Test the advanced AI models integration"""
    
    print("=" * 80)
    print("🤖 Testing Advanced AI Models Integration")
    print("🎯 Goal: Verify llama.cpp, OpenChat, and OpenHermes integration")
    print("=" * 80)
    
    try:
        # Test 1: Import and initialize advanced AI models
        print("\n📦 Test 1: Import Advanced AI Models")
        print("-" * 50)
        
        from agents.advanced_ai_models import ai_manager, initialize_advanced_ai, ModelCapability
        from agents.enhanced_model_selector import get_enhanced_selector
        
        print("✅ Successfully imported advanced AI modules")
        
        # Test 2: Initialize AI manager
        print("\n🚀 Test 2: Initialize AI Manager")
        print("-" * 50)
        
        await initialize_advanced_ai()
        print("✅ AI Manager initialized successfully")
        
        # Test 3: Check available models
        print("\n📋 Test 3: Check Available Models")
        print("-" * 50)
        
        models = ai_manager.get_available_models()
        print(f"Found {len(models)} configured AI models:")
        
        for model in models:
            status = "✅ Available" if model.get("available", False) else "❌ Unavailable"
            print(f"  - {model['name']} ({model['type']}) - {status}")
            print(f"    Capabilities: {', '.join(model['capabilities'])}")
            print(f"    Languages: {', '.join(model['languages'])}")
        
        # Test 4: Test model selection for different capabilities
        print("\n🎯 Test 4: Test Model Selection")
        print("-" * 50)
        
        test_capabilities = [
            ModelCapability.CONVERSATION,
            ModelCapability.QUESTION_ANSWERING,
            ModelCapability.TOURISM_ADVICE,
            ModelCapability.TEXT_GENERATION
        ]
        
        for capability in test_capabilities:
            selected_model = ai_manager.select_best_model(capability, language="en")
            print(f"  - {capability.value}: {selected_model or 'No suitable model found'}")
        
        # Test 5: Test enhanced model selector
        print("\n🔄 Test 5: Test Enhanced Model Selector")
        print("-" * 50)
        
        enhanced_selector = get_enhanced_selector()
        
        test_questions = [
            "Show me a walking person",
            "I need tourism advice for Bangkok",
            "What are the best temples to visit in Thailand?",
            "Can you recommend some traditional Thai food?"
        ]
        
        for question in test_questions:
            print(f"\nQuestion: '{question}'")
            try:
                # Test without advanced AI first
                result = await enhanced_selector.analyze_question_with_ai(
                    question=question,
                    use_advanced_ai=False,
                    language="en"
                )
                
                print(f"  Selected 3D Model: {result.get('selected_model', 'None')}")
                print(f"  Confidence: {result.get('confidence', 0):.2f}")
                print(f"  AI Enhancement Used: {result.get('ai_enhancement_used', False)}")
                
            except Exception as e:
                print(f"  ❌ Error: {e}")
        
        # Test 6: Test conversation capability (if models available)
        print("\n💬 Test 6: Test Conversation Capability")
        print("-" * 50)
        
        conversation_model = ai_manager.select_best_model(ModelCapability.CONVERSATION, prefer_local=True)
        
        if conversation_model:
            print(f"Testing conversation with model: {conversation_model}")
            try:
                result = await enhanced_selector.conversational_response(
                    message="Hello! Can you help me plan a trip to Thailand?",
                    language="en"
                )
                
                print(f"  Response: {result.get('response', 'No response')[:100]}...")
                print(f"  Suggested 3D Model: {result.get('suggested_3d_model', 'None')}")
                print(f"  AI Model Used: {result.get('ai_model_used', 'Unknown')}")
                
            except Exception as e:
                print(f"  ⚠️ Conversation test failed (expected if models not available): {e}")
        else:
            print("  ⚠️ No conversation model available for testing")
        
        # Test 7: Test API integration
        print("\n🌐 Test 7: Test API Integration")
        print("-" * 50)
        
        try:
            from api.advanced_ai_routes import router
            print("✅ Advanced AI API routes imported successfully")
            
            # Get available endpoints
            endpoints = []
            for route in router.routes:
                if hasattr(route, 'path'):
                    endpoints.append(f"{route.methods} {route.path}")
            
            print(f"Available API endpoints ({len(endpoints)}):")
            for endpoint in endpoints:
                print(f"  - {endpoint}")
                
        except Exception as e:
            print(f"  ❌ API integration error: {e}")
        
        # Test 8: Configuration validation
        print("\n⚙️ Test 8: Configuration Validation")
        print("-" * 50)
        
        config_path = "config/ai_models.json"
        if os.path.exists(config_path):
            print(f"✅ Configuration file exists: {config_path}")
            
            with open(config_path, 'r') as f:
                config = json.load(f)
            print(f"✅ Configuration loaded with {len(config)} model definitions")
            
            # Validate required fields
            required_fields = ["name", "model_type", "model_path", "capabilities", "language_support"]
            for model_name, model_config in config.items():
                missing_fields = [field for field in required_fields if field not in model_config]
                if missing_fields:
                    print(f"  ⚠️ Model {model_name} missing fields: {missing_fields}")
                else:
                    print(f"  ✅ Model {model_name} configuration valid")
        else:
            print(f"⚠️ Configuration file not found: {config_path}")
        
        print("\n" + "=" * 80)
        print("✅ Advanced AI Integration Test Completed Successfully!")
        print("=" * 80)
        
        # Summary
        available_models = sum(1 for model in models if model.get("available", False))
        total_models = len(models)
        
        print(f"\n📊 Summary:")
        print(f"  - Total configured models: {total_models}")
        print(f"  - Available models: {available_models}")
        print(f"  - Models needing setup: {total_models - available_models}")
        print(f"  - API endpoints: {len(endpoints) if 'endpoints' in locals() else 'Unknown'}")
        
        if available_models == 0:
            print(f"\n💡 Next Steps:")
            print(f"  1. Install llama-cpp-python: pip install llama-cpp-python")
            print(f"  2. Download model files (e.g., llama-2-7b-chat.gguf)")
            print(f"  3. Update model paths in {config_path}")
            print(f"  4. Test specific model integrations")
        
        return True
        
    except Exception as e:
        print(f"\n❌ Test failed with error: {e}")
        import traceback
        traceback.print_exc()
        return False

async def test_fallback_mode():
    """Test the system in fallback mode (without advanced models)"""
    
    print("\n🔄 Testing Fallback Mode (No Advanced AI)")
    print("-" * 50)
    
    try:
        from agents.enhanced_model_selector import get_enhanced_selector
        
        enhanced_selector = get_enhanced_selector()
        
        # Test basic 3D model selection
        result = await enhanced_selector.analyze_question_with_ai(
            question="Show me a walking animation",
            use_advanced_ai=False,
            language="en"
        )
        
        print(f"✅ Fallback mode works:")
        print(f"  - Selected Model: {result.get('selected_model')}")
        print(f"  - Confidence: {result.get('confidence', 0):.2f}")
        print(f"  - Description: {result.get('description', 'N/A')}")
        
        return True
        
    except Exception as e:
        print(f"❌ Fallback mode failed: {e}")
        return False

def main():
    """Main test function"""
    
    print("🧪 Advanced AI Models Integration Test Suite")
    print("=" * 80)
    
    # Change to the correct directory
    script_dir = os.path.dirname(os.path.abspath(__file__))
    os.chdir(script_dir)
    
    # Run tests
    start_time = time.time()
    
    try:
        # Test advanced AI integration
        success1 = asyncio.run(test_advanced_ai_integration())
        
        # Test fallback mode
        success2 = asyncio.run(test_fallback_mode())
        
        elapsed_time = time.time() - start_time
        
        print(f"\n⏱️ Total test time: {elapsed_time:.2f} seconds")
        
        if success1 and success2:
            print("🎉 All tests passed!")
            return 0
        else:
            print("⚠️ Some tests failed - check output above")
            return 1
            
    except KeyboardInterrupt:
        print("\n⚠️ Tests interrupted by user")
        return 1
    except Exception as e:
        print(f"\n❌ Test suite failed: {e}")
        return 1

if __name__ == "__main__":
    exit(main())