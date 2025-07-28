"""
Tourism Enhancement Demonstration
Shows the AI recommendation enhancements in action, including the specific
"indoor cafes near accommodations during rainy evenings" scenario
"""

import asyncio
import json
from datetime import datetime, timedelta
import requests
from pathlib import Path
import sys
import os

# Add parent directory for imports
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))

from models.tourist_interest_graph import TouristInterestGraph
from models.contextual_recommendations import ContextualRecommendationEngine, WeatherCondition, TimeOfDay
from api.tourism_routes import *


async def demonstrate_tourism_enhancements():
    """Demonstrate the tourism enhancement features"""
    
    print("🌟" * 30)
    print("TOURISM AI ENHANCEMENT DEMONSTRATION")
    print("🌟" * 30)
    
    # Initialize systems
    print("\n📊 Initializing Tourism AI Systems...")
    tourist_graph = TouristInterestGraph(storage_dir="demo_tourist_data")
    contextual_engine = ContextualRecommendationEngine(storage_dir="demo_contextual_data")
    
    print("✓ Tourist Interest Graph initialized")
    print("✓ Contextual Recommendation Engine initialized")
    
    # Available locations/models
    available_locations = ['Walking.fbx', 'Running.fbx', 'Idle.fbx', 'Man.fbx', 'Man_Rig.fbx']
    
    # === SCENARIO 1: Building User Interest Profile ===
    print("\n" + "="*60)
    print("SCENARIO 1: Building User Interest Profile")
    print("="*60)
    
    print("\n👤 Simulating user interactions to build interest profile...")
    
    # Create a user who likes indoor, relaxing activities
    indoor_interactions = [
        ("I want to see a cozy indoor cafe setting", "Idle.fbx"),
        ("Show me a relaxing indoor environment", "Man.fbx"), 
        ("Display a peaceful indoor space", "Idle.fbx"),
        ("I need something calm and indoor", "Idle.fbx"),
        ("Show me a comfortable indoor scene", "Man.fbx")
    ]
    
    user_id = "demo_user_indoor_lover"
    session_base = "demo_session"
    
    captured_interests = []
    
    for i, (query, model) in enumerate(indoor_interactions):
        interaction_data = {
            'query': query,
            'selected_model': model,
            'context': {
                'weather': {'condition': 'cloudy', 'temperature': 22},
                'time_of_day': 'afternoon',
                'location': {'city': 'Bangkok', 'country': 'Thailand'}
            },
            'feedback': {'satisfaction': 0.8 + (i * 0.04)},  # Increasing satisfaction
            'interaction_time': 35 + (i * 5)
        }
        
        interest = tourist_graph.capture_interest_from_interaction(
            user_id, f"{session_base}_{i}", interaction_data
        )
        captured_interests.append(interest)
        
        print(f"  {i+1}. '{query}' → {model}")
        print(f"     Interest: {interest.interest_type}, Tags: {interest.specific_tags}")
        print(f"     Confidence: {interest.confidence:.2f}, Location Pref: {interest.location_preference}")
    
    # Show user profile summary
    print(f"\n📈 User Profile Summary:")
    user_interests = tourist_graph.user_interests[user_id]
    interest_types = [i.interest_type for i in user_interests]
    location_prefs = [i.location_preference for i in user_interests]
    
    print(f"  - Total Interactions: {len(user_interests)}")
    print(f"  - Interest Types: {set(interest_types)}")
    print(f"  - Location Preferences: {set(location_prefs)}")
    print(f"  - Average Confidence: {sum(i.confidence for i in user_interests) / len(user_interests):.2f}")
    
    # === SCENARIO 2: Contextual Analysis ===
    print("\n" + "="*60)
    print("SCENARIO 2: Real-time Contextual Analysis")
    print("="*60)
    
    print("\n🌧️ Analyzing current context...")
    current_context = contextual_engine.get_current_context()
    
    print(f"Current Context:")
    print(f"  - Time: {current_context.time_of_day.value.replace('_', ' ').title()}")
    print(f"  - Season: {current_context.season.value.title()}")
    print(f"  - Weather: {current_context.weather_condition.value.title()}")
    print(f"  - Temperature: {current_context.temperature:.1f}°C")
    print(f"  - Humidity: {current_context.humidity:.1f}%")
    print(f"  - Crowd Level: {current_context.crowd_level.title()}")
    
    # === SCENARIO 3: The "Rainy Evening Indoor Cafes" Demo ===
    print("\n" + "="*60)
    print("SCENARIO 3: 'Rainy Evening Indoor Cafes' Demo")
    print("="*60)
    
    print("\n🌧️ Simulating rainy evening scenario...")
    
    # Create rainy evening context
    evening_time = datetime.now().replace(hour=19, minute=30, second=0)
    rainy_evening_context = contextual_engine.get_current_context(
        weather_override={
            'condition': WeatherCondition.RAINY,
            'temperature': 24.0,
            'humidity': 85.0,
            'wind_speed': 15.0,
            'precipitation_chance': 90.0,
            'uv_index': 1.0
        }
    )
    rainy_evening_context.time_of_day = TimeOfDay.EVENING
    
    print(f"Scenario Context:")
    print(f"  - Time: Evening (7:30 PM)")
    print(f"  - Weather: Heavy Rain")
    print(f"  - Temperature: {rainy_evening_context.temperature}°C")
    print(f"  - Precipitation: {rainy_evening_context.precipitation_chance}%")
    
    # Get tourist interest recommendations
    print(f"\n👤 Getting recommendations based on user's indoor preferences...")
    tourist_recommendations = tourist_graph.get_recommendations_for_user(
        user_id, 
        {
            'weather': 'rainy',
            'time': 'evening',
            'scenario': 'indoor cafes near accommodations'
        },
        available_locations,
        top_k=3
    )
    
    print("Tourist Interest Recommendations:")
    for i, rec in enumerate(tourist_recommendations, 1):
        print(f"  {i}. {rec['location_id']} (Score: {rec['score']:.2f})")
        print(f"     Reasons: {', '.join(rec['reasoning'])}")
        if rec['matching_interests']:
            print(f"     Matching Interests: {len(rec['matching_interests'])} found")
    
    # Get contextual recommendations
    print(f"\n🌡️ Getting contextual recommendations for rainy evening...")
    contextual_recommendations = contextual_engine.generate_contextual_recommendations(
        available_locations,
        user_preferences={'location_preference': 'indoor', 'activity_level': 'low'},
        context_override=rainy_evening_context,
        top_k=3
    )
    
    print("Contextual Recommendations:")
    for i, rec in enumerate(contextual_recommendations, 1):
        print(f"  {i}. {rec.location_name} (Suitability: {rec.suitability_score:.2f})")
        print(f"     Weather Dependency: {rec.weather_dependency}")
        print(f"     Reasons: {', '.join(rec.contextual_reasons)}")
        if rec.special_considerations:
            print(f"     Special Notes: {', '.join(rec.special_considerations)}")
        print(f"     Optimal Time: {rec.optimal_time_window[0]:02d}:00-{rec.optimal_time_window[1]:02d}:00")
    
    # === SCENARIO 4: Integrated AI Recommendation ===
    print("\n" + "="*60)
    print("SCENARIO 4: Integrated AI Recommendation")
    print("="*60)
    
    print("\n🤖 Combining all AI systems for optimal recommendation...")
    
    # Simulate integrated recommendation
    query = "I need indoor cafes near my accommodation during this rainy evening"
    
    # Start with basic model selection
    from api.model_routes import model_selector
    basic_selection = model_selector.analyze_question(query)
    print(f"Basic AI Selection: {basic_selection['selected_model']} (confidence: {basic_selection['confidence']:.2f})")
    
    # Apply tourist interest insights
    if tourist_recommendations:
        top_tourist_rec = tourist_recommendations[0]
        if top_tourist_rec['score'] > 0.7:
            print(f"Tourist Interest Override: {top_tourist_rec['location_id']} strongly preferred")
            final_model = top_tourist_rec['location_id']
            final_confidence = min(1.0, basic_selection['confidence'] + 0.3)
        else:
            final_model = basic_selection['selected_model']
            final_confidence = basic_selection['confidence']
    else:
        final_model = basic_selection['selected_model']
        final_confidence = basic_selection['confidence']
    
    # Apply contextual adjustments
    if contextual_recommendations:
        contextual_match = next(
            (rec for rec in contextual_recommendations if rec.location_id == final_model),
            None
        )
        
        if contextual_match and contextual_match.suitability_score < 0.3:
            # Current selection is poor for context, find better alternative
            best_contextual = max(contextual_recommendations, key=lambda x: x.suitability_score)
            if best_contextual.suitability_score > 0.7:
                print(f"Contextual Override: {best_contextual.location_id} better for rainy evening")
                final_model = best_contextual.location_id
                final_confidence = min(1.0, final_confidence + 0.2)
    
    print(f"\n🎯 FINAL INTEGRATED RECOMMENDATION:")
    print(f"   Model: {final_model}")
    print(f"   Confidence: {final_confidence:.2f}")
    
    # Explanation
    explanation_parts = []
    if tourist_recommendations and tourist_recommendations[0]['score'] > 0.5:
        explanation_parts.append("matches user's indoor preferences")
    if contextual_recommendations:
        best_contextual = max(contextual_recommendations, key=lambda x: x.suitability_score)
        if best_contextual.suitability_score > 0.6:
            explanation_parts.append("suitable for current rainy evening conditions")
    
    if explanation_parts:
        print(f"   Why: This recommendation {' and '.join(explanation_parts)}")
    else:
        print(f"   Why: Standard recommendation with contextual awareness")
    
    # === SCENARIO 5: Analytics and Learning ===
    print("\n" + "="*60)
    print("SCENARIO 5: System Analytics & Learning")
    print("="*60)
    
    print("\n📊 Generating system analytics...")
    
    # Tourist graph analytics
    tourist_analytics = tourist_graph.get_analytics()
    print(f"Tourist Interest Graph:")
    print(f"  - Total Users: {tourist_analytics['total_users']}")
    print(f"  - Total Interests: {tourist_analytics['total_interests']}")
    print(f"  - Interest Distribution: {tourist_analytics['interest_type_distribution']}")
    print(f"  - Average Interests per User: {tourist_analytics['avg_interests_per_user']:.1f}")
    
    # Contextual analytics
    contextual_analytics = contextual_engine.get_analytics()
    print(f"\nContextual Recommendation Engine:")
    print(f"  - Total Locations Analyzed: {contextual_analytics['total_locations']}")
    print(f"  - Current Average Suitability: {contextual_analytics['avg_suitability']:.2f}")
    print(f"  - Current Weather: {contextual_analytics['current_context']['weather_condition']}")
    print(f"  - Current Time: {contextual_analytics['current_context']['time_of_day']}")
    
    # Clustering demonstration
    print(f"\n🔗 Performing interest clustering...")
    clusters = tourist_graph.perform_interest_clustering(min_users=1)  # Low threshold for demo
    
    if clusters:
        print(f"Interest Clusters Discovered: {len(clusters)}")
        for cluster_id, cluster in clusters.items():
            print(f"  - {cluster.cluster_name}: {cluster.user_count} users")
            print(f"    Common interests: {', '.join(cluster.interest_types)}")
            if cluster.common_tags:
                print(f"    Common tags: {', '.join(cluster.common_tags[:3])}")
    else:
        print("No clusters found (need more diverse user data)")
    
    # === SCENARIO 6: Different Weather Comparison ===
    print("\n" + "="*60)
    print("SCENARIO 6: Weather Impact Comparison")
    print("="*60)
    
    print("\n☀️ Comparing recommendations across different weather conditions...")
    
    weather_scenarios = [
        ("Clear Sunny Morning", WeatherCondition.CLEAR, TimeOfDay.MORNING, 25.0),
        ("Rainy Evening", WeatherCondition.RAINY, TimeOfDay.EVENING, 22.0),
        ("Cloudy Afternoon", WeatherCondition.CLOUDY, TimeOfDay.AFTERNOON, 28.0)
    ]
    
    for scenario_name, weather, time_of_day, temp in weather_scenarios:
        print(f"\n{scenario_name}:")
        
        scenario_context = contextual_engine.get_current_context(
            weather_override={
                'condition': weather,
                'temperature': temp,
                'humidity': 70.0,
                'precipitation_chance': 90.0 if weather == WeatherCondition.RAINY else 10.0,
                'wind_speed': 10.0,
                'uv_index': 8.0 if weather == WeatherCondition.CLEAR else 3.0
            }
        )
        scenario_context.time_of_day = time_of_day
        
        scenario_recs = contextual_engine.generate_contextual_recommendations(
            available_locations[:3],
            context_override=scenario_context,
            top_k=2
        )
        
        for rec in scenario_recs:
            print(f"  - {rec.location_name}: {rec.suitability_score:.2f} suitability")
            print(f"    Primary reason: {rec.contextual_reasons[0] if rec.contextual_reasons else 'General suitability'}")
    
    print("\n" + "🎉"*30)
    print("DEMONSTRATION COMPLETE!")
    print("🎉"*30)
    
    print(f"\n📋 Summary of AI Tourism Enhancements:")
    print(f"✓ Tourist Interest Graph: Captures and learns from user preferences")
    print(f"✓ Contextual Recommendations: Adapts to weather, time, and conditions")
    print(f"✓ Integrated AI: Combines multiple systems for optimal suggestions")
    print(f"✓ Real-time Analysis: Responds to current environmental factors")
    print(f"✓ Learning System: Improves recommendations through user interactions")
    print(f"✓ Scenario Handling: Specifically addresses 'rainy evening indoor cafes'")
    
    # Clean up demo data
    import shutil
    try:
        shutil.rmtree("demo_tourist_data", ignore_errors=True)
        shutil.rmtree("demo_contextual_data", ignore_errors=True)
    except:
        pass


