"""
Enhanced User Profile Model with Personalization Features
Supports remembering names, places, seasons, budget, and provides personalized recommendations
"""

import json
import time
import hashlib
import sqlite3
from typing import Dict, List, Any, Optional, Tuple, Set
from dataclasses import dataclass, asdict, field
from datetime import datetime, timedelta
from pathlib import Path
from enum import Enum
import logging

logger = logging.getLogger(__name__)

class Season(Enum):
    HOT = "hot"  # มีนาคม - พฤษภาคม
    RAINY = "rainy"  # มิถุนายน - ตุลาคม  
    COOL = "cool"  # พฤศจิกายน - กุมภาพันธ์

class BudgetRange(Enum):
    BUDGET = "budget"  # งบประมาณจำกัด
    MID = "mid"  # งบประมาณปานกลาง
    LUXURY = "luxury"  # งบประมาณไม่จำกัด

class PlaceType(Enum):
    TEMPLE = "temple"  # วัด
    BEACH = "beach"  # ชายหาด
    MOUNTAIN = "mountain"  # ภูเขา
    CITY = "city"  # เมือง
    MARKET = "market"  # ตลาด
    MUSEUM = "museum"  # พิพิธภัณฑ์
    PARK = "park"  # สวนสาธารณะ
    RESTAURANT = "restaurant"  # ร้านอาหาร
    SHOPPING = "shopping"  # ช้อปปิ้ง

@dataclass
class PersonalInfo:
    """Personal information of the user"""
    name: str
    nickname: Optional[str] = None
    age_range: Optional[str] = None  # "18-25", "26-35", "36-45", "46+"
    language_preference: str = "th"  # "th" หรือ "en"
    location: Optional[str] = None  # ที่อยู่ปัจจุบัน
    created_at: str = field(default_factory=lambda: datetime.now().isoformat())
    updated_at: str = field(default_factory=lambda: datetime.now().isoformat())

@dataclass
class TravelPreferences:
    """Travel preferences and favorites"""
    favorite_places: List[str] = field(default_factory=list)  # รายชื่อสถานที่ที่ชอบ
    place_types: List[PlaceType] = field(default_factory=list)  # ประเภทสถานที่ที่ชอบ
    favorite_seasons: List[Season] = field(default_factory=list)  # ฤดูกาลที่ชอบ
    budget_range: BudgetRange = BudgetRange.MID
    travel_style: List[str] = field(default_factory=list)  # ["adventure", "relaxing", "cultural", "family"]
    accommodation_type: List[str] = field(default_factory=list)  # ["hotel", "resort", "hostel", "homestay"]
    transportation: List[str] = field(default_factory=list)  # ["car", "public", "walk", "motorbike"]
    group_preference: str = "solo"  # "solo", "couple", "family", "friends"
    activity_level: str = "medium"  # "low", "medium", "high"

@dataclass
class InteractionHistory:
    """History of user interactions"""
    total_conversations: int = 0
    total_recommendations_accepted: int = 0
    total_recommendations_declined: int = 0
    favorite_topics: List[str] = field(default_factory=list)
    last_interaction: Optional[str] = None
    conversation_themes: Dict[str, int] = field(default_factory=dict)  # theme -> count
    feedback_scores: List[float] = field(default_factory=list)  # list of satisfaction scores
    places_visited: List[str] = field(default_factory=list)  # places user has been to
    places_interested: List[str] = field(default_factory=list)  # places user wants to visit

@dataclass 
class MemoryEntry:
    """Individual memory entry for conversations"""
    entry_id: str
    conversation_id: str
    timestamp: str
    user_message: str
    bot_response: str
    context: Dict[str, Any] = field(default_factory=dict)
    importance_score: float = 0.5  # 0.0 to 1.0
    tags: List[str] = field(default_factory=list)
    referenced_places: List[str] = field(default_factory=list)

