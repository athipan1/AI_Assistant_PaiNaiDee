"""
Test external API integration for tourism features
Tests Google Places API, accommodation booking, and AI recommendations
"""

import pytest
import requests
import json

# Test server URL
BASE_URL = "http://localhost:8000"

def test_location_service_health():
    """Test location services health check"""
    response = requests.get(f"{BASE_URL}/location/health")
    assert response.status_code == 200
    
    data = response.json()
    assert data["status"] == "healthy"
    assert "services" in data
    assert "google_places" in data["services"]
    assert "accommodation_booking" in data["services"]
    assert "redis_cache" in data["services"]

def test_nearby_search():
    """Test nearby places search (mock data)"""
    response = requests.get(f"{BASE_URL}/location/nearby?lat=13.7563&lng=100.5018&radius=2000")
    assert response.status_code == 200
    
    data = response.json()
    assert "location" in data
    assert "accommodations" in data
    assert "restaurants" in data
    assert "attractions" in data
    assert data["location"]["lat"] == 13.7563
    assert data["location"]["lng"] == 100.5018

def test_accommodation_search():
    """Test accommodation search endpoint"""
    response = requests.post(f"{BASE_URL}/location/accommodations/search", json={
        "lat": 13.7563,
        "lng": 100.5018,
        "min_rating": 3.5
    })
    assert response.status_code == 200
    
    accommodations = response.json()
    assert isinstance(accommodations, list)
    
    # Check accommodation structure
    if accommodations:
        acc = accommodations[0]
        assert "accommodation_id" in acc
        assert "name" in acc
        assert "address" in acc
        assert "location" in acc
        assert "rating" in acc
        assert "price_per_night" in acc

def test_smart_accommodation_search():
    """Test AI-powered smart accommodation search"""
    response = requests.post(f"{BASE_URL}/location/accommodations/smart-search", json={
        "lat": 13.7563,
        "lng": 100.5018,
        "min_rating": 3.5,
        "budget": 2000,
        "property_type": "hotel",
        "preferred_amenities": ["Free WiFi", "Fitness Center"],
        "style": "city"
    })
    assert response.status_code == 200
    
    accommodations = response.json()
    assert isinstance(accommodations, list)
    
    # Verify AI analysis is included
    if accommodations:
        acc = accommodations[0]
        assert "match_analysis" in acc
        if acc["match_analysis"]:
            assert "match_score" in acc["match_analysis"]
            assert "match_reasons" in acc["match_analysis"]
            assert "recommendation" in acc["match_analysis"]

def test_places_search():
    """Test places search endpoint"""
    response = requests.post(f"{BASE_URL}/location/places/search", json={
        "lat": 13.7563,
        "lng": 100.5018,
        "radius": 5000,
        "place_types": ["restaurant"],
        "limit": 10
    })
    
    # Should return 200 even if no Google API key (empty results)
    assert response.status_code == 200
    places = response.json()
    assert isinstance(places, list)

def test_accommodation_ai_matching():
    """Test AI accommodation matching logic using actual API"""
    # First get accommodations
    response = requests.post(f"{BASE_URL}/location/accommodations/smart-search", json={
        "lat": 13.7563,
        "lng": 100.5018,
        "budget": 2000,
        "property_type": "hotel",
        "preferred_amenities": ["Free WiFi", "Fitness Center"],
        "style": "city"
    })
    
    assert response.status_code == 200
    accommodations = response.json()
    
    if accommodations:
        acc = accommodations[0]
        match_analysis = acc.get("match_analysis")
        
        if match_analysis:
            assert "match_score" in match_analysis
            assert "match_reasons" in match_analysis
            assert "recommendation" in match_analysis
            assert match_analysis["match_score"] >= 0.0  # Valid score range

if __name__ == "__main__":
    pytest.main([__file__, "-v"])