def test_api_endpoints():
    """Test the API endpoints if server is running"""
    
    print("\n" + "🔧"*30)
    print("API ENDPOINT TESTING")
    print("🔧"*30)
    
    base_url = "http://localhost:8000"
    
    # Test health endpoint
    try:
        response = requests.get(f"{base_url}/tourism/health/tourism", timeout=5)
        if response.status_code == 200:
            health = response.json()
            print(f"✓ Tourism systems health: {health['status']}")
            print(f"  - Tourist Interest Graph: {health['systems']['tourist_interest_graph']['status']}")
            print(f"  - Contextual Recommendations: {health['systems']['contextual_recommendations']['status']}")
        else:
            print(f"⚠️ Health check returned status: {response.status_code}")
    except requests.RequestException:
        print("ℹ️ Server not running - skipping API tests")
        print("   To test APIs, run: python main.py")
        return
    
    # Test current context
    try:
        response = requests.get(f"{base_url}/tourism/context/current", timeout=5)
        if response.status_code == 200:
            context = response.json()['current_context']
            print(f"\n✓ Current context retrieved:")
            print(f"  - Time: {context['time_of_day']}")
            print(f"  - Weather: {context['weather_condition']}")
            print(f"  - Temperature: {context['temperature']:.1f}°C")
    except requests.RequestException as e:
        print(f"⚠️ Context API error: {e}")
    
    # Test contextual recommendations
    try:
        payload = {
            "available_locations": ["Walking.fbx", "Idle.fbx", "Man.fbx"],
            "top_k": 2
        }
        response = requests.post(f"{base_url}/tourism/recommendations/contextual", 
                               json=payload, timeout=5)
        if response.status_code == 200:
            recs = response.json()
            print(f"\n✓ Contextual recommendations API working:")
            for rec in recs:
                print(f"  - {rec['location_name']}: {rec['suitability_score']:.2f}")
    except requests.RequestException as e:
        print(f"⚠️ Recommendations API error: {e}")


if __name__ == "__main__":
    # Run demonstration
    asyncio.run(demonstrate_tourism_enhancements())
    
    # Test API endpoints if available
    test_api_endpoints()