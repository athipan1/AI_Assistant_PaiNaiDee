"""
External API Integration for Tourism Services
Integrates with Google Places API, accommodation booking platforms, and 3D model platforms
"""

import os
import json
import aiohttp
import asyncio
import redis
import googlemaps
from typing import Dict, List, Optional, Any, Union
from dataclasses import dataclass, asdict
from datetime import datetime, timedelta
from pathlib import Path
import hashlib
import tempfile
from urllib.parse import urljoin, quote
import logging

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


@dataclass
class Place:
    """Represents a place from Google Places API"""
    place_id: str
    name: str
    address: str
    location: Dict[str, float]  # lat, lng
    rating: Optional[float] = None
    types: List[str] = None
    phone_number: Optional[str] = None
    website: Optional[str] = None
    photos: List[str] = None
    price_level: Optional[int] = None
    opening_hours: Optional[Dict] = None
    reviews: List[Dict] = None
    business_status: str = "OPERATIONAL"


@dataclass
class Accommodation:
    """Represents hotel/accommodation from booking platforms"""
    accommodation_id: str
    name: str
    address: str
    location: Dict[str, float]  # lat, lng
    rating: Optional[float] = None
    review_count: int = 0
    price_per_night: Optional[float] = None
    currency: str = "THB"
    images: List[str] = None
    amenities: List[str] = None
    room_types: List[Dict] = None
    booking_url: str = ""
    affiliate_link: str = ""
    cancellation_policy: str = ""
    check_in_time: str = ""
    check_out_time: str = ""
    distance_from_center: Optional[float] = None
    property_type: str = "hotel"  # hotel, resort, guesthouse, etc.


@dataclass
class ExternalModel:
    """Represents a 3D model from external platforms"""
    platform: str  # sketchfab, open3d, etc.
    external_id: str
    name: str
    description: str
    author: str
    thumbnail_url: str
    download_url: str
    view_url: str
    file_format: str
    file_size: Optional[int] = None
    license: str = "unknown"
    tags: List[str] = None
    categories: List[str] = None
    rating: Optional[float] = None
    download_count: int = 0
    is_free: bool = True
    created_at: Optional[str] = None
    updated_at: Optional[str] = None


@dataclass
class SearchFilter:
    """Search filters for external model discovery"""
    query: str = ""
    categories: List[str] = None
    file_formats: List[str] = None
    licenses: List[str] = None
    max_file_size: Optional[int] = None
    min_rating: Optional[float] = None
    free_only: bool = True
    sort_by: str = "relevance"  # relevance, popularity, date, rating
    limit: int = 20


@dataclass
class LocationSearchFilter:
    """Search filters for location-based services"""
    query: str = ""
    location: Dict[str, float] = None  # lat, lng
    radius: int = 5000  # meters
    place_types: List[str] = None  # restaurant, lodging, tourist_attraction, etc.
    min_rating: Optional[float] = None
    price_level: Optional[int] = None  # 0-4 (free to very expensive)
    open_now: bool = False
    sort_by: str = "prominence"  # prominence, distance, rating
    limit: int = 20


class RedisCache:
    """Redis-based caching for API responses"""
    
    def __init__(self, host: str = "localhost", port: int = 6379, db: int = 0):
        try:
            self.redis_client = redis.Redis(
                host=host, 
                port=port, 
                db=db, 
                decode_responses=True,
                socket_connect_timeout=5,
                socket_timeout=5
            )
            # Test connection
            self.redis_client.ping()
            self.enabled = True
            logger.info("Redis cache enabled")
        except (redis.ConnectionError, redis.TimeoutError) as e:
            logger.warning(f"Redis connection failed: {e}. Running without cache.")
            self.redis_client = None
            self.enabled = False
    
    def get(self, key: str) -> Optional[str]:
        """Get cached value"""
        if not self.enabled:
            return None
        try:
            return self.redis_client.get(key)
        except Exception as e:
            logger.warning(f"Redis get error: {e}")
            return None
    
    def set(self, key: str, value: str, ttl: int = 3600) -> bool:
        """Set cached value with TTL (seconds)"""
        if not self.enabled:
            return False
        try:
            return self.redis_client.setex(key, ttl, value)
        except Exception as e:
            logger.warning(f"Redis set error: {e}")
            return False
    
    def delete(self, key: str) -> bool:
        """Delete cached value"""
        if not self.enabled:
            return False
        try:
            return bool(self.redis_client.delete(key))
        except Exception as e:
            logger.warning(f"Redis delete error: {e}")
            return False
    
    def clear_prefix(self, prefix: str) -> int:
        """Clear all keys with given prefix"""
        if not self.enabled:
            return 0
        try:
            keys = self.redis_client.keys(f"{prefix}*")
            if keys:
                return self.redis_client.delete(*keys)
            return 0
        except Exception as e:
            logger.warning(f"Redis clear prefix error: {e}")
            return 0


