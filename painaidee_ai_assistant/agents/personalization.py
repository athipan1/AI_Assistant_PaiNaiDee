"""
Personalization Layer for 3D Model Selection
Manages user sessions, preferences, and provides personalized recommendations
"""

import json
import time
import hashlib
from typing import Dict, List, Any, Optional, Tuple
from dataclasses import dataclass, asdict
from datetime import datetime, timedelta
from pathlib import Path
import logging

logger = logging.getLogger(__name__)

@dataclass
class UserInteraction:
    """Record of a single user interaction"""
    timestamp: float
    query: str
    selected_model: str
    intent_style: str
    intent_purpose: str
    intent_motion: str
    confidence: float
    session_id: str
    feedback: Optional[str] = None  # positive, negative, neutral

@dataclass
class UserPreferences:
    """User preference profile"""
    preferred_styles: Dict[str, float]  # style -> weight
    preferred_purposes: Dict[str, float]  # purpose -> weight
    preferred_motions: Dict[str, float]  # motion -> weight
    favorite_models: Dict[str, int]  # model -> usage_count
    query_patterns: List[str]  # common query patterns
    last_updated: float
    total_interactions: int

@dataclass
class SessionContext:
    """Current session context and state"""
    session_id: str
    start_time: float
    last_activity: float
    interactions: List[UserInteraction]
    current_preferences: UserPreferences
    context_keywords: List[str]  # keywords from recent queries
    session_theme: Optional[str] = None  # inferred session theme

@dataclass
class Recommendation:
    """Personalized recommendation"""
    model_name: str
    confidence: float
    reasoning: str
    recommendation_type: str  # "preference_based", "session_based", "popularity_based"
    personalization_score: float

