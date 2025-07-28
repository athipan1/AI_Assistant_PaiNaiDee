# Tourism AI Enhancement Features Documentation

## Overview

This documentation describes the AI recommendation enhancements implemented for the PaiNaiDee tourism assistant, specifically addressing the requirements for Tourist Interest Graph and Contextual Recommendation Engine.

## Features Implemented

### 1. Tourist Interest Graph 🎯

**Purpose**: Captures user interests from browsing history and interactions, uses AI clustering to link interests with relevant locations.

**Key Components**:
- **Interest Capture**: Automatically extracts tourist interests from user queries and interactions
- **Interest Classification**: Categorizes interests into types (nature, city, culture, adventure, food, history)
- **User Profiling**: Builds detailed profiles including location preferences, activity levels, and time preferences
- **AI Clustering**: Groups similar users and interests to discover patterns
- **Association Mapping**: Links user interests with relevant locations/models
- **LOD Integration**: Provides high-resolution recommendations based on user interests

**Example Usage**:
```python
# Capture interest from user interaction
interest = tourist_graph.capture_interest_from_interaction(
    user_id="user123", 
    session_id="session456",
    interaction_data={
        'query': 'Show me peaceful indoor cafes',
        'selected_model': 'Idle.fbx',
        'context': {'weather': 'rainy', 'time': 'evening'},
        'feedback': {'satisfaction': 0.8}
    }
)

# Get personalized recommendations
recommendations = tourist_graph.get_recommendations_for_user(
    user_id="user123",
    context={'weather': 'rainy', 'time': 'evening'},
    available_locations=['Walking.fbx', 'Idle.fbx', 'Man.fbx']
)
```

### 2. Contextual Recommendation Engine 🌦️

**Purpose**: Analyzes real-time factors like time, weather, and seasonality to provide context-aware recommendations.

**Key Components**:
- **Real-time Context Analysis**: Weather, temperature, humidity, time of day, season
- **Location Suitability Scoring**: Calculates how suitable each location is for current conditions
- **Time-based Recommendations**: Optimizes suggestions based on time of day and user patterns
- **Weather Adaptation**: Adjusts recommendations based on weather conditions
- **Seasonal Preferences**: Considers seasonal suitability for different activities
- **Special Considerations**: Provides context-specific advice (umbrella, sunscreen, etc.)

**Example Usage**:
```python
# Get current contextual factors
context = contextual_engine.get_current_context()

# Generate contextual recommendations
recommendations = contextual_engine.generate_contextual_recommendations(
    available_locations=['Walking.fbx', 'Idle.fbx'],
    user_preferences={'location_preference': 'indoor'},
    top_k=3
)

# Get time-specific recommendations
evening_recs = contextual_engine.get_time_specific_recommendations(
    target_time=datetime.now().replace(hour=19),
    available_locations=['Walking.fbx', 'Idle.fbx'],
    scenario="rainy evening indoor cafes"
)
```

## API Endpoints

### Tourism Enhancement Routes

All tourism routes are prefixed with `/tourism/`

#### Interest Management
- `POST /tourism/capture_interest` - Capture user interest from interaction
- `GET /tourism/analytics/tourist_graph` - Get tourist interest analytics
- `POST /tourism/clustering/trigger` - Manually trigger interest clustering

#### Recommendations
- `POST /tourism/recommendations/tourist` - Get tourist interest-based recommendations
- `POST /tourism/recommendations/contextual` - Get contextual recommendations
- `POST /tourism/recommendations/time_specific` - Get time-specific recommendations
- `POST /tourism/recommendations/integrated` - Get integrated recommendations combining all systems

#### Context & Analytics
- `GET /tourism/context/current` - Get current contextual factors
- `GET /tourism/analytics/contextual` - Get contextual engine analytics
- `GET /tourism/health/tourism` - Health check for tourism systems

## Specific Scenario: "Rainy Evening Indoor Cafes" 🌧️☕

This implementation specifically addresses the scenario mentioned in the requirements: **"indoor cafes near accommodations during rainy evenings"**.

### How it Works:

1. **Interest Detection**: System identifies user preference for indoor, relaxing environments
2. **Weather Analysis**: Detects rainy conditions and adjusts recommendations accordingly
3. **Time Consideration**: Recognizes evening time and suggests appropriate activities
4. **Integrated Recommendation**: Combines user interests, weather, and time to suggest optimal options