class GooglePlacesConnector:
    """Connector for Google Places API"""
    
    def __init__(self, api_key: str = None):
        self.api_key = api_key or os.getenv("GOOGLE_PLACES_API_KEY")
        if not self.api_key:
            logger.warning("No Google Places API key provided")
            self.client = None
        else:
            self.client = googlemaps.Client(key=self.api_key)
        
        self.cache = RedisCache()
    
    async def search_places(self, search_filter: LocationSearchFilter) -> List[Place]:
        """Search for places using Google Places API"""
        if not self.client:
            logger.warning("Google Places API not configured")
            return []
        
        # Check cache first
        cache_key = f"places:{hashlib.md5(str(search_filter).encode()).hexdigest()}"
        cached_result = self.cache.get(cache_key)
        if cached_result:
            try:
                data = json.loads(cached_result)
                return [Place(**place_data) for place_data in data]
            except Exception as e:
                logger.warning(f"Cache deserialization error: {e}")
        
        try:
            # Prepare search parameters
            search_params = {
                'location': (search_filter.location['lat'], search_filter.location['lng']),
                'radius': search_filter.radius,
                'language': 'th'  # Thai language for results
            }
            
            if search_filter.query:
                search_params['query'] = search_filter.query
            
            if search_filter.place_types:
                search_params['type'] = search_filter.place_types[0]  # Google API accepts single type
            
            if search_filter.min_rating:
                search_params['min_price'] = 0
            
            if search_filter.open_now:
                search_params['open_now'] = True
            
            # Execute search
            if search_filter.query:
                results = self.client.places(
                    query=search_filter.query,
                    location=search_params['location'],
                    radius=search_params['radius']
                )
            else:
                results = self.client.places_nearby(
                    location=search_params['location'],
                    radius=search_params['radius'],
                    type=search_params.get('type')
                )
            
            # Parse results
            places = []
            for place_data in results.get('results', [])[:search_filter.limit]:
                place = self._parse_google_place(place_data)
                if place:
                    places.append(place)
            
            # Cache results
            try:
                cache_data = [asdict(place) for place in places]
                self.cache.set(cache_key, json.dumps(cache_data), ttl=1800)  # 30 minutes
            except Exception as e:
                logger.warning(f"Cache serialization error: {e}")
            
            return places
            
        except Exception as e:
            logger.error(f"Google Places API error: {e}")
            return []
    
    def _parse_google_place(self, place_data: Dict) -> Optional[Place]:
        """Parse Google Places API response into Place object"""
        try:
            location = place_data.get('geometry', {}).get('location', {})
            
            # Extract photos
            photos = []
            if 'photos' in place_data:
                for photo in place_data['photos'][:3]:  # Max 3 photos
                    photo_ref = photo.get('photo_reference')
                    if photo_ref:
                        photo_url = f"https://maps.googleapis.com/maps/api/place/photo?maxwidth=400&photoreference={photo_ref}&key={self.api_key}"
                        photos.append(photo_url)
            
            return Place(
                place_id=place_data.get('place_id', ''),
                name=place_data.get('name', 'Unknown'),
                address=place_data.get('formatted_address', place_data.get('vicinity', '')),
                location={'lat': location.get('lat', 0), 'lng': location.get('lng', 0)},
                rating=place_data.get('rating'),
                types=place_data.get('types', []),
                phone_number=place_data.get('formatted_phone_number'),
                website=place_data.get('website'),
                photos=photos,
                price_level=place_data.get('price_level'),
                opening_hours=place_data.get('opening_hours'),
                business_status=place_data.get('business_status', 'OPERATIONAL')
            )
            
        except Exception as e:
            logger.error(f"Error parsing Google place: {e}")
            return None
    
    async def get_place_details(self, place_id: str) -> Optional[Place]:
        """Get detailed information about a specific place"""
        if not self.client:
            return None
        
        # Check cache
        cache_key = f"place_details:{place_id}"
        cached_result = self.cache.get(cache_key)
        if cached_result:
            try:
                return Place(**json.loads(cached_result))
            except Exception as e:
                logger.warning(f"Cache error: {e}")
        
        try:
            result = self.client.place(
                place_id=place_id,
                fields=['name', 'formatted_address', 'geometry', 'rating', 'types', 'formatted_phone_number', 'website', 'photos', 'price_level', 'opening_hours', 'reviews'],
                language='th'
            )
            
            place_data = result.get('result', {})
            place = self._parse_google_place(place_data)
            
            if place:
                # Add reviews
                reviews = []
                for review in place_data.get('reviews', [])[:5]:  # Max 5 reviews
                    reviews.append({
                        'author': review.get('author_name', 'Anonymous'),
                        'rating': review.get('rating'),
                        'text': review.get('text', '')[:200],  # Truncate long reviews
                        'time': review.get('relative_time_description')
                    })
                place.reviews = reviews
                
                # Cache result
                try:
                    self.cache.set(cache_key, json.dumps(asdict(place)), ttl=3600)
                except Exception as e:
                    logger.warning(f"Cache error: {e}")
            
            return place
            
        except Exception as e:
            logger.error(f"Google Places detail error: {e}")
            return None


