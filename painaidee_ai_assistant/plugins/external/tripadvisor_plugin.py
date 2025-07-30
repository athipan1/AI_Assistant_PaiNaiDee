"""
TripAdvisor/Google Reviews Plugin for tourist reviews and ratings
"""

import asyncio
import json
import logging
from datetime import datetime
from typing import Dict, Any, List

import aiohttp
from ..base import PluginInterface, PluginConfig, PluginResponse

logger = logging.getLogger(__name__)


class TripAdvisorPlugin(PluginInterface):
    """Plugin for fetching tourist reviews and attraction ratings"""
    
    def __init__(self, config: PluginConfig):
        super().__init__(config)
        self.session: aiohttp.ClientSession = None
        
    async def initialize(self) -> bool:
        """Initialize the plugin"""
        try:
            self.session = aiohttp.ClientSession(
                timeout=aiohttp.ClientTimeout(total=self.config.timeout),
                headers=self.config.headers
            )
            self.status = self.status.ACTIVE
            logger.info("TripAdvisor plugin initialized successfully")
            return True
        except Exception as e:
            logger.error(f"Failed to initialize TripAdvisor plugin: {e}")
            self.status = self.status.ERROR
            return False
            
    async def cleanup(self) -> None:
        """Cleanup plugin resources"""
        if self.session:
            await self.session.close()
        await super().cleanup()
        
    async def execute(self, intent: str, parameters: Dict[str, Any]) -> PluginResponse:
        """Execute TripAdvisor API request"""
        try:
            if intent == "attractions":
                return await self._get_latest_attractions(parameters)
            elif intent == "reviews":
                return await self._get_reviews(parameters)
            else:
                # For demo purposes, return mock data
                return await self._get_mock_data(intent, parameters)
                
        except Exception as e:
            return PluginResponse(
                plugin_name=self.name,
                success=False,
                error=f"TripAdvisor plugin execution error: {str(e)}"
            )
            
    async def _get_latest_attractions(self, parameters: Dict[str, Any]) -> PluginResponse:
        """Get latest attractions for a province (mock implementation)"""
        province = parameters.get("province", "Bangkok")
        lang = parameters.get("lang", "en")
        
        # Mock data - in real implementation, this would call TripAdvisor API
        mock_attractions = [
            {
                "name": f"Top Attraction in {province}",
                "description": f"Highly rated tourist destination in {province}",
                "rating": 4.5,
                "review_count": 1250,
                "price_range": "$$",
                "category": "Cultural Site",
                "url": "https://tripadvisor.com/example",
                "timestamp": datetime.now().isoformat(),
                "photos": ["https://example.com/photo1.jpg"],
                "address": f"{province}, Thailand",
                "open_hours": "9:00 AM - 6:00 PM"
            },
            {
                "name": f"Hidden Gem in {province}",
                "description": f"Recently discovered beautiful spot in {province}",
                "rating": 4.8,
                "review_count": 89,
                "price_range": "$",
                "category": "Natural Wonder",
                "url": "https://tripadvisor.com/example2",
                "timestamp": datetime.now().isoformat(),
                "photos": ["https://example.com/photo2.jpg"],
                "address": f"{province}, Thailand",
                "open_hours": "24 Hours"
            }
        ]
        
        # Simulate API delay
        await asyncio.sleep(0.1)
        
        return PluginResponse(
            plugin_name=self.name,
            success=True,
            data=mock_attractions,
            metadata={
                "province": province,
                "language": lang,
                "source": "TripAdvisor API (Mock)",
                "total_results": len(mock_attractions),
                "api_version": "v1"
            }
        )
        
    async def _get_reviews(self, parameters: Dict[str, Any]) -> PluginResponse:
        """Get recent reviews for attractions"""
        location = parameters.get("location", parameters.get("province", "Bangkok"))
        lang = parameters.get("lang", "en")
        
        # Mock review data
        mock_reviews = [
            {
                "attraction_name": f"Popular Site in {location}",
                "reviewer_name": "Tourist123",
                "rating": 5,
                "review_text": "Amazing experience! Highly recommend visiting this place.",
                "review_date": "2024-07-25",
                "helpful_votes": 15,
                "photos": 3,
                "verified_review": True,
                "traveler_type": "Family"
            },
            {
                "attraction_name": f"Cultural Center {location}",
                "reviewer_name": "Explorer_Jane",
                "rating": 4,
                "review_text": "Beautiful architecture and rich history. Worth the visit!",
                "review_date": "2024-07-20",
                "helpful_votes": 8,
                "photos": 1,
                "verified_review": True,
                "traveler_type": "Solo"
            }
        ]
        
        return PluginResponse(
            plugin_name=self.name,
            success=True,
            data=mock_reviews,
            metadata={
                "location": location,
                "language": lang,
                "source": "TripAdvisor Reviews (Mock)",
                "total_reviews": len(mock_reviews),
                "average_rating": 4.5
            }
        )
        
    async def _get_mock_data(self, intent: str, parameters: Dict[str, Any]) -> PluginResponse:
        """Generate mock data for any intent"""
        return PluginResponse(
            plugin_name=self.name,
            success=True,
            data=[{
                "message": f"TripAdvisor plugin mock response for intent: {intent}",
                "parameters_received": parameters,
                "note": "This is a mock response. In production, this would fetch real TripAdvisor data."
            }],
            metadata={
                "intent": intent,
                "source": "TripAdvisor Mock",
                "timestamp": datetime.now().isoformat()
            }
        )
        
    async def health_check(self) -> bool:
        """Check if TripAdvisor API is accessible"""
        try:
            # In real implementation, this would ping TripAdvisor API
            # For mock, just check if session exists
            return self.session is not None and not self.session.closed
        except Exception:
            return False


def create_tripadvisor_plugin() -> TripAdvisorPlugin:
    """Factory function to create TripAdvisor plugin with default config"""
    config = PluginConfig(
        name="tripadvisor",
        description="TripAdvisor/Google Reviews plugin for tourist reviews and ratings",
        version="1.0.0",
        enabled=True,
        timeout=30,
        cache_ttl=300,  # 5 minutes cache
        rate_limit=60,  # 60 requests per minute
        base_url="https://api.tripadvisor.com",  # Mock URL
        headers={
            "User-Agent": "PaiNaiDee-AI-Assistant/1.0",
            "Accept": "application/json"
        },
        intents=["attractions", "reviews", "tourist", "rating", "place"],
        schema={
            "type": "object",
            "properties": {
                "name": {"type": "string"},
                "rating": {"type": "number"},
                "review_count": {"type": "integer"},
                "description": {"type": "string"},
                "url": {"type": "string"}
            }
        }
    )
    
    return TripAdvisorPlugin(config)