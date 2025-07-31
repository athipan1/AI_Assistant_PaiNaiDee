"""
Test for Personalization System
Tests the enhanced personalization features
"""

import pytest
import json
import asyncio
from fastapi.testclient import TestClient
from datetime import datetime

# Import the main app
import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from main import app
from models.user_profile import user_profile_manager, Season, BudgetRange, PlaceType
from models.chat_memory import enhanced_chat_memory

client = TestClient(app)

class TestPersonalizationSystem:
    """Test suite for personalization system"""
    
    @pytest.fixture(scope="class")
    def test_user_id(self):
        return "test_user_001"
    
    @pytest.fixture(scope="class") 
    def test_session_id(self):
        return "test_session_001"
    
    def test_create_user_profile(self, test_user_id):
        """Test creating a new user profile"""
        profile_data = {
            "name": "นายทดสอบ ระบบ",
            "nickname": "ทดสอบ",
            "age_range": "26-35",
            "language_preference": "th",
            "location": "กรุงเทพมหานคร",
            "budget_range": "mid"
        }
        
        response = client.post(f"/personalization/users/{test_user_id}/profile", json=profile_data)
        assert response.status_code == 200
        
        data = response.json()
        assert data["status"] == "success"
        assert data["user_id"] == test_user_id
        assert data["profile"]["name"] == "นายทดสอบ ระบบ"
        assert data["profile"]["language"] == "th"
    
    def test_get_user_profile(self, test_user_id):
        """Test retrieving user profile"""
        response = client.get(f"/personalization/users/{test_user_id}/profile")
        assert response.status_code == 200
        
        data = response.json()
        assert data["user_id"] == test_user_id
        assert data["name"] == "นายทดสอบ ระบบ"
        assert data["language"] == "th"
        assert data["budget_range"] == "mid"
    
    def test_update_travel_preferences(self, test_user_id):
        """Test updating travel preferences"""
        preferences = {
            "favorite_places": ["วัดพระแก้ว", "ชายหาดป่าตอง"],
            "favorite_seasons": ["cool", "hot"],
            "place_types": ["temple", "beach"],
            "travel_style": ["cultural", "relaxing"],
            "group_preference": "couple"
        }
        
        response = client.put(f"/personalization/users/{test_user_id}/profile/travel", json=preferences)
        assert response.status_code == 200
        
        data = response.json()
        assert data["status"] == "success"
        assert "favorite_places" in data["updated_preferences"]
    
    def test_start_conversation(self, test_user_id, test_session_id):
        """Test starting a conversation"""
        conversation_data = {
            "session_id": test_session_id
        }
        
        response = client.post(f"/personalization/users/{test_user_id}/conversations/start", json=conversation_data)
        assert response.status_code == 200
        
        data = response.json()
        assert data["status"] == "success"
        assert "conversation_id" in data
        assert data["user_name"] == "นายทดสอบ ระบบ"
        
        return data["conversation_id"]
    
    def test_add_memory(self, test_user_id):
        """Test adding conversation memory"""
        # First start a conversation
        conversation_data = {"session_id": "memory_test_session"}
        conv_response = client.post(f"/personalization/users/{test_user_id}/conversations/start", json=conversation_data)
        conversation_id = conv_response.json()["conversation_id"]
        
        memory_data = {
            "conversation_id": conversation_id,
            "user_message": "ผมอยากไปเที่ยวเชียงใหม่",
            "bot_response": "เชียงใหม่เป็นจังหวัดที่มีสถานที่ท่องเที่ยวหลากหลาย แนะนำดอยสุเทพและถนนคนเดิน",
            "context": {"weather": "cool", "season": "cool"},
            "importance_score": 0.8
        }
        
        response = client.post(f"/personalization/users/{test_user_id}/memory", json=memory_data)
        assert response.status_code == 200
        
        data = response.json()
        assert data["status"] == "success"
        assert "memory_entry_id" in data
    
    def test_get_personalized_recommendations(self, test_user_id):
        """Test getting personalized recommendations"""
        recommendation_data = {
            "query": "อยากไปเที่ยววัด",
            "context": {"season": "cool", "weather": "sunny"},
            "limit": 5
        }
        
        response = client.post(f"/personalization/users/{test_user_id}/recommendations", json=recommendation_data)
        assert response.status_code == 200
        
        data = response.json()
        assert data["status"] == "success"
        assert "recommendations" in data
        assert len(data["recommendations"]) <= 5
        assert "personalization_context" in data
        
        # Check if recommendations include temples (matching user's query)
        temple_found = any("วัด" in rec["place_name"] or rec["type"] == "temple" 
                          for rec in data["recommendations"])
        assert temple_found, "Should recommend temples based on query"
    
    def test_record_feedback(self, test_user_id):
        """Test recording user feedback"""
        feedback_data = {
            "recommendation": "วัดพระแก้ว",
            "feedback": "like",
            "satisfaction_score": 0.9
        }
        
        response = client.post(f"/personalization/users/{test_user_id}/feedback", json=feedback_data)
        assert response.status_code == 200
        
        data = response.json() 
        assert data["status"] == "success"
    
    def test_get_user_summary(self, test_user_id):
        """Test getting user summary"""
        response = client.get(f"/personalization/users/{test_user_id}/summary")
        assert response.status_code == 200
        
        data = response.json()
        assert data["status"] == "success"
        summary = data["summary"]
        
        assert summary["user_id"] == test_user_id
        assert summary["name"] == "นายทดสอบ ระบบ"
        assert summary["favorite_places"] == ["วัดพระแก้ว", "ชายหาดป่าตอง"]
        assert summary["budget_range"] == "mid"
        assert summary["personalization_score"] > 0
    
    def test_get_configuration_options(self):
        """Test getting configuration options"""
        response = client.get("/personalization/config/options")
        assert response.status_code == 200
        
        data = response.json()
        assert "seasons" in data
        assert "budget_ranges" in data
        assert "place_types" in data
        assert "travel_styles" in data
        
        # Check if Thai seasons are included
        assert "hot" in data["seasons"]
        assert "rainy" in data["seasons"]
        assert "cool" in data["seasons"]
    
    def test_personalized_chat_integration(self, test_user_id):
        """Test personalized chat integration"""
        chat_data = {
            "message": "แนะนำที่เที่ยววัดให้หน่อย",
            "session_id": "chat_test_session"
        }
        
        # Note: This endpoint needs user_id as query parameter
        response = client.post(f"/ai/personalized/chat?user_id={test_user_id}", 
                              json=chat_data)
        assert response.status_code == 200
        
        data = response.json()
        assert data["status"] == "success"
        assert "response" in data
        assert data["personalization_applied"] == True
        assert "personalization_context" in data
        
        # Check if response is personalized (should mention user's name)
        assert "ทดสอบ" in data["response"] or "นายทดสอบ" in data["response"]


