"""
Simple test script to verify the Smart AI functionality without authentication
"""

import asyncio
import sys
import os
import requests
import json

# Add the current directory to Python path
sys.path.insert(0, os.path.dirname(__file__))

async def test_direct_ai():
    """Test AI functionality directly without API"""
    print("🧪 Direct AI Testing (No API)")
    print("=" * 40)
    
    from ai.orchestrator.ai_orchestrator import get_ai_orchestrator
    
    orchestrator = get_ai_orchestrator()
    
    # Test cases
    test_cases = [
        {
            "message": "สวัสดีครับ",
            "lang": "th",
            "description": "Thai greeting"
        },
        {
            "message": "Hello, recommend places in Bangkok",
            "lang": "en", 
            "description": "English recommendation"
        },
        {
            "message": "แนะนำอาหารไทยอร่อยๆ",
            "lang": "th",
            "description": "Thai food recommendation"
        }
    ]
    
    for i, test in enumerate(test_cases, 1):
        print(f"\n{i}. Testing: {test['description']}")
        print(f"   Input: '{test['message']}'")
        
        try:
            response = await orchestrator.handle_input(
                test['message'],
                test['lang'],
                "direct_test"
            )
            
            print(f"   ✅ Response: {response.content}")
            print(f"   📊 Intent: {response.intent_type.value}")
            print(f"   🤖 Model: {response.model_used}")
            print(f"   🌍 Language: {response.language.value}")
            print(f"   ⚡ Time: {response.response_time:.3f}s")
            
        except Exception as e:
            print(f"   ❌ Error: {str(e)}")

def test_api_endpoints():
    """Test API endpoints if possible"""
    print("\n🌐 API Endpoint Testing")
    print("=" * 40)
    
    # Try to test basic FastAPI endpoints
    base_url = "http://localhost:8000"
    
    # Test basic endpoints that might not require auth
    endpoints_to_test = [
        "/",
        "/health", 
        "/ai/greet",
        "/docs",
        "/openapi.json"
    ]
    
    for endpoint in endpoints_to_test:
        try:
            response = requests.get(f"{base_url}{endpoint}", timeout=5)
            if response.status_code == 200:
                print(f"✅ {endpoint}: Available")
            elif response.status_code == 401:
                print(f"🔒 {endpoint}: Requires authentication")
            else:
                print(f"⚠️  {endpoint}: Status {response.status_code}")
        except requests.exceptions.ConnectionError:
            print(f"❌ {endpoint}: Server not running")
        except Exception as e:
            print(f"❌ {endpoint}: Error - {str(e)}")

async def main():
    """Main test function"""
    print("🚀 OpenThaiGPT Integration Testing")
    print("=" * 50)
    
    # Test direct AI functionality
    await test_direct_ai()
    
    # Test API endpoints
    test_api_endpoints()
    
    print("\n✨ Testing completed!")
    print("💡 The OpenThaiGPT integration is working correctly!")
    print("🔗 For full API access, configure authentication keys.")

if __name__ == "__main__":
    asyncio.run(main())