"""
Enhanced Memory System with LangChain Integration
Provides persistent chat memory and context management
"""

import json
import time
import sqlite3
from typing import Dict, List, Any, Optional, Tuple
from datetime import datetime, timedelta
from pathlib import Path
import logging
from dataclasses import dataclass, asdict
from abc import ABC, abstractmethod

# Try to import LangChain memory components
try:
    from langchain.memory import ConversationBufferWindowMemory, ConversationSummaryBufferMemory
    from langchain.memory.chat_message_histories import ChatMessageHistory
    from langchain.schema import BaseMessage, HumanMessage, AIMessage
    LANGCHAIN_AVAILABLE = True
except ImportError:
    LANGCHAIN_AVAILABLE = False
    # Create mock classes for graceful degradation
    class BaseMessage:
        def __init__(self, content: str):
            self.content = content
    
    class HumanMessage(BaseMessage):
        pass
    
    class AIMessage(BaseMessage):
        pass

logger = logging.getLogger(__name__)

@dataclass
class ConversationContext:
    """Context information for conversations"""
    user_id: str
    session_id: str
    conversation_id: str
    started_at: str
    current_topic: Optional[str] = None
    user_intent: Optional[str] = None
    mentioned_places: List[str] = None
    mentioned_preferences: Dict[str, Any] = None
    conversation_stage: str = "greeting"  # greeting, information_gathering, recommendation, follow_up
    last_activity: str = None

@dataclass 
class MemoryEntry:
    """Enhanced memory entry with semantic information"""
    entry_id: str
    user_id: str
    conversation_id: str
    timestamp: str
    human_message: str
    ai_message: str
    context: ConversationContext
    importance_score: float
    semantic_tags: List[str]
    entities_extracted: Dict[str, List[str]]  # {'places': [...], 'preferences': [...], etc.}
    emotion_tone: Optional[str] = None
    satisfaction_score: Optional[float] = None

class MemoryStore(ABC):
    """Abstract base class for memory storage"""
    
    @abstractmethod
    def save_memory(self, memory: MemoryEntry) -> bool:
        pass
    
    @abstractmethod
    def get_memories(self, user_id: str, limit: int = 10) -> List[MemoryEntry]:
        pass
    
    @abstractmethod
    def get_conversation_history(self, conversation_id: str) -> List[MemoryEntry]:
        pass
    
    @abstractmethod
    def search_memories(self, user_id: str, query: str, limit: int = 5) -> List[MemoryEntry]:
        pass

