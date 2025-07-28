"""
Search Agent
Handles place information search and summarization using BART
"""

import asyncio
import logging
from typing import Dict, List
from transformers import AutoTokenizer, AutoModelForSeq2SeqLM
import torch

# Import scraping utilities
from scraping.wikipedia_scraper import WikipediaScraper
from scraping.maps_scraper import MapsScraper

logger = logging.getLogger(__name__)

class SearchAgent:
    def __init__(self):
        self.model_name = "facebook/bart-large-cnn"
        self.tokenizer = None
        self.model = None
        self.device = "cuda" if torch.cuda.is_available() else "cpu"
        self._model_loaded = False
        
        # Initialize scrapers
        self.wikipedia_scraper = WikipediaScraper()
        self.maps_scraper = MapsScraper()
        
        # Fallback data for popular Thai destinations
        self.fallback_data = {
            "bangkok": {
                "images": [
                    "https://images.unsplash.com/photo-1506905925346-21bda4d32df4",
                    "https://images.unsplash.com/photo-1555400143-e2e1f9fee56b"
                ],
                "description": "Bangkok, Thailand's capital, is a large city known for ornate shrines and vibrant street life. The boat-filled Chao Phraya River feeds its network of canals, flowing past the Rattanakosin royal district, home to opulent Grand Palace and its sacred Wat Phra Kaew Temple.",
                "rating": 4.5
            },
            "chiang mai": {
                "images": [
                    "https://images.unsplash.com/photo-1552550049-db097c9480d1",
                    "https://images.unsplash.com/photo-1551634979-c687fc655905"
                ],
                "description": "Chiang Mai is a city in mountainous northern Thailand. Its Old City area still retains vestiges of walls and moats from its history as a cultural and religious center. It's also home to hundreds of elaborate Buddhist temples.",
                "rating": 4.7
            },
            "phuket": {
                "images": [
                    "https://images.unsplash.com/photo-1506905925346-21bda4d32df4",
                    "https://images.unsplash.com/photo-1548574505-5e239809ee19"
                ],
                "description": "Phuket, a rainforested, mountainous island in the Andaman Sea, has some of Thailand's most popular beaches, mainly situated along the clear waters of the western shore. The island is home to many high-end seaside resorts, spas and restaurants.",
                "rating": 4.6
            }
        }
    
    async def _load_model(self):
        """Load the BART model (lazy loading)"""
        if self._model_loaded:
            return
            
        try:
            logger.info(f"Loading model {self.model_name}...")
            
            # For demo purposes, we'll mock the model loading
            # In production, you would load the actual BART model:
            # self.tokenizer = AutoTokenizer.from_pretrained(self.model_name)
            # self.model = AutoModelForSeq2SeqLM.from_pretrained(self.model_name)
            # self.model.to(self.device)
            
            # Simulate loading time
            await asyncio.sleep(0.1)
            self._model_loaded = True
            logger.info("BART model loaded successfully (mock)")
            
        except Exception as e:
            logger.warning(f"Failed to load model: {e}. Using fallback responses.")
            self._model_loaded = False
    
    async def search_place_info(self, place_name: str, language: str = "en") -> Dict:
        """
        Search and summarize information about a place
        
        Args:
            place_name: Name of the place to search
            language: Language preference
        
        Returns:
            Dictionary with place information
        """
        try:
            await self._load_model()
            
            # Try to get information from multiple sources
            place_info = await self._gather_place_info(place_name, language)
            
            # Summarize the description if model is available
            if self._model_loaded and place_info.get("raw_description"):
                place_info["description"] = await self._summarize_text(
                    place_info["raw_description"]
                )
            
            # Clean up the response
            return {
                "images": place_info.get("images", []),
                "map_link": place_info.get("map_link", ""),
                "description": place_info.get("description", ""),
                "rating": place_info.get("rating", 0.0)
            }
            
        except Exception as e:
            logger.error(f"Error searching place info: {e}")
            return self._get_fallback_data(place_name)
    
    async def _gather_place_info(self, place_name: str, language: str) -> Dict:
        """Gather information from multiple sources"""
        place_info = {
            "images": [],
            "map_link": "",
            "description": "",
            "raw_description": "",
            "rating": 0.0
        }
        
        try:
            # Get Wikipedia information
            wiki_info = await self.wikipedia_scraper.search_place(place_name, language)
            if wiki_info:
                place_info["raw_description"] = wiki_info.get("summary", "")
                place_info["images"].extend(wiki_info.get("images", []))
            
            # Get Maps information
            maps_info = await self.maps_scraper.search_place(place_name)
            if maps_info:
                place_info["map_link"] = maps_info.get("map_link", "")
                place_info["rating"] = maps_info.get("rating", 0.0)
                place_info["images"].extend(maps_info.get("images", []))
            
            # Remove duplicates from images
            place_info["images"] = list(set(place_info["images"]))
            
            # If no description found, use fallback
            if not place_info["raw_description"]:
                fallback = self._get_fallback_data(place_name)
                place_info.update(fallback)
            
        except Exception as e:
            logger.error(f"Error gathering place info: {e}")
            place_info = self._get_fallback_data(place_name)
        
        return place_info
    
    async def _summarize_text(self, text: str, max_length: int = 150) -> str:
        """Summarize text using BART model"""
        try:
            if not self._model_loaded or len(text) < 100:
                return text[:max_length] + "..." if len(text) > max_length else text
            
            # For demo purposes, return a mock summary
            # In production, you would use:
            # inputs = self.tokenizer(text, return_tensors="pt", max_length=1024, truncation=True)
            # summary_ids = self.model.generate(
            #     inputs["input_ids"],
            #     max_length=max_length,
            #     min_length=30,
            #     do_sample=False
            # )
            # summary = self.tokenizer.decode(summary_ids[0], skip_special_tokens=True)
            
            # Mock summarization - take first sentences up to max_length
            sentences = text.split('. ')
            summary = ""
            for sentence in sentences:
                if len(summary + sentence) < max_length:
                    summary += sentence + ". "
                else:
                    break
            
            return summary.strip() or text[:max_length] + "..."
            
        except Exception as e:
            logger.error(f"Summarization failed: {e}")
            return text[:max_length] + "..." if len(text) > max_length else text
    
    def _get_fallback_data(self, place_name: str) -> Dict:
        """Get fallback data for popular destinations"""
        place_lower = place_name.lower()
        
        # Check for known places
        for key, data in self.fallback_data.items():
            if key in place_lower or place_lower in key:
                return {
                    "images": data["images"],
                    "map_link": f"https://www.google.com/maps/search/{place_name}",
                    "description": data["description"],
                    "rating": data["rating"]
                }
        
        # Generic fallback
        return {
            "images": [
                "https://images.unsplash.com/photo-1506905925346-21bda4d32df4?w=400"
            ],
            "map_link": f"https://www.google.com/maps/search/{place_name}",
            "description": f"{place_name} is a beautiful destination in Thailand. Known for its rich culture, stunning landscapes, and warm hospitality, it offers visitors an unforgettable experience of Thai heritage and natural beauty.",
            "rating": 4.0
        }