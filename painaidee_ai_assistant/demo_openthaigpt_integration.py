"""
OpenThaiGPT Integration Demo
Demonstrates the new Smart AI capabilities with Thai language support
"""

import asyncio
import sys
import os
import json
from datetime import datetime

# Add the current directory to Python path
sys.path.insert(0, os.path.dirname(__file__))

from ai.orchestrator.ai_orchestrator import get_ai_orchestrator

async def demo_smart_ai():
    """Demonstrate the Smart AI functionality"""
    
    print("🇹🇭 PaiNaiDee Smart AI Demo - OpenThaiGPT Integration")
    print("=" * 60)
    print()
    
    # Initialize orchestrator
    print("🚀 Initializing AI Orchestrator...")
    orchestrator = get_ai_orchestrator()
    
    # Show system status
    status = orchestrator.get_status()
    print(f"✅ Thai LLM Enabled: {status['thai_llm_enabled']}")
    print(f"✅ OpenAI Fallback: {status['openai_fallback_enabled']}")
    print(f"✅ Existing Agents: {status['agents_available']}")
    print()
    
    # Test scenarios
    test_scenarios = [
        {
            "name": "Thai Greeting",
            "input": "สวัสดีครับ ผมเป็นนักท่องเที่ยว",
            "lang": "th",
            "expected_intent": "greeting"
        },
        {
            "name": "Thai Tourism Recommendation", 
            "input": "แนะนำสถานที่ท่องเที่ยวในเชียงใหม่ที่เป็นธรรมชาติหน่อย",
            "lang": "th",
            "expected_intent": "recommendation"
        },
        {
            "name": "English Tourism Question",
            "input": "What is the best time to visit Bangkok?",
            "lang": "en", 
            "expected_intent": "question"
        },
        {
            "name": "Thai Emotion Expression",
            "input": "ผมรู้สึกเหนื่อยและเครียดจากการทำงาน อยากไปพักผ่อน",
            "lang": "th",
            "expected_intent": "emotion"
        },
        {
            "name": "Auto Language Detection",
            "input": "Where can I find the best pad thai in Bangkok?",
            "lang": "auto",
            "expected_intent": "search"
        },
        {
            "name": "Mixed Content Search",
            "input": "ค้นหาข้อมูลเกี่ยวกับ Grand Palace",
            "lang": "auto",
            "expected_intent": "search"
        }
    ]
    
    results = []
    
    for i, scenario in enumerate(test_scenarios, 1):
        print(f"🧪 Test {i}: {scenario['name']}")
        print(f"📝 Input: '{scenario['input']}'")
        print(f"🌍 Language: {scenario['lang']}")
        
        try:
            # Measure response time
            start_time = datetime.now()
            
            response = await orchestrator.handle_input(
                user_input=scenario['input'],
                lang=scenario['lang'],
                source="demo",
                context={"test_scenario": scenario['name']}
            )
            
            end_time = datetime.now()
            total_time = (end_time - start_time).total_seconds()
            
            # Display results
            print(f"✅ Response: {response.content}")
            print(f"🎯 Intent: {response.intent_type.value} (confidence: {response.confidence:.2f})")
            print(f"🤖 Model: {response.model_used}")
            print(f"🔤 Language: {response.language.value}")
            print(f"⏱️  Response Time: {total_time:.2f}s")
            
            # Store results
            results.append({
                "scenario": scenario['name'],
                "input": scenario['input'],
                "lang_requested": scenario['lang'],
                "response": response.content,
                "intent_detected": response.intent_type.value,
                "lang_detected": response.language.value,
                "model_used": response.model_used,
                "confidence": response.confidence,
                "response_time": total_time,
                "expected_intent": scenario['expected_intent'],
                "success": True
            })
            
        except Exception as e:
            print(f"❌ Error: {str(e)}")
            results.append({
                "scenario": scenario['name'],
                "input": scenario['input'],
                "error": str(e),
                "success": False
            })
        
        print("-" * 50)
        print()
    
    # Summary
    print("📊 DEMO SUMMARY")
    print("=" * 60)
    
    successful_tests = sum(1 for r in results if r.get('success', False))
    total_tests = len(results)
    
    print(f"✅ Successful Tests: {successful_tests}/{total_tests}")
    print(f"📈 Success Rate: {(successful_tests/total_tests)*100:.1f}%")
    
    if successful_tests > 0:
        avg_response_time = sum(r.get('response_time', 0) for r in results if r.get('success')) / successful_tests
        print(f"⚡ Average Response Time: {avg_response_time:.2f}s")
        
        # Model usage stats
        model_usage = {}
        for result in results:
            if result.get('success') and 'model_used' in result:
                model = result['model_used']
                model_usage[model] = model_usage.get(model, 0) + 1
        
        print("\n🤖 Model Usage Statistics:")
        for model, count in model_usage.items():
            print(f"   {model}: {count} times ({(count/successful_tests)*100:.1f}%)")
        
        # Intent classification accuracy
        correct_intents = sum(1 for r in results 
                            if r.get('success') and 
                            r.get('intent_detected') == r.get('expected_intent'))
        
        print(f"\n🎯 Intent Classification Accuracy: {correct_intents}/{successful_tests} ({(correct_intents/successful_tests)*100:.1f}%)")
    
    print("\n🎉 Demo completed successfully!")
    print("💡 The Smart AI system is ready for Thai tourism assistance!")
    
    # Save results to file
    with open('/tmp/smart_ai_demo_results.json', 'w', encoding='utf-8') as f:
        json.dump(results, f, ensure_ascii=False, indent=2)
    
    print(f"📄 Detailed results saved to: /tmp/smart_ai_demo_results.json")

