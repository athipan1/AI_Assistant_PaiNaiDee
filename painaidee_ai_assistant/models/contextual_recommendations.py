"""
Contextual Recommendation Engine
Analyzes real-time factors like time, weather, seasonality to provide 
context-aware tourism recommendations
"""

import json
import requests
from typing import Dict, List, Optional, Any, Tuple
from dataclasses import dataclass, asdict
from datetime import datetime, timedelta
from pathlib import Path
import math
from enum import Enum
import calendar


class WeatherCondition(Enum):
    CLEAR = "clear"
    CLOUDY = "cloudy"
    RAINY = "rainy"
    STORMY = "stormy"
    FOGGY = "foggy"
    SNOWY = "snowy"


class Season(Enum):
    SPRING = "spring"
    SUMMER = "summer"
    FALL = "fall"
    WINTER = "winter"


class TimeOfDay(Enum):
    EARLY_MORNING = "early_morning"  # 5-8 AM
    MORNING = "morning"              # 8-12 PM
    AFTERNOON = "afternoon"          # 12-5 PM
    EVENING = "evening"              # 5-8 PM
    NIGHT = "night"                  # 8 PM-5 AM


@dataclass
class ContextualFactors:
    """Real-time contextual factors for recommendations"""
    timestamp: str
    local_time: datetime
    time_of_day: TimeOfDay
    season: Season
    weather_condition: WeatherCondition
    temperature: float  # Celsius
    humidity: float  # Percentage
    wind_speed: float  # km/h
    precipitation_chance: float  # Percentage
    uv_index: float
    air_quality_index: Optional[int]
    location: Dict[str, Any]  # lat, lng, city, country
    special_events: List[str]  # festivals, holidays, etc.
    crowd_level: str  # low, medium, high
    accessibility_factors: Dict[str, Any]


@dataclass
class ContextualRecommendation:
    """A contextually-aware recommendation"""
    location_id: str
    location_name: str
    recommendation_type: str  # activity, place, model
    suitability_score: float  # 0-1
    contextual_reasons: List[str]
    optimal_time_window: Tuple[int, int]  # hour range
    weather_dependency: str  # indoor, outdoor, flexible
    seasonal_preference: List[Season]
    crowd_tolerance: str  # low, medium, high
    accessibility_level: str  # easy, moderate, challenging
    estimated_duration: int  # minutes
    special_considerations: List[str]