class AccommodationBookingConnector:
    """Connector for accommodation booking platforms (Agoda-compatible)"""
    
    def __init__(self, affiliate_id: str = None, api_key: str = None):
        self.affiliate_id = affiliate_id or os.getenv("BOOKING_AFFILIATE_ID")
        self.api_key = api_key or os.getenv("BOOKING_API_KEY")
        self.base_url = "https://partner-api.booking.com"  # Example URL
        self.cache = RedisCache()
        
        self.headers = {
            "User-Agent": "PaiNaiDee-Tourism-Assistant/1.0",
            "Accept": "application/json"
        }
        
        if self.api_key:
            self.headers["Authorization"] = f"Bearer {self.api_key}"
    
    async def search_accommodations(self, search_filter: LocationSearchFilter) -> List[Accommodation]:
        """Search for accommodations near a location"""
        
        # Check cache first
        cache_key = f"accommodations:{hashlib.md5(str(search_filter).encode()).hexdigest()}"
        cached_result = self.cache.get(cache_key)
        if cached_result:
            try:
                data = json.loads(cached_result)
                return [Accommodation(**acc_data) for acc_data in data]
            except Exception as e:
                logger.warning(f"Cache error: {e}")
        
        # Simulate API call (replace with actual implementation)
        accommodations = await self._mock_accommodation_search(search_filter)
        
        # Cache results
        try:
            cache_data = [asdict(acc) for acc in accommodations]
            self.cache.set(cache_key, json.dumps(cache_data), ttl=1800)
        except Exception as e:
            logger.warning(f"Cache error: {e}")
        
        return accommodations
    
    async def _mock_accommodation_search(self, search_filter: LocationSearchFilter) -> List[Accommodation]:
        """Mock accommodation search (replace with real API integration)"""
        # This is a placeholder implementation
        # In production, replace with actual Agoda/Booking.com API calls
        
        mock_accommodations = [
            {
                "accommodation_id": "hotel_001",
                "name": "ลอยล์ ณ บางแสน บีช รีสอร์ท",
                "address": "123 Beach Road, Bang Saen, Chonburi",
                "location": {"lat": 13.2827, "lng": 100.9267},
                "rating": 4.2,
                "review_count": 156,
                "price_per_night": 2500.0,
                "currency": "THB",
                "images": [
                    "https://example.com/hotel1_1.jpg",
                    "https://example.com/hotel1_2.jpg"
                ],
                "amenities": ["Free WiFi", "Swimming Pool", "Beach Access", "Restaurant"],
                "room_types": [
                    {"type": "Standard Room", "price": 2500, "capacity": 2},
                    {"type": "Deluxe Ocean View", "price": 3500, "capacity": 2}
                ],
                "booking_url": "https://booking.example.com/hotel_001",
                "affiliate_link": f"https://booking.example.com/hotel_001?aid={self.affiliate_id}",
                "cancellation_policy": "Free cancellation until 24 hours before check-in",
                "check_in_time": "15:00",
                "check_out_time": "12:00",
                "distance_from_center": 2.1,
                "property_type": "resort"
            },
            {
                "accommodation_id": "hotel_002", 
                "name": "ไบรท์ ซิตี้ โฮเทล",
                "address": "456 City Center, Bangkok",
                "location": {"lat": 13.7563, "lng": 100.5018},
                "rating": 4.0,
                "review_count": 89,
                "price_per_night": 1800.0,
                "currency": "THB",
                "images": [
                    "https://example.com/hotel2_1.jpg"
                ],
                "amenities": ["Free WiFi", "Fitness Center", "Business Center"],
                "room_types": [
                    {"type": "Standard Room", "price": 1800, "capacity": 2},
                    {"type": "Superior Room", "price": 2300, "capacity": 2}
                ],
                "booking_url": "https://booking.example.com/hotel_002",
                "affiliate_link": f"https://booking.example.com/hotel_002?aid={self.affiliate_id}",
                "cancellation_policy": "Free cancellation until 48 hours before check-in",
                "check_in_time": "14:00", 
                "check_out_time": "11:00",
                "distance_from_center": 0.5,
                "property_type": "hotel"
            }
        ]
        
        # Filter based on search criteria
        filtered_accommodations = []
        for acc_data in mock_accommodations:
            accommodation = Accommodation(**acc_data)
            
            # Apply filters
            if search_filter.min_rating and accommodation.rating < search_filter.min_rating:
                continue
                
            if search_filter.query and search_filter.query.lower() not in accommodation.name.lower():
                continue
            
            filtered_accommodations.append(accommodation)
        
        return filtered_accommodations[:search_filter.limit]
    
    async def get_accommodation_details(self, accommodation_id: str) -> Optional[Accommodation]:
        """Get detailed information about specific accommodation"""
        # Check cache
        cache_key = f"accommodation_details:{accommodation_id}"
        cached_result = self.cache.get(cache_key)
        if cached_result:
            try:
                return Accommodation(**json.loads(cached_result))
            except Exception as e:
                logger.warning(f"Cache error: {e}")
        
        # Mock implementation - replace with real API
        mock_details = {
            "accommodation_id": accommodation_id,
            "name": "Sample Hotel",
            "address": "123 Sample Street",
            "location": {"lat": 13.7563, "lng": 100.5018},
            "rating": 4.0,
            "review_count": 100,
            "price_per_night": 2000.0,
            "currency": "THB",
            "booking_url": f"https://booking.example.com/{accommodation_id}",
            "affiliate_link": f"https://booking.example.com/{accommodation_id}?aid={self.affiliate_id}"
        }
        
        accommodation = Accommodation(**mock_details)
        
        # Cache result
        try:
            self.cache.set(cache_key, json.dumps(asdict(accommodation)), ttl=3600)
        except Exception as e:
            logger.warning(f"Cache error: {e}")
        
        return accommodation


