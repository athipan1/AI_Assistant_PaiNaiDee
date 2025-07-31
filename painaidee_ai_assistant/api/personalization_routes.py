"""
Enhanced Personalization API Routes
API endpoints for user profile management and personalized recommendations
"""

from fastapi import APIRouter, HTTPException, Query, Body
from pydantic import BaseModel, Field
from typing import Dict, List, Any, Optional
import logging
from datetime import datetime

# Import our personalization models
from models.user_profile import (
    user_profile_manager, UserProfile, PersonalInfo, TravelPreferences, 
    Season, BudgetRange, PlaceType
)
from models.chat_memory import enhanced_chat_memory

logger = logging.getLogger(__name__)

# Pydantic models for API requests/responses
class CreateUserProfileRequest(BaseModel):
    name: str = Field(..., description="ชื่อผู้ใช้")
    nickname: Optional[str] = Field(None, description="ชื่อเล่น")
    age_range: Optional[str] = Field(None, description="ช่วงอายุ", example="26-35")
    language_preference: str = Field("th", description="ภาษาที่ต้องการ")
    location: Optional[str] = Field(None, description="ที่อยู่ปัจจุบัน")
    budget_range: str = Field("mid", description="ช่วงงบประมาณ", example="budget|mid|luxury")

class UpdatePersonalInfoRequest(BaseModel):
    name: Optional[str] = None
    nickname: Optional[str] = None
    age_range: Optional[str] = None
    language_preference: Optional[str] = None
    location: Optional[str] = None

class UpdateTravelPreferencesRequest(BaseModel):
    favorite_places: Optional[List[str]] = Field(None, description="สถานที่ที่ชอบ")
    place_types: Optional[List[str]] = Field(None, description="ประเภทสถานที่ที่ชอบ")
    favorite_seasons: Optional[List[str]] = Field(None, description="ฤดูกาลที่ชอบ")
    budget_range: Optional[str] = Field(None, description="ช่วงงบประมาณ")
    travel_style: Optional[List[str]] = Field(None, description="รูปแบบการเดินทาง")
    accommodation_type: Optional[List[str]] = Field(None, description="ประเภทที่พัก")
    transportation: Optional[List[str]] = Field(None, description="การเดินทาง")
    group_preference: Optional[str] = Field(None, description="การเดินทางแบบกลุ่ม")
    activity_level: Optional[str] = Field(None, description="ระดับกิจกรรม")

class AddMemoryRequest(BaseModel):
    conversation_id: str = Field(..., description="ID การสนทนา")
    user_message: str = Field(..., description="ข้อความจากผู้ใช้")
    bot_response: str = Field(..., description="คำตอบจากบอท")
    context: Optional[Dict[str, Any]] = Field(None, description="บริบทการสนทนา")
    importance_score: float = Field(0.5, description="คะแนนความสำคัญ", ge=0.0, le=1.0)
    emotion_tone: Optional[str] = Field(None, description="โทนอารมณ์")

class GetRecommendationsRequest(BaseModel):
    query: Optional[str] = Field("", description="คำค้นหา")
    context: Optional[Dict[str, Any]] = Field(None, description="บริบทปัจจุบัน")
    limit: int = Field(10, description="จำนวนคำแนะนำ", ge=1, le=20)

class RecordFeedbackRequest(BaseModel):
    recommendation: str = Field(..., description="คำแนะนำที่ให้ feedback")
    feedback: str = Field(..., description="ความคิดเห็น")
    satisfaction_score: Optional[float] = Field(None, description="คะแนนความพึงพอใจ", ge=0.0, le=1.0)

class StartConversationRequest(BaseModel):
    session_id: str = Field(..., description="ID เซสชั่น")

class UserProfileResponse(BaseModel):
    user_id: str
    name: str
    nickname: Optional[str]
    language: str
    location: Optional[str]
    favorite_places: List[str]
    favorite_seasons: List[str]
    budget_range: str
    travel_style: List[str]
    group_preference: str
    total_conversations: int
    total_memories: int
    acceptance_rate: float
    satisfaction_rate: float
    personalization_score: float

