"""
Tests for Group Trip Planning functionality
"""

import pytest
import json
from fastapi.testclient import TestClient
from main import app

client = TestClient(app)

class TestGroupTripPlanning:
    """Test group trip planning functionality"""
    
    def test_create_group_trip(self):
        """Test creating a new group trip"""
        response = client.post("/api/trip/group", json={
            "group_name": "Test Adventure",
            "creator_id": "test_user_001",
            "creator_username": "Test User",
            "destination_city": "Bangkok, Thailand",
            "start_date": "2024-08-01",
            "end_date": "2024-08-07"
        })
        
        assert response.status_code == 200
        data = response.json()
        
        assert data["group_name"] == "Test Adventure"
        assert data["creator_id"] == "test_user_001"
        assert data["destination_city"] == "Bangkok, Thailand"
        assert data["status"] == "draft"
        assert data["member_count"] == 1
        assert "group_id" in data
        assert "invitation_code" in data
        
        return data["group_id"]
    
    def test_set_user_preferences(self):
        """Test setting user travel preferences"""
        response = client.post("/api/user/preferences", json={
            "user_id": "test_user_001",
            "username": "Test User",
            "interest_types": ["culture", "food", "nature"],
            "activity_level": "medium",
            "budget_range": "mid",
            "time_preferences": ["morning", "afternoon"],
            "location_preferences": ["outdoor", "mixed"]
        })
        
        assert response.status_code == 200
        data = response.json()
        
        assert data["status"] == "success"
        assert data["user_id"] == "test_user_001"
        assert data["preferences"]["interest_types"] == ["culture", "food", "nature"]
        assert data["preferences"]["activity_level"] == "medium"
    
    def test_add_location_to_group(self):
        """Test adding a location to group trip"""
        # First create a group
        group_id = self.test_create_group_trip()
        
        response = client.post(f"/api/trip/group/{group_id}/locations?user_id=test_user_001", json={
            "location_name": "Wat Pho Temple",
            "location_type": "attraction",
            "description": "Beautiful temple with giant reclining Buddha",
            "coordinates": [13.7467, 100.4927],
            "tags": ["culture", "religion", "temple", "history"],
            "rating": 4.6,
            "price_range": "$",
            "duration_hours": 2.5,
            "best_time": ["morning", "afternoon"]
        })
        
        assert response.status_code == 200
        data = response.json()
        
        assert data["status"] == "success"
        assert "location_id" in data
    
    def test_get_group_locations(self):
        """Test retrieving group locations"""
        # Create group and add location
        group_id = self.test_create_group_trip()
        self.test_add_location_to_group()
        
        response = client.get(f"/api/trip/group/{group_id}/locations")
        
        assert response.status_code == 200
        data = response.json()
        
        assert "locations" in data
        assert "total" in data
        assert data["total"] >= 0
    
    def test_generate_group_plan(self):
        """Test AI-powered group plan generation"""
        # Create group, set preferences, and add locations
        group_id = self.test_create_group_trip()
        self.test_set_user_preferences()
        self.test_add_location_to_group()
        
        response = client.post("/api/group/plan", json={
            "group_id": group_id,
            "max_locations_per_day": 3,
            "include_alternatives": False,
            "optimization_focus": "balanced"
        })
        
        assert response.status_code == 200
        data = response.json()
        
        assert "plan_id" in data
        assert data["group_id"] == group_id
        assert "itinerary" in data
        assert "optimized_locations" in data
        assert "confidence_score" in data
        assert "compromise_analysis" in data
        
        # Check itinerary structure
        assert isinstance(data["itinerary"], list)
        if data["itinerary"]:
            day = data["itinerary"][0]
            assert "day" in day
            assert "date" in day
            assert "locations" in day
    
    def test_create_share_link(self):
        """Test creating public share link"""
        group_id = self.test_create_group_trip()
        
        response = client.post(f"/api/trip/group/{group_id}/share")
        
        assert response.status_code == 200
        data = response.json()
        
        assert "public_link" in data
        assert "full_url" in data
        assert data["public_link"].startswith("/group-trip/")
        assert data["full_url"].startswith("/group-trip-viewer.html?id=")
    
    def test_analyze_group_preferences(self):
        """Test group preference analysis"""
        group_id = self.test_create_group_trip()
        self.test_set_user_preferences()
        
        response = client.get(f"/api/group/{group_id}/analysis")
        
        assert response.status_code == 200
        data = response.json()
        
        assert "group_id" in data
        assert "analysis" in data
        assert "recommendations" in data
        
        analysis = data["analysis"]
        assert "member_count" in analysis
        assert "consensus_strength" in analysis
        assert "activity_level" in analysis
        assert "budget_range" in analysis