@dataclass
class UserProfile:
    """Complete user profile with personalization data"""
    user_id: str
    personal_info: PersonalInfo
    travel_preferences: TravelPreferences
    interaction_history: InteractionHistory
    memory_entries: List[MemoryEntry] = field(default_factory=list)
    profile_version: str = "1.0"
    created_at: str = field(default_factory=lambda: datetime.now().isoformat())
    updated_at: str = field(default_factory=lambda: datetime.now().isoformat())

class UserProfileManager:
    """
    Enhanced User Profile Manager with Personalization
    จัดการข้อมูลส่วนตัวและความชอบของผู้ใช้
    """
    
    def __init__(self, storage_dir: Optional[Path] = None):
        self.storage_dir = storage_dir or Path(__file__).parent.parent / "cache" / "user_profiles"
        self.storage_dir.mkdir(parents=True, exist_ok=True)
        
        # SQLite database for persistent storage
        self.db_path = self.storage_dir / "user_profiles.db"
        self._init_database()
        
        # In-memory cache for active users
        self.active_profiles: Dict[str, UserProfile] = {}
        
        # Memory settings
        self.memory_retention_days = 90  # Keep memories for 90 days
        self.max_memories_per_user = 1000  # Max memories per user
        
        # Load recently active profiles
        self._load_recent_profiles()
        
        # Thai places database (sample data)
        self.thai_places_db = self._init_thai_places_db()
        
    def _init_database(self):
        """Initialize SQLite database for user profiles"""
        try:
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            
            # User profiles table
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS user_profiles (
                    user_id TEXT PRIMARY KEY,
                    profile_data TEXT NOT NULL,
                    created_at TEXT NOT NULL,
                    updated_at TEXT NOT NULL,
                    last_accessed TEXT NOT NULL
                )
            ''')
            
            # Memory entries table
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS memory_entries (
                    entry_id TEXT PRIMARY KEY,
                    user_id TEXT NOT NULL,
                    conversation_id TEXT NOT NULL,
                    timestamp TEXT NOT NULL,
                    user_message TEXT NOT NULL,
                    bot_response TEXT NOT NULL,
                    context TEXT,
                    importance_score REAL,
                    tags TEXT,
                    referenced_places TEXT,
                    FOREIGN KEY (user_id) REFERENCES user_profiles (user_id)
                )
            ''')
            
            # Conversation sessions table
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS conversation_sessions (
                    session_id TEXT PRIMARY KEY,
                    user_id TEXT NOT NULL,
                    started_at TEXT NOT NULL,
                    ended_at TEXT,
                    message_count INTEGER DEFAULT 0,
                    session_theme TEXT,
                    FOREIGN KEY (user_id) REFERENCES user_profiles (user_id)
                )
            ''')
            
            conn.commit()
            conn.close()
            
        except Exception as e:
            logger.error(f"Error initializing database: {e}")
    
    def _init_thai_places_db(self) -> Dict[str, Dict[str, Any]]:
        """Initialize Thai places database for recommendations"""
        return {
            # กรุงเทพมหานคร
            "วัดพระแก้ว": {
                "name_en": "Temple of the Emerald Buddha",
                "type": PlaceType.TEMPLE,
                "province": "กรุงเทพมหานคร",
                "best_seasons": [Season.COOL, Season.HOT],
                "budget": BudgetRange.BUDGET,
                "keywords": ["temple", "bangkok", "emerald", "buddha", "พระแก้ว"]
            },
            "วัดอรุณราชวราราม": {
                "name_en": "Wat Arun",  
                "type": PlaceType.TEMPLE,
                "province": "กรุงเทพมหานคร",
                "best_seasons": [Season.COOL, Season.HOT],
                "budget": BudgetRange.BUDGET,
                "keywords": ["temple", "bangkok", "dawn", "arun", "อรุณ"]
            },
            "ตลาดนัดเจเจ": {
                "name_en": "Chatuchak Weekend Market",
                "type": PlaceType.MARKET,
                "province": "กรุงเทพมหานคร", 
                "best_seasons": [Season.COOL],
                "budget": BudgetRange.MID,
                "keywords": ["market", "shopping", "weekend", "chatuchak", "เจเจ"]
            },
            
            # เชียงใหม่
            "ดอยสุเทพ": {
                "name_en": "Doi Suthep",
                "type": PlaceType.MOUNTAIN,
                "province": "เชียงใหม่",
                "best_seasons": [Season.COOL, Season.HOT],
                "budget": BudgetRange.BUDGET,
                "keywords": ["mountain", "chiang mai", "temple", "view", "สุเทพ"]
            },
            "ถนนคนเดิน": {
                "name_en": "Chiang Mai Walking Street",
                "type": PlaceType.MARKET,
                "province": "เชียงใหม่",
                "best_seasons": [Season.COOL],
                "budget": BudgetRange.MID,
                "keywords": ["walking street", "market", "chiang mai", "night", "คนเดิน"]
            },
            
            # ภูเก็ต
            "หาดป่าตอง": {
                "name_en": "Patong Beach",
                "type": PlaceType.BEACH,
                "province": "ภูเก็ต",
                "best_seasons": [Season.COOL, Season.HOT],
                "budget": BudgetRange.MID,
                "keywords": ["beach", "phuket", "patong", "swimming", "ป่าตอง"]
            },
            "อ่าวพังงา": {
                "name_en": "Phang Nga Bay",
                "type": PlaceType.BEACH,
                "province": "ภูเก็ต",
                "best_seasons": [Season.COOL, Season.HOT], 
                "budget": BudgetRange.MID,
                "keywords": ["bay", "boat", "islands", "phang nga", "พังงา"]
            }
        }
    
    def create_user_profile(self, user_id: str, name: str, **kwargs) -> UserProfile:
        """Create a new user profile"""
        personal_info = PersonalInfo(
            name=name,
            nickname=kwargs.get('nickname'),
            age_range=kwargs.get('age_range'),
            language_preference=kwargs.get('language_preference', 'th'),
            location=kwargs.get('location')
        )
        
        travel_preferences = TravelPreferences(
            budget_range=BudgetRange(kwargs.get('budget_range', 'mid'))
        )
        
        interaction_history = InteractionHistory()
        
        profile = UserProfile(
            user_id=user_id,
            personal_info=personal_info,
            travel_preferences=travel_preferences,
            interaction_history=interaction_history
        )
        
        self.active_profiles[user_id] = profile
        self._save_profile(profile)
        
        return profile
    
    def get_user_profile(self, user_id: str) -> Optional[UserProfile]:
        """Get user profile by ID"""
        # Check active cache first
        if user_id in self.active_profiles:
            profile = self.active_profiles[user_id]
            profile.updated_at = datetime.now().isoformat()
            return profile
        
        # Load from database
        profile = self._load_profile(user_id)
        if profile:
            self.active_profiles[user_id] = profile
            
        return profile
    
    def update_personal_info(self, user_id: str, **updates) -> bool:
        """Update personal information"""
        profile = self.get_user_profile(user_id)
        if not profile:
            return False
            
        for key, value in updates.items():
            if hasattr(profile.personal_info, key):
                setattr(profile.personal_info, key, value)
        
        profile.personal_info.updated_at = datetime.now().isoformat()
        profile.updated_at = datetime.now().isoformat()
        
        self._save_profile(profile)
        return True
    
    def update_travel_preferences(self, user_id: str, **preferences) -> bool:
        """Update travel preferences"""
        profile = self.get_user_profile(user_id)
        if not profile:
            return False
            
        prefs = profile.travel_preferences
        
        # Update favorite places
        if 'favorite_places' in preferences:
            places = preferences['favorite_places']
            if isinstance(places, str):
                places = [places]
            prefs.favorite_places.extend(places)
            prefs.favorite_places = list(set(prefs.favorite_places))  # Remove duplicates
        
        # Update place types
        if 'place_types' in preferences:
            place_types = preferences['place_types']
            if isinstance(place_types, str):
                place_types = [place_types]
            for place_type in place_types:
                if isinstance(place_type, str):
                    try:
                        place_type = PlaceType(place_type)
                    except ValueError:
                        continue
                if place_type not in prefs.place_types:
                    prefs.place_types.append(place_type)
        
        # Update favorite seasons
        if 'favorite_seasons' in preferences:
            seasons = preferences['favorite_seasons']
            if isinstance(seasons, str):
                seasons = [seasons]
            for season in seasons:
                if isinstance(season, str):
                    try:
                        season = Season(season)
                    except ValueError:
                        continue
                if season not in prefs.favorite_seasons:
                    prefs.favorite_seasons.append(season)
        
        # Update budget range
        if 'budget_range' in preferences:
            budget = preferences['budget_range']
            if isinstance(budget, str):
                try:
                    prefs.budget_range = BudgetRange(budget)
                except ValueError:
                    pass
        
        # Update other preferences
        for key in ['travel_style', 'accommodation_type', 'transportation']:
            if key in preferences:
                values = preferences[key]
                if isinstance(values, str):
                    values = [values]
                current_list = getattr(prefs, key, [])
                current_list.extend(values)
                setattr(prefs, key, list(set(current_list)))
        
        # Update simple fields
        for key in ['group_preference', 'activity_level']:
            if key in preferences:
                setattr(prefs, key, preferences[key])
        
        profile.updated_at = datetime.now().isoformat()
        self._save_profile(profile)
        return True
    
    def add_memory(self, user_id: str, conversation_id: str, user_message: str, 
                   bot_response: str, context: Dict[str, Any] = None,
                   importance_score: float = 0.5, tags: List[str] = None) -> str:
        """Add a memory entry for the user"""
        profile = self.get_user_profile(user_id)
        if not profile:
            return None
            
        # Extract places from the conversation
        referenced_places = self._extract_places_from_text(user_message + " " + bot_response)
        
        entry_id = f"{user_id}_{conversation_id}_{int(time.time())}"
        memory = MemoryEntry(
            entry_id=entry_id,
            conversation_id=conversation_id,
            timestamp=datetime.now().isoformat(),
            user_message=user_message,
            bot_response=bot_response,
            context=context or {},
            importance_score=importance_score,
            tags=tags or [],
            referenced_places=referenced_places
        )
        
        profile.memory_entries.append(memory)
        
        # Maintain memory limit
        if len(profile.memory_entries) > self.max_memories_per_user:
            # Remove oldest memories with low importance
            profile.memory_entries.sort(key=lambda x: (x.importance_score, x.timestamp))
            profile.memory_entries = profile.memory_entries[-self.max_memories_per_user:]
        
        # Update interaction history
        profile.interaction_history.total_conversations += 1
        profile.interaction_history.last_interaction = datetime.now().isoformat()
        
        # Extract and update conversation themes
        themes = self._extract_themes_from_conversation(user_message, bot_response)
        for theme in themes:
            current_count = profile.interaction_history.conversation_themes.get(theme, 0)
            profile.interaction_history.conversation_themes[theme] = current_count + 1
        
        profile.updated_at = datetime.now().isoformat()
        self._save_profile(profile)
        self._save_memory_to_db(memory)
        
        return entry_id
    
    def get_relevant_memories(self, user_id: str, query: str, limit: int = 5) -> List[MemoryEntry]:
        """Get relevant memories for a query"""
        profile = self.get_user_profile(user_id)
        if not profile:
            return []
        
        query_lower = query.lower()
        scored_memories = []
        
        for memory in profile.memory_entries:
            score = 0.0
            
            # Text similarity (simple keyword matching)
            memory_text = (memory.user_message + " " + memory.bot_response).lower()
            query_words = query_lower.split()
            matching_words = sum(1 for word in query_words if word in memory_text)
            score += (matching_words / len(query_words)) * 0.4
            
            # Importance score
            score += memory.importance_score * 0.3
            
            # Recency (more recent = higher score)
            memory_time = datetime.fromisoformat(memory.timestamp)
            age_days = (datetime.now() - memory_time).days
            recency_score = max(0, 1 - (age_days / 30))  # Linear decay over 30 days
            score += recency_score * 0.2
            
            # Tags matching
            if memory.tags:
                tag_text = " ".join(memory.tags).lower()
                tag_matches = sum(1 for word in query_words if word in tag_text)
                if tag_matches > 0:
                    score += (tag_matches / len(query_words)) * 0.1
            
            if score > 0:
                scored_memories.append((score, memory))
        
        # Sort by score and return top results
        scored_memories.sort(key=lambda x: x[0], reverse=True)
        return [memory for score, memory in scored_memories[:limit]]
    
    def get_personalized_recommendations(self, user_id: str, query: str = "", 
                                       context: Dict[str, Any] = None) -> List[Dict[str, Any]]:
        """Get personalized travel recommendations"""
        profile = self.get_user_profile(user_id)
        if not profile:
            return self._get_default_recommendations()
        
        recommendations = []
        context = context or {}
        current_season = self._get_current_season()
        
        # Score places based on user preferences
        for place_name, place_info in self.thai_places_db.items():
            score = 0.0
            reasons = []
            
            # Budget matching
            if place_info['budget'] == profile.travel_preferences.budget_range:
                score += 0.3
                reasons.append(f"เหมาะสมกับงบประมาณ{place_info['budget'].value}")
            
            # Season matching
            if current_season in place_info['best_seasons']:
                score += 0.25
                reasons.append(f"เหมาะสมกับฤดูกาล{current_season.value}")
            
            # Favorite seasons
            for fav_season in profile.travel_preferences.favorite_seasons:
                if fav_season in place_info['best_seasons']:
                    score += 0.2
                    reasons.append(f"ตรงกับฤดูกาลที่ชอบ ({fav_season.value})")
                    break
            
            # Place type preferences
            if place_info['type'] in profile.travel_preferences.place_types:
                score += 0.3
                reasons.append(f"ตรงกับประเภทสถานที่ที่ชอบ ({place_info['type'].value})")
            
            # Favorite places (direct match or similar)
            for fav_place in profile.travel_preferences.favorite_places:
                if fav_place.lower() in place_name.lower() or place_name.lower() in fav_place.lower():
                    score += 0.4
                    reasons.append("ตรงกับสถานที่ที่เคยสนใจ")
                    break
            
            # Keyword matching from query
            if query:
                query_lower = query.lower()
                for keyword in place_info['keywords']:
                    if keyword in query_lower:
                        score += 0.2
                        reasons.append("ตรงกับสิ่งที่กำลังหา")
                        break
            
            # Memory-based recommendations
            relevant_memories = self.get_relevant_memories(user_id, place_name + " " + place_info['name_en'], limit=2)
            if relevant_memories:
                score += 0.15 * len(relevant_memories)
                reasons.append("เกี่ยวข้องกับการสนทนาที่ผ่านมา")
            
            # Interaction history
            if place_name in profile.interaction_history.places_interested:
                score += 0.25
                reasons.append("เคยแสดงความสนใจแล้ว")
            
            if score > 0:
                recommendations.append({
                    'place_name': place_name,
                    'place_name_en': place_info['name_en'],
                    'type': place_info['type'].value,
                    'province': place_info['province'],
                    'score': score,
                    'reasons': reasons,
                    'budget': place_info['budget'].value,
                    'best_seasons': [s.value for s in place_info['best_seasons']],
                    'personalization_level': 'high' if score > 0.5 else 'medium' if score > 0.2 else 'low'
                })
        
        # Sort by score
        recommendations.sort(key=lambda x: x['score'], reverse=True)
        
        return recommendations[:10]  # Return top 10
    
    def record_feedback(self, user_id: str, recommendation: str, feedback: str, 
                       satisfaction_score: float = None):
        """Record user feedback on recommendations"""
        profile = self.get_user_profile(user_id)
        if not profile:
            return
        
        # Update recommendation statistics
        if feedback.lower() in ['yes', 'accept', 'like', 'good']:
            profile.interaction_history.total_recommendations_accepted += 1
            # Add to places interested
            if recommendation not in profile.interaction_history.places_interested:
                profile.interaction_history.places_interested.append(recommendation)
        elif feedback.lower() in ['no', 'decline', 'dislike', 'bad']:
            profile.interaction_history.total_recommendations_declined += 1
        
        # Record satisfaction score
        if satisfaction_score is not None:
            profile.interaction_history.feedback_scores.append(satisfaction_score)
            # Keep only recent 50 scores
            if len(profile.interaction_history.feedback_scores) > 50:
                profile.interaction_history.feedback_scores = profile.interaction_history.feedback_scores[-50:]
        
        profile.updated_at = datetime.now().isoformat()
        self._save_profile(profile)
    
    def get_user_summary(self, user_id: str) -> Dict[str, Any]:
        """Get a summary of user's profile and preferences"""
        profile = self.get_user_profile(user_id)
        if not profile:
            return {"error": "User not found"}
        
        # Calculate satisfaction rate
        satisfaction_rate = 0.0
        if profile.interaction_history.feedback_scores:
            satisfaction_rate = sum(profile.interaction_history.feedback_scores) / len(profile.interaction_history.feedback_scores)
        
        # Calculate acceptance rate
        total_recs = profile.interaction_history.total_recommendations_accepted + profile.interaction_history.total_recommendations_declined
        acceptance_rate = 0.0
        if total_recs > 0:
            acceptance_rate = profile.interaction_history.total_recommendations_accepted / total_recs
        
        return {
            'user_id': user_id,
            'name': profile.personal_info.name,
            'nickname': profile.personal_info.nickname,
            'language': profile.personal_info.language_preference,
            'location': profile.personal_info.location,
            'favorite_places': profile.travel_preferences.favorite_places,
            'favorite_seasons': [s.value for s in profile.travel_preferences.favorite_seasons],
            'budget_range': profile.travel_preferences.budget_range.value,
            'travel_style': profile.travel_preferences.travel_style,
            'group_preference': profile.travel_preferences.group_preference,
            'total_conversations': profile.interaction_history.total_conversations,
            'total_memories': len(profile.memory_entries),
            'acceptance_rate': acceptance_rate,
            'satisfaction_rate': satisfaction_rate,
            'top_conversation_themes': dict(sorted(profile.interaction_history.conversation_themes.items(), 
                                                 key=lambda x: x[1], reverse=True)[:5]),
            'places_interested': profile.interaction_history.places_interested,
            'profile_age_days': (datetime.now() - datetime.fromisoformat(profile.created_at)).days,
            'last_interaction': profile.interaction_history.last_interaction,
            'personalization_score': self._calculate_personalization_score(profile)
        }
    
    def _calculate_personalization_score(self, profile: UserProfile) -> float:
        """Calculate how well we know this user (0-1)"""
        score = 0.0
        
        # Basic info completeness
        if profile.personal_info.name: score += 0.1
        if profile.personal_info.nickname: score += 0.05
        if profile.personal_info.location: score += 0.1
        
        # Travel preferences completeness
        if profile.travel_preferences.favorite_places: score += 0.2
        if profile.travel_preferences.favorite_seasons: score += 0.15
        if profile.travel_preferences.place_types: score += 0.15
        if profile.travel_preferences.budget_range != BudgetRange.MID: score += 0.1  # Non-default
        
        # Interaction richness
        if profile.interaction_history.total_conversations >= 5: score += 0.1
        if len(profile.memory_entries) >= 10: score += 0.1
        if profile.interaction_history.feedback_scores: score += 0.05
        
        return min(1.0, score)
    
    def _extract_places_from_text(self, text: str) -> List[str]:
        """Extract place names from text"""
        text_lower = text.lower()
        places = []
        
        for place_name in self.thai_places_db.keys():
            if place_name in text or place_name.lower() in text_lower:
                places.append(place_name)
        
        # Also check English names
        for place_name, place_info in self.thai_places_db.items():
            if place_info['name_en'].lower() in text_lower:
                places.append(place_name)
        
        return list(set(places))
    
    def _extract_themes_from_conversation(self, user_message: str, bot_response: str) -> List[str]:
        """Extract conversation themes"""
        text = (user_message + " " + bot_response).lower()
        themes = []
        
        theme_keywords = {
            'travel_planning': ['เที่ยว', 'ท่องเที่ยว', 'เดินทาง', 'travel', 'trip', 'visit'],
            'accommodation': ['โรงแรม', 'ที่พัก', 'resort', 'hotel', 'stay', 'accommodation'],
            'food': ['อาหาร', 'กิน', 'ร้านอาหาร', 'food', 'eat', 'restaurant', 'cuisine'],
            'culture': ['วัด', 'วัฒนธรรม', 'ประเพณี', 'temple', 'culture', 'tradition'],
            'nature': ['ธรรมชาติ', 'ภูเขา', 'ป่า', 'nature', 'mountain', 'forest'],
            'beach': ['ชายหาด', 'ทะเล', 'เกาะ', 'beach', 'sea', 'island'],
            'shopping': ['ช้อปปิ้ง', 'ตลาด', 'ซื้อของ', 'shopping', 'market', 'buy'],
            'budget': ['ราคา', 'งบประมาณ', 'ถูก', 'แพง', 'price', 'budget', 'cost', 'expensive', 'cheap']
        }
        
        for theme, keywords in theme_keywords.items():
            if any(keyword in text for keyword in keywords):
                themes.append(theme)
        
        return themes
    
    def _get_current_season(self) -> Season:
        """Get current Thai season"""
        month = datetime.now().month
        if month in [3, 4, 5]:
            return Season.HOT
        elif month in [6, 7, 8, 9, 10]:
            return Season.RAINY
        else:
            return Season.COOL
    
    def _get_default_recommendations(self) -> List[Dict[str, Any]]:
        """Get default recommendations for new users"""
        current_season = self._get_current_season()
        recommendations = []
        
        for place_name, place_info in list(self.thai_places_db.items())[:5]:
            score = 0.3
            reasons = ["แนะนำสำหรับผู้ใช้ใหม่"]
            
            if current_season in place_info['best_seasons']:
                score += 0.2
                reasons.append(f"เหมาะสมกับฤดูกาล{current_season.value}")
            
            recommendations.append({
                'place_name': place_name,
                'place_name_en': place_info['name_en'],
                'type': place_info['type'].value,
                'province': place_info['province'],
                'score': score,
                'reasons': reasons,
                'budget': place_info['budget'].value,
                'best_seasons': [s.value for s in place_info['best_seasons']],
                'personalization_level': 'default'
            })
        
        return recommendations
    
    def _save_profile(self, profile: UserProfile):
        """Save profile to database"""
        try:
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            
            profile_data = json.dumps(asdict(profile), ensure_ascii=False, default=str)
            
            cursor.execute('''
                INSERT OR REPLACE INTO user_profiles 
                (user_id, profile_data, created_at, updated_at, last_accessed)
                VALUES (?, ?, ?, ?, ?)
            ''', (
                profile.user_id,
                profile_data,
                profile.created_at,
                profile.updated_at,
                datetime.now().isoformat()
            ))
            
            conn.commit()
            conn.close()
            
        except Exception as e:
            logger.error(f"Error saving profile: {e}")
    
    def _load_profile(self, user_id: str) -> Optional[UserProfile]:
        """Load profile from database"""
        try:
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            
            cursor.execute('''
                SELECT profile_data FROM user_profiles WHERE user_id = ?
            ''', (user_id,))
            
            row = cursor.fetchone()
            conn.close()
            
            if row:
                profile_data = json.loads(row[0])
                # Reconstruct objects from dict
                profile_data['personal_info'] = PersonalInfo(**profile_data['personal_info'])
                
                # Reconstruct travel preferences
                travel_prefs = profile_data['travel_preferences']
                
                # Handle enum conversion for place_types
                place_types = []
                for pt in travel_prefs.get('place_types', []):
                    if isinstance(pt, str):
                        try:
                            place_types.append(PlaceType(pt))
                        except ValueError:
                            # Skip invalid place types
                            continue
                    else:
                        place_types.append(pt)
                travel_prefs['place_types'] = place_types
                
                # Handle enum conversion for favorite_seasons
                favorite_seasons = []
                for s in travel_prefs.get('favorite_seasons', []):
                    if isinstance(s, str):
                        try:
                            favorite_seasons.append(Season(s))
                        except ValueError:
                            # Skip invalid seasons
                            continue
                    else:
                        favorite_seasons.append(s)
                travel_prefs['favorite_seasons'] = favorite_seasons
                
                # Handle enum conversion for budget_range
                budget_range = travel_prefs.get('budget_range', 'mid')
                if isinstance(budget_range, str):
                    try:
                        travel_prefs['budget_range'] = BudgetRange(budget_range)
                    except ValueError:
                        travel_prefs['budget_range'] = BudgetRange.MID
                else:
                    travel_prefs['budget_range'] = budget_range
                profile_data['travel_preferences'] = TravelPreferences(**travel_prefs)
                
                profile_data['interaction_history'] = InteractionHistory(**profile_data['interaction_history'])
                
                # Reconstruct memory entries
                memory_entries = []
                for mem_data in profile_data.get('memory_entries', []):
                    memory_entries.append(MemoryEntry(**mem_data))
                profile_data['memory_entries'] = memory_entries
                
                return UserProfile(**profile_data)
            
        except Exception as e:
            logger.error(f"Error loading profile: {e}")
        
        return None
    
    def _save_memory_to_db(self, memory: MemoryEntry):
        """Save memory entry to database"""
        try:
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            
            cursor.execute('''
                INSERT OR REPLACE INTO memory_entries
                (entry_id, user_id, conversation_id, timestamp, user_message, bot_response,
                 context, importance_score, tags, referenced_places)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            ''', (
                memory.entry_id,
                memory.entry_id.split('_')[0],  # Extract user_id
                memory.conversation_id,
                memory.timestamp,
                memory.user_message,
                memory.bot_response,
                json.dumps(memory.context, ensure_ascii=False),
                memory.importance_score,
                json.dumps(memory.tags, ensure_ascii=False),
                json.dumps(memory.referenced_places, ensure_ascii=False)
            ))
            
            conn.commit()
            conn.close()
            
        except Exception as e:
            logger.error(f"Error saving memory: {e}")
    
    def _load_recent_profiles(self):
        """Load recently accessed profiles into memory"""
        try:
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            
            # Load profiles accessed in the last 7 days
            week_ago = (datetime.now() - timedelta(days=7)).isoformat()
            cursor.execute('''
                SELECT user_id FROM user_profiles 
                WHERE last_accessed >= ? 
                ORDER BY last_accessed DESC
                LIMIT 50
            ''', (week_ago,))
            
            user_ids = [row[0] for row in cursor.fetchall()]
            conn.close()
            
            # Load these profiles into memory
            for user_id in user_ids:
                profile = self._load_profile(user_id)
                if profile:
                    self.active_profiles[user_id] = profile
                    
        except Exception as e:
            logger.error(f"Error loading recent profiles: {e}")


# Global instance
user_profile_manager = UserProfileManager()