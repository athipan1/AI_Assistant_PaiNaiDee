# AI_Assistant_PaiNaiDee | ผู้ช่วย AI ไปไหนดี

## 🎯 Complete AI Voice Assistant Solution

A comprehensive AI-powered voice assistant for Thai tourism featuring both a **Python FastAPI backend** and a **React Native + Expo mobile app** with 3D visualization, speech recognition, and location-based recommendations.

### 📱 **NEW: Mobile Voice Assistant App**

**All Requirements Implemented ✅**
- **React Native + Expo**: Cross-platform mobile app
- **Speech-to-Text**: Voice command recognition (Google STT ready)  
- **Location Access**: Real-time GPS + nearby place detection
- **3D AR Scene**: Three.js visualization with emotion responses
- **AI Voice Responses**: Text-to-speech in Thai and English
- **Haptic Feedback**: Vibration patterns for place recommendations
- **Thai NLP Support**: Full bilingual interface with cultural context

![Thai Interface](https://github.com/user-attachments/assets/7bea1acd-155b-41b1-bf18-feb3131af4d6)
![English Interface with 3D](https://github.com/user-attachments/assets/7cd6b440-ed30-4cf4-97f0-d5c3a4330935)

## 🚀 Quick Start

### Automated Setup (Recommended)
```bash
# Clone and setup everything automatically
git clone https://github.com/athipan1/AI_Assistant_PaiNaiDee.git
cd AI_Assistant_PaiNaiDee
chmod +x setup.sh
./setup.sh
```

### Manual Setup

**1. Backend Server (Python FastAPI)**
```bash
cd painaidee_ai_assistant
python -m venv venv
source venv/bin/activate  # Windows: venv\Scripts\activate
pip install -r requirements.txt
python main.py
```

**2. Mobile App (React Native + Expo)**
```bash
cd mobile-app
npm install --legacy-peer-deps
npm start  # or npm run web for browser testing
```

**3. Configuration**
Update `mobile-app/src/config/index.ts` with your backend IP:
```typescript
API_BASE_URL: 'http://YOUR_BACKEND_IP:8000'
```

## 📋 System Architecture

```
AI_Assistant_PaiNaiDee/
├── painaidee_ai_assistant/     # Python FastAPI Backend
│   ├── api/                    # REST API endpoints
│   ├── agents/                 # AI agents (emotion, model selection)
│   ├── models/                 # Tourism & context models
│   ├── static/                 # Web 3D viewer
│   └── main.py                 # FastAPI server
│
├── mobile-app/                 # React Native + Expo App
│   ├── src/
│   │   ├── components/         # React components
│   │   ├── services/           # Core services (AI, Speech, Location, Haptic)
│   │   ├── hooks/              # Custom React hooks
│   │   └── screens/            # App screens
│   ├── App.tsx                 # Main app component
│   └── app.json                # Expo configuration
│
└── setup.sh                    # Automated setup script
```

## 🎯 Features Overview

### Backend Features (Python FastAPI)
- **3D Model Visualization**: Interactive 3D viewer with AI model selection
- **Emotion Analysis**: BERT-based sentiment detection with gesture mapping
- **Tourism Intelligence**: Context-aware recommendations with user interest tracking
- **Multimodal Action Plans**: Coordinated speech, gesture, and UI responses
- **Plugin System**: External API integration (TripAdvisor, Thai News, Cultural Sites)
- **Performance Optimization**: Caching, CDN support, health monitoring

### Mobile App Features (React Native + Expo)

#### 🎤 Voice Interface
- **Natural Voice Commands**: "หาร้านอาหารใกล้ฉัน", "Find restaurants near me"
- **Speech-to-Text**: Expo Speech API with Google STT integration ready
- **Text-to-Speech**: AI responds with synthesized voice in Thai/English
- **Voice Command Processing**: Real-time AI analysis with emotion detection

#### 📍 Location & Places
- **Real-time GPS**: Continuous location tracking with background updates
- **Nearby Places**: Restaurants, temples, hotels, attractions, markets
- **Distance Calculation**: Accurate distance to places with ratings
- **Contextual Recommendations**: Weather, time, and preference-based suggestions

#### 🎮 3D AR Visualization
- **Three.js Integration**: Hardware-accelerated 3D rendering
- **Emotion-Responsive Animations**: 3D objects react to user emotions
- **Interactive Scenes**: Rotating models with particle effects
- **AR-Style Interface**: Overlay information on 3D scenes

#### 📳 Haptic Feedback System
- **Smart Vibrations**: Different patterns for different interactions
- **Place Recommendations**: Special vibration when places are found
- **Voice Feedback**: Haptic confirmation for voice commands
- **Error Notifications**: Distinct patterns for errors and success

#### 🌏 Thai Language Support
- **Complete Bilingual Interface**: Seamless Thai ↔ English switching
- **Cultural Context**: Thai tourism terminology and place categories
- **Thai NLP Processing**: Backend Thai language models
- **Voice Synthesis**: Natural Thai speech generation

## 🔧 Development

### Backend Development
```bash
cd painaidee_ai_assistant
python main.py --reload  # Development mode with auto-reload
# Access API docs: http://localhost:8000/docs
```

### Mobile App Development
```bash
cd mobile-app
npm start                # Start Expo development server
npm run android         # Run on Android device
npm run ios            # Run on iOS device (macOS only)
npm run web            # Run in web browser
```

### Testing the Integration
1. **Start Backend**: `cd painaidee_ai_assistant && python main.py`
2. **Start Mobile App**: `cd mobile-app && npm start`
3. **Test Voice Commands**: Use the microphone button to test voice recognition
4. **Test 3D Visualization**: Toggle the AR view to see 3D animations
5. **Test Language Switch**: Toggle between Thai and English interfaces

## 📱 Mobile App Usage

### Voice Commands
1. **Tap microphone button** to start listening
2. **Speak your command**:
   - Thai: "หาร้านอาหารใกล้ฉัน", "แนะนำสถานที่ท่องเที่ยว"
   - English: "Find restaurants near me", "Recommend attractions"
3. **AI responds with voice** and shows relevant places
4. **Feel haptic feedback** when places are recommended

### Quick Commands
- Preset buttons for common tourism queries
- One-tap access to popular searches
- Instant AI processing with visual feedback

### 3D AR Experience
- Toggle 3D view with AR button (👾/📱)
- Interactive 3D objects that respond to emotions
- Particle effects and dynamic animations
- Color changes based on AI-detected emotions

### Bilingual Interface
- Seamless language switching (TH ↔ EN)
- Complete UI translation
- Voice announcement of language changes
- Cultural context preservation

## 🌟 Technical Highlights

### Architecture Benefits
- **Separation of Concerns**: Backend handles AI/data, mobile handles UX
- **Reusable Backend**: Web and mobile clients use same AI APIs
- **Cross-Platform Mobile**: Single React Native codebase for iOS/Android
- **Real-time Integration**: WebSocket support for live updates
- **Scalable Design**: Microservices-ready architecture

### Performance Optimizations
- **3D Rendering**: Hardware-accelerated WebGL with LOD system
- **API Caching**: Redis caching for frequently accessed data
- **Image Optimization**: Compressed images and progressive loading
- **Background Processing**: Location updates and AI processing in background
- **Memory Management**: Efficient resource cleanup and garbage collection

### Security & Privacy
- **Location Privacy**: Location data processed locally when possible
- **Voice Data**: Speech processed securely with user consent
- **API Security**: Rate limiting and authentication ready
- **Data Encryption**: HTTPS for all API communications
- **Permissions**: Granular mobile permissions for features

## 📊 API Integration

The mobile app integrates with comprehensive backend APIs:

### Core AI APIs
- `POST /ai/select_model_with_emotion` - AI model selection with emotion analysis
- `POST /action/quick_action` - Generate multimodal action plans
- `POST /emotion/analyze_emotion` - Emotion analysis from text/voice

### Tourism APIs
- `POST /tourism/recommendations/integrated` - Context-aware place recommendations
- `POST /tourism/recommendations/contextual` - Weather and time-based suggestions
- `GET /tourism/analytics/tourist_graph` - User interest analytics

### Location & Places
- `GET /location/nearby_places` - Find places near user location
- `POST /location/analyze_context` - Analyze location context for recommendations

## 🎯 Production Deployment

### Backend Deployment
```bash
# Docker deployment
docker build -t painaidee-backend .
docker run -p 8000:8000 painaidee-backend

# Or direct deployment
uvicorn main:app --host 0.0.0.0 --port 8000 --workers 4
```

### Mobile App Deployment
```bash
# Build Android APK
expo build:android

# Build iOS IPA
expo build:ios

# Deploy to app stores
expo submit
```

### Cloud Deployment Options
- **Backend**: AWS ECS, Google Cloud Run, Heroku, DigitalOcean
- **Mobile**: Expo Application Services (EAS) for builds and updates
- **Database**: PostgreSQL/MongoDB for user data and preferences
- **CDN**: CloudFront/CloudFlare for 3D model assets

## 🌍 Legacy Web Features

The original web-based system continues to provide:

### ✨ Web 3D Model Selection
- **Natural Language Processing**: Ask questions like "Show me a walking person"
- **Smart Model Mapping**: AI analyzes keywords and context to select appropriate 3D models
- **Confidence Scoring**: Each selection includes confidence percentage for transparency
- **Multi-language Support**: Supports both English and Thai language queries

### 🎭 Advanced Emotion Analysis System
- **Sentiment Analysis**: BERT-based emotion detection from user text input
- **Emotion-to-Gesture Mapping**: Automatic mapping of 9 emotions to appropriate 3D gestures
- **Tone Adjustment**: Dynamic tone adjustment based on detected user emotions
- **Context Awareness**: Considers conversation context for better emotional understanding
- **Thai Cultural Gestures**: Specialized gesture library adapted for Thai cultural context

### 🌍 Tourism Intelligence Features
- **Tourist Interest Graph**: Captures and analyzes user interests from browsing history
- **Contextual Recommendations**: Real-time recommendations based on weather, time, and location
- **Weather Integration**: Suggests indoor/outdoor activities based on current conditions
- **Seasonal Adaptations**: Provides season-appropriate travel suggestions
- **Cultural Context**: Understands Thai tourism preferences and cultural nuances

### 🎮 Interactive 3D Viewer
- **Mouse Controls**: Rotate, zoom, and pan around 3D models
- **Click Interactions**: Click on models to view detailed information
- **Real-time Updates**: Seamless model switching based on user queries
- **Emotion-based Gestures**: Models display appropriate gestures based on user sentiment
- **Performance Optimization**: LOD (Level of Detail) system for smooth performance

### 🎪 Multimodal Action Plan System
- **Speech Output**: Text-to-speech in Thai and English
- **Gesture Animation**: Coordinated 3D gestures (nod, point, wave, etc.)
- **Scene Interaction**: Dynamic camera movement and focus
- **UI Integration**: Automatic display of relevant UI components and buttons

### 📦 Available 3D Models
- **Man.fbx**: Basic human character model (296 KB)
- **Idle.fbx**: Character in standing/idle pose (1.09 MB)
- **Walking.fbx**: Walking animation sequence (743 KB)
- **Running.fbx**: Running animation sequence (734 KB)
- **Man_Rig.fbx**: Rigged character for custom animations (698 KB)

### 🌐 Web API Endpoints

#### Core AI & Model Selection
- `POST /ai/select_model` - AI model selection based on questions
- `POST /ai/select_model_with_emotion` - Enhanced model selection with emotion analysis
- `GET /ai/models` - List all available 3D models
- `GET /ai/models/{model_name}` - Get specific model information
- `GET /models/{model_name}` - Download 3D model files

#### Emotion Analysis
- `POST /emotion/analyze_emotion` - Analyze user emotion from text
- `POST /emotion/recommend_gesture` - Get gesture recommendations for emotions
- `POST /emotion/analyze_and_recommend` - Combined emotion analysis and gesture recommendation
- `GET /emotion/gesture_mappings` - Get all emotion-to-gesture mappings
- `GET /emotion/health` - Emotion analysis service health check

#### Tourism Intelligence
- `POST /tourism/capture_interest` - Capture user interest from interaction
- `POST /tourism/recommendations/tourist` - Get tourist interest-based recommendations
- `POST /tourism/recommendations/contextual` - Get contextual recommendations
- `POST /tourism/recommendations/time_specific` - Get time-specific recommendations
- `POST /tourism/recommendations/integrated` - Get integrated recommendations
- `GET /tourism/context/current` - Get current contextual factors
- `GET /tourism/analytics/tourist_graph` - Get tourist interest analytics

#### Multimodal Action Plans
- `POST /action_plan/generate_plan` - Generate multimodal action plan
- `POST /action_plan/execute_plan` - Execute coordinated actions
- `POST /action_plan/quick_action` - Generate quick action from natural language
- `GET /action_plan/templates` - Get available action templates

#### Performance & Management
- `GET /performance/system_health` - Overall system health check
- `GET /performance/model_performance` - 3D model performance metrics
- `POST /admin/cache/clear` - Clear system caches
- `GET /versioning/models` - Model version information

## 🤝 Contributing

We welcome contributions! Areas for contribution include:

### Development Areas
- **Enhanced 3D Models**: More sophisticated 3D tourism models
- **Voice Recognition**: Improved Thai speech recognition accuracy
- **AR Features**: Advanced AR capabilities with object detection
- **Tourism Data**: More comprehensive place databases
- **Performance**: Optimization for lower-end devices
- **Accessibility**: Enhanced accessibility features

### For Thai Developers | สำหรับนักพัฒนาชาวไทย

#### Getting Started | เริ่มต้นการมีส่วนร่วม
1. **Fork โปรเจกต์** - คลิก Fork ที่มุมขวาบนของหน้า GitHub
2. **Clone โปรเจกต์** - โคลนโปรเจกต์มายังเครื่องของคุณ
3. **สร้าง Branch ใหม่** - สร้าง branch สำหรับฟีเจอร์ใหม่
4. **พัฒนาและทดสอบ** - เพิ่มฟีเจอร์ใหม่และเขียนการทดสอบ
5. **ส่ง Pull Request** - ส่งการเปลี่ยนแปลงกลับมายังโปรเจกต์หลัก

#### Thai Language Contributions | การมีส่วนร่วมด้านภาษาไทย
- **การแปล**: ช่วยแปลเอกสารและข้อความในระบบ
- **ข้อมูลวัฒนธรรม**: เพิ่มข้อมูลเกี่ยวกับวัฒนธรรมไทยและท่องเที่ยว
- **การทดสอบภาษาไทย**: ทดสอบความสามารถในการประมวลผลภาษาไทย
- **ฐานข้อมูลท่องเที่ยว**: เพิ่มข้อมูลสถานที่ท่องเที่ยวในประเทศไทย

## 📄 License

This project is licensed under the MIT License - promoting open-source development for Thai tourism technology.

---

**Made with ❤️ for Thai tourism and AI innovation**

**สร้างด้วยความรักเพื่อการท่องเที่ยวไทยและนวัตกรรม AI**

### 🔗 Quick Links
- **🎮 Try Web Demo**: `http://localhost:8000/static/demo.html`
- **📱 Mobile Demo**: `http://localhost:8081` (after running mobile app)
- **📚 API Documentation**: `http://localhost:8000/docs`
- **🏛️ 3D Gallery**: `http://localhost:8000/static/gallery.html`
- **🤖 Admin Dashboard**: `http://localhost:8000/admin`