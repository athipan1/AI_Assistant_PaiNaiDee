"""
Trip Recommendation Module
Provides intelligent travel recommendations for Thai tourism
"""

import logging
from typing import Dict, Any, List, Optional
import asyncio
import random

logger = logging.getLogger(__name__)

class TripRecommender:
    """
    Trip recommendation system for Thai tourism
    """
    
    def __init__(self):
        # Sample trip data - in production this would come from a database
        self.trip_data = {
            "bangkok": {
                "th": {
                    "name": "กรุงเทพมหานคร",
                    "description": "เมืองหลวงที่เต็มไปด้วยวัฒนธรรม วัด และอาหารอร่อย",
                    "attractions": ["วัดพระแก้ว", "วัดอรุณ", "ตลาดจตุจักร", "สยามพารากอน"],
                    "food": ["ต้มยำกุ้ง", "ผัดไทย", "มันกะทิ", "ข้าวผัด"],
                    "tips": "ควรหลีกเลี่ยงชั่วโมงเร่งด่วน และใช้ BTS หรือ MRT ในการเดินทาง"
                },
                "en": {
                    "name": "Bangkok",
                    "description": "The vibrant capital city full of culture, temples, and delicious food",
                    "attractions": ["Grand Palace", "Wat Arun", "Chatuchak Market", "Siam Paragon"],
                    "food": ["Tom Yum Goong", "Pad Thai", "Mango Sticky Rice", "Fried Rice"],
                    "tips": "Avoid rush hours and use BTS or MRT for transportation"
                }
            },
            "chiang mai": {
                "th": {
                    "name": "เชียงใหม่",
                    "description": "เมืองโบราณล้านนา ล้อมรอบด้วยธรรมชาติและวัฒนธรรมท้องถิ่น",
                    "attractions": ["วัดพระธาตุดอยสุเทพ", "ย่านนิมมานเหมินท์", "วัดเจดีย์หลวง", "ตลาดวรรณพ"],
                    "food": ["ข้าวซอย", "แกงฮังเล", "ลาบ", "ส้าส่า"],
                    "tips": "ควรเช่ารถหรือมอเตอร์ไซค์เพื่อความสะดวกในการท่องเที่ยว"
                },
                "en": {
                    "name": "Chiang Mai",
                    "description": "Ancient Lanna city surrounded by nature and local culture",
                    "attractions": ["Doi Suthep Temple", "Nimmanhaemin Road", "Wat Chedi Luang", "Warorot Market"],
                    "food": ["Khao Soi", "Gaeng Hang Le", "Larb", "Sai Ua"],
                    "tips": "Consider renting a car or scooter for convenient sightseeing"
                }
            },
            "phuket": {
                "th": {
                    "name": "ภูเก็ต",
                    "description": "เกาะมุกของทะเลอันดามัน ด้วยหาดทรายขาวและน้ำทะเลใส",
                    "attractions": ["หาดป่าตอง", "บิ๊กพุทธา", "เก่าเมืองภูเก็ต", "เกาะพีพี"],
                    "food": ["แกงส้มปลา", "หอยทอด", "ก๋วยเตี๋ยวหอยทอด", "น้ำพริกกะปิ"],
                    "tips": "ช่วงเดือนพฤศจิกายน-เมษายนเป็นช่วงที่ดีที่สุดสำหรับการท่องเที่ยว"
                },
                "en": {
                    "name": "Phuket",
                    "description": "Pearl of the Andaman Sea with white sandy beaches and crystal clear waters",
                    "attractions": ["Patong Beach", "Big Buddha", "Phuket Old Town", "Phi Phi Islands"],
                    "food": ["Gaeng Som Pla", "Hoy Tod", "Kuay Teow Hoy Tod", "Nam Prik Gapi"],
                    "tips": "November to April is the best time to visit"
                }
            }
        }
        
        logger.info("Trip recommender initialized with sample data")
    
    async def get_trips(
        self,
        user_profile: Dict[str, Any],
        query: Optional[str] = None,
        language: str = "th"
    ) -> Dict[str, Any]:
        """
        Get trip recommendations based on user profile and query
        
        Args:
            user_profile: User preferences and profile data
            query: Optional search query
            language: Language for response ("th" or "en")
            
        Returns:
            Dictionary with trip recommendations
        """
        try:
            # Extract preferences from user profile
            interests = user_profile.get("interests", [])
            budget = user_profile.get("budget", "medium")
            duration = user_profile.get("duration", 3)  # days
            
            # If query contains specific location, prioritize it
            location_matches = self._find_location_matches(query or "")
            
            if location_matches:
                # Return specific location recommendations
                recommendations = []
                for location in location_matches[:3]:  # Max 3 recommendations
                    if location in self.trip_data:
                        rec = self._format_recommendation(location, language, user_profile)
                        recommendations.append(rec)
                
                return {
                    "recommendations": recommendations,
                    "total": len(recommendations),
                    "query": query,
                    "language": language,
                    "status": "success"
                }
            else:
                # General recommendations based on interests
                return await self._get_general_recommendations(user_profile, language)
                
        except Exception as e:
            logger.error(f"Error in get_trips: {str(e)}")
            return self._fallback_recommendations(language)
    
    def _find_location_matches(self, query: str) -> List[str]:
        """Find location matches in query text"""
        if not query:
            return []
        
        query_lower = query.lower()
        matches = []
        
        # Check for location keywords
        location_keywords = {
            "bangkok": ["bangkok", "กรุงเทพ", "บางกอก"],
            "chiang mai": ["chiang mai", "เชียงใหม่", "chiangmai"],
            "phuket": ["phuket", "ภูเก็ต", "puket"]
        }
        
        for location, keywords in location_keywords.items():
            if any(keyword in query_lower for keyword in keywords):
                matches.append(location)
        
        return matches
    
    def _format_recommendation(
        self,
        location: str,
        language: str,
        user_profile: Dict[str, Any]
    ) -> Dict[str, Any]:
        """Format a single location recommendation"""
        location_data = self.trip_data[location][language]
        
        # Customize recommendation based on user profile
        interests = user_profile.get("interests", [])
        duration = user_profile.get("duration", 3)
        
        # Select attractions based on interests
        all_attractions = location_data["attractions"]
        recommended_attractions = all_attractions[:min(duration, len(all_attractions))]
        
        return {
            "location": location_data["name"],
            "description": location_data["description"],
            "attractions": recommended_attractions,
            "food": location_data["food"][:3],  # Top 3 food items
            "tips": location_data["tips"],
            "duration": f"{duration} วัน" if language == "th" else f"{duration} days",
            "match_score": self._calculate_match_score(interests, location)
        }
    
    def _calculate_match_score(self, interests: List[str], location: str) -> float:
        """Calculate how well location matches user interests"""
        # Simple scoring based on location characteristics
        location_features = {
            "bangkok": ["culture", "food", "shopping", "temples", "nightlife"],
            "chiang mai": ["nature", "culture", "adventure", "temples", "mountains"],
            "phuket": ["beaches", "water sports", "nightlife", "islands", "relaxation"]
        }
        
        if not interests or location not in location_features:
            return 0.5  # Default score
        
        features = location_features[location]
        matches = sum(1 for interest in interests if interest.lower() in [f.lower() for f in features])
        
        return min(matches / len(interests), 1.0) if interests else 0.5
    
    async def _get_general_recommendations(
        self,
        user_profile: Dict[str, Any],
        language: str
    ) -> Dict[str, Any]:
        """Get general recommendations when no specific location is mentioned"""
        interests = user_profile.get("interests", [])
        recommendations = []
        
        # Score all locations based on user interests
        location_scores = []
        for location in self.trip_data.keys():
            score = self._calculate_match_score(interests, location)
            location_scores.append((location, score))
        
        # Sort by score and take top 3
        location_scores.sort(key=lambda x: x[1], reverse=True)
        
        for location, score in location_scores[:3]:
            rec = self._format_recommendation(location, language, user_profile)
            recommendations.append(rec)
        
        return {
            "recommendations": recommendations,
            "total": len(recommendations),
            "user_interests": interests,
            "language": language,
            "status": "success"
        }
    
    def _fallback_recommendations(self, language: str) -> Dict[str, Any]:
        """Provide fallback recommendations when main logic fails"""
        # Return a random popular destination
        location = random.choice(list(self.trip_data.keys()))
        default_profile = {"interests": [], "duration": 3}
        
        rec = self._format_recommendation(location, language, default_profile)
        
        return {
            "recommendations": [rec],
            "total": 1,
            "language": language,
            "status": "fallback"
        }
    
    async def get_location_details(self, location: str, language: str = "th") -> Dict[str, Any]:
        """Get detailed information about a specific location"""
        location_key = location.lower().replace(" ", " ")
        
        # Map common variations
        location_mapping = {
            "bangkok": "bangkok",
            "กรุงเทพ": "bangkok",
            "chiang mai": "chiang mai",
            "เชียงใหม่": "chiang mai",
            "phuket": "phuket",
            "ภูเก็ต": "phuket"
        }
        
        mapped_location = location_mapping.get(location_key)
        
        if mapped_location and mapped_location in self.trip_data:
            data = self.trip_data[mapped_location][language]
            return {
                "location": data["name"],
                "description": data["description"],
                "attractions": data["attractions"],
                "food": data["food"],
                "tips": data["tips"],
                "status": "success"
            }
        else:
            return {
                "error": f"Location '{location}' not found",
                "status": "not_found"
            }

def create_trip_recommender() -> TripRecommender:
    """Create and return trip recommender instance"""
    return TripRecommender()