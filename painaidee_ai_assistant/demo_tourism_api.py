#!/usr/bin/env python3
"""
Demo script for the new tourism external API features
Demonstrates Google Places API integration and accommodation booking with AI recommendations
"""

import requests
import json
import time
from typing import Dict, Any

BASE_URL = "http://localhost:8000"

def print_header(title: str):
    """Print a formatted header"""
    print("\n" + "="*60)
    print(f"🌴 {title}")
    print("="*60)

def print_json(data: Dict[Any, Any], title: str = ""):
    """Pretty print JSON data"""
    if title:
        print(f"\n📋 {title}:")
    print(json.dumps(data, indent=2, ensure_ascii=False))

def check_service_health():
    """Check the health of location services"""
    print_header("Service Health Check")
    
    try:
        response = requests.get(f"{BASE_URL}/location/health")
        if response.status_code == 200:
            health_data = response.json()
            print_json(health_data)
            return True
        else:
            print(f"❌ Health check failed: {response.status_code}")
            return False
    except Exception as e:
        print(f"❌ Failed to connect to server: {e}")
        return False

def demo_nearby_search():
    """Demo nearby places search"""
    print_header("Nearby Places Search (Bangkok)")
    
    # Bangkok coordinates
    lat, lng = 13.7563, 100.5018
    
    try:
        response = requests.get(
            f"{BASE_URL}/location/nearby",
            params={
                "lat": lat,
                "lng": lng,
                "radius": 2000,
                "include_restaurants": True,
                "include_attractions": True,
                "include_accommodations": True
            }
        )
        
        if response.status_code == 200:
            data = response.json()
            print(f"📍 Location: {data['location']}")
            print(f"🔍 Search radius: {data['radius']} meters")
            print(f"🏨 Accommodations found: {len(data.get('accommodations', []))}")
            print(f"🍽️ Restaurants found: {len(data.get('restaurants', []))}")
            print(f"🎯 Attractions found: {len(data.get('attractions', []))}")
            
            # Show first accommodation if available
            if data.get('accommodations'):
                print_json(data['accommodations'][0], "Sample Accommodation")
        else:
            print(f"❌ Search failed: {response.status_code}")
            
    except Exception as e:
        print(f"❌ Error during nearby search: {e}")

def demo_smart_accommodation_search():
    """Demo AI-powered accommodation search"""
    print_header("AI-Powered Accommodation Search")
    
    # User preferences for demonstration
    search_request = {
        "lat": 13.7563,
        "lng": 100.5018,
        "min_rating": 3.5,
        "budget": 2000,
        "property_type": "hotel",
        "preferred_amenities": ["Free WiFi", "Fitness Center"],
        "style": "city"
    }
    
    print("🔍 Search Parameters:")
    print_json(search_request)
    
    try:
        response = requests.post(
            f"{BASE_URL}/location/accommodations/smart-search",
            json=search_request
        )
        
        if response.status_code == 200:
            accommodations = response.json()
            print(f"\n✅ Found {len(accommodations)} matching accommodations")
            
            for i, acc in enumerate(accommodations, 1):
                print(f"\n🏨 Hotel #{i}: {acc['name']}")
                print(f"📍 Address: {acc['address']}")
                print(f"⭐ Rating: {acc['rating']}/5.0 ({acc['review_count']} reviews)")
                print(f"💰 Price: ฿{acc['price_per_night']:,.0f} per night")
                print(f"🏢 Type: {acc['property_type']}")
                print(f"🛎️ Amenities: {', '.join(acc['amenities'][:3])}...")
                
                # Show AI analysis
                if acc.get('match_analysis'):
                    analysis = acc['match_analysis']
                    print(f"🤖 AI Match Score: {analysis['match_score']:.1%}")
                    print(f"💡 Recommendation: {analysis['recommendation']}")
                    print(f"📝 Reasons: {', '.join(analysis['match_reasons'][:2])}")
        else:
            print(f"❌ Search failed: {response.status_code}")
            
    except Exception as e:
        print(f"❌ Error during smart search: {e}")

def demo_places_search():
    """Demo Google Places search"""
    print_header("Google Places API Search")
    
    search_request = {
        "lat": 13.7563,
        "lng": 100.5018,
        "radius": 5000,
        "place_types": ["restaurant"],
        "min_rating": 4.0,
        "limit": 5
    }
    
    print("🔍 Searching for restaurants...")
    print_json(search_request)
    
    try:
        response = requests.post(
            f"{BASE_URL}/location/places/search",
            json=search_request
        )
        
        if response.status_code == 200:
            places = response.json()
            print(f"\n✅ Found {len(places)} restaurants")
            
            if not places:
                print("ℹ️ No results (Google Places API key not configured)")
                print("💡 This would return real restaurant data with a valid API key")
            else:
                for place in places:
                    print(f"\n🍽️ {place['name']}")
                    print(f"📍 {place['address']}")
                    if place.get('rating'):
                        print(f"⭐ {place['rating']}/5.0")
        else:
            print(f"❌ Search failed: {response.status_code}")
            
    except Exception as e:
        print(f"❌ Error during places search: {e}")

def main():
    """Run the demo"""
    print("🇹🇭 PaiNaiDee AI Assistant - Tourism API Demo")
    print("=" * 60)
    print("This demo showcases the new external API integration features:")
    print("• Google Places API for location-based search")
    print("• Accommodation booking with AI recommendations")
    print("• Redis caching for performance")
    print("• Smart matching algorithms")
    
    # Check if server is running
    if not check_service_health():
        print("\n❌ Please start the server first:")
        print("python main.py")
        return
    
    # Run demos
    demo_nearby_search()
    time.sleep(1)
    
    demo_smart_accommodation_search()
    time.sleep(1)
    
    demo_places_search()
    
    print_header("Demo Complete!")
    print("🎉 All tourism API features demonstrated successfully!")
    print("🌐 Visit the web interface:")
    print(f"   • Main app: {BASE_URL}/static/index.html")
    print(f"   • Accommodations: {BASE_URL}/static/accommodations.html")
    print(f"   • Near me: {BASE_URL}/static/near-me.html")
    print(f"   • API docs: {BASE_URL}/docs")

if __name__ == "__main__":
    main()