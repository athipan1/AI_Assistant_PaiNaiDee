#!/usr/bin/env python3
"""
Demo script for Advanced AI Models Integration
Showcases the new llama.cpp, OpenChat, and OpenHermes capabilities
"""

import asyncio
import json
import time
from typing import Dict, Any
import sys
import os

# Add the current directory to the path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from agents.enhanced_model_selector import get_enhanced_selector
from agents.advanced_ai_models import get_ai_manager, initialize_advanced_ai

def print_header(title: str):
    """Print a formatted header"""
    print("\n" + "=" * 80)
    print(f"🎯 {title}")
    print("=" * 80)

def print_section(title: str):
    """Print a formatted section"""
    print(f"\n📋 {title}")
    print("-" * 60)

def print_result(label: str, value: Any, indent: int = 0):
    """Print a formatted result"""
    prefix = "  " * indent
    if isinstance(value, dict):
        print(f"{prefix}✅ {label}:")
        for k, v in value.items():
            print(f"{prefix}  - {k}: {v}")
    else:
        print(f"{prefix}✅ {label}: {value}")

async def demo_enhanced_model_selection():
    """Demo enhanced 3D model selection with AI"""
    
    print_section("Enhanced 3D Model Selection")
    
    selector = get_enhanced_selector()
    
    demo_questions = [
        "Show me a person walking in traditional Thai style",
        "I want to see someone running to catch a bus",
        "Display a calm standing meditation pose",
        "Can you show me a character for cultural dance?",
        "I need an idle animation for my Thai tourism app"
    ]
    
    for i, question in enumerate(demo_questions, 1):
        print(f"\n{i}. Question: '{question}'")
        
        try:
            start_time = time.time()
            
            # Test both with and without AI enhancement
            result_basic = await selector.analyze_question_with_ai(
                question=question,
                use_advanced_ai=False,
                language="en"
            )
            
            result_enhanced = await selector.analyze_question_with_ai(
                question=question,
                use_advanced_ai=True,
                language="en"
            )
            
            processing_time = time.time() - start_time
            
            print(f"   Basic Selection:")
            print(f"   - Model: {result_basic.get('selected_model')}")
            print(f"   - Confidence: {result_basic.get('confidence', 0):.2f}")
            
            print(f"   Enhanced Selection:")
            print(f"   - Model: {result_enhanced.get('selected_model')}")
            print(f"   - Confidence: {result_enhanced.get('confidence', 0):.2f}")
            print(f"   - AI Enhanced: {result_enhanced.get('ai_enhancement_used', False)}")
            
            if result_enhanced.get('enhanced_analysis'):
                ai_analysis = result_enhanced['enhanced_analysis']
                print(f"   - AI Model: {ai_analysis.get('model_used', 'N/A')}")
                print(f"   - AI Explanation: {ai_analysis.get('ai_explanation', 'N/A')[:100]}...")
            
            print(f"   - Processing Time: {processing_time:.2f}s")
            
        except Exception as e:
            print(f"   ❌ Error: {e}")

async def demo_tourism_advice():
    """Demo AI-powered tourism advice"""
    
    print_section("AI Tourism Advice")
    
    selector = get_enhanced_selector()
    
    tourism_questions = [
        {
            "question": "What are the best temples to visit in Bangkok for first-time visitors?",
            "location": "Bangkok, Thailand",
            "preferences": {"interests": ["culture", "history"], "budget": "moderate"}
        },
        {
            "question": "Recommend traditional Thai food experiences in Chiang Mai",
            "location": "Chiang Mai, Thailand", 
            "preferences": {"dietary": "vegetarian", "spice_level": "mild"}
        },
        {
            "question": "What cultural festivals should I attend in Thailand?",
            "location": "Thailand",
            "preferences": {"season": "cool", "type": "cultural"}
        }
    ]
    
    for i, query in enumerate(tourism_questions, 1):
        print(f"\n{i}. Question: '{query['question']}'")
        print(f"   Location: {query['location']}")
        print(f"   Preferences: {query['preferences']}")
        
        try:
            start_time = time.time()
            
            result = await selector.get_tourism_advice(
                question=query['question'],
                location=query['location'],
                preferences=query['preferences'],
                language="en"
            )
            
            processing_time = time.time() - start_time
            
            print(f"   Response:")
            advice = result.get('advice', 'No advice available')
            print(f"   - Advice: {advice[:200]}...")
            print(f"   - Related 3D Model: {result.get('related_3d_model', 'None')}")
            print(f"   - AI Model Used: {result.get('ai_model_used', 'Unknown')}")
            print(f"   - Processing Time: {processing_time:.2f}s")
            
        except Exception as e:
            print(f"   ❌ Error: {e}")

