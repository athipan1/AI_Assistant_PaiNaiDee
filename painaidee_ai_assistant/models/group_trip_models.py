"""
Group Trip Planning Data Models
Handles group travel planning, user preferences, and AI-powered group optimization
"""

import json
import uuid
from typing import Dict, List, Optional, Any, Set
from dataclasses import dataclass, asdict
from datetime import datetime, timedelta
from pathlib import Path
from enum import Enum

class TripStatus(Enum):
    DRAFT = "draft"
    PLANNING = "planning"
    ACTIVE = "active"
    COMPLETED = "completed"
    CANCELLED = "cancelled"

class PreferenceCategory(Enum):
    INTEREST_TYPE = "interest_type"  # nature, culture, adventure, food, etc.
    ACTIVITY_LEVEL = "activity_level"  # low, medium, high
    TIME_PREFERENCE = "time_preference"  # morning, afternoon, evening, night
    LOCATION_TYPE = "location_type"  # indoor, outdoor, mixed
    BUDGET_RANGE = "budget_range"  # budget, mid, luxury
    GROUP_SIZE = "group_size"  # small, medium, large

@dataclass
class UserPreference:
    """Represents individual user travel preferences"""
    user_id: str
    username: str
    preferences: Dict[str, Any]  # category -> value/weight
    favorite_locations: List[str]
    disliked_locations: List[str]
    special_requirements: List[str]  # accessibility, dietary, etc.
    availability: Dict[str, bool]  # date/time availability
    weight: float = 1.0  # user's influence weight in group decisions
    created_at: str = None
    updated_at: str = None
    
    def __post_init__(self):
        if self.created_at is None:
            self.created_at = datetime.now().isoformat()
        if self.updated_at is None:
            self.updated_at = datetime.now().isoformat()

@dataclass
class Location:
    """Represents a travel location/destination"""
    location_id: str
    name: str
    location_type: str  # attraction, restaurant, hotel, activity
    coordinates: List[float]  # [lat, lng]
    description: str
    tags: List[str]
    rating: float
    price_range: str  # $, $$, $$$, $$$$
    duration_hours: float  # typical visit duration
    best_time: List[str]  # preferred times to visit
    requirements: List[str]  # special requirements
    
@dataclass
class TripGroup:
    """Represents a group trip with multiple users"""
    group_id: str
    group_name: str
    creator_id: str
    member_ids: List[str]
    status: TripStatus
    destination_city: str
    trip_dates: Dict[str, str]  # start_date, end_date
    shared_locations: List[Location]  # locations added by group members
    group_preferences: Dict[str, Any]  # aggregated preferences
    public_link: Optional[str] = None
    invitation_code: Optional[str] = None
    created_at: str = None
    updated_at: str = None
    
    def __post_init__(self):
        if self.created_at is None:
            self.created_at = datetime.now().isoformat()
        if self.updated_at is None:
            self.updated_at = datetime.now().isoformat()
        if self.group_id is None:
            self.group_id = str(uuid.uuid4())
        if self.invitation_code is None:
            self.invitation_code = str(uuid.uuid4())[:8].upper()

@dataclass
class GroupPlan:
    """AI-generated travel plan for a group"""
    plan_id: str
    group_id: str
    itinerary: List[Dict[str, Any]]  # day-by-day schedule
    optimized_locations: List[Location]  # AI-selected best locations
    travel_routes: List[Dict[str, Any]]  # routes between locations
    time_allocation: Dict[str, float]  # time spent on each activity type
    compromise_analysis: Dict[str, Any]  # how preferences were balanced
    confidence_score: float  # AI confidence in this plan
    alternative_plans: List[Dict[str, Any]] = None  # backup options
    generated_at: str = None
    
    def __post_init__(self):
        if self.generated_at is None:
            self.generated_at = datetime.now().isoformat()
        if self.plan_id is None:
            self.plan_id = str(uuid.uuid4())

