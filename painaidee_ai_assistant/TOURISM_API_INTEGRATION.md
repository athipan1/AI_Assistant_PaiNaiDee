# External API Integration - Tourism Features

## Overview

This implementation adds comprehensive external API integration for tourism services to the PaiNaiDee AI Assistant, including Google Places API integration, accommodation booking capabilities, and AI-powered recommendations.

## Features Implemented

### 1. Google Places API Integration (`models/external_apis.py`)

**GooglePlacesConnector Class:**
- Search for places by location, type, and rating
- Get detailed place information including photos and reviews
- Caching support with Redis fallback
- Thai language support

**Key Methods:**
```python
async def search_places(self, search_filter: LocationSearchFilter) -> List[Place]
async def get_place_details(self, place_id: str) -> Optional[Place]
```

### 2. Accommodation Booking System

**AccommodationBookingConnector Class:**
- Agoda-compatible accommodation search
- Mock implementation with realistic Thai hotel data
- Affiliate link support for revenue generation
- Price filtering and availability checking

**Key Methods:**
```python
async def search_accommodations(self, search_filter: LocationSearchFilter) -> List[Accommodation]
async def get_accommodation_details(self, accommodation_id: str) -> Optional[Accommodation]
```

### 3. AI-Powered Matching System

**Features:**
- Budget compatibility analysis
- Property type matching
- Amenity preference scoring
- Style analysis with keyword matching
- Confidence scoring with detailed reasoning

**Algorithm:**
```python
def analyze_accommodation_match(self, accommodation: Accommodation, user_preferences: Dict[str, Any]) -> Dict[str, Any]:
    # Returns match_score (0.0-1.0), match_reasons, and recommendation level
```

### 4. Redis Caching Infrastructure

**RedisCache Class:**
- Automatic fallback to in-memory caching if Redis unavailable
- Configurable TTL (Time To Live) for different data types
- Error handling and logging
- Prefix-based cache clearing

### 5. New API Endpoints (`api/location_routes.py`)

| Endpoint | Method | Purpose |
|----------|--------|---------|
| `/location/health` | GET | Service health monitoring |
| `/location/nearby` | GET | Quick nearby search (all categories) |
| `/location/places/search` | POST | Google Places search |
| `/location/places/{place_id}` | GET | Detailed place information |
| `/location/accommodations/search` | POST | Basic accommodation search |
| `/location/accommodations/smart-search` | POST | AI-powered accommodation search |
| `/location/tourism/comprehensive` | POST | Comprehensive tourism recommendations |

### 6. Frontend Implementation

**Accommodations Page (`static/accommodations.html`):**
- User preference form (budget, type, style, amenities)
- Geolocation API integration
- AI match analysis display
- Responsive Bootstrap 5 design
- Thai language interface

**Near Me Page (`static/near-me.html`):**
- Real-time location detection
- Quick search buttons for common place types
- Categorized results display
- Interactive and modern UI design

## Technical Architecture

### Data Models

```python
@dataclass
class Place:
    place_id: str
    name: str
    address: str
    location: Dict[str, float]  # lat, lng
    rating: Optional[float]
    types: List[str]
    photos: List[str]
    # ... additional fields

@dataclass
class Accommodation:
    accommodation_id: str
    name: str
    address: str
    location: Dict[str, float]
    rating: Optional[float]
    price_per_night: Optional[float]
    amenities: List[str]
    booking_url: str
    affiliate_link: str
    # ... additional fields
```

### Configuration

Environment variables for production deployment:
```bash
# Google Places API (optional)
GOOGLE_PLACES_API_KEY=your_api_key

# Accommodation booking (optional)
BOOKING_AFFILIATE_ID=your_affiliate_id
BOOKING_API_KEY=your_api_key

# Redis caching (optional)
REDIS_HOST=localhost
REDIS_PORT=6379
REDIS_DB=0
```

## Usage Examples

### Basic Nearby Search
```bash
curl "http://localhost:8000/location/nearby?lat=13.7563&lng=100.5018&radius=2000"
```

### AI-Powered Accommodation Search
```bash
curl -X POST "http://localhost:8000/location/accommodations/smart-search" \
  -H "Content-Type: application/json" \
  -d '{
    "lat": 13.7563,
    "lng": 100.5018,
    "budget": 2000,
    "property_type": "hotel",
    "preferred_amenities": ["Free WiFi", "Fitness Center"],
    "style": "city"
  }'
```

### Response Example with AI Analysis
```json
{
  "accommodation_id": "hotel_002",
  "name": "ไบรท์ ซิตี้ โฮเทล",
  "address": "456 City Center, Bangkok",
  "rating": 4.0,
  "price_per_night": 1800.0,
  "amenities": ["Free WiFi", "Fitness Center", "Business Center"],
  "affiliate_link": "https://booking.example.com/hotel_002?aid=your_id",
  "match_analysis": {
    "match_score": 0.9,
    "match_reasons": [
      "Within budget",
      "Matches preferred type: hotel",
      "High rating",
      "Has preferred amenities: Free WiFi, Fitness Center"
    ],
    "recommendation": "excellent"
  }
}
```

## Testing

Run the test suite:
```bash
python -m pytest tests/test_tourism_external_apis.py -v
```

Run the demo:
```bash
python demo_tourism_api.py
```

## Performance Features

1. **Redis Caching**: 30-minute cache for search results, 1-hour for details
2. **Async Operations**: Non-blocking API calls with concurrent search
3. **Error Handling**: Graceful degradation when external services are unavailable
4. **Rate Limiting Ready**: Prepared for API rate limiting implementation

## Future Enhancements

1. **Real API Integration**: Easy connection to Agoda, Booking.com APIs
2. **Advanced AI**: Machine learning models for better recommendation accuracy
3. **Social Features**: User reviews and ratings integration
4. **Multilingual**: Extended language support beyond Thai and English
5. **Mobile App**: React Native or Flutter mobile application

## Production Deployment

The system is production-ready with:
- Comprehensive error handling and logging
- Environment-based configuration
- Scalable architecture with caching
- Security considerations (API key management)
- Thai tourism market optimization