class ContextualRecommendationEngine:
    """Engine for context-aware tourism recommendations"""
    
    def __init__(self, storage_dir: str = "contextual_data"):
        self.storage_dir = Path(storage_dir)
        self.storage_dir.mkdir(exist_ok=True)
        
        # Location profiles with contextual preferences
        self.location_profiles: Dict[str, Dict[str, Any]] = {}
        
        # Weather service configuration (mock for now)
        self.weather_api_key = None
        self.weather_service_url = "https://api.openweathermap.org/data/2.5"
        
        # Contextual rules and weights
        self.contextual_weights = {
            'weather_match': 0.4,
            'time_suitability': 0.3,
            'seasonal_preference': 0.2,
            'crowd_preference': 0.1
        }
        
        # Time-based activity recommendations
        self.time_based_preferences = {
            TimeOfDay.EARLY_MORNING: {
                'preferred_activities': ['sunrise viewing', 'quiet walks', 'meditation'],
                'indoor_outdoor_ratio': 0.3,  # 30% indoor preference
                'energy_level': 'low'
            },
            TimeOfDay.MORNING: {
                'preferred_activities': ['sightseeing', 'museums', 'markets'],
                'indoor_outdoor_ratio': 0.5,
                'energy_level': 'medium'
            },
            TimeOfDay.AFTERNOON: {
                'preferred_activities': ['outdoor activities', 'sports', 'adventure'],
                'indoor_outdoor_ratio': 0.2,
                'energy_level': 'high'
            },
            TimeOfDay.EVENING: {
                'preferred_activities': ['dining', 'entertainment', 'cultural shows'],
                'indoor_outdoor_ratio': 0.7,
                'energy_level': 'medium'
            },
            TimeOfDay.NIGHT: {
                'preferred_activities': ['nightlife', 'indoor entertainment', 'rest'],
                'indoor_outdoor_ratio': 0.8,
                'energy_level': 'low'
            }
        }
        
        # Weather-based recommendations
        self.weather_preferences = {
            WeatherCondition.CLEAR: {
                'outdoor_boost': 0.8,
                'recommended_activities': ['hiking', 'sightseeing', 'outdoor sports'],
                'avoid_activities': []
            },
            WeatherCondition.CLOUDY: {
                'outdoor_boost': 0.6,
                'recommended_activities': ['walking tours', 'photography', 'markets'],
                'avoid_activities': ['beach activities']
            },
            WeatherCondition.RAINY: {
                'outdoor_boost': 0.1,
                'recommended_activities': ['museums', 'cafes', 'indoor entertainment'],
                'avoid_activities': ['hiking', 'outdoor sports', 'beach']
            },
            WeatherCondition.STORMY: {
                'outdoor_boost': 0.0,
                'recommended_activities': ['hotels', 'malls', 'indoor attractions'],
                'avoid_activities': ['any outdoor activity']
            }
        }
        
        # Initialize location profiles
        self._initialize_location_profiles()
        
        # Load existing data
        self._load_data()
    
    def _initialize_location_profiles(self):
        """Initialize contextual profiles for available locations/models"""
        
        # Profile for 3D models with contextual suitability
        model_profiles = {
            'Walking.fbx': {
                'weather_suitability': {
                    WeatherCondition.CLEAR: 0.9,
                    WeatherCondition.CLOUDY: 0.8,
                    WeatherCondition.RAINY: 0.3,
                    WeatherCondition.STORMY: 0.1
                },
                'time_suitability': {
                    TimeOfDay.EARLY_MORNING: 0.8,
                    TimeOfDay.MORNING: 0.9,
                    TimeOfDay.AFTERNOON: 0.9,
                    TimeOfDay.EVENING: 0.7,
                    TimeOfDay.NIGHT: 0.3
                },
                'seasonal_preference': [Season.SPRING, Season.SUMMER, Season.FALL],
                'indoor_outdoor': 'outdoor',
                'optimal_temperature_range': (15, 30),  # Celsius
                'crowd_tolerance': 'medium',
                'accessibility': 'easy',
                'duration_minutes': 30,
                'activity_type': 'walking_exercise'
            },
            'Running.fbx': {
                'weather_suitability': {
                    WeatherCondition.CLEAR: 0.95,
                    WeatherCondition.CLOUDY: 0.9,
                    WeatherCondition.RAINY: 0.2,
                    WeatherCondition.STORMY: 0.0
                },
                'time_suitability': {
                    TimeOfDay.EARLY_MORNING: 0.9,
                    TimeOfDay.MORNING: 0.8,
                    TimeOfDay.AFTERNOON: 0.6,
                    TimeOfDay.EVENING: 0.8,
                    TimeOfDay.NIGHT: 0.4
                },
                'seasonal_preference': [Season.SPRING, Season.SUMMER, Season.FALL],
                'indoor_outdoor': 'outdoor',
                'optimal_temperature_range': (10, 25),
                'crowd_tolerance': 'low',
                'accessibility': 'moderate',
                'duration_minutes': 45,
                'activity_type': 'running_exercise'
            },
            'Idle.fbx': {
                'weather_suitability': {
                    WeatherCondition.CLEAR: 0.7,
                    WeatherCondition.CLOUDY: 0.8,
                    WeatherCondition.RAINY: 0.9,
                    WeatherCondition.STORMY: 0.9
                },
                'time_suitability': {
                    TimeOfDay.EARLY_MORNING: 0.6,
                    TimeOfDay.MORNING: 0.5,
                    TimeOfDay.AFTERNOON: 0.4,
                    TimeOfDay.EVENING: 0.8,
                    TimeOfDay.NIGHT: 0.9
                },
                'seasonal_preference': [Season.WINTER, Season.FALL],
                'indoor_outdoor': 'indoor',
                'optimal_temperature_range': (18, 26),
                'crowd_tolerance': 'high',
                'accessibility': 'easy',
                'duration_minutes': 60,
                'activity_type': 'relaxation'
            },
            'Man.fbx': {
                'weather_suitability': {
                    WeatherCondition.CLEAR: 0.6,
                    WeatherCondition.CLOUDY: 0.7,
                    WeatherCondition.RAINY: 0.8,
                    WeatherCondition.STORMY: 0.8
                },
                'time_suitability': {
                    TimeOfDay.EARLY_MORNING: 0.5,
                    TimeOfDay.MORNING: 0.7,
                    TimeOfDay.AFTERNOON: 0.8,
                    TimeOfDay.EVENING: 0.7,
                    TimeOfDay.NIGHT: 0.6
                },
                'seasonal_preference': [Season.SPRING, Season.SUMMER, Season.FALL, Season.WINTER],
                'indoor_outdoor': 'flexible',
                'optimal_temperature_range': (15, 30),
                'crowd_tolerance': 'medium',
                'accessibility': 'easy',
                'duration_minutes': 20,
                'activity_type': 'general_viewing'
            },
            'Man_Rig.fbx': {
                'weather_suitability': {
                    WeatherCondition.CLEAR: 0.5,
                    WeatherCondition.CLOUDY: 0.6,
                    WeatherCondition.RAINY: 0.8,
                    WeatherCondition.STORMY: 0.9
                },
                'time_suitability': {
                    TimeOfDay.EARLY_MORNING: 0.4,
                    TimeOfDay.MORNING: 0.7,
                    TimeOfDay.AFTERNOON: 0.9,
                    TimeOfDay.EVENING: 0.8,
                    TimeOfDay.NIGHT: 0.7
                },
                'seasonal_preference': [Season.SPRING, Season.SUMMER, Season.FALL, Season.WINTER],
                'indoor_outdoor': 'indoor',
                'optimal_temperature_range': (18, 28),
                'crowd_tolerance': 'low',
                'accessibility': 'easy',
                'duration_minutes': 40,
                'activity_type': 'technical_study'
            }
        }
        
        self.location_profiles.update(model_profiles)
    
    def _load_data(self):
        """Load existing contextual data"""
        try:
            profiles_file = self.storage_dir / "location_profiles.json"
            if profiles_file.exists():
                with open(profiles_file, 'r') as f:
                    saved_profiles = json.load(f)
                    # Merge with initialized profiles
                    self.location_profiles.update(saved_profiles)
        except Exception as e:
            print(f"Error loading contextual data: {e}")
    
    def _save_data(self):
        """Save contextual data"""
        try:
            # Convert enums to strings for JSON serialization
            serializable_profiles = {}
            for location_id, profile in self.location_profiles.items():
                serializable_profile = {}
                for key, value in profile.items():
                    if isinstance(value, dict):
                        # Handle enum keys in dictionaries
                        serializable_dict = {}
                        for k, v in value.items():
                            if hasattr(k, 'value'):
                                serializable_dict[k.value] = v
                            else:
                                serializable_dict[k] = v
                        serializable_profile[key] = serializable_dict
                    elif isinstance(value, list):
                        # Handle enum values in lists
                        serializable_list = []
                        for item in value:
                            if hasattr(item, 'value'):
                                serializable_list.append(item.value)
                            else:
                                serializable_list.append(item)
                        serializable_profile[key] = serializable_list
                    else:
                        serializable_profile[key] = value
                
                serializable_profiles[location_id] = serializable_profile
            
            with open(self.storage_dir / "location_profiles.json", 'w') as f:
                json.dump(serializable_profiles, f, indent=2)
        except Exception as e:
            print(f"Error saving contextual data: {e}")
    
    def get_current_context(self, location: Dict[str, Any] = None, 
                          weather_override: Dict[str, Any] = None) -> ContextualFactors:
        """Get current contextual factors"""
        
        now = datetime.now()
        
        # Determine time of day
        hour = now.hour
        if 5 <= hour < 8:
            time_of_day = TimeOfDay.EARLY_MORNING
        elif 8 <= hour < 12:
            time_of_day = TimeOfDay.MORNING
        elif 12 <= hour < 17:
            time_of_day = TimeOfDay.AFTERNOON
        elif 17 <= hour < 20:
            time_of_day = TimeOfDay.EVENING
        else:
            time_of_day = TimeOfDay.NIGHT
        
        # Determine season (Northern Hemisphere)
        month = now.month
        if month in [3, 4, 5]:
            season = Season.SPRING
        elif month in [6, 7, 8]:
            season = Season.SUMMER
        elif month in [9, 10, 11]:
            season = Season.FALL
        else:
            season = Season.WINTER
        
        # Get weather (mock data or from API)
        weather_data = self._get_weather_data(location, weather_override)
        
        # Get special events (mock for now)
        special_events = self._get_special_events(now, location)
        
        # Estimate crowd level based on time and day
        crowd_level = self._estimate_crowd_level(now)
        
        return ContextualFactors(
            timestamp=now.isoformat(),
            local_time=now,
            time_of_day=time_of_day,
            season=season,
            weather_condition=weather_data['condition'],
            temperature=weather_data['temperature'],
            humidity=weather_data['humidity'],
            wind_speed=weather_data['wind_speed'],
            precipitation_chance=weather_data['precipitation_chance'],
            uv_index=weather_data['uv_index'],
            air_quality_index=weather_data.get('air_quality'),
            location=location or {'city': 'Bangkok', 'country': 'Thailand'},
            special_events=special_events,
            crowd_level=crowd_level,
            accessibility_factors={}
        )
    
    def _get_weather_data(self, location: Dict[str, Any] = None, 
                         weather_override: Dict[str, Any] = None) -> Dict[str, Any]:
        """Get weather data (mock implementation)"""
        
        if weather_override:
            return weather_override
        
        # Mock weather data for demonstration
        # In production, this would call a real weather API
        import random
        
        conditions = [WeatherCondition.CLEAR, WeatherCondition.CLOUDY, 
                     WeatherCondition.RAINY]
        
        return {
            'condition': random.choice(conditions),
            'temperature': random.uniform(20, 35),  # Typical Bangkok temperature
            'humidity': random.uniform(60, 90),
            'wind_speed': random.uniform(5, 20),
            'precipitation_chance': random.uniform(0, 40),
            'uv_index': random.uniform(3, 11),
            'air_quality': random.randint(50, 150)
        }
    
    def _get_special_events(self, current_time: datetime, 
                          location: Dict[str, Any] = None) -> List[str]:
        """Get special events for current time/location"""
        
        events = []
        
        # Check for holidays/festivals (simplified)
        month_day = f"{current_time.month:02d}-{current_time.day:02d}"
        
        thai_events = {
            "01-01": "New Year's Day",
            "02-14": "Valentine's Day",
            "04-13": "Songkran Festival",
            "05-01": "Labour Day",
            "12-25": "Christmas Day",
            "12-31": "New Year's Eve"
        }
        
        if month_day in thai_events:
            events.append(thai_events[month_day])
        
        # Check for weekly patterns
        weekday = current_time.weekday()
        if weekday in [5, 6]:  # Weekend
            events.append("Weekend")
        
        return events
    
    def _estimate_crowd_level(self, current_time: datetime) -> str:
        """Estimate crowd level based on time patterns"""
        
        hour = current_time.hour
        weekday = current_time.weekday()
        
        # Weekend is generally more crowded
        if weekday in [5, 6]:
            if 10 <= hour <= 18:
                return "high"
            elif 8 <= hour <= 20:
                return "medium"
            else:
                return "low"
        else:
            # Weekday patterns
            if 12 <= hour <= 14 or 17 <= hour <= 19:  # Lunch and after work
                return "medium"
            elif 9 <= hour <= 16:
                return "low"
            else:
                return "low"
    
    def generate_contextual_recommendations(self, 
                                          available_locations: List[str],
                                          user_preferences: Dict[str, Any] = None,
                                          context_override: ContextualFactors = None,
                                          top_k: int = 5) -> List[ContextualRecommendation]:
        """Generate contextually-aware recommendations"""
        
        # Get current context
        context = context_override or self.get_current_context()
        
        recommendations = []
        
        for location_id in available_locations:
            if location_id not in self.location_profiles:
                continue
            
            profile = self.location_profiles[location_id]
            
            # Calculate contextual suitability score
            suitability_score = self._calculate_contextual_suitability(
                profile, context, user_preferences
            )
            
            if suitability_score > 0.1:  # Only include reasonably suitable options
                
                # Generate contextual reasons
                reasons = self._generate_contextual_reasons(profile, context)
                
                # Determine optimal time window
                optimal_window = self._determine_optimal_time_window(profile, context)
                
                # Get special considerations
                considerations = self._get_special_considerations(profile, context)
                
                recommendation = ContextualRecommendation(
                    location_id=location_id,
                    location_name=location_id.replace('.fbx', '').replace('_', ' ').title(),
                    recommendation_type='model',
                    suitability_score=suitability_score,
                    contextual_reasons=reasons,
                    optimal_time_window=optimal_window,
                    weather_dependency=profile.get('indoor_outdoor', 'flexible'),
                    seasonal_preference=profile.get('seasonal_preference', []),
                    crowd_tolerance=profile.get('crowd_tolerance', 'medium'),
                    accessibility_level=profile.get('accessibility', 'easy'),
                    estimated_duration=profile.get('duration_minutes', 30),
                    special_considerations=considerations
                )
                
                recommendations.append(recommendation)
        
        # Sort by suitability score and return top_k
        recommendations.sort(key=lambda x: x.suitability_score, reverse=True)
        return recommendations[:top_k]
    
    def _calculate_contextual_suitability(self, 
                                        profile: Dict[str, Any],
                                        context: ContextualFactors,
                                        user_preferences: Dict[str, Any] = None) -> float:
        """Calculate how suitable a location is given current context"""
        
        total_score = 0.0
        
        # Weather suitability
        weather_scores = profile.get('weather_suitability', {})
        weather_score = weather_scores.get(context.weather_condition, 0.5)
        total_score += weather_score * self.contextual_weights['weather_match']
        
        # Time suitability
        time_scores = profile.get('time_suitability', {})
        time_score = time_scores.get(context.time_of_day, 0.5)
        total_score += time_score * self.contextual_weights['time_suitability']
        
        # Seasonal preference
        seasonal_preferences = profile.get('seasonal_preference', [])
        if context.season in seasonal_preferences:
            seasonal_score = 1.0
        elif len(seasonal_preferences) == 0:
            seasonal_score = 0.7  # Neutral
        else:
            seasonal_score = 0.3  # Off-season
        total_score += seasonal_score * self.contextual_weights['seasonal_preference']
        
        # Crowd preference matching
        profile_crowd_tolerance = profile.get('crowd_tolerance', 'medium')
        crowd_match_score = self._calculate_crowd_match(
            profile_crowd_tolerance, context.crowd_level
        )
        total_score += crowd_match_score * self.contextual_weights['crowd_preference']
        
        # Temperature suitability
        temp_range = profile.get('optimal_temperature_range', (0, 50))
        if temp_range[0] <= context.temperature <= temp_range[1]:
            temp_score = 1.0
        else:
            # Gradual degradation outside optimal range
            if context.temperature < temp_range[0]:
                temp_score = max(0.0, 1.0 - (temp_range[0] - context.temperature) / 10)
            else:
                temp_score = max(0.0, 1.0 - (context.temperature - temp_range[1]) / 10)
            
        total_score *= temp_score  # Temperature is a multiplier
        
        # Rain penalty for outdoor activities
        if (profile.get('indoor_outdoor') == 'outdoor' and 
            context.weather_condition == WeatherCondition.RAINY):
            total_score *= 0.3
        
        # Special event boost
        if context.special_events:
            activity_type = profile.get('activity_type', '')
            if any(event.lower() in activity_type.lower() for event in context.special_events):
                total_score *= 1.2
        
        return min(1.0, total_score)
    
    def _calculate_crowd_match(self, tolerance: str, current_level: str) -> float:
        """Calculate how well crowd levels match user tolerance"""
        
        tolerance_scores = {
            'low': {'low': 1.0, 'medium': 0.5, 'high': 0.2},
            'medium': {'low': 0.8, 'medium': 1.0, 'high': 0.6},
            'high': {'low': 0.6, 'medium': 0.8, 'high': 1.0}
        }
        
        return tolerance_scores.get(tolerance, {}).get(current_level, 0.5)
    
    def _generate_contextual_reasons(self, profile: Dict[str, Any], 
                                   context: ContextualFactors) -> List[str]:
        """Generate human-readable reasons for recommendation"""
        
        reasons = []
        
        # Weather-based reasons
        weather_condition = context.weather_condition
        if weather_condition == WeatherCondition.CLEAR:
            if profile.get('indoor_outdoor') == 'outdoor':
                reasons.append("Perfect clear weather for outdoor activities")
        elif weather_condition == WeatherCondition.RAINY:
            if profile.get('indoor_outdoor') == 'indoor':
                reasons.append("Great indoor option during rainy weather")
        
        # Time-based reasons
        time_of_day = context.time_of_day
        time_prefs = self.time_based_preferences.get(time_of_day, {})
        activity_type = profile.get('activity_type', '')
        
        preferred_activities = time_prefs.get('preferred_activities', [])
        if any(activity in activity_type for activity in preferred_activities):
            reasons.append(f"Ideal for {time_of_day.value.replace('_', ' ')} activities")
        
        # Temperature reasons
        temp_range = profile.get('optimal_temperature_range', (0, 50))
        if temp_range[0] <= context.temperature <= temp_range[1]:
            reasons.append(f"Optimal temperature ({context.temperature:.1f}°C) for this activity")
        
        # Crowd reasons
        if context.crowd_level == 'low' and profile.get('crowd_tolerance') == 'low':
            reasons.append("Low crowd levels - perfect for peaceful experience")
        
        # Seasonal reasons
        if context.season in profile.get('seasonal_preference', []):
            reasons.append(f"Recommended for {context.season.value} season")
        
        # Special event reasons
        if context.special_events:
            for event in context.special_events:
                if event.lower() != 'weekend':
                    reasons.append(f"Special consideration for {event}")
        
        # Default reason if none generated
        if not reasons:
            reasons.append("Suitable based on current conditions")
        
        return reasons[:3]  # Limit to top 3 reasons
    
    def _determine_optimal_time_window(self, profile: Dict[str, Any], 
                                     context: ContextualFactors) -> Tuple[int, int]:
        """Determine optimal time window for activity"""
        
        time_suitability = profile.get('time_suitability', {})
        
        # Find the time periods with highest suitability scores
        best_times = []
        for time_period, score in time_suitability.items():
            if score >= 0.7:  # High suitability threshold
                best_times.append(time_period)
        
        if not best_times:
            # Return current time as fallback
            current_hour = context.local_time.hour
            return (current_hour, current_hour + 2)
        
        # Convert time periods to hour ranges
        time_ranges = {
            TimeOfDay.EARLY_MORNING: (5, 8),
            TimeOfDay.MORNING: (8, 12),
            TimeOfDay.AFTERNOON: (12, 17),
            TimeOfDay.EVENING: (17, 20),
            TimeOfDay.NIGHT: (20, 24)
        }
        
        # Return the first optimal range
        return time_ranges.get(best_times[0], (9, 17))
    
    def _get_special_considerations(self, profile: Dict[str, Any], 
                                  context: ContextualFactors) -> List[str]:
        """Get special considerations based on context"""
        
        considerations = []
        
        # Weather considerations
        if context.weather_condition == WeatherCondition.RAINY:
            considerations.append("Bring umbrella or rainwear")
        elif context.weather_condition == WeatherCondition.STORMY:
            considerations.append("Consider postponing until weather improves")
        
        # Temperature considerations
        if context.temperature > 35:
            considerations.append("Very hot - stay hydrated and seek shade")
        elif context.temperature < 15:
            considerations.append("Cool weather - dress warmly")
        
        # UV considerations
        if context.uv_index > 8:
            considerations.append("High UV - use sunscreen and protective clothing")
        
        # Humidity considerations
        if context.humidity > 80:
            considerations.append("High humidity - take breaks and stay hydrated")
        
        # Crowd considerations
        if context.crowd_level == 'high':
            considerations.append("Expect crowds - arrive early or consider alternative times")
        
        # Air quality considerations
        if context.air_quality_index and context.air_quality_index > 150:
            considerations.append("Poor air quality - consider indoor alternatives")
        
        return considerations
    
    def get_time_specific_recommendations(self, target_time: datetime,
                                        available_locations: List[str],
                                        scenario: str = None) -> List[ContextualRecommendation]:
        """Get recommendations for a specific time scenario"""
        
        # Create mock context for target time
        target_context = self.get_current_context()
        target_context.local_time = target_time
        
        # Update time of day
        hour = target_time.hour
        if 5 <= hour < 8:
            target_context.time_of_day = TimeOfDay.EARLY_MORNING
        elif 8 <= hour < 12:
            target_context.time_of_day = TimeOfDay.MORNING
        elif 12 <= hour < 17:
            target_context.time_of_day = TimeOfDay.AFTERNOON
        elif 17 <= hour < 20:
            target_context.time_of_day = TimeOfDay.EVENING
        else:
            target_context.time_of_day = TimeOfDay.NIGHT
        
        # Apply scenario-specific modifications
        if scenario:
            target_context = self._apply_scenario(target_context, scenario)
        
        return self.generate_contextual_recommendations(
            available_locations, context_override=target_context
        )
    
    def _apply_scenario(self, context: ContextualFactors, scenario: str) -> ContextualFactors:
        """Apply scenario-specific context modifications"""
        
        scenario_lower = scenario.lower()
        
        if 'rainy' in scenario_lower or 'rain' in scenario_lower:
            context.weather_condition = WeatherCondition.RAINY
            context.precipitation_chance = 90
        
        if 'evening' in scenario_lower:
            context.time_of_day = TimeOfDay.EVENING
        
        if 'indoor' in scenario_lower:
            # Modify context to favor indoor activities
            if context.weather_condition == WeatherCondition.CLEAR:
                context.weather_condition = WeatherCondition.CLOUDY
        
        if 'cafe' in scenario_lower or 'coffee' in scenario_lower:
            context.time_of_day = TimeOfDay.MORNING
            context.weather_condition = WeatherCondition.CLOUDY
        
        return context
    
    def get_analytics(self) -> Dict[str, Any]:
        """Get analytics about contextual recommendations"""
        
        current_context = self.get_current_context()
        
        # Calculate average suitability scores for current context
        location_scores = {}
        for location_id, profile in self.location_profiles.items():
            score = self._calculate_contextual_suitability(profile, current_context)
            location_scores[location_id] = score
        
        return {
            'current_context': {
                'time_of_day': current_context.time_of_day.value,
                'season': current_context.season.value,
                'weather_condition': current_context.weather_condition.value,
                'temperature': current_context.temperature,
                'crowd_level': current_context.crowd_level
            },
            'location_suitability_scores': location_scores,
            'total_locations': len(self.location_profiles),
            'avg_suitability': sum(location_scores.values()) / len(location_scores) if location_scores else 0,
            'contextual_weights': self.contextual_weights,
            'last_updated': datetime.now().isoformat()
        }


# Initialize global contextual recommendation engine
contextual_engine = ContextualRecommendationEngine()