class SketchfabConnector:
    """Connector for Sketchfab API"""
    
    def __init__(self, api_token: str = None):
        self.api_token = api_token or os.getenv("SKETCHFAB_API_TOKEN")
        self.base_url = "https://api.sketchfab.com/v3"
        self.headers = {
            "Authorization": f"Token {self.api_token}" if self.api_token else None,
            "User-Agent": "PaiNaiDee-3D-Platform/1.0"
        }
    
    async def search_models(self, search_filter: SearchFilter) -> List[ExternalModel]:
        """Search for models on Sketchfab"""
        if not self.api_token:
            print("Warning: No Sketchfab API token provided")
            return []
        
        try:
            params = {
                "q": search_filter.query,
                "count": min(search_filter.limit, 100),
                "sort_by": self._map_sort_field(search_filter.sort_by)
            }
            
            if search_filter.categories:
                params["categories"] = ",".join(search_filter.categories)
            
            if search_filter.free_only:
                params["downloadable"] = "true"
            
            async with aiohttp.ClientSession() as session:
                async with session.get(
                    f"{self.base_url}/models",
                    headers=self.headers,
                    params=params
                ) as response:
                    if response.status == 200:
                        data = await response.json()
                        return self._parse_sketchfab_models(data.get("results", []))
                    else:
                        print(f"Sketchfab API error: {response.status}")
                        return []
                        
        except Exception as e:
            print(f"Error searching Sketchfab: {e}")
            return []
    
    def _map_sort_field(self, sort_by: str) -> str:
        """Map generic sort field to Sketchfab specific field"""
        mapping = {
            "relevance": "relevance",
            "popularity": "viewCount",
            "date": "publishedAt",
            "rating": "likeCount"
        }
        return mapping.get(sort_by, "relevance")
    
    def _parse_sketchfab_models(self, models_data: List[Dict]) -> List[ExternalModel]:
        """Parse Sketchfab API response into ExternalModel objects"""
        models = []
        
        for model_data in models_data:
            try:
                # Extract thumbnail URL
                thumbnails = model_data.get("thumbnails", {}).get("images", [])
                thumbnail_url = thumbnails[0]["url"] if thumbnails else ""
                
                # Check if downloadable
                download_url = ""
                is_downloadable = model_data.get("isDownloadable", False)
                if is_downloadable and "archives" in model_data:
                    archives = model_data["archives"]
                    if archives:
                        download_url = archives[0].get("url", "")
                
                model = ExternalModel(
                    platform="sketchfab",
                    external_id=model_data["uid"],
                    name=model_data.get("name", "Untitled"),
                    description=model_data.get("description", ""),
                    author=model_data.get("user", {}).get("displayName", "Unknown"),
                    thumbnail_url=thumbnail_url,
                    download_url=download_url,
                    view_url=f"https://sketchfab.com/3d-models/{model_data['uid']}",
                    file_format="unknown",
                    license=model_data.get("license", {}).get("label", "unknown"),
                    tags=model_data.get("tags", []),
                    categories=[cat["name"] for cat in model_data.get("categories", [])],
                    rating=model_data.get("likeCount", 0) / 100.0,  # Normalize to 0-1
                    download_count=model_data.get("downloadCount", 0),
                    is_free=is_downloadable,
                    created_at=model_data.get("publishedAt"),
                    updated_at=model_data.get("updatedAt")
                )
                
                models.append(model)
                
            except Exception as e:
                print(f"Error parsing Sketchfab model: {e}")
                continue
        
        return models
    
    async def get_model_details(self, model_id: str) -> Optional[ExternalModel]:
        """Get detailed information about a specific model"""
        if not self.api_token:
            return None
        
        try:
            async with aiohttp.ClientSession() as session:
                async with session.get(
                    f"{self.base_url}/models/{model_id}",
                    headers=self.headers
                ) as response:
                    if response.status == 200:
                        data = await response.json()
                        models = self._parse_sketchfab_models([data])
                        return models[0] if models else None
                    
        except Exception as e:
            print(f"Error getting Sketchfab model details: {e}")
        
        return None