class SQLiteMemoryStore(MemoryStore):
    """SQLite-based memory storage"""
    
    def __init__(self, db_path: Path):
        self.db_path = db_path
        self._init_database()
    
    def _init_database(self):
        """Initialize SQLite database for memory storage"""
        try:
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            
            # Enhanced memory table
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS enhanced_memories (
                    entry_id TEXT PRIMARY KEY,
                    user_id TEXT NOT NULL,
                    conversation_id TEXT NOT NULL,
                    timestamp TEXT NOT NULL,
                    human_message TEXT NOT NULL,
                    ai_message TEXT NOT NULL,
                    context_data TEXT,
                    importance_score REAL,
                    semantic_tags TEXT,
                    entities_extracted TEXT,
                    emotion_tone TEXT,
                    satisfaction_score REAL,
                    created_at TEXT DEFAULT CURRENT_TIMESTAMP
                )
            ''')
            
            cursor.execute('CREATE INDEX IF NOT EXISTS idx_enhanced_memories_user_id ON enhanced_memories(user_id)')
            cursor.execute('CREATE INDEX IF NOT EXISTS idx_enhanced_memories_conversation_id ON enhanced_memories(conversation_id)')
            cursor.execute('CREATE INDEX IF NOT EXISTS idx_enhanced_memories_timestamp ON enhanced_memories(timestamp)')
            
            # Conversation contexts table
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS conversation_contexts (
                    conversation_id TEXT PRIMARY KEY,
                    user_id TEXT NOT NULL,
                    session_id TEXT NOT NULL,
                    started_at TEXT NOT NULL,
                    ended_at TEXT,
                    current_topic TEXT,
                    user_intent TEXT,
                    mentioned_places TEXT,
                    mentioned_preferences TEXT,
                    conversation_stage TEXT,
                    last_activity TEXT,
                    message_count INTEGER DEFAULT 0
                )
            ''')
            
            cursor.execute('CREATE INDEX IF NOT EXISTS idx_conversation_contexts_user_id ON conversation_contexts(user_id)')
            cursor.execute('CREATE INDEX IF NOT EXISTS idx_conversation_contexts_session_id ON conversation_contexts(session_id)')
            
            conn.commit()
            conn.close()
            
        except Exception as e:
            logger.error(f"Error initializing memory database: {e}")
    
    def save_memory(self, memory: MemoryEntry) -> bool:
        """Save memory entry to database"""
        try:
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            
            cursor.execute('''
                INSERT OR REPLACE INTO enhanced_memories
                (entry_id, user_id, conversation_id, timestamp, human_message, ai_message,
                 context_data, importance_score, semantic_tags, entities_extracted,
                 emotion_tone, satisfaction_score)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            ''', (
                memory.entry_id,
                memory.user_id,
                memory.conversation_id,
                memory.timestamp,
                memory.human_message,
                memory.ai_message,
                json.dumps(asdict(memory.context), ensure_ascii=False, default=str),
                memory.importance_score,
                json.dumps(memory.semantic_tags, ensure_ascii=False),
                json.dumps(memory.entities_extracted, ensure_ascii=False),
                memory.emotion_tone,
                memory.satisfaction_score
            ))
            
            conn.commit()
            conn.close()
            return True
            
        except Exception as e:
            logger.error(f"Error saving memory: {e}")
            return False
    
    def get_memories(self, user_id: str, limit: int = 10) -> List[MemoryEntry]:
        """Get recent memories for user"""
        try:
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            
            cursor.execute('''
                SELECT * FROM enhanced_memories 
                WHERE user_id = ? 
                ORDER BY timestamp DESC 
                LIMIT ?
            ''', (user_id, limit))
            
            rows = cursor.fetchall()
            conn.close()
            
            memories = []
            for row in rows:
                context_data = json.loads(row[6]) if row[6] else {}
                context = ConversationContext(**context_data)
                
                memory = MemoryEntry(
                    entry_id=row[0],
                    user_id=row[1],
                    conversation_id=row[2],
                    timestamp=row[3],
                    human_message=row[4],
                    ai_message=row[5],
                    context=context,
                    importance_score=row[7] or 0.5,
                    semantic_tags=json.loads(row[8]) if row[8] else [],
                    entities_extracted=json.loads(row[9]) if row[9] else {},
                    emotion_tone=row[10],
                    satisfaction_score=row[11]
                )
                memories.append(memory)
            
            return memories
            
        except Exception as e:
            logger.error(f"Error getting memories: {e}")
            return []
    
    def get_conversation_history(self, conversation_id: str) -> List[MemoryEntry]:
        """Get all memories for a specific conversation"""
        try:
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            
            cursor.execute('''
                SELECT * FROM enhanced_memories 
                WHERE conversation_id = ? 
                ORDER BY timestamp ASC
            ''', (conversation_id,))
            
            rows = cursor.fetchall()
            conn.close()
            
            memories = []
            for row in rows:
                context_data = json.loads(row[6]) if row[6] else {}
                context = ConversationContext(**context_data)
                
                memory = MemoryEntry(
                    entry_id=row[0],
                    user_id=row[1],
                    conversation_id=row[2],
                    timestamp=row[3],
                    human_message=row[4],
                    ai_message=row[5],
                    context=context,
                    importance_score=row[7] or 0.5,
                    semantic_tags=json.loads(row[8]) if row[8] else [],
                    entities_extracted=json.loads(row[9]) if row[9] else {},
                    emotion_tone=row[10],
                    satisfaction_score=row[11]
                )
                memories.append(memory)
            
            return memories
            
        except Exception as e:
            logger.error(f"Error getting conversation history: {e}")
            return []
    
    def search_memories(self, user_id: str, query: str, limit: int = 5) -> List[MemoryEntry]:
        """Search memories using basic text matching"""
        try:
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            
            # Simple text search in messages and semantic tags
            search_pattern = f"%{query.lower()}%"
            cursor.execute('''
                SELECT * FROM enhanced_memories 
                WHERE user_id = ? AND (
                    LOWER(human_message) LIKE ? OR 
                    LOWER(ai_message) LIKE ? OR
                    LOWER(semantic_tags) LIKE ?
                )
                ORDER BY importance_score DESC, timestamp DESC
                LIMIT ?
            ''', (user_id, search_pattern, search_pattern, search_pattern, limit))
            
            rows = cursor.fetchall()
            conn.close()
            
            memories = []
            for row in rows:
                context_data = json.loads(row[6]) if row[6] else {}
                context = ConversationContext(**context_data)
                
                memory = MemoryEntry(
                    entry_id=row[0],
                    user_id=row[1],
                    conversation_id=row[2],
                    timestamp=row[3],
                    human_message=row[4],
                    ai_message=row[5],
                    context=context,
                    importance_score=row[7] or 0.5,
                    semantic_tags=json.loads(row[8]) if row[8] else [],
                    entities_extracted=json.loads(row[9]) if row[9] else {},
                    emotion_tone=row[10],
                    satisfaction_score=row[11]
                )
                memories.append(memory)
            
            return memories
            
        except Exception as e:
            logger.error(f"Error searching memories: {e}")
            return []