def create_personalization_routes() -> APIRouter:
    """Create personalization API routes"""
    router = APIRouter(prefix="/personalization", tags=["Personalization"])
    
    @router.post("/users/{user_id}/profile")
    async def create_user_profile(user_id: str, request: CreateUserProfileRequest):
        """สร้างโปรไฟล์ผู้ใช้ใหม่ - Create new user profile"""
        try:
            # Check if user already exists
            existing_profile = user_profile_manager.get_user_profile(user_id)
            if existing_profile:
                raise HTTPException(status_code=400, detail="User profile already exists")
            
            # Create new profile
            profile = user_profile_manager.create_user_profile(
                user_id=user_id,
                name=request.name,
                nickname=request.nickname,
                age_range=request.age_range,
                language_preference=request.language_preference,
                location=request.location,
                budget_range=request.budget_range
            )
            
            return {
                "status": "success",
                "message": "สร้างโปรไฟล์ผู้ใช้สำเร็จ",
                "user_id": user_id,
                "profile": {
                    "name": profile.personal_info.name,
                    "nickname": profile.personal_info.nickname,
                    "language": profile.personal_info.language_preference,
                    "budget_range": profile.travel_preferences.budget_range.value,
                    "created_at": profile.created_at
                }
            }
            
        except Exception as e:
            logger.error(f"Error creating user profile: {e}")
            raise HTTPException(status_code=500, detail=str(e))
    
    @router.get("/users/{user_id}/profile")
    async def get_user_profile(user_id: str) -> UserProfileResponse:
        """ดูโปรไฟล์ผู้ใช้ - Get user profile"""
        try:
            profile = user_profile_manager.get_user_profile(user_id)
            if not profile:
                raise HTTPException(status_code=404, detail="User profile not found")
            
            summary = user_profile_manager.get_user_summary(user_id)
            
            return UserProfileResponse(
                user_id=user_id,
                name=summary['name'],
                nickname=summary['nickname'],
                language=summary['language'],
                location=summary['location'],
                favorite_places=summary['favorite_places'],
                favorite_seasons=summary['favorite_seasons'],
                budget_range=summary['budget_range'],
                travel_style=summary['travel_style'],
                group_preference=summary['group_preference'],
                total_conversations=summary['total_conversations'],
                total_memories=summary['total_memories'],
                acceptance_rate=summary['acceptance_rate'],
                satisfaction_rate=summary['satisfaction_rate'],
                personalization_score=summary['personalization_score']
            )
            
        except HTTPException:
            raise
        except Exception as e:
            logger.error(f"Error getting user profile: {e}")
            raise HTTPException(status_code=500, detail=str(e))
    
    @router.put("/users/{user_id}/profile/personal")
    async def update_personal_info(user_id: str, request: UpdatePersonalInfoRequest):
        """อัปเดตข้อมูลส่วนตัว - Update personal information"""
        try:
            # Convert request to dict, excluding None values
            updates = {k: v for k, v in request.dict().items() if v is not None}
            
            if not updates:
                raise HTTPException(status_code=400, detail="No updates provided")
            
            success = user_profile_manager.update_personal_info(user_id, **updates)
            if not success:
                raise HTTPException(status_code=404, detail="User profile not found")
            
            return {
                "status": "success",
                "message": "อัปเดตข้อมูลส่วนตัวสำเร็จ",
                "updated_fields": list(updates.keys())
            }
            
        except HTTPException:
            raise
        except Exception as e:
            logger.error(f"Error updating personal info: {e}")
            raise HTTPException(status_code=500, detail=str(e))
    
    @router.put("/users/{user_id}/profile/travel")
    async def update_travel_preferences(user_id: str, request: UpdateTravelPreferencesRequest):
        """อัปเดตความชอบการเดินทาง - Update travel preferences"""
        try:
            # Convert request to dict, excluding None values
            preferences = {k: v for k, v in request.dict().items() if v is not None}
            
            if not preferences:
                raise HTTPException(status_code=400, detail="No preferences provided")
            
            success = user_profile_manager.update_travel_preferences(user_id, **preferences)
            if not success:
                raise HTTPException(status_code=404, detail="User profile not found")
            
            return {
                "status": "success",
                "message": "อัปเดตความชอบการเดินทางสำเร็จ",
                "updated_preferences": list(preferences.keys())
            }
            
        except HTTPException:
            raise
        except Exception as e:
            logger.error(f"Error updating travel preferences: {e}")
            raise HTTPException(status_code=500, detail=str(e))
    
    @router.post("/users/{user_id}/conversations/start")
    async def start_conversation(user_id: str, request: StartConversationRequest):
        """เริ่มการสนทนาใหม่ - Start new conversation"""
        try:
            # Check if user exists
            profile = user_profile_manager.get_user_profile(user_id)
            if not profile:
                raise HTTPException(status_code=404, detail="User profile not found")
            
            conversation_id = enhanced_chat_memory.start_conversation(user_id, request.session_id)
            
            return {
                "status": "success",
                "message": "เริ่มการสนทนาใหม่สำเร็จ",
                "conversation_id": conversation_id,
                "user_name": profile.personal_info.name,
                "language": profile.personal_info.language_preference
            }
            
        except HTTPException:
            raise
        except Exception as e:
            logger.error(f"Error starting conversation: {e}")
            raise HTTPException(status_code=500, detail=str(e))
    
    @router.post("/users/{user_id}/memory")
    async def add_memory(user_id: str, request: AddMemoryRequest):
        """เพิ่มความจำการสนทนา - Add conversation memory"""
        try:
            # Add memory to chat system
            entry_id = enhanced_chat_memory.add_interaction(
                conversation_id=request.conversation_id,
                human_message=request.user_message,
                ai_message=request.bot_response,
                context_updates=request.context,
                importance_score=request.importance_score,
                emotion_tone=request.emotion_tone
            )
            
            if not entry_id:
                raise HTTPException(status_code=500, detail="Failed to add memory")
            
            # Also add to user profile system
            profile_entry_id = user_profile_manager.add_memory(
                user_id=user_id,
                conversation_id=request.conversation_id,
                user_message=request.user_message,
                bot_response=request.bot_response,
                context=request.context,
                importance_score=request.importance_score
            )
            
            return {
                "status": "success",
                "message": "เพิ่มความจำสำเร็จ",
                "memory_entry_id": entry_id,
                "profile_entry_id": profile_entry_id
            }
            
        except HTTPException:
            raise
        except Exception as e:
            logger.error(f"Error adding memory: {e}")
            raise HTTPException(status_code=500, detail=str(e))
    
    @router.get("/users/{user_id}/memory")
    async def get_user_memories(user_id: str, query: str = Query("", description="คำค้นหา"), 
                               limit: int = Query(5, description="จำนวนความจำ", ge=1, le=20)):
        """ดูความจำของผู้ใช้ - Get user memories"""
        try:
            if query:
                # Search memories with query
                memory_context = enhanced_chat_memory.get_user_memory_context(user_id, query, limit)
                memories = memory_context['relevant_memories']
            else:
                # Get recent memories
                memory_entries = enhanced_chat_memory.memory_store.get_memories(user_id, limit)
                memories = [
                    {
                        'human_message': mem.human_message,
                        'ai_message': mem.ai_message,
                        'timestamp': mem.timestamp,
                        'importance_score': mem.importance_score,
                        'semantic_tags': mem.semantic_tags
                    }
                    for mem in memory_entries
                ]
                memory_context = {
                    'mentioned_places': [],
                    'mentioned_preferences': {},
                    'conversation_themes': [],
                    'memory_strength': len(memories) / 10.0
                }
            
            return {
                "status": "success",
                "memories": memories,
                "context": memory_context,
                "total_memories": len(memories)
            }
            
        except Exception as e:
            logger.error(f"Error getting user memories: {e}")
            raise HTTPException(status_code=500, detail=str(e))
    
    @router.post("/users/{user_id}/recommendations")
    async def get_personalized_recommendations(user_id: str, request: GetRecommendationsRequest):
        """ขอคำแนะนำแบบส่วนตัว - Get personalized recommendations"""
        try:
            # Get personalized recommendations
            recommendations = user_profile_manager.get_personalized_recommendations(
                user_id=user_id,
                query=request.query,
                context=request.context
            )
            
            # Get memory context for additional personalization
            if request.query:
                memory_context = enhanced_chat_memory.get_user_memory_context(user_id, request.query, 3)
            else:
                memory_context = {'mentioned_places': [], 'mentioned_preferences': {}}
            
            # Get user summary for context
            user_summary = user_profile_manager.get_user_summary(user_id)
            
            return {
                "status": "success",
                "recommendations": recommendations[:request.limit],
                "personalization_context": {
                    "user_name": user_summary.get('name'),
                    "personalization_score": user_summary.get('personalization_score', 0.0),
                    "memory_context": memory_context,
                    "total_conversations": user_summary.get('total_conversations', 0),
                    "favorite_places": user_summary.get('favorite_places', []),
                    "favorite_seasons": user_summary.get('favorite_seasons', []),
                    "budget_range": user_summary.get('budget_range', 'mid')
                },
                "query": request.query,
                "total_recommendations": len(recommendations)
            }
            
        except Exception as e:
            logger.error(f"Error getting recommendations: {e}")
            raise HTTPException(status_code=500, detail=str(e))
    
    @router.post("/users/{user_id}/feedback")
    async def record_feedback(user_id: str, request: RecordFeedbackRequest):
        """บันทึกความคิดเห็น - Record user feedback"""
        try:
            user_profile_manager.record_feedback(
                user_id=user_id,
                recommendation=request.recommendation,
                feedback=request.feedback,
                satisfaction_score=request.satisfaction_score
            )
            
            return {
                "status": "success",
                "message": "บันทึกความคิดเห็นสำเร็จ",
                "feedback": request.feedback,
                "recommendation": request.recommendation
            }
            
        except Exception as e:
            logger.error(f"Error recording feedback: {e}")
            raise HTTPException(status_code=500, detail=str(e))
    
    @router.get("/users/{user_id}/summary")
    async def get_user_summary(user_id: str):
        """ดูสรุปผู้ใช้ - Get user summary"""
        try:
            summary = user_profile_manager.get_user_summary(user_id)
            return {
                "status": "success",
                "summary": summary
            }
            
        except Exception as e:
            logger.error(f"Error getting user summary: {e}")
            raise HTTPException(status_code=500, detail=str(e))
    
    @router.get("/users/{user_id}/conversations/{conversation_id}/memory")
    async def get_conversation_memory(user_id: str, conversation_id: str):
        """ดูความจำการสนทนา - Get conversation memory"""
        try:
            memory = enhanced_chat_memory.get_conversation_memory(conversation_id)
            
            return {
                "status": "success",
                "conversation_memory": memory
            }
            
        except Exception as e:
            logger.error(f"Error getting conversation memory: {e}")
            raise HTTPException(status_code=500, detail=str(e))
    
    @router.get("/config/options")
    async def get_configuration_options():
        """ดูตัวเลือกการตั้งค่า - Get configuration options"""
        return {
            "seasons": [season.value for season in Season],
            "budget_ranges": [budget.value for budget in BudgetRange],
            "place_types": [place.value for place in PlaceType],
            "travel_styles": ["adventure", "relaxing", "cultural", "family", "romantic", "business"],
            "accommodation_types": ["hotel", "resort", "hostel", "homestay", "apartment", "guesthouse"],
            "transportation": ["car", "public", "walk", "motorbike", "taxi", "train", "plane"],
            "group_preferences": ["solo", "couple", "family", "friends", "group"],
            "activity_levels": ["low", "medium", "high"],
            "age_ranges": ["18-25", "26-35", "36-45", "46-55", "56+"],
            "languages": ["th", "en"]
        }
    
    @router.delete("/users/{user_id}/profile")
    async def delete_user_profile(user_id: str):
        """ลบโปรไฟล์ผู้ใช้ - Delete user profile"""
        try:
            # This would implement profile deletion
            # For now, we'll return a placeholder
            raise HTTPException(status_code=501, detail="Profile deletion not implemented yet")
            
        except HTTPException:
            raise
        except Exception as e:
            logger.error(f"Error deleting user profile: {e}")
            raise HTTPException(status_code=500, detail=str(e))
    
    return router