class Open3DConnector:
    """Connector for Open3D model repository"""
    
    def __init__(self):
        self.base_url = "https://open3d.org/api/v1"
        self.headers = {
            "User-Agent": "PaiNaiDee-3D-Platform/1.0"
        }
    
    async def search_models(self, search_filter: SearchFilter) -> List[ExternalModel]:
        """Search for models in Open3D repository"""
        # Note: This is a simplified implementation
        # In practice, Open3D might not have a public API or might require different authentication
        
        try:
            # Simulate Open3D search results
            sample_models = [
                {
                    "id": "open3d_bunny",
                    "name": "Stanford Bunny",
                    "description": "Classic 3D test model - Stanford Bunny mesh",
                    "author": "Stanford Graphics Lab",
                    "file_format": "ply",
                    "file_size": 1048576,
                    "tags": ["test", "classic", "mesh", "bunny"],
                    "license": "academic"
                },
                {
                    "id": "open3d_teapot",
                    "name": "Utah Teapot",
                    "description": "Classic Utah teapot reference model",
                    "author": "Martin Newell",
                    "file_format": "obj",
                    "file_size": 524288,
                    "tags": ["test", "classic", "teapot"],
                    "license": "public_domain"
                }
            ]
            
            models = []
            for model_data in sample_models:
                if search_filter.query.lower() in model_data["name"].lower():
                    model = ExternalModel(
                        platform="open3d",
                        external_id=model_data["id"],
                        name=model_data["name"],
                        description=model_data["description"],
                        author=model_data["author"],
                        thumbnail_url=f"https://open3d.org/thumbnails/{model_data['id']}.jpg",
                        download_url=f"https://open3d.org/models/{model_data['id']}.{model_data['file_format']}",
                        view_url=f"https://open3d.org/models/{model_data['id']}",
                        file_format=model_data["file_format"],
                        file_size=model_data["file_size"],
                        license=model_data["license"],
                        tags=model_data["tags"],
                        is_free=True,
                        rating=0.9  # High quality reference models
                    )
                    models.append(model)
            
            return models[:search_filter.limit]
            
        except Exception as e:
            print(f"Error searching Open3D: {e}")
            return []