async def demo_conversation():
    """Demo conversational AI with 3D model context"""
    
    print_section("Conversational AI")
    
    selector = get_enhanced_selector()
    
    conversation_flow = [
        "Hello! I'm planning a trip to Thailand. Can you help?",
        "I'm interested in cultural experiences. What do you recommend?",
        "Can you show me some traditional dance movements?",
        "What about temple etiquette? I want to be respectful.",
        "Thank you! This has been very helpful."
    ]
    
    conversation_history = []
    
    for i, message in enumerate(conversation_flow, 1):
        print(f"\n{i}. User: {message}")
        
        try:
            start_time = time.time()
            
            result = await selector.conversational_response(
                message=message,
                conversation_history=conversation_history[-4:],  # Keep last 4 exchanges
                language="en"
            )
            
            processing_time = time.time() - start_time
            
            response = result.get('response', 'No response available')
            print(f"   Assistant: {response[:200]}...")
            
            if result.get('suggested_3d_model'):
                print(f"   💡 Suggested 3D Model: {result['suggested_3d_model']}")
                print(f"   📄 Model Description: {result.get('model_description', 'N/A')}")
            
            print(f"   🤖 AI Model: {result.get('ai_model_used', 'Unknown')}")
            print(f"   ⏱️ Time: {processing_time:.2f}s")
            
            # Add to conversation history
            conversation_history.extend([
                {"role": "user", "content": message},
                {"role": "assistant", "content": response}
            ])
            
        except Exception as e:
            print(f"   ❌ Error: {e}")

async def demo_model_capabilities():
    """Demo model capabilities and availability"""
    
    print_section("Available AI Models")
    
    ai_manager = get_ai_manager()
    selector = get_enhanced_selector()
    
    try:
        # Get model information
        model_info = await selector.get_available_ai_models()
        
        print(f"📊 System Overview:")
        print(f"   - Advanced AI Models: {model_info.get('total_advanced_models', 0)}")
        print(f"   - Available Advanced Models: {model_info.get('available_advanced_models', 0)}")
        print(f"   - 3D Models: {model_info.get('total_3d_models', 0)}")
        print(f"   - Supported Capabilities: {len(model_info.get('capabilities', []))}")
        
        print(f"\n🤖 Advanced AI Models:")
        for model in model_info.get('advanced_ai_models', []):
            status = "✅ Available" if model.get('available') else "❌ Unavailable"
            print(f"   - {model['name']} ({model['type']}) - {status}")
            print(f"     Capabilities: {', '.join(model.get('capabilities', []))}")
            print(f"     Languages: {', '.join(model.get('languages', []))}")
            print(f"     Priority: {model.get('priority', 'N/A')}")
        
        print(f"\n🎯 3D Models:")
        for model in model_info.get('threed_models', [])[:3]:  # Show first 3
            print(f"   - {model.get('name', 'Unknown')}")
            print(f"     Description: {model.get('description', 'N/A')}")
            print(f"     Size: {model.get('size', 0) / 1024 / 1024:.1f} MB")
        
        print(f"\n🎨 Capabilities Available:")
        for capability in model_info.get('capabilities', []):
            print(f"   - {capability}")
        
    except Exception as e:
        print(f"❌ Error getting model info: {e}")

async def main():
    """Main demo function"""
    
    print_header("🎮 PaiNaiDee Advanced AI Integration Demo")
    print("This demo showcases the new advanced AI capabilities:")
    print("• llama.cpp integration for efficient local inference")
    print("• OpenChat support for conversational AI")  
    print("• OpenHermes integration for human-like communication")
    print("• Enhanced 3D model selection with AI insights")
    print("• Tourism-focused AI advice and recommendations")
    
    try:
        # Initialize AI system
        print_section("System Initialization")
        print("🚀 Initializing advanced AI system...")
        
        await initialize_advanced_ai()
        print("✅ Advanced AI system initialized successfully")
        
        # Run demos
        await demo_model_capabilities()
        await demo_enhanced_model_selection()
        await demo_tourism_advice()
        await demo_conversation()
        
        print_header("🎉 Demo Complete!")
        print("The advanced AI integration is working successfully!")
        print("\n📖 Next Steps:")
        print("1. Install llama-cpp-python for local llama.cpp models")
        print("2. Download specific model files (GGUF for llama.cpp)")
        print("3. Update config/ai_models.json with your model paths")
        print("4. Test with actual model inference")
        print("5. Integrate with your frontend application")
        
        print("\n🔗 API Endpoints Available:")
        print("• POST /advanced_ai/generate - General AI text generation")
        print("• POST /advanced_ai/conversation - Natural conversation")
        print("• POST /advanced_ai/tourism_advisor - Tourism advice")
        print("• POST /ai/select_model_enhanced - Enhanced 3D model selection")
        print("• GET /advanced_ai/models - List available models")
        print("• GET /advanced_ai/health - System health check")
        
    except Exception as e:
        print(f"\n❌ Demo failed: {e}")
        import traceback
        traceback.print_exc()
        return 1
    
    return 0

if __name__ == "__main__":
    exit(asyncio.run(main()))