async def demo_api_example():
    """Show example of how to use the API"""
    print("\n" + "="*60)
    print("🔌 API USAGE EXAMPLE")
    print("="*60)
    
    api_example = """
# Example API Request to /api/ai/ask-smart

POST /api/ai/ask-smart
Content-Type: application/json

{
    "message": "แนะนำทริปในเชียงใหม่ที่ธรรมชาติหน่อย",
    "language": "th",
    "source": "3D-assistant",
    "context": {
        "user_location": "Bangkok",
        "travel_dates": "2024-12-01"
    },
    "user_profile": {
        "interests": ["nature", "culture"],
        "budget": "medium",
        "duration": 3
    }
}

# Expected Response:
{
    "content": "เชียงใหม่มีสถานที่ท่องเที่ยวธรรมชาติที่สวยงามมากมาย...",
    "intent_type": "recommendation",
    "language": "th", 
    "model_used": "openthaigpt",
    "confidence": 0.95,
    "response_time": 0.85,
    "metadata": {
        "source": "3D-assistant",
        "context": {...},
        "processing_time": 0.85
    },
    "status": "success"
}
"""
    
    print(api_example)
    
    websocket_example = """
# WebSocket Streaming Example

const ws = new WebSocket('ws://localhost:8000/api/ai/chat-stream');

ws.onopen = () => {
    ws.send(JSON.stringify({
        message: "สวัสดีครับ อยากทราบข้อมูลการท่องเที่ยวภูเก็ต",
        language: "th",
        source: "web"
    }));
};

ws.onmessage = (event) => {
    const data = JSON.parse(event.data);
    console.log(data.content); // AI response
};
"""
    
    print("🌐 WebSocket Streaming Example:")
    print(websocket_example)

if __name__ == "__main__":
    print("Starting OpenThaiGPT Integration Demo...")
    print()
    
    try:
        # Run the main demo
        asyncio.run(demo_smart_ai())
        
        # Show API examples
        asyncio.run(demo_api_example())
        
    except KeyboardInterrupt:
        print("\n👋 Demo interrupted by user")
    except Exception as e:
        print(f"\n❌ Demo failed: {str(e)}")
        import traceback
        traceback.print_exc()
    
    print("\n🙏 Thank you for trying the OpenThaiGPT integration!")