class ExternalAPIManager:
    """Manages integration with multiple external platforms including tourism services"""
    
    def __init__(self, config_file: str = "external_apis.json"):
        self.config_file = Path(config_file)
        self.config = self._load_config()
        
        # Initialize connectors
        self.connectors = {
            "sketchfab": SketchfabConnector(self.config.get("sketchfab", {}).get("api_token")),
            "open3d": Open3DConnector(),
            "google_places": GooglePlacesConnector(self.config.get("google_places", {}).get("api_key")),
            "accommodation": AccommodationBookingConnector(
                self.config.get("accommodation", {}).get("affiliate_id"),
                self.config.get("accommodation", {}).get("api_key")
            )
        }
        
        # Cache for search results
        self.search_cache = {}
        self.cache_ttl = 3600  # 1 hour
        
        # Downloaded models tracking
        self.downloaded_models = self._load_downloaded_models()
        
        # Initialize Redis cache
        self.redis_cache = RedisCache()
    
    def _load_config(self) -> Dict[str, Any]:
        """Load external API configuration"""
        default_config = {
            "enabled_platforms": ["sketchfab", "open3d", "google_places", "accommodation"],
            "search_timeout": 30,
            "download_timeout": 300,
            "max_file_size": 50 * 1024 * 1024,  # 50MB
            "auto_import": False,
            "moderation_required": True,
            "sketchfab": {
                "api_token": os.getenv("SKETCHFAB_API_TOKEN"),
                "rate_limit": 60  # requests per hour
            },
            "open3d": {
                "enabled": True
            },
            "google_places": {
                "api_key": os.getenv("GOOGLE_PLACES_API_KEY"),
                "rate_limit": 1000,  # requests per day
                "default_radius": 5000,  # meters
                "default_language": "th"
            },
            "accommodation": {
                "affiliate_id": os.getenv("BOOKING_AFFILIATE_ID"),
                "api_key": os.getenv("BOOKING_API_KEY"),
                "rate_limit": 100,  # requests per hour
                "default_currency": "THB"
            },
            "redis": {
                "host": os.getenv("REDIS_HOST", "localhost"),
                "port": int(os.getenv("REDIS_PORT", "6379")),
                "db": int(os.getenv("REDIS_DB", "0"))
            }
        }
        
        if self.config_file.exists():
            try:
                with open(self.config_file, 'r') as f:
                    loaded_config = json.load(f)
                    default_config.update(loaded_config)
            except Exception as e:
                logger.error(f"Error loading external API config: {e}")
        
        return default_config
    
    async def search_places_nearby(self, location: Dict[str, float], query: str = "", 
                                 place_types: List[str] = None, radius: int = 5000,
                                 min_rating: float = None, limit: int = 20) -> List[Place]:
        """Search for places near a location using Google Places API"""
        if "google_places" not in self.connectors:
            return []
        
        search_filter = LocationSearchFilter(
            query=query,
            location=location,
            radius=radius,
            place_types=place_types,
            min_rating=min_rating,
            limit=limit
        )
        
        connector = self.connectors["google_places"]
        return await connector.search_places(search_filter)
    
    async def search_accommodations_nearby(self, location: Dict[str, float], 
                                         query: str = "", min_rating: float = None,
                                         limit: int = 20) -> List[Accommodation]:
        """Search for accommodations near a location"""
        if "accommodation" not in self.connectors:
            return []
        
        search_filter = LocationSearchFilter(
            query=query,
            location=location,
            radius=10000,  # 10km for accommodations
            min_rating=min_rating,
            limit=limit
        )
        
        connector = self.connectors["accommodation"]
        return await connector.search_accommodations(search_filter)
    
    async def get_tourism_recommendations(self, location: Dict[str, float], 
                                        user_preferences: Dict[str, Any] = None) -> Dict[str, List]:
        """Get comprehensive tourism recommendations for a location"""
        recommendations = {
            "restaurants": [],
            "attractions": [],
            "accommodations": [],
            "activities": []
        }
        
        try:
            # Search for different types of places concurrently
            tasks = [
                self.search_places_nearby(
                    location=location,
                    place_types=["restaurant"],
                    min_rating=4.0,
                    limit=10
                ),
                self.search_places_nearby(
                    location=location,
                    place_types=["tourist_attraction"],
                    min_rating=4.0,
                    limit=10
                ),
                self.search_accommodations_nearby(
                    location=location,
                    min_rating=4.0,
                    limit=10
                ),
                self.search_places_nearby(
                    location=location,
                    place_types=["amusement_park", "zoo", "museum"],
                    min_rating=4.0,
                    limit=10
                )
            ]
            
            results = await asyncio.gather(*tasks, return_exceptions=True)
            
            # Process results
            if not isinstance(results[0], Exception):
                recommendations["restaurants"] = results[0]
            if not isinstance(results[1], Exception):
                recommendations["attractions"] = results[1]
            if not isinstance(results[2], Exception):
                recommendations["accommodations"] = results[2]
            if not isinstance(results[3], Exception):
                recommendations["activities"] = results[3]
            
        except Exception as e:
            logger.error(f"Error getting tourism recommendations: {e}")
        
        return recommendations
    
    def analyze_accommodation_match(self, accommodation: Accommodation, 
                                  user_preferences: Dict[str, Any]) -> Dict[str, Any]:
        """AI analysis of how well an accommodation matches user preferences"""
        # Simple rule-based matching (can be enhanced with ML models)
        match_score = 0.0
        match_reasons = []
        
        # Budget preference
        if "budget" in user_preferences:
            budget = user_preferences["budget"]
            if accommodation.price_per_night:
                if accommodation.price_per_night <= budget:
                    match_score += 0.3
                    match_reasons.append("Within budget")
                elif accommodation.price_per_night <= budget * 1.2:
                    match_score += 0.1
                    match_reasons.append("Slightly over budget but good value")
        
        # Accommodation type preference
        if "property_type" in user_preferences:
            preferred_type = user_preferences["property_type"]
            if accommodation.property_type == preferred_type:
                match_score += 0.2
                match_reasons.append(f"Matches preferred type: {preferred_type}")
        
        # Rating preference
        if accommodation.rating and accommodation.rating >= 4.0:
            match_score += 0.2
            match_reasons.append("High rating")
        
        # Amenities matching
        if "preferred_amenities" in user_preferences and accommodation.amenities:
            preferred_amenities = user_preferences["preferred_amenities"]
            matching_amenities = set(accommodation.amenities) & set(preferred_amenities)
            if matching_amenities:
                match_score += len(matching_amenities) * 0.1
                match_reasons.append(f"Has preferred amenities: {', '.join(matching_amenities)}")
        
        # Style analysis (simple keyword matching)
        user_style = user_preferences.get("style", "").lower()
        accommodation_name = accommodation.name.lower()
        
        style_keywords = {
            "luxury": ["luxury", "premium", "deluxe", "royal", "grand"],
            "budget": ["budget", "economy", "value", "cheap"],
            "boutique": ["boutique", "design", "art", "unique"],
            "beach": ["beach", "ocean", "sea", "coastal"],
            "city": ["city", "urban", "downtown", "center"],
            "resort": ["resort", "spa", "wellness", "retreat"]
        }
        
        if user_style in style_keywords:
            keywords = style_keywords[user_style]
            for keyword in keywords:
                if keyword in accommodation_name:
                    match_score += 0.15
                    match_reasons.append(f"Matches {user_style} style")
                    break
        
        return {
            "match_score": min(match_score, 1.0),  # Cap at 1.0
            "match_reasons": match_reasons,
            "recommendation": "excellent" if match_score >= 0.8 else "good" if match_score >= 0.6 else "moderate"
        }
    
    def _load_downloaded_models(self) -> Dict[str, Dict]:
        """Load metadata of previously downloaded models"""
        downloaded_file = Path("downloaded_models.json")
        if downloaded_file.exists():
            try:
                with open(downloaded_file, 'r') as f:
                    return json.load(f)
            except Exception as e:
                print(f"Error loading downloaded models: {e}")
        return {}
    
    def _save_downloaded_models(self):
        """Save downloaded models metadata"""
        try:
            with open("downloaded_models.json", 'w') as f:
                json.dump(self.downloaded_models, f, indent=2)
        except Exception as e:
            print(f"Error saving downloaded models: {e}")
    
    async def search_all_platforms(self, search_filter: SearchFilter) -> Dict[str, List[ExternalModel]]:
        """Search across all enabled platforms"""
        results = {}
        
        # Check cache first
        cache_key = self._generate_cache_key(search_filter)
        if cache_key in self.search_cache:
            cache_entry = self.search_cache[cache_key]
            if datetime.now().timestamp() - cache_entry["timestamp"] < self.cache_ttl:
                return cache_entry["results"]
        
        # Search each enabled platform
        search_tasks = []
        enabled_platforms = self.config.get("enabled_platforms", [])
        
        for platform in enabled_platforms:
            if platform in self.connectors:
                task = self._search_platform(platform, search_filter)
                search_tasks.append((platform, task))
        
        # Execute searches concurrently
        for platform, task in search_tasks:
            try:
                models = await asyncio.wait_for(task, timeout=self.config["search_timeout"])
                results[platform] = models
            except asyncio.TimeoutError:
                print(f"Search timeout for platform: {platform}")
                results[platform] = []
            except Exception as e:
                print(f"Error searching platform {platform}: {e}")
                results[platform] = []
        
        # Cache results
        self.search_cache[cache_key] = {
            "results": results,
            "timestamp": datetime.now().timestamp()
        }
        
        return results
    
    async def _search_platform(self, platform: str, search_filter: SearchFilter) -> List[ExternalModel]:
        """Search a specific platform"""
        connector = self.connectors.get(platform)
        if connector:
            return await connector.search_models(search_filter)
        return []
    
    def _generate_cache_key(self, search_filter: SearchFilter) -> str:
        """Generate cache key for search filter"""
        filter_dict = asdict(search_filter)
        filter_str = json.dumps(filter_dict, sort_keys=True)
        return hashlib.md5(filter_str.encode()).hexdigest()
    
    async def get_unified_search_results(self, search_filter: SearchFilter) -> List[ExternalModel]:
        """Get unified search results from all platforms, sorted by relevance"""
        platform_results = await self.search_all_platforms(search_filter)
        
        # Combine and rank results
        all_models = []
        for platform, models in platform_results.items():
            all_models.extend(models)
        
        # Sort by relevance score (combination of rating, download count, etc.)
        def relevance_score(model: ExternalModel) -> float:
            score = 0.0
            
            # Query relevance (simple keyword matching)
            query_lower = search_filter.query.lower()
            if query_lower in model.name.lower():
                score += 2.0
            if query_lower in model.description.lower():
                score += 1.0
            if any(query_lower in tag.lower() for tag in (model.tags or [])):
                score += 1.5
            
            # Platform quality bonus
            platform_bonus = {"sketchfab": 1.0, "open3d": 1.5}
            score += platform_bonus.get(model.platform, 0.5)
            
            # Rating and popularity
            if model.rating:
                score += model.rating * 2.0
            
            if model.download_count > 100:
                score += 1.0
            
            # Free models bonus
            if model.is_free:
                score += 0.5
            
            return score
        
        sorted_models = sorted(all_models, key=relevance_score, reverse=True)
        return sorted_models[:search_filter.limit]
    
    async def download_model(self, model: ExternalModel, local_path: str = None) -> Dict[str, Any]:
        """Download a model from external platform"""
        if not model.download_url or not model.is_free:
            return {
                "status": "error",
                "message": "Model is not available for download"
            }
        
        if model.file_size and model.file_size > self.config["max_file_size"]:
            return {
                "status": "error",
                "message": f"Model too large: {model.file_size} bytes"
            }
        
        try:
            # Generate local path if not provided
            if not local_path:
                safe_name = "".join(c for c in model.name if c.isalnum() or c in (' ', '-', '_'))
                local_path = f"downloads/{model.platform}_{model.external_id}_{safe_name}.{model.file_format}"
            
            # Create directory if needed
            Path(local_path).parent.mkdir(parents=True, exist_ok=True)
            
            # Download file
            async with aiohttp.ClientSession() as session:
                async with session.get(
                    model.download_url,
                    timeout=aiohttp.ClientTimeout(total=self.config["download_timeout"])
                ) as response:
                    if response.status == 200:
                        with open(local_path, 'wb') as f:
                            async for chunk in response.content.iter_chunked(8192):
                                f.write(chunk)
                        
                        # Verify file size
                        actual_size = os.path.getsize(local_path)
                        
                        # Record download
                        download_record = {
                            "model": asdict(model),
                            "local_path": local_path,
                            "downloaded_at": datetime.now().isoformat(),
                            "file_size": actual_size,
                            "status": "pending_moderation" if self.config["moderation_required"] else "approved"
                        }
                        
                        self.downloaded_models[f"{model.platform}_{model.external_id}"] = download_record
                        self._save_downloaded_models()
                        
                        return {
                            "status": "success",
                            "message": "Model downloaded successfully",
                            "local_path": local_path,
                            "file_size": actual_size,
                            "moderation_required": self.config["moderation_required"]
                        }
                    else:
                        return {
                            "status": "error",
                            "message": f"Download failed: HTTP {response.status}"
                        }
            
        except Exception as e:
            return {
                "status": "error",
                "message": f"Download error: {str(e)}"
            }
    
    def get_downloaded_models(self, status: str = None) -> List[Dict[str, Any]]:
        """Get list of downloaded models, optionally filtered by status"""
        models = list(self.downloaded_models.values())
        
        if status:
            models = [m for m in models if m.get("status") == status]
        
        return models
    
    def moderate_model(self, model_key: str, approved: bool, notes: str = "") -> Dict[str, Any]:
        """Moderate a downloaded model (approve/reject)"""
        if model_key not in self.downloaded_models:
            return {
                "status": "error",
                "message": "Model not found"
            }
        
        model_record = self.downloaded_models[model_key]
        model_record["status"] = "approved" if approved else "rejected"
        model_record["moderation_notes"] = notes
        model_record["moderated_at"] = datetime.now().isoformat()
        
        self._save_downloaded_models()
        
        return {
            "status": "success",
            "message": f"Model {'approved' if approved else 'rejected'}",
            "model_status": model_record["status"]
        }
    
    def get_platform_stats(self) -> Dict[str, Any]:
        """Get statistics about external platform integration"""
        stats = {
            "enabled_platforms": self.config.get("enabled_platforms", []),
            "total_downloaded": len(self.downloaded_models),
            "pending_moderation": len([m for m in self.downloaded_models.values() 
                                     if m.get("status") == "pending_moderation"]),
            "approved_models": len([m for m in self.downloaded_models.values() 
                                  if m.get("status") == "approved"]),
            "rejected_models": len([m for m in self.downloaded_models.values() 
                                  if m.get("status") == "rejected"]),
            "cache_entries": len(self.search_cache),
            "platforms": {}
        }
        
        # Platform-specific stats
        for platform in self.config.get("enabled_platforms", []):
            platform_models = [m for m in self.downloaded_models.values() 
                             if m.get("model", {}).get("platform") == platform]
            stats["platforms"][platform] = {
                "downloaded_count": len(platform_models),
                "connector_available": platform in self.connectors
            }
        
        return stats


# Initialize global external API manager
external_api_manager = ExternalAPIManager()