class TestUserProfileManager:
    """Test UserProfileManager directly"""
    
    def test_direct_profile_creation(self):
        """Test creating profile directly through manager"""
        test_id = "direct_test_user"
        
        profile = user_profile_manager.create_user_profile(
            user_id=test_id,
            name="Direct Test User",
            nickname="DirectTest",
            location="Test Location",
            budget_range="luxury"
        )
        
        assert profile.user_id == test_id
        assert profile.personal_info.name == "Direct Test User"
        assert profile.travel_preferences.budget_range == BudgetRange.LUXURY
    
    def test_travel_preference_updates(self):
        """Test updating travel preferences directly"""
        test_id = "direct_test_user"
        
        success = user_profile_manager.update_travel_preferences(
            test_id,
            favorite_places=["Bangkok", "Phuket"],
            favorite_seasons=["cool", "hot"],
            place_types=["city", "beach"]
        )
        
        assert success == True
        
        profile = user_profile_manager.get_user_profile(test_id)
        assert "Bangkok" in profile.travel_preferences.favorite_places
        assert Season.COOL in profile.travel_preferences.favorite_seasons
        assert PlaceType.CITY in profile.travel_preferences.place_types
    
    def test_memory_management(self):
        """Test memory management functionality"""
        test_id = "direct_test_user"
        conversation_id = "test_conversation_001"
        
        # Add memory
        entry_id = user_profile_manager.add_memory(
            user_id=test_id,
            conversation_id=conversation_id,
            user_message="I want to visit temples in Bangkok",
            bot_response="I recommend Wat Phra Kaew and Wat Arun",
            context={"topic": "temples", "location": "bangkok"}
        )
        
        assert entry_id is not None
        
        # Get relevant memories
        memories = user_profile_manager.get_relevant_memories(test_id, "temple", limit=5)
        assert len(memories) > 0
        assert any("temple" in mem.user_message.lower() for mem in memories)