class PersonalizationEngine:
    """
    Personalization engine that tracks user preferences and provides 
    tailored model recommendations based on session memory and user profiles
    """
    
    def __init__(self, storage_dir: Optional[Path] = None):
        self.storage_dir = storage_dir or Path(__file__).parent.parent / "cache" / "personalization"
        self.storage_dir.mkdir(parents=True, exist_ok=True)
        
        # Active sessions (in-memory)
        self.active_sessions: Dict[str, SessionContext] = {}
        
        # User profiles (persistent)
        self.user_profiles: Dict[str, UserPreferences] = {}
        
        # Global statistics
        self.global_stats = {
            "total_users": 0,
            "total_interactions": 0,
            "popular_models": {},
            "popular_intents": {},
            "last_updated": time.time()
        }
        
        # Load existing data
        self._load_data()
        
        # Session timeout (30 minutes)
        self.session_timeout = 30 * 60
        
        # Recommendation weights
        self.recommendation_weights = {
            "user_history": 0.4,
            "session_context": 0.3,
            "global_popularity": 0.2,
            "recency": 0.1
        }
    
    def start_session(self, user_id: Optional[str] = None) -> str:
        """Start a new user session"""
        if user_id is None:
            # Generate anonymous session ID
            session_id = self._generate_session_id()
        else:
            # Use user-based session ID
            session_id = f"user_{user_id}_{int(time.time())}"
        
        # Get or create user preferences
        if user_id and user_id in self.user_profiles:
            current_prefs = self.user_profiles[user_id]
        else:
            current_prefs = self._create_default_preferences()
        
        session = SessionContext(
            session_id=session_id,
            start_time=time.time(),
            last_activity=time.time(),
            interactions=[],
            current_preferences=current_prefs,
            context_keywords=[]
        )
        
        self.active_sessions[session_id] = session
        return session_id
    
    def record_interaction(self, session_id: str, query: str, selected_model: str,
                          intent_style: str, intent_purpose: str, intent_motion: str,
                          confidence: float, feedback: Optional[str] = None) -> None:
        """Record a user interaction"""
        if session_id not in self.active_sessions:
            logger.warning(f"Session {session_id} not found, creating new session")
            self.start_session()
            if session_id not in self.active_sessions:
                session_id = self.start_session()
        
        session = self.active_sessions[session_id]
        
        interaction = UserInteraction(
            timestamp=time.time(),
            query=query,
            selected_model=selected_model,
            intent_style=intent_style,
            intent_purpose=intent_purpose,
            intent_motion=intent_motion,
            confidence=confidence,
            session_id=session_id,
            feedback=feedback
        )
        
        session.interactions.append(interaction)
        session.last_activity = time.time()
        
        # Update session context
        self._update_session_context(session, query, intent_style, intent_purpose, intent_motion)
        
        # Update user preferences
        self._update_user_preferences(session, interaction)
        
        # Update global statistics
        self._update_global_stats(interaction)
        
        # Auto-save periodically
        if len(session.interactions) % 5 == 0:
            self._save_data()
    
    def get_recommendations(self, session_id: str, query: str, 
                          available_models: List[str], 
                          top_k: int = 3) -> List[Recommendation]:
        """Get personalized recommendations for a query"""
        if session_id not in self.active_sessions:
            # Create temporary session for recommendations
            temp_session_id = self.start_session()
            session = self.active_sessions[temp_session_id]
        else:
            session = self.active_sessions[session_id]
        
        recommendations = []
        
        # 1. User history-based recommendations
        history_recs = self._get_history_based_recommendations(session, query, available_models)
        
        # 2. Session context-based recommendations
        context_recs = self._get_context_based_recommendations(session, query, available_models)
        
        # 3. Global popularity-based recommendations
        popularity_recs = self._get_popularity_based_recommendations(available_models)
        
        # 4. Combine and rank recommendations
        combined_recs = self._combine_recommendations(
            history_recs, context_recs, popularity_recs, available_models
        )
        
        return combined_recs[:top_k]
    
    def update_preferences_from_feedback(self, session_id: str, interaction_index: int,
                                       feedback: str) -> None:
        """Update preferences based on user feedback"""
        if session_id not in self.active_sessions:
            return
        
        session = self.active_sessions[session_id]
        if interaction_index >= len(session.interactions):
            return
        
        interaction = session.interactions[interaction_index]
        interaction.feedback = feedback
        
        # Adjust preferences based on feedback
        if feedback == "positive":
            self._boost_preferences(session, interaction, 1.2)
        elif feedback == "negative":
            self._boost_preferences(session, interaction, 0.8)
    
    def get_session_summary(self, session_id: str) -> Dict[str, Any]:
        """Get summary of current session"""
        if session_id not in self.active_sessions:
            return {"error": "Session not found"}
        
        session = self.active_sessions[session_id]
        
        # Calculate session statistics
        model_usage = {}
        intent_distribution = {"style": {}, "purpose": {}, "motion": {}}
        
        for interaction in session.interactions:
            # Model usage
            model_usage[interaction.selected_model] = model_usage.get(interaction.selected_model, 0) + 1
            
            # Intent distribution
            intent_distribution["style"][interaction.intent_style] = \
                intent_distribution["style"].get(interaction.intent_style, 0) + 1
            intent_distribution["purpose"][interaction.intent_purpose] = \
                intent_distribution["purpose"].get(interaction.intent_purpose, 0) + 1
            intent_distribution["motion"][interaction.intent_motion] = \
                intent_distribution["motion"].get(interaction.intent_motion, 0) + 1
        
        return {
            "session_id": session_id,
            "duration": time.time() - session.start_time,
            "interactions_count": len(session.interactions),
            "model_usage": model_usage,
            "intent_distribution": intent_distribution,
            "session_theme": session.session_theme,
            "context_keywords": session.context_keywords
        }
    
    def _generate_session_id(self) -> str:
        """Generate a unique session ID"""
        timestamp = str(time.time())
        random_data = f"{timestamp}_{hash(timestamp)}"
        return hashlib.md5(random_data.encode()).hexdigest()[:16]
    
    def _create_default_preferences(self) -> UserPreferences:
        """Create default user preferences"""
        return UserPreferences(
            preferred_styles={"neutral": 1.0, "realistic": 0.5, "stylized": 0.5},
            preferred_purposes={"display": 1.0, "animation": 0.5, "static": 0.5, "rigged": 0.3},
            preferred_motions={"idle": 1.0, "walking": 0.5, "running": 0.3, "custom": 0.2, "none": 0.8},
            favorite_models={},
            query_patterns=[],
            last_updated=time.time(),
            total_interactions=0
        )
    
    def _update_session_context(self, session: SessionContext, query: str,
                               intent_style: str, intent_purpose: str, intent_motion: str) -> None:
        """Update session context with new interaction"""
        # Extract keywords from query
        import re
        keywords = re.findall(r'\b\w+\b', query.lower())
        
        # Add new keywords to context (keep recent ones)
        session.context_keywords.extend(keywords)
        session.context_keywords = list(set(session.context_keywords[-20:]))  # Keep last 20 unique keywords
        
        # Infer session theme based on patterns
        if len(session.interactions) >= 3:
            session.session_theme = self._infer_session_theme(session)
    
    def _infer_session_theme(self, session: SessionContext) -> Optional[str]:
        """Infer the theme of the current session"""
        recent_interactions = session.interactions[-5:]  # Last 5 interactions
        
        # Count intent patterns
        styles = [interaction.intent_style for interaction in recent_interactions]
        purposes = [interaction.intent_purpose for interaction in recent_interactions]
        motions = [interaction.intent_motion for interaction in recent_interactions]
        
        # Determine dominant patterns
        style_counts = {style: styles.count(style) for style in set(styles)}
        purpose_counts = {purpose: purposes.count(purpose) for purpose in set(purposes)}
        motion_counts = {motion: motions.count(motion) for motion in set(motions)}
        
        dominant_style = max(style_counts, key=style_counts.get) if style_counts else None
        dominant_purpose = max(purpose_counts, key=purpose_counts.get) if purpose_counts else None
        dominant_motion = max(motion_counts, key=motion_counts.get) if motion_counts else None
        
        # Generate theme description
        theme_parts = []
        if dominant_style and style_counts[dominant_style] >= 2:
            theme_parts.append(f"{dominant_style} style")
        if dominant_purpose and purpose_counts[dominant_purpose] >= 2:
            theme_parts.append(f"{dominant_purpose} focused")
        if dominant_motion and motion_counts[dominant_motion] >= 2:
            theme_parts.append(f"{dominant_motion} motion")
        
        return ", ".join(theme_parts) if theme_parts else None
    
    def _update_user_preferences(self, session: SessionContext, interaction: UserInteraction) -> None:
        """Update user preferences based on new interaction"""
        prefs = session.current_preferences
        
        # Update style preferences
        prefs.preferred_styles[interaction.intent_style] = \
            prefs.preferred_styles.get(interaction.intent_style, 0) + 0.1
        
        # Update purpose preferences
        prefs.preferred_purposes[interaction.intent_purpose] = \
            prefs.preferred_purposes.get(interaction.intent_purpose, 0) + 0.1
        
        # Update motion preferences
        prefs.preferred_motions[interaction.intent_motion] = \
            prefs.preferred_motions.get(interaction.intent_motion, 0) + 0.1
        
        # Update favorite models
        prefs.favorite_models[interaction.selected_model] = \
            prefs.favorite_models.get(interaction.selected_model, 0) + 1
        
        # Update query patterns
        if interaction.query not in prefs.query_patterns:
            prefs.query_patterns.append(interaction.query)
            prefs.query_patterns = prefs.query_patterns[-10:]  # Keep last 10 patterns
        
        prefs.total_interactions += 1
        prefs.last_updated = time.time()
    
    def _boost_preferences(self, session: SessionContext, interaction: UserInteraction, factor: float) -> None:
        """Boost or reduce preferences based on feedback"""
        prefs = session.current_preferences
        
        # Adjust preferences with the given factor
        prefs.preferred_styles[interaction.intent_style] *= factor
        prefs.preferred_purposes[interaction.intent_purpose] *= factor
        prefs.preferred_motions[interaction.intent_motion] *= factor
        
        if factor > 1.0:
            # Positive feedback - boost model preference
            prefs.favorite_models[interaction.selected_model] = \
                prefs.favorite_models.get(interaction.selected_model, 0) + 2
        else:
            # Negative feedback - reduce model preference
            if interaction.selected_model in prefs.favorite_models:
                prefs.favorite_models[interaction.selected_model] = \
                    max(0, prefs.favorite_models[interaction.selected_model] - 1)
    
    def _update_global_stats(self, interaction: UserInteraction) -> None:
        """Update global usage statistics"""
        self.global_stats["total_interactions"] += 1
        
        # Update popular models
        model_count = self.global_stats["popular_models"].get(interaction.selected_model, 0) + 1
        self.global_stats["popular_models"][interaction.selected_model] = model_count
        
        # Update popular intents
        intent_key = f"{interaction.intent_style}_{interaction.intent_purpose}_{interaction.intent_motion}"
        intent_count = self.global_stats["popular_intents"].get(intent_key, 0) + 1
        self.global_stats["popular_intents"][intent_key] = intent_count
        
        self.global_stats["last_updated"] = time.time()
    
    def _get_history_based_recommendations(self, session: SessionContext, query: str,
                                         available_models: List[str]) -> List[Recommendation]:
        """Generate recommendations based on user history"""
        recommendations = []
        prefs = session.current_preferences
        
        # Sort models by user preference (favorite models and preference alignment)
        model_scores = {}
        
        for model in available_models:
            score = 0
            reasoning_parts = []
            
            # Favorite model bonus
            if model in prefs.favorite_models:
                score += prefs.favorite_models[model] * 0.5
                reasoning_parts.append(f"Previously used {prefs.favorite_models[model]} times")
            
            # Preference alignment (would need model metadata mapping)
            # For now, use simple heuristics
            if "walking" in model.lower() and prefs.preferred_motions.get("walking", 0) > 0.7:
                score += 0.3
                reasoning_parts.append("Matches walking preference")
            
            if "rig" in model.lower() and prefs.preferred_purposes.get("rigged", 0) > 0.7:
                score += 0.3
                reasoning_parts.append("Matches rigged model preference")
            
            if score > 0:
                model_scores[model] = score
                recommendations.append(Recommendation(
                    model_name=model,
                    confidence=min(score, 1.0),
                    reasoning="; ".join(reasoning_parts) if reasoning_parts else "Based on user history",
                    recommendation_type="preference_based",
                    personalization_score=score
                ))
        
        recommendations.sort(key=lambda x: x.personalization_score, reverse=True)
        return recommendations
    
    def _get_context_based_recommendations(self, session: SessionContext, query: str,
                                         available_models: List[str]) -> List[Recommendation]:
        """Generate recommendations based on current session context"""
        recommendations = []
        
        if not session.interactions:
            return recommendations
        
        # Analyze recent interaction patterns
        recent_models = [interaction.selected_model for interaction in session.interactions[-3:]]
        recent_model_counts = {model: recent_models.count(model) for model in set(recent_models)}
        
        # Context keywords from recent queries
        context_score = {}
        for model in available_models:
            score = 0
            reasoning_parts = []
            
            # Recent model continuity
            if model in recent_model_counts:
                score += recent_model_counts[model] * 0.2
                reasoning_parts.append(f"Recently used in session")
            
            # Context keyword matching
            model_lower = model.lower()
            for keyword in session.context_keywords:
                if keyword in model_lower:
                    score += 0.1
                    reasoning_parts.append(f"Matches session context: {keyword}")
            
            # Session theme alignment
            if session.session_theme:
                if "animation" in session.session_theme and ("walking" in model_lower or "running" in model_lower):
                    score += 0.3
                    reasoning_parts.append("Aligns with session animation theme")
                
                if "static" in session.session_theme and ("idle" in model_lower or "man" in model_lower):
                    score += 0.3
                    reasoning_parts.append("Aligns with session static theme")
            
            if score > 0:
                recommendations.append(Recommendation(
                    model_name=model,
                    confidence=min(score, 1.0),
                    reasoning="; ".join(reasoning_parts) if reasoning_parts else "Based on session context",
                    recommendation_type="session_based",
                    personalization_score=score
                ))
        
        recommendations.sort(key=lambda x: x.personalization_score, reverse=True)
        return recommendations
    
    def _get_popularity_based_recommendations(self, available_models: List[str]) -> List[Recommendation]:
        """Generate recommendations based on global popularity"""
        recommendations = []
        
        total_usage = sum(self.global_stats["popular_models"].values()) or 1
        
        for model in available_models:
            usage_count = self.global_stats["popular_models"].get(model, 0)
            popularity_score = usage_count / total_usage
            
            if popularity_score > 0:
                recommendations.append(Recommendation(
                    model_name=model,
                    confidence=popularity_score,
                    reasoning=f"Popular choice (used {usage_count} times globally)",
                    recommendation_type="popularity_based",
                    personalization_score=popularity_score
                ))
        
        recommendations.sort(key=lambda x: x.personalization_score, reverse=True)
        return recommendations
    
    def _combine_recommendations(self, history_recs: List[Recommendation],
                               context_recs: List[Recommendation],
                               popularity_recs: List[Recommendation],
                               available_models: List[str]) -> List[Recommendation]:
        """Combine different recommendation sources"""
        combined_scores = {}
        combined_reasoning = {}
        
        # Process each recommendation type
        for recs, weight_key in [(history_recs, "user_history"), 
                                (context_recs, "session_context"), 
                                (popularity_recs, "global_popularity")]:
            weight = self.recommendation_weights[weight_key]
            
            for rec in recs:
                if rec.model_name not in combined_scores:
                    combined_scores[rec.model_name] = 0
                    combined_reasoning[rec.model_name] = []
                
                combined_scores[rec.model_name] += rec.personalization_score * weight
                combined_reasoning[rec.model_name].append(f"{rec.recommendation_type}: {rec.reasoning}")
        
        # Create final recommendations
        final_recommendations = []
        for model, score in combined_scores.items():
            reasoning = "; ".join(combined_reasoning[model])
            final_recommendations.append(Recommendation(
                model_name=model,
                confidence=min(score, 1.0),
                reasoning=reasoning,
                recommendation_type="combined",
                personalization_score=score
            ))
        
        # Add any missing models with default scores
        for model in available_models:
            if model not in combined_scores:
                final_recommendations.append(Recommendation(
                    model_name=model,
                    confidence=0.1,
                    reasoning="Default recommendation",
                    recommendation_type="default",
                    personalization_score=0.1
                ))
        
        final_recommendations.sort(key=lambda x: x.personalization_score, reverse=True)
        return final_recommendations
    
    def _save_data(self) -> None:
        """Save user data to persistent storage"""
        try:
            # Save user profiles
            profiles_file = self.storage_dir / "user_profiles.json"
            with open(profiles_file, 'w') as f:
                # Convert to serializable format
                serializable_profiles = {}
                for user_id, prefs in self.user_profiles.items():
                    serializable_profiles[user_id] = asdict(prefs)
                json.dump(serializable_profiles, f, indent=2)
            
            # Save global stats
            stats_file = self.storage_dir / "global_stats.json"
            with open(stats_file, 'w') as f:
                json.dump(self.global_stats, f, indent=2)
            
        except Exception as e:
            logger.error(f"Error saving personalization data: {e}")
    
    def _load_data(self) -> None:
        """Load user data from persistent storage"""
        try:
            # Load user profiles
            profiles_file = self.storage_dir / "user_profiles.json"
            if profiles_file.exists():
                with open(profiles_file, 'r') as f:
                    profiles_data = json.load(f)
                    for user_id, prefs_dict in profiles_data.items():
                        self.user_profiles[user_id] = UserPreferences(**prefs_dict)
            
            # Load global stats
            stats_file = self.storage_dir / "global_stats.json"
            if stats_file.exists():
                with open(stats_file, 'r') as f:
                    self.global_stats.update(json.load(f))
            
        except Exception as e:
            logger.error(f"Error loading personalization data: {e}")
    
    def cleanup_expired_sessions(self) -> None:
        """Remove expired sessions"""
        current_time = time.time()
        expired_sessions = []
        
        for session_id, session in self.active_sessions.items():
            if current_time - session.last_activity > self.session_timeout:
                expired_sessions.append(session_id)
        
        for session_id in expired_sessions:
            del self.active_sessions[session_id]
        
        if expired_sessions:
            logger.info(f"Cleaned up {len(expired_sessions)} expired sessions")

