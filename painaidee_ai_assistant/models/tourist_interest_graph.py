"""
Tourist Interest Graph System
Captures user interests, performs clustering, and creates association mappings
for AI-powered tourism recommendations
"""

import json
import numpy as np
from typing import Dict, List, Optional, Any, Tuple, Set
from dataclasses import dataclass, asdict
from datetime import datetime, timedelta
from pathlib import Path
import pickle
from collections import defaultdict, Counter
import threading
import time
import math
from sklearn.cluster import KMeans, DBSCAN
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.metrics.pairwise import cosine_similarity
import warnings
warnings.filterwarnings('ignore')


@dataclass
class TouristInterest:
    """Represents a user's tourist interest"""
    interest_id: str
    user_id: str
    session_id: str
    interest_type: str  # 'nature', 'city', 'culture', 'adventure', 'food', 'history'
    specific_tags: List[str]  # e.g., ['hiking', 'waterfalls', 'mountains']
    location_preference: str  # 'indoor', 'outdoor', 'mixed'
    time_preference: str  # 'morning', 'afternoon', 'evening', 'night', 'flexible'
    activity_level: str  # 'low', 'medium', 'high'
    group_size: str  # 'solo', 'couple', 'family', 'group'
    budget_range: str  # 'budget', 'mid', 'luxury'
    interaction_strength: float  # 0.0 to 1.0 - how strongly user expressed this interest
    confidence: float  # 0.0 to 1.0 - system confidence in this interest
    timestamp: str
    context: Dict[str, Any]  # weather, season, etc. when interest was captured


@dataclass
class LocationAssociation:
    """Represents association between interests and locations/models"""
    location_id: str
    location_name: str
    location_type: str  # 'model', 'place', 'activity'
    associated_interests: List[str]
    relevance_scores: Dict[str, float]  # interest_type -> relevance score
    contextual_factors: Dict[str, Any]  # weather_suitable, time_suitable, etc.
    popularity_score: float
    last_updated: str


@dataclass
class InterestCluster:
    """Represents a cluster of similar interests"""
    cluster_id: str
    cluster_name: str
    interest_types: List[str]
    common_tags: List[str]
    centroid_features: Dict[str, float]
    user_count: int
    representative_interests: List[str]
    created_at: str
    updated_at: str