def create_personalization_integration_routes() -> APIRouter:
    """Create integration routes for personalization with existing AI systems"""
    router = APIRouter(prefix="/ai/personalized", tags=["AI Personalization"])
    
    @router.post("/chat")
    async def personalized_chat(
        user_id: str = Query(..., description="User ID"),
        message: str = Body(..., description="User message"),
        conversation_id: Optional[str] = Body(None, description="Conversation ID"),
        session_id: Optional[str] = Body(None, description="Session ID")
    ):
        """AI Chat with personalization - แชทกับ AI พร้อมระบบส่วนตัว"""
        try:
            # Get user profile for personalization
            profile = user_profile_manager.get_user_profile(user_id)
            if not profile:
                raise HTTPException(status_code=404, detail="User profile not found")
            
            # Start conversation if needed
            if not conversation_id:
                if not session_id:
                    session_id = f"session_{int(datetime.now().timestamp())}"
                conversation_id = enhanced_chat_memory.start_conversation(user_id, session_id)
            
            # Get user memory context
            memory_context = enhanced_chat_memory.get_user_memory_context(user_id, message, limit=3)
            
            # Get personalized recommendations context
            recommendations = user_profile_manager.get_personalized_recommendations(user_id, message)
            
            # Build personalized context for AI
            personalized_context = {
                "user_name": profile.personal_info.name,
                "user_language": profile.personal_info.language_preference,
                "favorite_places": profile.travel_preferences.favorite_places,
                "favorite_seasons": [s.value for s in profile.travel_preferences.favorite_seasons],
                "budget_range": profile.travel_preferences.budget_range.value,
                "travel_style": profile.travel_preferences.travel_style,
                "memory_context": memory_context,
                "relevant_recommendations": recommendations[:3],
                "personalization_score": user_profile_manager._calculate_personalization_score(profile)
            }
            
            # This would integrate with the existing AI system
            # For now, we'll create a simple personalized response
            ai_response = _generate_personalized_response(message, personalized_context)
            
            # Save interaction to memory
            enhanced_chat_memory.add_interaction(
                conversation_id=conversation_id,
                human_message=message,
                ai_message=ai_response,
                importance_score=0.7  # Higher importance for direct chat
            )
            
            return {
                "status": "success",
                "response": ai_response,
                "conversation_id": conversation_id,
                "personalization_applied": True,
                "personalization_context": personalized_context,
                "recommendations": recommendations[:3] if recommendations else []
            }
            
        except HTTPException:
            raise
        except Exception as e:
            logger.error(f"Error in personalized chat: {e}")
            raise HTTPException(status_code=500, detail=str(e))
    
    return router

def _generate_personalized_response(message: str, context: Dict[str, Any]) -> str:
    """Generate a personalized response (placeholder implementation)"""
    user_name = context.get('user_name', 'คุณ')
    language = context.get('user_language', 'th')
    
    # Simple personalized response based on context
    if language == 'th':
        greeting = f"สวัสดีค่ะ คุณ{user_name} "
        
        if context.get('favorite_places'):
            places = ", ".join(context['favorite_places'][:2])
            greeting += f"เห็นว่าคุณชอบ {places} "
        
        if context.get('budget_range'):
            budget = context['budget_range']
            if budget == 'budget':
                greeting += "และชอบแบบประหยัด "
            elif budget == 'luxury':
                greeting += "และชอบแบบหรูหรา "
        
        return greeting + "มีอะไรให้ช่วยเหลือเกี่ยวกับการท่องเที่ยวไหมคะ?"
    else:
        greeting = f"Hello {user_name}! "
        
        if context.get('favorite_places'):
            places = ", ".join(context['favorite_places'][:2])
            greeting += f"I see you like {places}. "
        
        return greeting + "How can I help you with travel recommendations today?"