class EnhancedChatMemory:
    """
    Enhanced chat memory system with LangChain integration
    ระบบหน่วยความจำการสนทนาที่ปรับปรุงแล้ว
    """
    
    def __init__(self, storage_dir: Optional[Path] = None):
        self.storage_dir = storage_dir or Path(__file__).parent.parent / "cache" / "chat_memory"
        self.storage_dir.mkdir(parents=True, exist_ok=True)
        
        # Initialize memory store
        self.memory_store = SQLiteMemoryStore(self.storage_dir / "chat_memory.db")
        
        # Active conversation contexts
        self.active_contexts: Dict[str, ConversationContext] = {}
        
        # LangChain memory instances (if available)
        self.langchain_memories: Dict[str, Any] = {}
        
        # Memory configuration
        self.max_buffer_size = 20  # Number of recent messages to keep in buffer
        self.max_summary_tokens = 1000  # Max tokens for conversation summary
        self.importance_threshold = 0.3  # Minimum importance score to retain memory
        
        # Entity extraction patterns (simple keyword-based)
        self.place_keywords = [
            # Bangkok
            'กรุงเทพ', 'bangkok', 'วัดพระแก้ว', 'วัดอรุณ', 'เจเจ', 'chatuchak',
            # Chiang Mai  
            'เชียงใหม่', 'chiang mai', 'ดอยสุเทพ', 'ถนนคนเดิน',
            # Phuket
            'ภูเก็ต', 'phuket', 'ป่าตอง', 'patong', 'พังงา', 'phang nga',
            # General places
            'วัด', 'temple', 'ชายหาด', 'beach', 'ภูเขา', 'mountain', 'ตลาด', 'market'
        ]
        
        self.preference_keywords = {
            'budget': ['ราคา', 'งบประมาณ', 'ถูก', 'แพง', 'budget', 'price', 'cost', 'expensive', 'cheap'],
            'season': ['ฤดู', 'หน้าร้อน', 'หน้าฝน', 'หน้าหนาว', 'season', 'hot', 'rainy', 'cool'],
            'activity': ['กิจกรรม', 'เล่น', 'พักผ่อน', 'ผจญภัย', 'activity', 'adventure', 'relax'],
            'accommodation': ['โรงแรม', 'ที่พัก', 'รีสอร์ท', 'hotel', 'resort', 'stay']
        }
    
    def start_conversation(self, user_id: str, session_id: str) -> str:
        """Start a new conversation and return conversation ID"""
        conversation_id = f"{user_id}_{session_id}_{int(time.time())}"
        
        context = ConversationContext(
            user_id=user_id,
            session_id=session_id,
            conversation_id=conversation_id,
            started_at=datetime.now().isoformat(),
            mentioned_places=[],
            mentioned_preferences={},
            last_activity=datetime.now().isoformat()
        )
        
        self.active_contexts[conversation_id] = context
        self._save_conversation_context(context)
        
        # Initialize LangChain memory if available
        if LANGCHAIN_AVAILABLE:
            try:
                self.langchain_memories[conversation_id] = ConversationBufferWindowMemory(
                    k=self.max_buffer_size,
                    return_messages=True,
                    memory_key="chat_history"
                )
            except Exception as e:
                logger.warning(f"Could not initialize LangChain memory: {e}")
        
        return conversation_id
    
    def add_interaction(self, conversation_id: str, human_message: str, ai_message: str,
                       context_updates: Dict[str, Any] = None, importance_score: float = 0.5,
                       emotion_tone: str = None) -> str:
        """Add a conversation interaction to memory"""
        
        # Get or create conversation context
        if conversation_id not in self.active_contexts:
            # Try to load from database or create new
            context = self._load_conversation_context(conversation_id)
            if not context:
                # Extract user_id and session_id from conversation_id
                parts = conversation_id.split('_')
                if len(parts) >= 2:
                    user_id = parts[0]
                    session_id = parts[1]
                    conversation_id = self.start_conversation(user_id, session_id)
                else:
                    logger.error(f"Invalid conversation_id format: {conversation_id}")
                    return None
            else:
                self.active_contexts[conversation_id] = context
        
        context = self.active_contexts[conversation_id]
        
        # Update context with new information
        if context_updates:
            for key, value in context_updates.items():
                if hasattr(context, key):
                    setattr(context, key, value)
        
        # Extract entities from messages
        entities = self._extract_entities(human_message + " " + ai_message)
        
        # Update context with extracted entities
        if entities.get('places'):
            context.mentioned_places.extend(entities['places'])
            context.mentioned_places = list(set(context.mentioned_places))  # Remove duplicates
        
        for pref_type, preferences in entities.get('preferences', {}).items():
            if pref_type not in context.mentioned_preferences:
                context.mentioned_preferences[pref_type] = []
            context.mentioned_preferences[pref_type].extend(preferences)
            context.mentioned_preferences[pref_type] = list(set(context.mentioned_preferences[pref_type]))
        
        # Generate semantic tags
        semantic_tags = self._generate_semantic_tags(human_message, ai_message, entities)
        
        # Create memory entry
        entry_id = f"{conversation_id}_{int(time.time() * 1000)}"
        memory = MemoryEntry(
            entry_id=entry_id,
            user_id=context.user_id,
            conversation_id=conversation_id,
            timestamp=datetime.now().isoformat(),
            human_message=human_message,
            ai_message=ai_message,
            context=context,
            importance_score=importance_score,
            semantic_tags=semantic_tags,
            entities_extracted=entities,
            emotion_tone=emotion_tone
        )
        
        # Save to memory store
        success = self.memory_store.save_memory(memory)
        
        if success:
            # Update LangChain memory if available
            if LANGCHAIN_AVAILABLE and conversation_id in self.langchain_memories:
                try:
                    lc_memory = self.langchain_memories[conversation_id]
                    lc_memory.chat_memory.add_user_message(human_message)
                    lc_memory.chat_memory.add_ai_message(ai_message)
                except Exception as e:
                    logger.warning(f"Could not update LangChain memory: {e}")
            
            # Update context
            context.last_activity = datetime.now().isoformat()
            self._save_conversation_context(context)
        
        return entry_id if success else None
    
    def get_conversation_memory(self, conversation_id: str, include_summary: bool = True) -> Dict[str, Any]:
        """Get conversation memory for LangChain or other AI systems"""
        
        # Get conversation history
        memories = self.memory_store.get_conversation_history(conversation_id)
        
        if not memories:
            return {
                'messages': [],
                'summary': '',
                'context': {},
                'total_interactions': 0
            }
        
        # Format messages for LangChain
        messages = []
        for memory in memories:
            messages.append({
                'type': 'human',
                'content': memory.human_message,
                'timestamp': memory.timestamp
            })
            messages.append({
                'type': 'ai', 
                'content': memory.ai_message,
                'timestamp': memory.timestamp
            })
        
        # Generate conversation summary
        summary = self._generate_conversation_summary(memories) if include_summary else ""
        
        # Get context
        context = self.active_contexts.get(conversation_id, {})
        
        return {
            'messages': messages,
            'summary': summary,
            'context': asdict(context) if hasattr(context, '__dict__') else context,
            'total_interactions': len(memories),
            'mentioned_places': getattr(context, 'mentioned_places', []),
            'mentioned_preferences': getattr(context, 'mentioned_preferences', {}),
            'conversation_stage': getattr(context, 'conversation_stage', 'unknown')
        }
    
    def get_user_memory_context(self, user_id: str, current_query: str, limit: int = 5) -> Dict[str, Any]:
        """Get relevant user memory context for current query"""
        
        # Search for relevant memories
        relevant_memories = self.memory_store.search_memories(user_id, current_query, limit)
        
        # Get recent memories
        recent_memories = self.memory_store.get_memories(user_id, limit)
        
        # Combine and deduplicate
        all_memories = relevant_memories + recent_memories
        seen_ids = set()
        unique_memories = []
        for memory in all_memories:
            if memory.entry_id not in seen_ids:
                unique_memories.append(memory)
                seen_ids.add(memory.entry_id)
        
        # Extract key information
        mentioned_places = set()
        mentioned_preferences = {}
        conversation_themes = set()
        
        for memory in unique_memories:
            # Places
            mentioned_places.update(memory.entities_extracted.get('places', []))
            
            # Preferences
            for pref_type, prefs in memory.entities_extracted.get('preferences', {}).items():
                if pref_type not in mentioned_preferences:
                    mentioned_preferences[pref_type] = set()
                mentioned_preferences[pref_type].update(prefs)
            
            # Themes
            conversation_themes.update(memory.semantic_tags)
        
        # Convert sets to lists for JSON serialization
        return {
            'relevant_memories': [
                {
                    'human_message': mem.human_message,
                    'ai_message': mem.ai_message,
                    'timestamp': mem.timestamp,
                    'importance_score': mem.importance_score,
                    'semantic_tags': mem.semantic_tags
                }
                for mem in unique_memories[:limit]
            ],
            'mentioned_places': list(mentioned_places),
            'mentioned_preferences': {k: list(v) for k, v in mentioned_preferences.items()},
            'conversation_themes': list(conversation_themes),
            'memory_strength': len(unique_memories) / 10.0  # Normalized memory strength
        }
    
    def get_langchain_memory(self, conversation_id: str):
        """Get LangChain memory object for integration"""
        if not LANGCHAIN_AVAILABLE:
            return None
        
        return self.langchain_memories.get(conversation_id)
    
    def cleanup_old_memories(self, days_to_keep: int = 90):
        """Clean up old memories"""
        # This would be implemented to remove old memories
        # For now, we'll keep all memories
        pass
    
    def _extract_entities(self, text: str) -> Dict[str, List[str]]:
        """Extract entities from text using keyword matching"""
        text_lower = text.lower()
        entities = {
            'places': [],
            'preferences': {}
        }
        
        # Extract places
        for place in self.place_keywords:
            if place in text_lower:
                entities['places'].append(place)
        
        # Extract preferences
        for pref_type, keywords in self.preference_keywords.items():
            for keyword in keywords:
                if keyword in text_lower:
                    if pref_type not in entities['preferences']:
                        entities['preferences'][pref_type] = []
                    entities['preferences'][pref_type].append(keyword)
        
        return entities
    
    def _generate_semantic_tags(self, human_message: str, ai_message: str, entities: Dict[str, Any]) -> List[str]:
        """Generate semantic tags for the conversation"""
        tags = []
        text = (human_message + " " + ai_message).lower()
        
        # Intent-based tags
        if any(word in text for word in ['แนะนำ', 'recommend', 'suggest', 'ช่วย']):
            tags.append('recommendation_request')
        
        if any(word in text for word in ['ขอบคุณ', 'thank', 'ดี', 'good', 'ชอบ', 'like']):
            tags.append('positive_feedback')
        
        if any(word in text for word in ['ไม่', 'not', 'ไม่ชอบ', 'dislike', 'แย่', 'bad']):
            tags.append('negative_feedback')
        
        # Topic-based tags
        if entities.get('places'):
            tags.append('places_discussion')
        
        if entities.get('preferences'):
            tags.append('preferences_discussion')
        
        if any(word in text for word in ['เที่ยว', 'ท่องเที่ยว', 'travel', 'trip']):
            tags.append('travel_planning')
        
        if any(word in text for word in ['อาหาร', 'กิน', 'food', 'eat', 'restaurant']):
            tags.append('food_discussion')
        
        if any(word in text for word in ['ที่พัก', 'โรงแรม', 'hotel', 'accommodation']):
            tags.append('accommodation_discussion')
        
        return tags
    
    def _generate_conversation_summary(self, memories: List[MemoryEntry]) -> str:
        """Generate a summary of the conversation"""
        if not memories:
            return ""
        
        # Simple summary generation
        total_interactions = len(memories)
        mentioned_places = set()
        mentioned_preferences = set()
        
        for memory in memories:
            mentioned_places.update(memory.entities_extracted.get('places', []))
            for prefs in memory.entities_extracted.get('preferences', {}).values():
                mentioned_preferences.update(prefs)
        
        summary_parts = []
        summary_parts.append(f"การสนทนามี {total_interactions} รอบ")
        
        if mentioned_places:
            places_str = ", ".join(list(mentioned_places)[:3])
            summary_parts.append(f"พูดถึงสถานที่: {places_str}")
        
        if mentioned_preferences:
            prefs_str = ", ".join(list(mentioned_preferences)[:3])
            summary_parts.append(f"พูดถึงความชอบ: {prefs_str}")
        
        return ". ".join(summary_parts)
    
    def _save_conversation_context(self, context: ConversationContext):
        """Save conversation context to database"""
        try:
            conn = sqlite3.connect(self.memory_store.db_path)
            cursor = conn.cursor()
            
            cursor.execute('''
                INSERT OR REPLACE INTO conversation_contexts
                (conversation_id, user_id, session_id, started_at, current_topic,
                 user_intent, mentioned_places, mentioned_preferences, conversation_stage, last_activity)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            ''', (
                context.conversation_id,
                context.user_id,
                context.session_id,
                context.started_at,
                context.current_topic,
                context.user_intent,
                json.dumps(context.mentioned_places, ensure_ascii=False),
                json.dumps(context.mentioned_preferences, ensure_ascii=False),
                context.conversation_stage,
                context.last_activity
            ))
            
            conn.commit()
            conn.close()
            
        except Exception as e:
            logger.error(f"Error saving conversation context: {e}")
    
    def _load_conversation_context(self, conversation_id: str) -> Optional[ConversationContext]:
        """Load conversation context from database"""
        try:
            conn = sqlite3.connect(self.memory_store.db_path)
            cursor = conn.cursor()
            
            cursor.execute('''
                SELECT * FROM conversation_contexts WHERE conversation_id = ?
            ''', (conversation_id,))
            
            row = cursor.fetchone()
            conn.close()
            
            if row:
                return ConversationContext(
                    conversation_id=row[0],
                    user_id=row[1],
                    session_id=row[2],
                    started_at=row[3],
                    current_topic=row[5],
                    user_intent=row[6],
                    mentioned_places=json.loads(row[7]) if row[7] else [],
                    mentioned_preferences=json.loads(row[8]) if row[8] else {},
                    conversation_stage=row[9] or "greeting",
                    last_activity=row[10]
                )
            
        except Exception as e:
            logger.error(f"Error loading conversation context: {e}")
        
        return None


# Global instance
enhanced_chat_memory = EnhancedChatMemory()