class TestGroupTripIntegration:
    """Integration tests for complete group trip workflow"""
    
    def test_complete_group_trip_workflow(self):
        """Test complete workflow from creation to planning"""
        
        # 1. Create group trip
        create_response = client.post("/api/trip/group", json={
            "group_name": "Complete Test Trip",
            "creator_id": "integration_user",
            "creator_username": "Integration User",
            "destination_city": "Chiang Mai, Thailand",
            "start_date": "2024-09-01",
            "end_date": "2024-09-05"
        })
        
        assert create_response.status_code == 200
        group_data = create_response.json()
        group_id = group_data["group_id"]
        
        # 2. Set user preferences
        prefs_response = client.post("/api/user/preferences", json={
            "user_id": "integration_user",
            "username": "Integration User",
            "interest_types": ["nature", "adventure", "culture"],
            "activity_level": "high",
            "budget_range": "mid",
            "time_preferences": ["morning", "afternoon"],
            "location_preferences": ["outdoor", "mixed"]
        })
        
        assert prefs_response.status_code == 200
        
        # 3. Add multiple locations
        locations = [
            {
                "location_name": "Doi Suthep Temple",
                "location_type": "attraction",
                "description": "Sacred temple on mountain with city views",
                "coordinates": [18.8044, 98.9222],
                "tags": ["culture", "temple", "nature", "views"],
                "rating": 4.7,
                "price_range": "$",
                "duration_hours": 3.0,
                "best_time": ["morning", "afternoon"]
            },
            {
                "location_name": "Elephant Nature Park",
                "location_type": "activity",
                "description": "Ethical elephant sanctuary and rescue center",
                "coordinates": [19.0633, 98.8581],
                "tags": ["nature", "animals", "ethical", "adventure"],
                "rating": 4.8,
                "price_range": "$$$",
                "duration_hours": 8.0,
                "best_time": ["morning"]
            }
        ]
        
        for location in locations:
            loc_response = client.post(
                f"/api/trip/group/{group_id}/locations?user_id=integration_user",
                json=location
            )
            assert loc_response.status_code == 200
        
        # 4. Generate AI plan
        plan_response = client.post("/api/group/plan", json={
            "group_id": group_id,
            "max_locations_per_day": 2,
            "include_alternatives": False,
            "optimization_focus": "balanced"
        })
        
        assert plan_response.status_code == 200
        plan_data = plan_response.json()
        
        # Verify plan quality
        assert plan_data["confidence_score"] > 0
        assert len(plan_data["optimized_locations"]) >= 1
        assert len(plan_data["itinerary"]) == 5  # 5 days
        
        # 5. Create share link
        share_response = client.post(f"/api/trip/group/{group_id}/share")
        assert share_response.status_code == 200
        share_data = share_response.json()
        
        # 6. Test public access
        public_id = share_data["public_link"].split("/")[-1]
        public_response = client.get(f"/api/trip/group/public/{public_id}")
        assert public_response.status_code == 200
        
        public_data = public_response.json()
        assert public_data["group_id"] == group_id
        assert public_data["group_name"] == "Complete Test Trip"
        
        print("✅ Complete group trip workflow test passed!")

if __name__ == "__main__":
    # Run tests
    test_group = TestGroupTripPlanning()
    test_integration = TestGroupTripIntegration()
    
    print("Running Group Trip Planning Tests...")
    
    try:
        test_group.test_create_group_trip()
        print("✅ Create group trip test passed")
        
        test_group.test_set_user_preferences()
        print("✅ Set user preferences test passed")
        
        test_integration.test_complete_group_trip_workflow()
        print("✅ All integration tests passed")
        
        print("\n🎉 All Group Trip Planning tests completed successfully!")
        
    except Exception as e:
        print(f"❌ Test failed: {e}")
        import traceback
        traceback.print_exc()