class GroupTripManager:
    """Manages group trips, preferences, and AI planning"""
    
    def __init__(self, storage_dir: str = "tourist_data/group_trips"):
        self.storage_dir = Path(storage_dir)
        self.storage_dir.mkdir(parents=True, exist_ok=True)
        
        # In-memory storage (could be replaced with database)
        self.groups: Dict[str, TripGroup] = {}
        self.user_preferences: Dict[str, UserPreference] = {}
        self.group_plans: Dict[str, GroupPlan] = {}
        self.public_links: Dict[str, str] = {}  # public_link -> group_id
        
        # Load existing data
        self._load_data()
    
    def create_group(self, group_name: str, creator_id: str, creator_username: str, 
                    destination_city: str, trip_dates: Dict[str, str]) -> TripGroup:
        """Create a new group trip"""
        group = TripGroup(
            group_id=str(uuid.uuid4()),
            group_name=group_name,
            creator_id=creator_id,
            member_ids=[creator_id],
            status=TripStatus.DRAFT,
            destination_city=destination_city,
            trip_dates=trip_dates,
            shared_locations=[],
            group_preferences={},
            public_link=None
        )
        
        self.groups[group.group_id] = group
        self._save_data()
        return group
    
    def add_member(self, group_id: str, user_id: str, invitation_code: str = None) -> bool:
        """Add member to group trip"""
        if group_id not in self.groups:
            return False
            
        group = self.groups[group_id]
        if invitation_code and group.invitation_code != invitation_code:
            return False
            
        if user_id not in group.member_ids:
            group.member_ids.append(user_id)
            group.updated_at = datetime.now().isoformat()
            self._save_data()
        
        return True
    
    def set_user_preferences(self, user_id: str, username: str, preferences: Dict[str, Any],
                           favorite_locations: List[str] = None, 
                           disliked_locations: List[str] = None) -> UserPreference:
        """Set or update user travel preferences"""
        user_pref = UserPreference(
            user_id=user_id,
            username=username,
            preferences=preferences,
            favorite_locations=favorite_locations or [],
            disliked_locations=disliked_locations or [],
            special_requirements=[],
            availability={}
        )
        
        self.user_preferences[user_id] = user_pref
        self._save_data()
        return user_pref
    
    def add_location_to_group(self, group_id: str, location: Location, added_by: str) -> bool:
        """Add a location to group's shared locations"""
        if group_id not in self.groups:
            return False
            
        group = self.groups[group_id]
        location.added_by = added_by  # Track who added it
        group.shared_locations.append(location)
        group.updated_at = datetime.now().isoformat()
        self._save_data()
        return True
    
    def generate_public_link(self, group_id: str) -> str:
        """Generate public sharing link for group trip"""
        if group_id not in self.groups:
            return None
            
        public_id = str(uuid.uuid4())
        public_link = f"/group-trip/{public_id}"
        
        group = self.groups[group_id]
        group.public_link = public_link
        self.public_links[public_id] = group_id
        
        self._save_data()
        return public_link
    
    def get_group_by_public_link(self, public_id: str) -> Optional[TripGroup]:
        """Get group by public link ID"""
        if public_id not in self.public_links:
            return None
        
        group_id = self.public_links[public_id]
        return self.groups.get(group_id)
    
    def analyze_group_preferences(self, group_id: str) -> Dict[str, Any]:
        """Analyze and aggregate group member preferences"""
        if group_id not in self.groups:
            return {}
            
        group = self.groups[group_id]
        member_preferences = []
        
        for member_id in group.member_ids:
            if member_id in self.user_preferences:
                member_preferences.append(self.user_preferences[member_id])
        
        if not member_preferences:
            return {}
        
        # Aggregate preferences using weighted averages
        aggregated = {}
        
        # Interest types - find most common
        interest_counts = {}
        for pref in member_preferences:
            interests = pref.preferences.get('interest_types', [])
            for interest in interests:
                interest_counts[interest] = interest_counts.get(interest, 0) + pref.weight
        
        # Activity level - weighted average
        activity_levels = {'low': 1, 'medium': 2, 'high': 3}
        activity_sum = 0
        weight_sum = 0
        for pref in member_preferences:
            level = pref.preferences.get('activity_level', 'medium')
            activity_sum += activity_levels[level] * pref.weight
            weight_sum += pref.weight
        
        avg_activity = activity_sum / weight_sum if weight_sum > 0 else 2
        activity_result = 'low' if avg_activity < 1.5 else 'high' if avg_activity > 2.5 else 'medium'
        
        # Budget range - find compromise
        budget_levels = {'budget': 1, 'mid': 2, 'luxury': 3}
        budget_sum = 0
        weight_sum = 0
        for pref in member_preferences:
            budget = pref.preferences.get('budget_range', 'mid')
            budget_sum += budget_levels[budget] * pref.weight
            weight_sum += pref.weight
        
        avg_budget = budget_sum / weight_sum if weight_sum > 0 else 2
        budget_result = 'budget' if avg_budget < 1.5 else 'luxury' if avg_budget > 2.5 else 'mid'
        
        aggregated = {
            'top_interests': sorted(interest_counts.items(), key=lambda x: x[1], reverse=True)[:3],
            'activity_level': activity_result,
            'budget_range': budget_result,
            'member_count': len(member_preferences),
            'consensus_strength': self._calculate_consensus_strength(member_preferences)
        }
        
        return aggregated
    
    def _calculate_consensus_strength(self, preferences: List[UserPreference]) -> float:
        """Calculate how much the group agrees on preferences (0-1)"""
        if len(preferences) < 2:
            return 1.0
            
        # Calculate similarity between all pairs of preferences
        similarities = []
        for i in range(len(preferences)):
            for j in range(i + 1, len(preferences)):
                sim = self._preference_similarity(preferences[i], preferences[j])
                similarities.append(sim)
        
        return sum(similarities) / len(similarities) if similarities else 0.0
    
    def _preference_similarity(self, pref1: UserPreference, pref2: UserPreference) -> float:
        """Calculate similarity between two user preferences (0-1)"""
        # Simple similarity based on overlapping interests and preferences
        p1_interests = set(pref1.preferences.get('interest_types', []))
        p2_interests = set(pref2.preferences.get('interest_types', []))
        
        if not p1_interests and not p2_interests:
            interest_sim = 1.0
        elif not p1_interests or not p2_interests:
            interest_sim = 0.0
        else:
            interest_sim = len(p1_interests & p2_interests) / len(p1_interests | p2_interests)
        
        # Activity level similarity
        activity_sim = 1.0 if pref1.preferences.get('activity_level') == pref2.preferences.get('activity_level') else 0.5
        
        # Budget similarity
        budget_sim = 1.0 if pref1.preferences.get('budget_range') == pref2.preferences.get('budget_range') else 0.5
        
        return (interest_sim + activity_sim + budget_sim) / 3.0
    
    def _save_data(self):
        """Save data to storage"""
        # Save groups
        groups_file = self.storage_dir / "groups.json"
        with open(groups_file, 'w', encoding='utf-8') as f:
            groups_data = {}
            for gid, group in self.groups.items():
                group_dict = asdict(group)
                # Convert enum to string
                group_dict['status'] = group.status.value
                groups_data[gid] = group_dict
            json.dump(groups_data, f, ensure_ascii=False, indent=2)
        
        # Save user preferences
        prefs_file = self.storage_dir / "user_preferences.json"
        with open(prefs_file, 'w', encoding='utf-8') as f:
            prefs_data = {uid: asdict(pref) for uid, pref in self.user_preferences.items()}
            json.dump(prefs_data, f, ensure_ascii=False, indent=2)
        
        # Save public links
        links_file = self.storage_dir / "public_links.json"
        with open(links_file, 'w', encoding='utf-8') as f:
            json.dump(self.public_links, f, ensure_ascii=False, indent=2)
    
    def _load_data(self):
        """Load data from storage"""
        try:
            # Load groups
            groups_file = self.storage_dir / "groups.json"
            if groups_file.exists():
                with open(groups_file, 'r', encoding='utf-8') as f:
                    groups_data = json.load(f)
                    for gid, data in groups_data.items():
                        # Convert dict back to TripGroup
                        data['status'] = TripStatus(data['status'])
                        locations = []
                        for loc_data in data.get('shared_locations', []):
                            locations.append(Location(**loc_data))
                        data['shared_locations'] = locations
                        self.groups[gid] = TripGroup(**data)
            
            # Load user preferences
            prefs_file = self.storage_dir / "user_preferences.json"
            if prefs_file.exists():
                with open(prefs_file, 'r', encoding='utf-8') as f:
                    prefs_data = json.load(f)
                    for uid, data in prefs_data.items():
                        self.user_preferences[uid] = UserPreference(**data)
            
            # Load public links
            links_file = self.storage_dir / "public_links.json"
            if links_file.exists():
                with open(links_file, 'r', encoding='utf-8') as f:
                    self.public_links = json.load(f)
                    
        except Exception as e:
            print(f"Warning: Could not load group trip data: {e}")

# Global instance
group_trip_manager = GroupTripManager()