class TestChatMemorySystem:
    """Test enhanced chat memory system"""
    
    def test_conversation_management(self):
        """Test conversation start and memory addition"""
        test_user = "memory_test_user"
        test_session = "memory_test_session"
        
        # Start conversation
        conversation_id = enhanced_chat_memory.start_conversation(test_user, test_session)
        assert conversation_id is not None
        assert test_user in conversation_id
        
        # Add memory
        entry_id = enhanced_chat_memory.add_interaction(
            conversation_id=conversation_id,
            human_message="ผมชอบเที่ยวธรรมชาติ",
            ai_message="แนะนำดอยอินทนนท์และเขาใหญ่สำหรับคุณ",
            importance_score=0.7,
            emotion_tone="positive"
        )
        
        assert entry_id is not None
    
    def test_memory_retrieval(self):
        """Test memory search and retrieval"""
        test_user = "memory_test_user"
        
        # Search memories
        memories = enhanced_chat_memory.memory_store.search_memories(
            test_user, "ธรรมชาติ", limit=5
        )
        
        # Should find the memory we added
        assert len(memories) > 0
        nature_memory_found = any("ธรรมชาติ" in mem.human_message for mem in memories)
        assert nature_memory_found
    
    def test_user_memory_context(self):
        """Test getting user memory context"""
        test_user = "memory_test_user"
        
        context = enhanced_chat_memory.get_user_memory_context(
            test_user, "เที่ยวภูเขา", limit=3
        )
        
        assert "relevant_memories" in context
        assert "mentioned_places" in context
        assert "conversation_themes" in context
        assert "memory_strength" in context
        
        # Should have some memory strength > 0
        assert context["memory_strength"] > 0


def test_integration_flow():
    """Test the complete integration flow"""
    user_id = "integration_test_user"
    
    # 1. Create user profile
    profile_data = {
        "name": "Integration Test",
        "language_preference": "th",
        "budget_range": "mid"
    }
    
    response = client.post(f"/personalization/users/{user_id}/profile", json=profile_data)
    assert response.status_code == 200
    
    # 2. Update preferences
    preferences = {
        "favorite_places": ["วัดพระแก้ว"],
        "favorite_seasons": ["cool"],
        "travel_style": ["cultural"]
    }
    
    response = client.put(f"/personalization/users/{user_id}/profile/travel", json=preferences)
    assert response.status_code == 200
    
    # 3. Start conversation and add memory
    conv_response = client.post(f"/personalization/users/{user_id}/conversations/start", 
                               json={"session_id": "integration_session"})
    conversation_id = conv_response.json()["conversation_id"]
    
    memory_data = {
        "conversation_id": conversation_id,
        "user_message": "อยากไปเที่ยววัดที่มีประวัติศาสตร์",
        "bot_response": "แนะนำวัดพระแก้วและวัดอรุณราชวราราม",
        "importance_score": 0.8
    }
    
    response = client.post(f"/personalization/users/{user_id}/memory", json=memory_data)
    assert response.status_code == 200
    
    # 4. Get personalized recommendations
    rec_response = client.post(f"/personalization/users/{user_id}/recommendations", 
                              json={"query": "วัดที่สวย", "limit": 5})
    assert rec_response.status_code == 200
    
    recommendations = rec_response.json()["recommendations"]
    assert len(recommendations) > 0
    
    # Should prioritize temples due to user preferences and memory
    temple_recommendations = [r for r in recommendations if r["type"] == "temple"]
    assert len(temple_recommendations) > 0
    
    # 5. Record positive feedback
    feedback_response = client.post(f"/personalization/users/{user_id}/feedback", 
                                   json={
                                       "recommendation": "วัดพระแก้ว",
                                       "feedback": "like",
                                       "satisfaction_score": 0.9
                                   })
    assert feedback_response.status_code == 200
    
    # 6. Check final user summary
    summary_response = client.get(f"/personalization/users/{user_id}/summary")
    summary = summary_response.json()["summary"]
    
    assert summary["total_conversations"] > 0
    assert summary["acceptance_rate"] > 0  # Should have positive feedback
    assert summary["personalization_score"] > 0.5  # Should be well personalized


if __name__ == "__main__":
    # Run tests manually if needed
    test_flow = test_integration_flow()
    print("Integration test completed successfully!")