### Example API Call:
```bash
curl -X POST http://localhost:8000/tourism/recommendations/integrated \
  -H "Content-Type: application/json" \
  -d '{
    "user_id": "cafe_lover",
    "query": "I need indoor cafes near my accommodation during this rainy evening",
    "available_locations": ["Walking.fbx", "Idle.fbx", "Man.fbx"],
    "user_context": {"weather": "rainy", "time": "evening", "scenario": "indoor cafes"}
  }'
```

### Response Example:
```json
{
  "selected_model": "Idle.fbx",
  "confidence": 0.85,
  "contextual_recommendations": [
    {
      "location_id": "Idle.fbx",
      "location_name": "Idle",
      "suitability_score": 0.9,
      "contextual_reasons": [
        "Great indoor option during rainy weather",
        "Perfect for evening relaxation"
      ],
      "weather_dependency": "indoor",
      "special_considerations": ["Bring umbrella"]
    }
  ],
  "integration_reasoning": [
    "Matches user's indoor preferences",
    "Suitable for current rainy evening conditions"
  ]
}
```

## Technical Architecture

### System Integration

The tourism enhancements integrate seamlessly with existing systems:

1. **LOD Model Integration**: Uses existing LOD prediction for performance optimization
2. **Model Selection**: Enhances existing AI model selection with tourist interests
3. **Session Management**: Leverages existing session tracking for personalization
4. **Analytics**: Extends existing analytics framework

### Data Storage

- **Tourist Interest Data**: Stored in JSON format with persistent storage
- **Contextual Profiles**: Location profiles with weather/time suitability scores
- **User Sessions**: Session-based tracking with interest history
- **Clustering Results**: ML-generated user clusters for pattern discovery

### Machine Learning Components

1. **Interest Classification**: TF-IDF vectorization with keyword matching
2. **User Clustering**: K-means and DBSCAN clustering algorithms
3. **Recommendation Scoring**: Multi-factor scoring with temporal decay
4. **Contextual Analysis**: Rule-based and weighted scoring systems

## Performance Features

### Optimization
- **Background Processing**: Interest clustering runs in background threads
- **Caching**: Results cached for improved response times
- **Lazy Loading**: Systems initialize components on-demand
- **Temporal Decay**: Older interests have reduced impact over time

### Scalability
- **Modular Design**: Components can be scaled independently
- **Configurable Parameters**: Tunable weights and thresholds
- **Storage Abstraction**: Can be adapted for different storage backends
- **API Versioning**: Routes designed for future extensions

## Testing & Validation

### Comprehensive Test Suite
- **22 unit tests** covering all major functionality
- **Integration tests** for system interaction
- **Scenario tests** including the specific "rainy evening" case
- **Performance tests** for optimization validation

### Test Coverage
- Interest capture and classification
- Contextual suitability calculation
- Weather and time-based recommendations
- User clustering algorithms
- API endpoint functionality
- Integration scenarios

## Deployment

### Requirements
- Python 3.8+
- scikit-learn for ML clustering
- FastAPI for API endpoints
- Existing PaiNaiDee infrastructure

### Quick Start
```bash
# Install additional dependencies
pip install scikit-learn

# Start server (tourism features auto-enabled)
python main.py

# Test tourism health
curl http://localhost:8000/tourism/health/tourism
```

## Future Enhancements

### Planned Improvements
- **External Weather APIs**: Integration with real weather services
- **Advanced ML Models**: Deep learning for better interest prediction
- **Real-time Learning**: Continuous model updates from user feedback
- **Multi-language Support**: Interest detection in multiple languages
- **Social Features**: Group recommendations and social clustering

### Extension Points
- **Custom Interest Categories**: Add domain-specific interest types
- **External Data Sources**: Integrate tourism databases and reviews
- **Mobile Context**: GPS location and device-specific optimizations
- **Accessibility Features**: Enhanced recommendations for accessibility needs

## Monitoring & Analytics

### Available Metrics
- **User Interest Distribution**: Track popular interest types
- **Contextual Performance**: Monitor recommendation accuracy
- **System Health**: Component status and performance metrics
- **Usage Patterns**: Analyze user behavior and preferences

### Dashboard Features
- Real-time system status
- Interest clustering visualization
- Contextual suitability heatmaps
- User engagement metrics

---

**Note**: This implementation provides a solid foundation for AI-powered tourism recommendations while maintaining compatibility with existing systems and ensuring high performance and scalability.