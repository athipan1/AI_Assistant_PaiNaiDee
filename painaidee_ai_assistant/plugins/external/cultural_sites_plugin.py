"""
Cultural Sites Plugin for Department of Fine Arts data
"""

import asyncio
import json
import logging
from datetime import datetime
from typing import Dict, Any, List

import aiohttp
from ..base import PluginInterface, PluginConfig, PluginResponse

logger = logging.getLogger(__name__)


class CulturalSitesPlugin(PluginInterface):
    """Plugin for fetching historical and cultural site information from Department of Fine Arts"""
    
    def __init__(self, config: PluginConfig):
        super().__init__(config)
        self.session: aiohttp.ClientSession = None
        
        # Database of popular Thai temples and cultural sites
        self.cultural_database = {
            "wat phra kaew": {
                "th": {
                    "name": "วัดพระแก้ว",
                    "official_name": "วัดพระศรีรัตนศาสดาราม",
                    "description": "วัดหลวงที่สำคัญที่สุดในประเทศไทย ตั้งอยู่ในพระบรมมหาราชวัง",
                    "history": "สร้างขึ้นในสมัยรัชกาลที่ 1 เพื่อเป็นที่ประดิษฐานพระแก้วมรกต",
                    "significance": "เป็นวัดหลวงและเป็นสัญลักษณ์สำคัญของชาติไทย",
                    "architecture": "สถาปัตยกรรมไทยแบบดั้งเดิมผสมผสานกับศิลปะจากยุคต่างๆ",
                    "artifacts": ["พระแก้วมรกต", "ภาพจิตรกรรมฝาผนัง", "พระพุทธรูปโบราณ"]
                },
                "en": {
                    "name": "Wat Phra Kaew",
                    "official_name": "Temple of the Emerald Buddha",
                    "description": "The most sacred Buddhist temple in Thailand, located within the Grand Palace complex",
                    "history": "Built during the reign of King Rama I to house the Emerald Buddha",
                    "significance": "Royal temple and important national symbol of Thailand",
                    "architecture": "Traditional Thai architecture combined with artistic elements from various periods",
                    "artifacts": ["Emerald Buddha", "Mural paintings", "Ancient Buddha statues"]
                },
                "location": {
                    "province": "Bangkok",
                    "district": "Phra Nakhon",
                    "coordinates": {"lat": 13.7500, "lng": 100.4917},
                    "address": "Na Phra Lan Road, Phra Borom Maha Ratchawang, Phra Nakhon, Bangkok 10200"
                },
                "visiting_info": {
                    "open_hours": "8:30 AM - 3:30 PM",
                    "ticket_price": "500 THB",
                    "dress_code": "Formal attire required",
                    "photography": "Limited areas only"
                }
            },
            "wat arun": {
                "th": {
                    "name": "วัดอรุณ",
                    "official_name": "วัดอรุณราชวราราม",
                    "description": "วัดที่มีเจดีย์สูงเป็นสัญลักษณ์ริมแม่น้ำเจ้าพระยา",
                    "history": "สร้างในสมัยอยุธยา ปรับปรุงในสมัยรัชกาลที่ 2",
                    "significance": "วัดที่สวยงามริมแม่น้ำเจ้าพระยา เป็นสัญลักษณ์ของกรุงเทพฯ",
                    "architecture": "เจดีย์สไตล์เขมรผสมไทย ประดับด้วยเศษกระเบื้องและเครื่องถ้วยจีน",
                    "artifacts": ["พระปรางค์หลัก", "รูปปั้นยักษ์", "พระพุทธรูปหลวงพ่อโต"]
                },
                "en": {
                    "name": "Wat Arun",
                    "official_name": "Temple of Dawn",
                    "description": "Famous temple with towering spire along the Chao Phraya River",
                    "history": "Built during Ayutthaya period, renovated during reign of King Rama II",
                    "significance": "Beautiful riverside temple and symbol of Bangkok",
                    "architecture": "Khmer-style tower decorated with ceramic shards and Chinese porcelain",
                    "artifacts": ["Main Prang Tower", "Giant Guardian Statues", "Luang Pho To Buddha"]
                },
                "location": {
                    "province": "Bangkok",
                    "district": "Bangkok Yai",
                    "coordinates": {"lat": 13.7436, "lng": 100.4886},
                    "address": "158 Thanon Wang Doem, Wat Arun, Bangkok Yai, Bangkok 10600"
                },
                "visiting_info": {
                    "open_hours": "8:00 AM - 6:00 PM",
                    "ticket_price": "100 THB",
                    "dress_code": "Conservative dress required",
                    "photography": "Allowed with restrictions"
                }
            },
            "wat pho": {
                "th": {
                    "name": "วัดโพธิ์",
                    "official_name": "วัดพระเชตุพนวิมลมังคลาราม",
                    "description": "วัดโบราณที่มีพระพุทธไสยาสน์ใหญ่ที่สุดในประเทศไทย",
                    "history": "สร้างในสมัยอยุธยา เป็นมหาวิทยาลยแรกของไทย",
                    "significance": "ศูนย์กลางการเรียนรู้การแพทย์แผนไทยและการนวด",
                    "architecture": "สถาปัตยกรรมไทยโบราณ มีเจดีย์และพระอุโบสถหลายหลัง",
                    "artifacts": ["พระพุทธไสยาสน์", "เจดีย์สี่องค์", "หินประกับ 108 ใบ"]
                },
                "en": {
                    "name": "Wat Pho",
                    "official_name": "Temple of the Reclining Buddha",
                    "description": "Ancient temple famous for the largest reclining Buddha statue in Thailand",
                    "history": "Built during Ayutthaya period, considered Thailand's first university",
                    "significance": "Center for traditional Thai medicine and massage",
                    "architecture": "Ancient Thai architecture with multiple chedis and ordination halls",
                    "artifacts": ["Reclining Buddha", "Four Royal Chedis", "108 Bronze Bowls"]
                },
                "location": {
                    "province": "Bangkok",
                    "district": "Phra Nakhon",
                    "coordinates": {"lat": 13.7465, "lng": 100.4927},
                    "address": "2 Sanamchai Road, Grand Palace Subdistrict, Phra Nakhon District, Bangkok 10200"
                },
                "visiting_info": {
                    "open_hours": "8:00 AM - 6:30 PM",
                    "ticket_price": "200 THB",
                    "dress_code": "Conservative dress required",
                    "photography": "Allowed with fee"
                }
            }
        }
        
    async def initialize(self) -> bool:
        """Initialize the plugin"""
        try:
            self.session = aiohttp.ClientSession(
                timeout=aiohttp.ClientTimeout(total=self.config.timeout),
                headers=self.config.headers
            )
            self.status = self.status.ACTIVE
            logger.info("Cultural Sites plugin initialized successfully")
            return True
        except Exception as e:
            logger.error(f"Failed to initialize Cultural Sites plugin: {e}")
            self.status = self.status.ERROR
            return False
            
    async def cleanup(self) -> None:
        """Cleanup plugin resources"""
        if self.session:
            await self.session.close()
        await super().cleanup()
        
    async def execute(self, intent: str, parameters: Dict[str, Any]) -> PluginResponse:
        """Execute Cultural Sites API request"""
        try:
            if intent == "cultural":
                return await self._get_temple_info(parameters)
            elif intent == "attractions":
                return await self._get_cultural_attractions(parameters)
            else:
                return await self._search_cultural_sites(intent, parameters)
                
        except Exception as e:
            return PluginResponse(
                plugin_name=self.name,
                success=False,
                error=f"Cultural Sites plugin execution error: {str(e)}"
            )
            
    async def _get_temple_info(self, parameters: Dict[str, Any]) -> PluginResponse:
        """Get specific temple information"""
        wat_name = parameters.get("wat_name", "").lower()
        lang = parameters.get("lang", "en")
        
        # Search in cultural database
        found_site = None
        for key, site_data in self.cultural_database.items():
            if wat_name in key or any(wat_name in name.lower() for name in [
                site_data[lang]["name"].lower(),
                site_data[lang]["official_name"].lower()
            ]):
                found_site = site_data
                break
        
        if found_site:
            # Return detailed information about the found temple
            site_info = found_site[lang].copy()
            site_info.update(found_site["location"])
            site_info.update(found_site["visiting_info"])
            
            result_data = [site_info]
        else:
            # Return general temple information if specific temple not found
            result_data = [{
                "message": f"Temple information for '{wat_name}' not found in database",
                "suggestion": "Try searching for popular temples like Wat Phra Kaew, Wat Arun, or Wat Pho",
                "available_temples": list(self.cultural_database.keys())
            }]
        
        # Simulate API delay
        await asyncio.sleep(0.1)
        
        return PluginResponse(
            plugin_name=self.name,
            success=True,
            data=result_data,
            metadata={
                "wat_name": wat_name,
                "language": lang,
                "source": "Department of Fine Arts (Mock)",
                "database_size": len(self.cultural_database),
                "search_type": "temple_info"
            }
        )
        
    async def _get_cultural_attractions(self, parameters: Dict[str, Any]) -> PluginResponse:
        """Get cultural attractions in a specific area"""
        province = parameters.get("province", parameters.get("location", "Bangkok"))
        lang = parameters.get("lang", "en")
        
        # Filter cultural sites by province
        matching_sites = []
        for site_data in self.cultural_database.values():
            if province.lower() in site_data["location"]["province"].lower():
                site_info = site_data[lang].copy()
                site_info.update({
                    "province": site_data["location"]["province"],
                    "district": site_data["location"]["district"],
                    "coordinates": site_data["location"]["coordinates"],
                    "open_hours": site_data["visiting_info"]["open_hours"],
                    "ticket_price": site_data["visiting_info"]["ticket_price"]
                })
                matching_sites.append(site_info)
        
        if not matching_sites:
            # Return mock data for other provinces
            matching_sites = [{
                "name": f"Cultural Site in {province}",
                "description": f"Important historical and cultural site located in {province}",
                "significance": f"Represents the rich cultural heritage of {province}",
                "open_hours": "8:00 AM - 5:00 PM",
                "ticket_price": "50-100 THB",
                "note": "This is mock data. Actual data would come from Department of Fine Arts database."
            }]
        
        return PluginResponse(
            plugin_name=self.name,
            success=True,
            data=matching_sites,
            metadata={
                "province": province,
                "language": lang,
                "source": "Department of Fine Arts Cultural Database (Mock)",
                "total_sites": len(matching_sites),
                "search_type": "cultural_attractions"
            }
        )
        
    async def _search_cultural_sites(self, intent: str, parameters: Dict[str, Any]) -> PluginResponse:
        """General cultural sites search"""
        query = parameters.get("query", intent)
        lang = parameters.get("lang", "en")
        
        # Simple keyword search across all cultural data
        matching_sites = []
        for site_data in self.cultural_database.values():
            site_text = " ".join([
                site_data[lang]["name"],
                site_data[lang]["description"],
                site_data[lang]["significance"]
            ]).lower()
            
            if any(keyword.lower() in site_text for keyword in query.split()):
                site_info = site_data[lang].copy()
                site_info.update(site_data["location"])
                matching_sites.append(site_info)
                
        if not matching_sites:
            matching_sites = [{
                "message": f"No cultural sites found matching: {query}",
                "suggestion": "Try searching for temples, museums, or historical sites",
                "popular_sites": ["Wat Phra Kaew", "Wat Arun", "Wat Pho"]
            }]
        
        return PluginResponse(
            plugin_name=self.name,
            success=True,
            data=matching_sites,
            metadata={
                "query": query,
                "language": lang,
                "source": "Cultural Sites Search (Mock)",
                "total_results": len(matching_sites),
                "search_type": "general_search"
            }
        )
        
    async def health_check(self) -> bool:
        """Check if Department of Fine Arts API is accessible"""
        try:
            return self.session is not None and not self.session.closed
        except Exception:
            return False


def create_cultural_sites_plugin() -> CulturalSitesPlugin:
    """Factory function to create Cultural Sites plugin with default config"""
    config = PluginConfig(
        name="cultural_sites",
        description="Department of Fine Arts plugin for historical and cultural site information",
        version="1.0.0",
        enabled=True,
        timeout=30,
        cache_ttl=1800,  # 30 minutes cache for cultural data
        rate_limit=120,  # 120 requests per minute
        base_url="https://api.finearts.go.th",  # Mock URL
        headers={
            "User-Agent": "PaiNaiDee-AI-Assistant/1.0",
            "Accept": "application/json",
            "Accept-Language": "th,en"
        },
        intents=["cultural", "history", "temple", "wat", "heritage", "museum", "art"],
        schema={
            "type": "object",
            "properties": {
                "name": {"type": "string"},
                "description": {"type": "string"},
                "history": {"type": "string"},
                "significance": {"type": "string"},
                "location": {"type": "object"},
                "visiting_info": {"type": "object"}
            }
        }
    )
    
    return CulturalSitesPlugin(config)