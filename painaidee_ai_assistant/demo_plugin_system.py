"""
Plugin System Demonstration
Shows all implemented functionality with examples
"""

import asyncio
import aiohttp
import json
from datetime import datetime

async def demo_plugin_system():
    """Comprehensive demonstration of the plugin system"""
    
    print("🚀 PaiNaiDee AI Assistant - Plugin System Demo")
    print("=" * 60)
    print("🎯 Real-time Information Retrieval from External APIs")
    print("=" * 60)
    
    async with aiohttp.ClientSession() as session:
        
        # 1. Demonstrate the specific endpoints requested
        print("\n📍 1. SPECIFIC PLUGIN ENDPOINTS (As Requested)")
        print("-" * 45)
        
        # TripAdvisor/Google Reviews Plugin
        print("\n🏖️  Latest Attractions in Chiang Mai:")
        async with session.get("http://localhost:8000/plugin/get_latest_attractions?province=ChiangMai") as resp:
            data = await resp.json()
            for attraction in data["attractions"]:
                print(f"   • {attraction['name']} - ⭐ {attraction['rating']}/5 ({attraction['review_count']} reviews)")
                print(f"     📍 {attraction['address']}")
        
        # Thai News Plugin  
        print("\n📰 Event News (Thai Language):")
        async with session.get("http://localhost:8000/plugin/get_event_news?lang=th") as resp:
            data = await resp.json()
            for news in data["news"]:
                print(f"   • {news['title']}")
                print(f"     📅 {news['publish_date']} | 📺 {news['source']}")
        
        # Cultural Sites Plugin
        print("\n🏛️  Temple Information - Wat Phra Kaew:")
        async with session.get("http://localhost:8000/plugin/get_temple_info?wat_name=Wat%20Phra%20Kaew") as resp:
            data = await resp.json()
            temple = data["temple_info"][0]
            print(f"   • {temple['name']} ({temple['official_name']})")
            print(f"     📖 {temple['description']}")
            print(f"     🎫 {temple['ticket_price']} | ⏰ {temple['open_hours']}")
        
        # 2. Demonstrate intent classification
        print("\n📍 2. INTELLIGENT INTENT CLASSIFICATION")
        print("-" * 45)
        
        queries = [
            "Where are the best temples to visit in Bangkok?",
            "ข่าวการท่องเที่ยวล่าสุดในประเทศไทย",
            "Tell me about cultural sites in Thailand"
        ]
        
        for query in queries:
            print(f"\n🤔 User Query: '{query}'")
            
            async with session.post("http://localhost:8000/plugin/query", 
                                   json={"question": query, "language": "auto"}) as resp:
                data = await resp.json()
                if data["success"]:
                    print(f"   🧠 AI Selected Plugins: {data['plugins_used']}")
                    print(f"   ⚡ Execution Time: {data['execution_time_ms']:.1f}ms")
                    print(f"   📊 Retrieved {len(data['results'])} plugin responses")
        
        # 3. Demonstrate admin functionality
        print("\n📍 3. PLUGIN ADMINISTRATION")
        print("-" * 45)
        
        # List all plugins
        async with session.get("http://localhost:8000/plugin/list") as resp:
            data = await resp.json()
            print(f"\n🔧 System Status: {data['total_plugins']} plugins, {data['enabled_plugins']} enabled")
            
            for plugin in data["plugins"]:
                status_icon = "🟢" if plugin["enabled"] else "🔴"
                print(f"   {status_icon} {plugin['name']}: {plugin['status']} ({plugin['request_count']} requests)")
        
        # Health check
        async with session.post("http://localhost:8000/plugin/health") as resp:
            data = await resp.json()
            print(f"\n🏥 Health Status: {data['overall_status'].upper()}")
            for plugin, healthy in data["plugin_health"].items():
                health_icon = "💚" if healthy else "💔"
                print(f"   {health_icon} {plugin}: {'Healthy' if healthy else 'Unhealthy'}")
        
        # 4. Demonstrate caching performance
        print("\n📍 4. CACHING & PERFORMANCE")
        print("-" * 45)
        
        test_url = "http://localhost:8000/plugin/get_latest_attractions?province=Bangkok"
        
        # First request (fresh)
        start = datetime.now()
        async with session.get(test_url) as resp:
            first_time = (datetime.now() - start).total_seconds() * 1000
        
        # Second request (cached)
        start = datetime.now()
        async with session.get(test_url) as resp:
            second_time = (datetime.now() - start).total_seconds() * 1000
        
        print(f"\n⚡ Performance Comparison:")
        print(f"   🆕 First Request (Fresh):  {first_time:.1f}ms")
        print(f"   🗄️  Second Request (Cached): {second_time:.1f}ms")
        print(f"   📈 Cache Speedup: {(first_time/second_time):.1f}x faster")
        
        # 5. Show plugin features summary
        print("\n📍 5. PLUGIN SYSTEM FEATURES")
        print("-" * 45)
        
        features = [
            "✅ Asynchronous & timeout-safe plugin execution",
            "✅ Intelligent caching with configurable TTL",
            "✅ Intent classification for automatic plugin selection", 
            "✅ Multi-language support (Thai & English)",
            "✅ Real-time health monitoring and statistics",
            "✅ Dynamic plugin enable/disable functionality",
            "✅ Comprehensive error handling and logging",
            "✅ RESTful API endpoints for all operations",
            "✅ Schema validation for data consistency",
            "✅ Rate limiting and abuse prevention"
        ]
        
        for feature in features:
            print(f"   {feature}")
        
        print("\n📍 6. AVAILABLE API ENDPOINTS")
        print("-" * 45)
        
        endpoints = [
            "/plugin/get_latest_attractions?province=<name>",
            "/plugin/get_event_news?lang=<th|en>", 
            "/plugin/get_temple_info?wat_name=<name>",
            "/plugin/query (POST) - Smart intent-based querying",
            "/plugin/execute (POST) - Direct plugin execution",
            "/plugin/list - List all plugins with status",
            "/plugin/health (POST) - System health check",
            "/admin/plugins/ - Admin dashboard",
            "/admin/plugins/list - Detailed admin listing",
            "/admin/plugins/<name>/enable|disable - Plugin control"
        ]
        
        for endpoint in endpoints:
            print(f"   📡 {endpoint}")
        
        print("\n" + "=" * 60)
        print("🎉 Plugin System Successfully Demonstrated!")
        print("🔗 External API Integration Ready for Production")
        print("📚 Full API Documentation: http://localhost:8000/docs")
        print("=" * 60)

if __name__ == "__main__":
    asyncio.run(demo_plugin_system())