class TouristInterestGraph:
    """AI-powered tourist interest graph with clustering and association mapping"""
    
    def __init__(self, storage_dir: str = "tourist_data"):
        self.storage_dir = Path(storage_dir)
        self.storage_dir.mkdir(exist_ok=True)
        
        # Interest storage
        self.user_interests: Dict[str, List[TouristInterest]] = defaultdict(list)
        self.location_associations: Dict[str, LocationAssociation] = {}
        self.interest_clusters: Dict[str, InterestCluster] = {}
        
        # Clustering models
        self.interest_vectorizer = TfidfVectorizer(max_features=100, stop_words='english')
        self.kmeans_model = None
        self.dbscan_model = None
        
        # Association mapping
        self.interest_location_matrix = None
        self.association_weights = {
            'direct_interaction': 1.0,
            'semantic_similarity': 0.7,
            'user_clustering': 0.5,
            'contextual_match': 0.8,
            'popularity_boost': 0.3
        }
        
        # Background processing
        self._clustering_thread = None
        self._stop_clustering = False
        
        # Interest categories with typical tags
        self.interest_categories = {
            'nature': ['hiking', 'waterfalls', 'mountains', 'forests', 'wildlife', 'parks', 'beaches', 'lakes'],
            'city': ['architecture', 'skyline', 'urban', 'buildings', 'streets', 'downtown', 'districts'],
            'culture': ['temples', 'museums', 'art', 'traditional', 'ceremonies', 'festivals', 'heritage'],
            'adventure': ['sports', 'climbing', 'diving', 'rafting', 'extreme', 'challenge', 'thrill'],
            'food': ['restaurants', 'street food', 'local cuisine', 'markets', 'cooking', 'taste', 'dining'],
            'history': ['ancient', 'ruins', 'monuments', 'historical', 'archaeological', 'old', 'heritage']
        }
        
        # Load existing data
        self._load_data()
        
        # Start background clustering
        self._start_background_clustering()
    
    def _load_data(self):
        """Load existing tourist data"""
        try:
            # Load user interests
            interests_file = self.storage_dir / "user_interests.json"
            if interests_file.exists():
                with open(interests_file, 'r') as f:
                    data = json.load(f)
                    for user_id, interests_data in data.items():
                        self.user_interests[user_id] = [
                            TouristInterest(**interest) for interest in interests_data
                        ]
            
            # Load location associations
            associations_file = self.storage_dir / "location_associations.json"
            if associations_file.exists():
                with open(associations_file, 'r') as f:
                    data = json.load(f)
                    self.location_associations = {
                        k: LocationAssociation(**v) for k, v in data.items()
                    }
            
            # Load clusters
            clusters_file = self.storage_dir / "interest_clusters.json"
            if clusters_file.exists():
                with open(clusters_file, 'r') as f:
                    data = json.load(f)
                    self.interest_clusters = {
                        k: InterestCluster(**v) for k, v in data.items()
                    }
                    
        except Exception as e:
            print(f"Error loading tourist data: {e}")
    
    def _save_data(self):
        """Save tourist data to storage"""
        try:
            # Save user interests
            interests_data = {
                user_id: [asdict(interest) for interest in interests]
                for user_id, interests in self.user_interests.items()
            }
            with open(self.storage_dir / "user_interests.json", 'w') as f:
                json.dump(interests_data, f, indent=2)
            
            # Save location associations
            associations_data = {
                k: asdict(v) for k, v in self.location_associations.items()
            }
            with open(self.storage_dir / "location_associations.json", 'w') as f:
                json.dump(associations_data, f, indent=2)
            
            # Save clusters
            clusters_data = {
                k: asdict(v) for k, v in self.interest_clusters.items()
            }
            with open(self.storage_dir / "interest_clusters.json", 'w') as f:
                json.dump(clusters_data, f, indent=2)
                
        except Exception as e:
            print(f"Error saving tourist data: {e}")
    
    def capture_interest_from_interaction(self, user_id: str, session_id: str,
                                        interaction_data: Dict[str, Any]) -> TouristInterest:
        """Capture tourist interest from user interaction"""
        
        # Extract interest signals from interaction
        query = interaction_data.get('query', '').lower()
        selected_model = interaction_data.get('selected_model', '')
        context = interaction_data.get('context', {})
        
        # Classify interest type based on query and model
        interest_type = self._classify_interest_type(query, selected_model)
        specific_tags = self._extract_specific_tags(query, interest_type)
        
        # Infer preferences from interaction
        location_preference = self._infer_location_preference(query, context)
        time_preference = self._infer_time_preference(query, context)
        activity_level = self._infer_activity_level(query, selected_model)
        group_size = self._infer_group_size(query, context)
        budget_range = self._infer_budget_range(query, context)
        
        # Calculate interaction strength and confidence
        interaction_strength = self._calculate_interaction_strength(interaction_data)
        confidence = self._calculate_interest_confidence(query, specific_tags, context)
        
        # Create interest record
        interest = TouristInterest(
            interest_id=f"{user_id}_{session_id}_{len(self.user_interests[user_id])}",
            user_id=user_id,
            session_id=session_id,
            interest_type=interest_type,
            specific_tags=specific_tags,
            location_preference=location_preference,
            time_preference=time_preference,
            activity_level=activity_level,
            group_size=group_size,
            budget_range=budget_range,
            interaction_strength=interaction_strength,
            confidence=confidence,
            timestamp=datetime.now().isoformat(),
            context=context
        )
        
        # Store interest
        self.user_interests[user_id].append(interest)
        
        # Update location associations
        self._update_location_associations(interest, selected_model)
        
        # Save data
        self._save_data()
        
        return interest
    
    def _classify_interest_type(self, query: str, selected_model: str) -> str:
        """Classify the type of tourist interest"""
        query_lower = query.lower()
        
        # Check each category for keyword matches
        category_scores = {}
        for category, keywords in self.interest_categories.items():
            score = sum(1 for keyword in keywords if keyword in query_lower)
            category_scores[category] = score
        
        # Special rules for 3D models
        if 'walking' in selected_model.lower() or 'running' in selected_model.lower():
            category_scores['adventure'] = category_scores.get('adventure', 0) + 2
        
        # Return category with highest score, default to 'nature'
        if category_scores:
            return max(category_scores, key=category_scores.get)
        return 'nature'
    
    def _extract_specific_tags(self, query: str, interest_type: str) -> List[str]:
        """Extract specific tags from query relevant to interest type"""
        query_lower = query.lower()
        relevant_tags = []
        
        # Get keywords for this interest type
        category_keywords = self.interest_categories.get(interest_type, [])
        
        # Find matching keywords
        for keyword in category_keywords:
            if keyword in query_lower:
                relevant_tags.append(keyword)
        
        # Add common tourism tags
        tourism_tags = ['scenic', 'popular', 'famous', 'beautiful', 'peaceful', 'exciting']
        for tag in tourism_tags:
            if tag in query_lower:
                relevant_tags.append(tag)
        
        return relevant_tags[:5]  # Limit to top 5 tags
    
    def _infer_location_preference(self, query: str, context: Dict[str, Any]) -> str:
        """Infer indoor/outdoor preference"""
        query_lower = query.lower()
        
        indoor_keywords = ['indoor', 'inside', 'cafe', 'restaurant', 'museum', 'mall', 'hotel']
        outdoor_keywords = ['outdoor', 'outside', 'park', 'beach', 'mountain', 'hiking', 'nature']
        
        indoor_score = sum(1 for keyword in indoor_keywords if keyword in query_lower)
        outdoor_score = sum(1 for keyword in outdoor_keywords if keyword in query_lower)
        
        if indoor_score > outdoor_score:
            return 'indoor'
        elif outdoor_score > indoor_score:
            return 'outdoor'
        else:
            return 'mixed'
    
    def _infer_time_preference(self, query: str, context: Dict[str, Any]) -> str:
        """Infer time of day preference"""
        query_lower = query.lower()
        current_hour = datetime.now().hour
        
        time_keywords = {
            'morning': ['morning', 'sunrise', 'early', 'breakfast'],
            'afternoon': ['afternoon', 'lunch', 'midday'],
            'evening': ['evening', 'sunset', 'dinner'],
            'night': ['night', 'nightlife', 'late']
        }
        
        for time_period, keywords in time_keywords.items():
            if any(keyword in query_lower for keyword in keywords):
                return time_period
        
        # Infer from current time if no explicit mention
        if 6 <= current_hour < 12:
            return 'morning'
        elif 12 <= current_hour < 17:
            return 'afternoon'
        elif 17 <= current_hour < 21:
            return 'evening'
        else:
            return 'night'
    
    def _infer_activity_level(self, query: str, selected_model: str) -> str:
        """Infer activity level preference"""
        query_lower = query.lower()
        model_lower = selected_model.lower()
        
        high_activity = ['running', 'hiking', 'climbing', 'adventure', 'sports', 'active']
        low_activity = ['relaxing', 'peaceful', 'calm', 'sitting', 'idle', 'rest']
        
        if any(word in query_lower or word in model_lower for word in high_activity):
            return 'high'
        elif any(word in query_lower or word in model_lower for word in low_activity):
            return 'low'
        else:
            return 'medium'
    
    def _infer_group_size(self, query: str, context: Dict[str, Any]) -> str:
        """Infer group size preference"""
        query_lower = query.lower()
        
        group_keywords = {
            'solo': ['solo', 'alone', 'myself', 'individual'],
            'couple': ['couple', 'romantic', 'two', 'date'],
            'family': ['family', 'kids', 'children', 'parents'],
            'group': ['group', 'friends', 'team', 'together']
        }
        
        for group_type, keywords in group_keywords.items():
            if any(keyword in query_lower for keyword in keywords):
                return group_type
        
        return 'solo'  # Default assumption
    
    def _infer_budget_range(self, query: str, context: Dict[str, Any]) -> str:
        """Infer budget preference"""
        query_lower = query.lower()
        
        if any(word in query_lower for word in ['cheap', 'budget', 'affordable', 'free']):
            return 'budget'
        elif any(word in query_lower for word in ['luxury', 'premium', 'expensive', 'high-end']):
            return 'luxury'
        else:
            return 'mid'
    
    def _calculate_interaction_strength(self, interaction_data: Dict[str, Any]) -> float:
        """Calculate how strongly this interaction indicates interest"""
        base_strength = 0.5
        
        # Boost for specific queries
        query = interaction_data.get('query', '').lower()
        if len(query.split()) > 3:  # More detailed queries show stronger intent
            base_strength += 0.2
        
        # Boost for positive feedback
        feedback = interaction_data.get('feedback', {})
        if feedback.get('satisfaction', 0) > 0.7:
            base_strength += 0.3
        
        # Boost for longer interaction time
        interaction_time = interaction_data.get('interaction_time', 0)
        if interaction_time > 30:  # 30+ seconds indicates engagement
            base_strength += 0.2
        
        return min(1.0, base_strength)
    
    def _calculate_interest_confidence(self, query: str, tags: List[str], 
                                     context: Dict[str, Any]) -> float:
        """Calculate confidence in interest classification"""
        base_confidence = 0.5
        
        # Higher confidence for more specific queries
        if len(tags) > 2:
            base_confidence += 0.3
        
        # Higher confidence for clear keywords
        if len(query.split()) > 2:
            base_confidence += 0.2
        
        return min(1.0, base_confidence)
    
    def _update_location_associations(self, interest: TouristInterest, location_id: str):
        """Update associations between interests and locations/models"""
        
        if location_id not in self.location_associations:
            # Create new association
            self.location_associations[location_id] = LocationAssociation(
                location_id=location_id,
                location_name=location_id.replace('.fbx', '').replace('_', ' ').title(),
                location_type='model',
                associated_interests=[interest.interest_type],
                relevance_scores={interest.interest_type: interest.interaction_strength},
                contextual_factors={
                    'location_preference': interest.location_preference,
                    'time_preference': interest.time_preference,
                    'activity_level': interest.activity_level
                },
                popularity_score=1.0,
                last_updated=datetime.now().isoformat()
            )
        else:
            # Update existing association
            association = self.location_associations[location_id]
            
            # Add new interest type if not present
            if interest.interest_type not in association.associated_interests:
                association.associated_interests.append(interest.interest_type)
            
            # Update relevance score (weighted average)
            current_score = association.relevance_scores.get(interest.interest_type, 0)
            new_score = (current_score + interest.interaction_strength) / 2
            association.relevance_scores[interest.interest_type] = new_score
            
            # Update popularity
            association.popularity_score += 0.1
            association.last_updated = datetime.now().isoformat()
    
    def perform_interest_clustering(self, min_users: int = 5) -> Dict[str, InterestCluster]:
        """Perform clustering on user interests to find patterns"""
        
        if len(self.user_interests) < min_users:
            return self.interest_clusters
        
        # Prepare data for clustering
        all_interests = []
        interest_features = []
        
        for user_id, interests in self.user_interests.items():
            for interest in interests:
                all_interests.append(interest)
                
                # Create feature vector for clustering
                feature_text = f"{interest.interest_type} {' '.join(interest.specific_tags)} {interest.location_preference} {interest.activity_level}"
                interest_features.append(feature_text)
        
        if len(interest_features) < min_users:
            return self.interest_clusters
        
        try:
            # Vectorize interests
            feature_vectors = self.interest_vectorizer.fit_transform(interest_features)
            
            # Perform K-means clustering
            n_clusters = min(8, max(2, len(set(i.interest_type for i in all_interests))))
            self.kmeans_model = KMeans(n_clusters=n_clusters, random_state=42)
            cluster_labels = self.kmeans_model.fit_predict(feature_vectors)
            
            # Create cluster objects
            clusters = defaultdict(list)
            for interest, label in zip(all_interests, cluster_labels):
                clusters[label].append(interest)
            
            # Generate cluster descriptions
            new_clusters = {}
            for cluster_id, cluster_interests in clusters.items():
                if len(cluster_interests) >= 2:  # Only meaningful clusters
                    cluster_name = self._generate_cluster_name(cluster_interests)
                    
                    # Extract common characteristics
                    interest_types = [i.interest_type for i in cluster_interests]
                    common_tags = self._find_common_tags(cluster_interests)
                    
                    # Create cluster
                    cluster = InterestCluster(
                        cluster_id=f"cluster_{cluster_id}",
                        cluster_name=cluster_name,
                        interest_types=list(set(interest_types)),
                        common_tags=common_tags,
                        centroid_features=self._calculate_centroid_features(cluster_interests),
                        user_count=len(set(i.user_id for i in cluster_interests)),
                        representative_interests=[i.interest_id for i in cluster_interests[:3]],
                        created_at=datetime.now().isoformat(),
                        updated_at=datetime.now().isoformat()
                    )
                    
                    new_clusters[cluster.cluster_id] = cluster
            
            self.interest_clusters.update(new_clusters)
            self._save_data()
            
            return new_clusters
            
        except Exception as e:
            print(f"Error in interest clustering: {e}")
            return self.interest_clusters
    
    def _generate_cluster_name(self, interests: List[TouristInterest]) -> str:
        """Generate a descriptive name for a cluster"""
        # Count most common interest types and tags
        interest_types = Counter(i.interest_type for i in interests)
        all_tags = []
        for i in interests:
            all_tags.extend(i.specific_tags)
        common_tags = Counter(all_tags)
        
        # Generate name
        top_type = interest_types.most_common(1)[0][0] if interest_types else "mixed"
        top_tag = common_tags.most_common(1)[0][0] if common_tags else "general"
        
        return f"{top_type.title()} - {top_tag.title()} Enthusiasts"
    
    def _find_common_tags(self, interests: List[TouristInterest]) -> List[str]:
        """Find tags common to multiple interests in cluster"""
        all_tags = []
        for interest in interests:
            all_tags.extend(interest.specific_tags)
        
        tag_counts = Counter(all_tags)
        # Return tags that appear in at least 25% of interests
        min_count = max(1, len(interests) * 0.25)
        return [tag for tag, count in tag_counts.items() if count >= min_count]
    
    def _calculate_centroid_features(self, interests: List[TouristInterest]) -> Dict[str, float]:
        """Calculate centroid features for a cluster"""
        if not interests:
            return {}
        
        # Calculate average numeric features
        interaction_strengths = [i.interaction_strength for i in interests]
        confidences = [i.confidence for i in interests]
        
        # Calculate categorical feature distributions
        location_prefs = Counter(i.location_preference for i in interests)
        time_prefs = Counter(i.time_preference for i in interests)
        activity_levels = Counter(i.activity_level for i in interests)
        
        return {
            'avg_interaction_strength': sum(interaction_strengths) / len(interaction_strengths),
            'avg_confidence': sum(confidences) / len(confidences),
            'location_preference_dist': dict(location_prefs),
            'time_preference_dist': dict(time_prefs),
            'activity_level_dist': dict(activity_levels),
            'cluster_size': len(interests)
        }
    
    def get_recommendations_for_user(self, user_id: str, context: Dict[str, Any], 
                                   available_locations: List[str], top_k: int = 5) -> List[Dict[str, Any]]:
        """Get personalized recommendations based on user's interest graph"""
        
        user_interests = self.user_interests.get(user_id, [])
        if not user_interests:
            # Return default recommendations for new users
            return self._get_default_recommendations(available_locations, context, top_k)
        
        recommendations = []
        
        for location_id in available_locations:
            score = self._calculate_recommendation_score(
                user_interests, location_id, context
            )
            
            if score > 0:
                recommendations.append({
                    'location_id': location_id,
                    'score': score,
                    'reasoning': self._explain_recommendation(user_interests, location_id, context),
                    'matching_interests': self._get_matching_interests(user_interests, location_id),
                    'confidence': min(1.0, score)
                })
        
        # Sort by score and return top_k
        recommendations.sort(key=lambda x: x['score'], reverse=True)
        return recommendations[:top_k]
    
    def _calculate_recommendation_score(self, user_interests: List[TouristInterest], 
                                      location_id: str, context: Dict[str, Any]) -> float:
        """Calculate recommendation score for a location based on user interests"""
        
        if location_id not in self.location_associations:
            return 0.1  # Small base score for unknown locations
        
        association = self.location_associations[location_id]
        total_score = 0.0
        
        # Score based on direct interest matches
        for interest in user_interests:
            if interest.interest_type in association.relevance_scores:
                relevance = association.relevance_scores[interest.interest_type]
                strength = interest.interaction_strength
                confidence = interest.confidence
                
                # Apply temporal decay (recent interests matter more)
                interest_time = datetime.fromisoformat(interest.timestamp)
                age_days = (datetime.now() - interest_time).days
                temporal_weight = math.exp(-age_days / 30)  # 30-day half-life
                
                interest_score = relevance * strength * confidence * temporal_weight
                total_score += interest_score * self.association_weights['direct_interaction']
        
        # Boost for contextual matches
        contextual_score = self._calculate_contextual_match(
            user_interests, association, context
        )
        total_score += contextual_score * self.association_weights['contextual_match']
        
        # Boost for popularity
        popularity_boost = min(0.3, association.popularity_score / 10)
        total_score += popularity_boost * self.association_weights['popularity_boost']
        
        # Cluster-based boosting
        cluster_boost = self._calculate_cluster_boost(user_interests, location_id)
        total_score += cluster_boost * self.association_weights['user_clustering']
        
        return min(1.0, total_score)
    
    def _calculate_contextual_match(self, user_interests: List[TouristInterest],
                                  association: LocationAssociation, 
                                  context: Dict[str, Any]) -> float:
        """Calculate how well location matches current context"""
        
        match_score = 0.0
        
        # Time of day matching
        current_hour = datetime.now().hour
        user_time_prefs = Counter(i.time_preference for i in user_interests)
        
        if current_hour in range(6, 12) and user_time_prefs.get('morning', 0) > 0:
            match_score += 0.2
        elif current_hour in range(12, 17) and user_time_prefs.get('afternoon', 0) > 0:
            match_score += 0.2
        elif current_hour in range(17, 21) and user_time_prefs.get('evening', 0) > 0:
            match_score += 0.2
        elif current_hour in range(21, 6) and user_time_prefs.get('night', 0) > 0:
            match_score += 0.2
        
        # Weather/season matching (if provided in context)
        weather = context.get('weather', {})
        if weather.get('condition') == 'rainy':
            # Prefer indoor locations during rain
            user_location_prefs = Counter(i.location_preference for i in user_interests)
            if user_location_prefs.get('indoor', 0) > 0:
                match_score += 0.3
        
        return match_score
    
    def _calculate_cluster_boost(self, user_interests: List[TouristInterest], 
                               location_id: str) -> float:
        """Calculate boost based on user's cluster membership"""
        
        if not self.interest_clusters:
            return 0.0
        
        user_interest_types = set(i.interest_type for i in user_interests)
        boost = 0.0
        
        for cluster in self.interest_clusters.values():
            # Check if user interests overlap with cluster
            cluster_interest_types = set(cluster.interest_types)
            overlap = len(user_interest_types.intersection(cluster_interest_types))
            
            if overlap > 0:
                # Check if location is popular in this cluster
                if location_id in self.location_associations:
                    association = self.location_associations[location_id]
                    cluster_relevance = sum(
                        association.relevance_scores.get(itype, 0) 
                        for itype in cluster_interest_types
                    ) / len(cluster_interest_types)
                    
                    cluster_boost = (overlap / len(user_interest_types)) * cluster_relevance
                    boost += cluster_boost
        
        return min(0.5, boost)
    
    def _explain_recommendation(self, user_interests: List[TouristInterest],
                              location_id: str, context: Dict[str, Any]) -> List[str]:
        """Generate explanation for recommendation"""
        reasons = []
        
        if location_id in self.location_associations:
            association = self.location_associations[location_id]
            
            # Interest-based reasons
            matching_types = []
            for interest in user_interests:
                if interest.interest_type in association.relevance_scores:
                    matching_types.append(interest.interest_type)
            
            if matching_types:
                reasons.append(f"Matches your interest in {', '.join(set(matching_types))}")
            
            # Context-based reasons
            current_hour = datetime.now().hour
            if 17 <= current_hour <= 21:
                reasons.append("Good for evening activities")
            
            # Popularity reasons
            if association.popularity_score > 5:
                reasons.append("Popular choice among similar users")
        
        if not reasons:
            reasons.append("Recommended based on general preferences")
        
        return reasons
    
    def _get_matching_interests(self, user_interests: List[TouristInterest], 
                              location_id: str) -> List[str]:
        """Get user interests that match this location"""
        
        if location_id not in self.location_associations:
            return []
        
        association = self.location_associations[location_id]
        matching = []
        
        for interest in user_interests:
            if interest.interest_type in association.associated_interests:
                matching.append(interest.interest_id)
        
        return matching
    
    def _get_default_recommendations(self, available_locations: List[str],
                                   context: Dict[str, Any], top_k: int) -> List[Dict[str, Any]]:
        """Get default recommendations for new users"""
        recommendations = []
        
        for location_id in available_locations[:top_k]:
            recommendations.append({
                'location_id': location_id,
                'score': 0.5,
                'reasoning': ["Default recommendation for new user"],
                'matching_interests': [],
                'confidence': 0.3
            })
        
        return recommendations
    
    def _start_background_clustering(self):
        """Start background thread for periodic clustering"""
        def clustering_loop():
            while not self._stop_clustering:
                try:
                    self.perform_interest_clustering()
                    time.sleep(3600)  # Run every hour
                except Exception as e:
                    print(f"Error in background clustering: {e}")
                    time.sleep(300)  # Wait 5 minutes on error
        
        self._clustering_thread = threading.Thread(target=clustering_loop, daemon=True)
        self._clustering_thread.start()
    
    def get_analytics(self) -> Dict[str, Any]:
        """Get analytics about the tourist interest graph"""
        total_interests = sum(len(interests) for interests in self.user_interests.values())
        
        # Interest type distribution
        all_interest_types = []
        for interests in self.user_interests.values():
            all_interest_types.extend(i.interest_type for i in interests)
        
        interest_type_dist = dict(Counter(all_interest_types))
        
        # Cluster statistics
        cluster_stats = {
            'total_clusters': len(self.interest_clusters),
            'avg_cluster_size': np.mean([c.user_count for c in self.interest_clusters.values()]) if self.interest_clusters else 0,
            'cluster_names': [c.cluster_name for c in self.interest_clusters.values()]
        }
        
        return {
            'total_users': len(self.user_interests),
            'total_interests': total_interests,
            'total_locations': len(self.location_associations),
            'interest_type_distribution': interest_type_dist,
            'cluster_statistics': cluster_stats,
            'avg_interests_per_user': total_interests / len(self.user_interests) if self.user_interests else 0,
            'last_updated': datetime.now().isoformat()
        }


# Initialize global tourist interest graph
tourist_graph = TouristInterestGraph()