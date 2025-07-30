"""
Test script for the Plugin System
Tests all plugin functionality including external API integration
"""

import asyncio
import aiohttp
import json
from datetime import datetime

class PluginSystemTester:
    def __init__(self, base_url="http://localhost:8000"):
        self.base_url = base_url
        self.session = None
        
    async def setup(self):
        """Setup test session"""
        self.session = aiohttp.ClientSession()
        
    async def cleanup(self):
        """Cleanup test session"""
        if self.session:
            await self.session.close()
            
    async def test_plugin_list(self):
        """Test plugin listing"""
        print("\n🔍 Testing Plugin List...")
        async with self.session.get(f"{self.base_url}/plugin/list") as response:
            data = await response.json()
            print(f"Status: {response.status}")
            print(f"Total Plugins: {data.get('total_plugins', 0)}")
            print(f"Enabled Plugins: {data.get('enabled_plugins', 0)}")
            for plugin in data.get('plugins', []):
                print(f"  - {plugin['name']}: {plugin['status']} ({'enabled' if plugin['enabled'] else 'disabled'})")
            return response.status == 200
            
    async def test_specific_endpoints(self):
        """Test the specific endpoints requested in requirements"""
        tests = [
            {
                "name": "Latest Attractions (ChiangMai)",
                "url": f"{self.base_url}/plugin/get_latest_attractions?province=ChiangMai",
                "expected_keys": ["province", "attractions", "metadata"]
            },
            {
                "name": "Event News (Thai)",
                "url": f"{self.base_url}/plugin/get_event_news?lang=th",
                "expected_keys": ["language", "news", "metadata"]
            },
            {
                "name": "Temple Info (Wat Phra Kaew)",
                "url": f"{self.base_url}/plugin/get_temple_info?wat_name=Wat%20Phra%20Kaew",
                "expected_keys": ["wat_name", "temple_info", "metadata"]
            }
        ]
        
        print("\n🎯 Testing Specific Plugin Endpoints...")
        results = []
        
        for test in tests:
            print(f"\n  Testing: {test['name']}")
            try:
                async with self.session.get(test["url"]) as response:
                    data = await response.json()
                    status_ok = response.status == 200
                    keys_present = all(key in data for key in test["expected_keys"])
                    
                    print(f"    Status: {response.status} ({'✅' if status_ok else '❌'})")
                    print(f"    Required keys: {'✅' if keys_present else '❌'}")
                    
                    if status_ok and keys_present:
                        print(f"    Data preview: {len(data.get(test['expected_keys'][1], []))} items")
                        
                    results.append(status_ok and keys_present)
                    
            except Exception as e:
                print(f"    Error: {e} ❌")
                results.append(False)
                
        return all(results)
        
    async def test_intent_classification(self):
        """Test intent classification and plugin selection"""
        test_queries = [
            {
                "question": "What are the best temples in Bangkok?",
                "expected_plugins": ["tripadvisor", "cultural_sites"],
                "language": "en"
            },
            {
                "question": "ข่าวท่องเที่ยวล่าสุด",
                "expected_plugins": ["thai_news"],
                "language": "th"
            },
            {
                "question": "Latest attractions in Phuket with reviews",
                "expected_plugins": ["tripadvisor"],
                "language": "en"
            }
        ]
        
        print("\n🧠 Testing Intent Classification...")
        results = []
        
        for query in test_queries:
            print(f"\n  Query: {query['question']}")
            
            payload = {
                "question": query["question"],
                "language": query["language"],
                "max_plugins": 3
            }
            
            try:
                async with self.session.post(
                    f"{self.base_url}/plugin/query",
                    json=payload
                ) as response:
                    data = await response.json()
                    
                    if response.status == 200 and data.get("success"):
                        plugins_used = data.get("plugins_used", [])
                        print(f"    Plugins used: {plugins_used}")
                        print(f"    Execution time: {data.get('execution_time_ms', 0):.2f}ms")
                        print(f"    Results: {len(data.get('results', []))} plugin responses")
                        
                        # Check if expected plugins were used
                        expected_found = any(p in plugins_used for p in query["expected_plugins"])
                        print(f"    Expected plugin match: {'✅' if expected_found else '❌'}")
                        
                        results.append(expected_found)
                    else:
                        print(f"    Failed: {data.get('error', 'Unknown error')} ❌")
                        results.append(False)
                        
            except Exception as e:
                print(f"    Error: {e} ❌")
                results.append(False)
                
        return all(results)
        
    async def test_admin_functionality(self):
        """Test admin plugin management"""
        print("\n👨‍💼 Testing Admin Functionality...")
        
        # Test admin stats
        print("  Testing admin stats...")
        async with self.session.get(f"{self.base_url}/plugin/admin/stats") as response:
            stats_ok = response.status == 200
            print(f"    Admin stats: {'✅' if stats_ok else '❌'}")
            
        # Test plugin health check
        print("  Testing plugin health check...")
        async with self.session.post(f"{self.base_url}/plugin/health") as response:
            health_ok = response.status == 200
            if health_ok:
                data = await response.json()
                overall_status = data.get("overall_status")
                print(f"    Health status: {overall_status} {'✅' if overall_status == 'healthy' else '❌'}")
            else:
                print(f"    Health check failed ❌")
                
        # Test admin plugin list
        print("  Testing admin plugin list...")
        async with self.session.get(f"{self.base_url}/admin/plugins/list") as response:
            admin_list_ok = response.status == 200
            print(f"    Admin plugin list: {'✅' if admin_list_ok else '❌'}")
            
        return stats_ok and health_ok and admin_list_ok
        
    async def test_caching_and_performance(self):
        """Test caching functionality"""
        print("\n⚡ Testing Caching and Performance...")
        
        # Make the same request twice to test caching
        test_url = f"{self.base_url}/plugin/get_latest_attractions?province=Bangkok"
        
        # First request
        start_time = datetime.now()
        async with self.session.get(test_url) as response1:
            first_time = (datetime.now() - start_time).total_seconds() * 1000
            data1 = await response1.json()
            
        # Second request (should be cached)
        start_time = datetime.now()
        async with self.session.get(test_url) as response2:
            second_time = (datetime.now() - start_time).total_seconds() * 1000
            data2 = await response2.json()
            
        print(f"  First request: {first_time:.2f}ms")
        print(f"  Second request: {second_time:.2f}ms")
        
        # Check if second request was faster (indicating cache hit)
        cache_working = second_time < first_time
        print(f"  Cache performance: {'✅' if cache_working else '❌'}")
        
        return cache_working
        
    async def test_error_handling(self):
        """Test error handling and edge cases"""
        print("\n🚨 Testing Error Handling...")
        
        # Test non-existent plugin
        print("  Testing non-existent plugin...")
        payload = {
            "plugin_name": "non_existent_plugin",
            "intent": "test",
            "parameters": {}
        }
        
        async with self.session.post(f"{self.base_url}/plugin/execute", json=payload) as response:
            not_found_ok = response.status == 404
            print(f"    Non-existent plugin handling: {'✅' if not_found_ok else '❌'}")
            
        # Test invalid intent
        print("  Testing plugin with empty query...")
        payload = {
            "question": "",
            "language": "en"
        }
        
        async with self.session.post(f"{self.base_url}/plugin/query", json=payload) as response:
            # Should handle gracefully
            empty_query_ok = response.status in [200, 400]  # Either success or valid error
            print(f"    Empty query handling: {'✅' if empty_query_ok else '❌'}")
            
        return not_found_ok and empty_query_ok
        
    async def run_all_tests(self):
        """Run all tests"""
        print("🚀 Starting Plugin System Tests...")
        print("=" * 50)
        
        await self.setup()
        
        try:
            test_results = {
                "Plugin List": await self.test_plugin_list(),
                "Specific Endpoints": await self.test_specific_endpoints(),
                "Intent Classification": await self.test_intent_classification(),
                "Admin Functionality": await self.test_admin_functionality(),
                "Caching & Performance": await self.test_caching_and_performance(),
                "Error Handling": await self.test_error_handling()
            }
            
            print("\n" + "=" * 50)
            print("📊 Test Results Summary:")
            print("=" * 50)
            
            passed = 0
            total = len(test_results)
            
            for test_name, result in test_results.items():
                status = "✅ PASSED" if result else "❌ FAILED"
                print(f"  {test_name:<25} {status}")
                if result:
                    passed += 1
                    
            print("=" * 50)
            print(f"Overall: {passed}/{total} tests passed ({passed/total*100:.1f}%)")
            
            if passed == total:
                print("🎉 All tests passed! Plugin system is working correctly.")
            else:
                print("⚠️  Some tests failed. Please check the implementation.")
                
            return passed == total
            
        finally:
            await self.cleanup()


async def main():
    """Main test function"""
    tester = PluginSystemTester()
    success = await tester.run_all_tests()
    return success

if __name__ == "__main__":
    asyncio.run(main())