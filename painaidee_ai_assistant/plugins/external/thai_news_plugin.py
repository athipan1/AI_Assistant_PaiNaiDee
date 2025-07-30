"""
Thai News Plugin for ThaiPBS and major news outlets
"""

import asyncio
import json
import logging
from datetime import datetime, timedelta
from typing import Dict, Any, List

import aiohttp
from ..base import PluginInterface, PluginConfig, PluginResponse

logger = logging.getLogger(__name__)


class ThaiNewsPlugin(PluginInterface):
    """Plugin for fetching travel and event news from Thai news sources"""
    
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
            logger.info("Thai News plugin initialized successfully")
            return True
        except Exception as e:
            logger.error(f"Failed to initialize Thai News plugin: {e}")
            self.status = self.status.ERROR
            return False
            
    async def cleanup(self) -> None:
        """Cleanup plugin resources"""
        if self.session:
            await self.session.close()
        await super().cleanup()
        
    async def execute(self, intent: str, parameters: Dict[str, Any]) -> PluginResponse:
        """Execute Thai News API request"""
        try:
            if intent == "news":
                return await self._get_event_news(parameters)
            elif intent == "events":
                return await self._get_travel_events(parameters)
            else:
                return await self._get_mock_news(intent, parameters)
                
        except Exception as e:
            return PluginResponse(
                plugin_name=self.name,
                success=False,
                error=f"Thai News plugin execution error: {str(e)}"
            )
            
    async def _get_event_news(self, parameters: Dict[str, Any]) -> PluginResponse:
        """Get latest travel and event news"""
        lang = parameters.get("lang", "th")
        category = parameters.get("category", "travel")
        
        # Mock news data - in real implementation, this would call ThaiPBS API
        if lang == "th":
            mock_news = [
                {
                    "title": "เทศกาลลอยกระทงสุดยิ่งใหญ่ที่สุขกรรม จังหวัดเชียงใหม่",
                    "summary": "การจัดงานเทศกาลลอยกระทงแบบดั้งเดิมที่จะจัดขึ้นในเดือนพฤศจิกายนนี้",
                    "content": "เชียงใหม่เตรียมจัดเทศกาลลอยกระทงใหญ่ที่สุดในภาคเหนือ พร้อมกิจกรรมวัฒนธรรมมากมาย",
                    "publish_date": (datetime.now() - timedelta(hours=2)).isoformat(),
                    "source": "ไทยพีบีเอส",
                    "category": "ท่องเที่ยว",
                    "location": "เชียงใหม่",
                    "url": "https://thaipbs.or.th/news/example1",
                    "tags": ["เทศกาล", "ลอยกระทง", "เชียงใหม่", "วัฒนธรรม"],
                    "image_url": "https://example.com/loy-krathong.jpg"
                },
                {
                    "title": "เปิดเส้นทางใหม่เชื่อมโยงอุทยานแห่งชาติเขาใหญ่",
                    "summary": "กรมอุทยานแห่งชาติเปิดเส้นทางธรรมชาติใหม่สำหรับนักท่องเที่ยว",
                    "content": "เส้นทางใหม่นี้จะให้นักท่องเที่ยวสัมผัสธรรมชาติอย่างใกล้ชิดและปลอดภัย",
                    "publish_date": (datetime.now() - timedelta(hours=6)).isoformat(),
                    "source": "กรมอุทยานแห่งชาติ",
                    "category": "ท่องเที่ยว",
                    "location": "เขาใหญ่",
                    "url": "https://dnp.go.th/news/example2",
                    "tags": ["อุทยาน", "เขาใหญ่", "ธรรมชาติ", "เส้นทางใหม่"],
                    "image_url": "https://example.com/khao-yai.jpg"
                }
            ]
        else:
            mock_news = [
                {
                    "title": "Grand Loy Krathong Festival Coming to Chiang Mai",
                    "summary": "Chiang Mai prepares for the largest traditional Loy Krathong festival in November",
                    "content": "Chiang Mai is organizing the biggest Loy Krathong festival in Northern Thailand with numerous cultural activities.",
                    "publish_date": (datetime.now() - timedelta(hours=2)).isoformat(),
                    "source": "Thai PBS",
                    "category": "Tourism",
                    "location": "Chiang Mai",
                    "url": "https://thaipbs.or.th/news/example1",
                    "tags": ["festival", "loy krathong", "chiang mai", "culture"],
                    "image_url": "https://example.com/loy-krathong.jpg"
                },
                {
                    "title": "New Nature Trail Opens at Khao Yai National Park",
                    "summary": "Department of National Parks opens new nature trail for tourists",
                    "content": "The new trail allows tourists to experience nature up close while ensuring safety.",
                    "publish_date": (datetime.now() - timedelta(hours=6)).isoformat(),
                    "source": "Department of National Parks",
                    "category": "Tourism",
                    "location": "Khao Yai",
                    "url": "https://dnp.go.th/news/example2",
                    "tags": ["national park", "khao yai", "nature", "new trail"],
                    "image_url": "https://example.com/khao-yai.jpg"
                }
            ]
        
        # Simulate API delay
        await asyncio.sleep(0.15)
        
        return PluginResponse(
            plugin_name=self.name,
            success=True,
            data=mock_news,
            metadata={
                "language": lang,
                "category": category,
                "source": "Thai News Sources (Mock)",
                "total_articles": len(mock_news),
                "last_updated": datetime.now().isoformat()
            }
        )
        
    async def _get_travel_events(self, parameters: Dict[str, Any]) -> PluginResponse:
        """Get upcoming travel events"""
        lang = parameters.get("lang", "th")
        location = parameters.get("location", "Thailand")
        
        # Mock event data
        if lang == "th":
            mock_events = [
                {
                    "event_name": "งานสัปดาห์วัฒนธรรมไทย",
                    "description": "งานแสดงวัฒนธรรมไทยและการแสดงดั้งเดิม",
                    "start_date": (datetime.now() + timedelta(days=7)).isoformat(),
                    "end_date": (datetime.now() + timedelta(days=14)).isoformat(),
                    "location": "สวนลุมพินี กรุงเทพฯ",
                    "organizer": "การท่องเที่ยวแห่งประเทศไทย",
                    "ticket_price": "ฟรี",
                    "website": "https://tat.or.th/events/culture-week",
                    "contact": "02-250-5500",
                    "highlights": ["การแสดงรำไทย", "อาหารไทย", "งานหัตถกรรม"]
                }
            ]
        else:
            mock_events = [
                {
                    "event_name": "Thai Culture Week",
                    "description": "Exhibition of Thai culture and traditional performances",
                    "start_date": (datetime.now() + timedelta(days=7)).isoformat(),
                    "end_date": (datetime.now() + timedelta(days=14)).isoformat(),
                    "location": "Lumpini Park, Bangkok",
                    "organizer": "Tourism Authority of Thailand",
                    "ticket_price": "Free",
                    "website": "https://tat.or.th/events/culture-week",
                    "contact": "02-250-5500",
                    "highlights": ["Thai Dance Performances", "Thai Food", "Handicrafts"]
                }
            ]
        
        return PluginResponse(
            plugin_name=self.name,
            success=True,
            data=mock_events,
            metadata={
                "language": lang,
                "location": location,
                "source": "Thai Events Database (Mock)",
                "total_events": len(mock_events),
                "search_period": "Next 30 days"
            }
        )
        
    async def _get_mock_news(self, intent: str, parameters: Dict[str, Any]) -> PluginResponse:
        """Generate mock news data for any intent"""
        return PluginResponse(
            plugin_name=self.name,
            success=True,
            data=[{
                "message": f"Thai News plugin mock response for intent: {intent}",
                "parameters_received": parameters,
                "note": "This is a mock response. In production, this would fetch real news from ThaiPBS and other sources."
            }],
            metadata={
                "intent": intent,
                "source": "Thai News Mock",
                "timestamp": datetime.now().isoformat()
            }
        )
        
    async def health_check(self) -> bool:
        """Check if news sources are accessible"""
        try:
            return self.session is not None and not self.session.closed
        except Exception:
            return False


def create_thai_news_plugin() -> ThaiNewsPlugin:
    """Factory function to create Thai News plugin with default config"""
    config = PluginConfig(
        name="thai_news",
        description="Thai news plugin for ThaiPBS and major news outlets",
        version="1.0.0",
        enabled=True,
        timeout=30,
        cache_ttl=600,  # 10 minutes cache for news
        rate_limit=30,  # 30 requests per minute
        base_url="https://api.thaipbs.or.th",  # Mock URL
        headers={
            "User-Agent": "PaiNaiDee-AI-Assistant/1.0",
            "Accept": "application/json",
            "Accept-Language": "th,en"
        },
        intents=["news", "event", "happening", "update", "current", "latest"],
        schema={
            "type": "object",
            "properties": {
                "title": {"type": "string"},
                "summary": {"type": "string"},
                "publish_date": {"type": "string"},
                "source": {"type": "string"},
                "url": {"type": "string"}
            }
        }
    )
    
    return ThaiNewsPlugin(config)