# Global instance
personalization_engine = PersonalizationEngine()

def test_personalization():
    """Test the personalization engine"""
    engine = PersonalizationEngine()
    
    # Create a test session
    session_id = engine.start_session("test_user")
    print(f"Started session: {session_id}")
    
    # Simulate user interactions
    interactions = [
        ("Show me a walking person", "Walking.fbx", "neutral", "animation", "walking", 0.8),
        ("I need animation for my game", "Man_Rig.fbx", "neutral", "rigged", "custom", 0.7),
        ("Display a character running", "Running.fbx", "neutral", "animation", "running", 0.9),
        ("Show me walking again", "Walking.fbx", "neutral", "animation", "walking", 0.9),
        ("I want an idle pose", "Idle.fbx", "neutral", "static", "idle", 0.8)
    ]
    
    available_models = ["Man.fbx", "Idle.fbx", "Walking.fbx", "Running.fbx", "Man_Rig.fbx"]
    
    for query, model, style, purpose, motion, confidence in interactions:
        engine.record_interaction(session_id, query, model, style, purpose, motion, confidence)
        
        print(f"\nAfter query: '{query}'")
        print(f"Selected: {model}")
        
        # Get recommendations for next interaction
        recommendations = engine.get_recommendations(session_id, query, available_models, top_k=3)
        print("Recommendations:")
        for i, rec in enumerate(recommendations, 1):
            print(f"  {i}. {rec.model_name} (score: {rec.personalization_score:.2f}, type: {rec.recommendation_type})")
            print(f"     Reasoning: {rec.reasoning}")
    
    # Show session summary
    summary = engine.get_session_summary(session_id)
    print(f"\nSession Summary:")
    print(f"Duration: {summary['duration']:.1f} seconds")
    print(f"Interactions: {summary['interactions_count']}")
    print(f"Model usage: {summary['model_usage']}")
    print(f"Session theme: {summary['session_theme']}")

if __name__ == "__main__":
    test_personalization()