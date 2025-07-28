"""
Wikipedia Scraper
Fetches place information from Wikipedia
"""

import asyncio
import logging
from typing import Dict, List, Optional
import wikipedia
import requests

logger = logging.getLogger(__name__)

class WikipediaScraper:
    def __init__(self):
        # Set Wikipedia language
        wikipedia.set_lang("en")
    
    async def search_place(self, place_name: str, language: str = "en") -> Optional[Dict]:
        """
        Search for place information on Wikipedia
        
        Args:
            place_name: Name of the place to search
            language: Language preference
        
        Returns:
            Dictionary with Wikipedia information or None
        """
        try:
            # Set language for Wikipedia
            if language == "th":
                wikipedia.set_lang("th")
            else:
                wikipedia.set_lang("en")
            
            # Search for the place
            search_results = await asyncio.to_thread(
                wikipedia.search, place_name, results=3
            )
            
            if not search_results:
                logger.warning(f"No Wikipedia results found for: {place_name}")
                return None
            
            # Try to get page information for the best match
            for result in search_results:
                try:
                    page = await asyncio.to_thread(
                        wikipedia.page, result
                    )
                    
                    # Extract information
                    info = {
                        "title": page.title,
                        "summary": page.summary,
                        "url": page.url,
                        "images": self._filter_images(page.images[:5]),  # Limit to 5 images
                        "coordinates": getattr(page, 'coordinates', None)
                    }
                    
                    logger.info(f"Successfully fetched Wikipedia info for: {result}")
                    return info
                    
                except wikipedia.exceptions.DisambiguationError as e:
                    # Try the first option from disambiguation
                    try:
                        page = await asyncio.to_thread(
                            wikipedia.page, e.options[0]
                        )
                        info = {
                            "title": page.title,
                            "summary": page.summary,
                            "url": page.url,
                            "images": self._filter_images(page.images[:5]),
                            "coordinates": getattr(page, 'coordinates', None)
                        }
                        return info
                    except:
                        continue
                        
                except wikipedia.exceptions.PageError:
                    continue
                except Exception as e:
                    logger.error(f"Error fetching page {result}: {e}")
                    continue
            
            logger.warning(f"Could not fetch detailed info for: {place_name}")
            return None
            
        except Exception as e:
            logger.error(f"Wikipedia search failed for {place_name}: {e}")
            return None
    
    def _filter_images(self, images: List[str]) -> List[str]:
        """Filter and validate image URLs"""
        valid_images = []
        
        for img_url in images:
            try:
                # Basic URL validation
                if img_url and isinstance(img_url, str):
                    # Check if it's a valid image URL
                    if any(ext in img_url.lower() for ext in ['.jpg', '.jpeg', '.png', '.gif']):
                        # Avoid certain unwanted images
                        skip_keywords = ['commons-logo', 'wikimedia', 'edit-icon']
                        if not any(keyword in img_url.lower() for keyword in skip_keywords):
                            valid_images.append(img_url)
                
                # Limit to 3 images to avoid overwhelming the response
                if len(valid_images) >= 3:
                    break
                    
            except Exception as e:
                logger.warning(f"Error processing image URL {img_url}: {e}")
                continue
        
        return valid_images
    
    async def get_coordinates(self, place_name: str) -> Optional[tuple]:
        """Get coordinates for a place from Wikipedia"""
        try:
            info = await self.search_place(place_name)
            if info and info.get("coordinates"):
                return info["coordinates"]
        except Exception as e:
            logger.error(f"Error getting coordinates: {e}")
        
        return None