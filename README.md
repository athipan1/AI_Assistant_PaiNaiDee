# AI_Assistant_PaiNaiDee | ผู้ช่วย AI ไปไหนดี

## 🎯 Overview | ภาพรวมโปรเจกต์

PaiNaiDee AI Assistant is an intelligent Thai tourism assistant that now features **3D model visualization** with AI-powered question analysis. Users can ask questions in natural language and the AI will automatically select and display relevant 3D models to enhance the user experience.

### ภาษาไทย | Thai Summary
**ผู้ช่วย AI ไปไหนดี** เป็นระบบผู้ช่วยท่องเที่ยวอัจฉริยะสำหรับประเทศไทย ที่มาพร้อมกับ:
- 🤖 การวิเคราะห์อารมณ์และการแสดงท่าทางแบบ 3D
- 🌍 ระบบแนะนำสถานที่ท่องเที่ยวตามบริบท (สภาพอากาศ เวลา ความสนใจ)
- 🎭 การโต้ตอบแบบหลายรูปแบบ (เสียง ภาพ การแสดงผล 3D)
- 🧠 AI ขั้นสูงที่เข้าใจภาษาธรรมชาติและตอบสนองตามอารมณ์ผู้ใช้
- 📱 API ที่ครบครันสำหรับการพัฒนาแอพพลิเคชั่นท่องเที่ยว

![PaiNaiDee 3D Demo](https://github.com/user-attachments/assets/36c99aa7-4aa5-4df7-9f9c-bcf94e4d5e8d)

## ✨ Features | ฟีเจอร์หลัก

### 🤖 AI-Powered 3D Model Selection | ระบบเลือกโมเดล 3D อัตโนมัติ
- **Natural Language Processing**: Ask questions like "Show me a walking person" or "Display running animation"
- **Smart Model Mapping**: AI analyzes keywords and context to select appropriate 3D models
- **Confidence Scoring**: Each selection includes confidence percentage for transparency
- **Multi-language Support**: Supports both English and Thai language queries

### 🎭 Advanced Emotion Analysis System | ระบบวิเคราะห์อารมณ์ขั้นสูง
- **Sentiment Analysis**: BERT-based emotion detection from user text input
- **Emotion-to-Gesture Mapping**: Automatic mapping of 9 emotions to appropriate 3D gestures
- **Tone Adjustment**: Dynamic tone adjustment based on detected user emotions
- **Context Awareness**: Considers conversation context for better emotional understanding
- **Thai Cultural Gestures**: Specialized gesture library adapted for Thai cultural context

### 🌍 Tourism Intelligence Features | ระบบแนะนำท่องเที่ยวอัจฉริยะ
- **Tourist Interest Graph**: Captures and analyzes user interests from browsing history
- **Contextual Recommendations**: Real-time recommendations based on weather, time, and location
- **Weather Integration**: Suggests indoor/outdoor activities based on current conditions
- **Seasonal Adaptations**: Provides season-appropriate travel suggestions
- **Cultural Context**: Understands Thai tourism preferences and cultural nuances

### 🎮 Interactive 3D Viewer | ระบบแสดงผล 3D แบบโต้ตอบ
- **Mouse Controls**: Rotate, zoom, and pan around 3D models
- **Click Interactions**: Click on models to view detailed information
- **Real-time Updates**: Seamless model switching based on user queries
- **Emotion-based Gestures**: Models display appropriate gestures based on user sentiment
- **Performance Optimization**: LOD (Level of Detail) system for smooth performance

### 🎪 Multimodal Action Plan System | ระบบแผนการทำงานแบบหลายรูปแบบ
- **Speech Output**: Text-to-speech in Thai and English
- **Gesture Animation**: Coordinated 3D gestures (nod, point, wave, etc.)
- **Scene Interaction**: Dynamic camera movement and focus
- **UI Integration**: Automatic display of relevant UI components and buttons

### 📦 Available 3D Models | โมเดล 3D ที่มีให้ใช้งาน
- **Man.fbx**: Basic human character model (296 KB)
- **Idle.fbx**: Character in standing/idle pose (1.09 MB)
- **Walking.fbx**: Walking animation sequence (743 KB)
- **Running.fbx**: Running animation sequence (734 KB)
- **Man_Rig.fbx**: Rigged character for custom animations (698 KB)

### 🌐 API Endpoints | จุดเชื่อมต่อ API

#### Core AI & Model Selection | AI หลักและการเลือกโมเดล
- `POST /ai/select_model` - AI model selection based on questions
- `POST /ai/select_model_with_emotion` - Enhanced model selection with emotion analysis
- `GET /ai/models` - List all available 3D models
- `GET /ai/models/{model_name}` - Get specific model information
- `GET /models/{model_name}` - Download 3D model files

#### Emotion Analysis | การวิเคราะห์อารมณ์
- `POST /emotion/analyze_emotion` - Analyze user emotion from text
- `POST /emotion/recommend_gesture` - Get gesture recommendations for emotions
- `POST /emotion/analyze_and_recommend` - Combined emotion analysis and gesture recommendation
- `GET /emotion/gesture_mappings` - Get all emotion-to-gesture mappings
- `GET /emotion/health` - Emotion analysis service health check

#### Tourism Intelligence | ระบบท่องเที่ยวอัจฉริยะ
- `POST /tourism/capture_interest` - Capture user interest from interaction
- `POST /tourism/recommendations/tourist` - Get tourist interest-based recommendations
- `POST /tourism/recommendations/contextual` - Get contextual recommendations
- `POST /tourism/recommendations/time_specific` - Get time-specific recommendations
- `POST /tourism/recommendations/integrated` - Get integrated recommendations
- `GET /tourism/context/current` - Get current contextual factors
- `GET /tourism/analytics/tourist_graph` - Get tourist interest analytics

#### Multimodal Action Plans | แผนการทำงานแบบหลายรูปแบบ
- `POST /action_plan/generate_plan` - Generate multimodal action plan
- `POST /action_plan/execute_plan` - Execute coordinated actions
- `POST /action_plan/quick_action` - Generate quick action from natural language
- `GET /action_plan/templates` - Get available action templates

#### Performance & Management | ประสิทธิภาพและการจัดการ
- `GET /performance/system_health` - Overall system health check
- `GET /performance/model_performance` - 3D model performance metrics
- `POST /admin/cache/clear` - Clear system caches
- `GET /versioning/models` - Model version information

## 🚀 Quick Start | เริ่มต้นใช้งาน

### 🌟 การทดลองใช้งานแบบง่าย | Easy Testing Options

#### 🚀 Deploy บน Hugging Face Spaces (แบบถาวร | Permanent)
สำหรับการใช้งานจริงและการแบ่งปันโปรเจกต์ | For production use and project sharing

[![🤗 Deploy on Hugging Face Spaces](https://huggingface.co/datasets/huggingface/badges/raw/main/deploy-to-spaces-lg.svg)](https://huggingface.co/spaces/new?template=athipan1/AI_Assistant_PaiNaiDee)

**ขั้นตอนการ Deploy | Deployment Steps:**
1. คลิกปุ่ม "Deploy on Hugging Face Spaces" ด้านบน
2. สร้างบัญชี Hugging Face (ฟรี) หากยังไม่มี - [สมัครที่นี่](https://huggingface.co/join)
3. ตั้งชื่อ Space ของคุณ เช่น "my-painaidee-assistant" 
4. เลือก "Public" หรือ "Private" ตามต้องการ
5. คลิก "Create Space" และรอการติดตั้งประมาณ 5-10 นาที
6. เข้าใช้งานผ่าน URL ที่ได้รับ เช่น `https://huggingface.co/spaces/yourname/my-painaidee-assistant`

**วิธีใช้งานหลังจาก Deploy:**
- เปิด Web interface ผ่าน Gradio
- ทดสอบ AI model selection และ emotion analysis
- เข้าถึง API documentation ที่ `/docs`
- ใช้งาน 3D viewer (หากพร้อมใช้งาน)

**ข้อดี | Benefits:**
- ✅ ใช้งานได้ตลอด 24/7
- ✅ แบ่งปันให้คนอื่นได้ง่าย
- ✅ ไม่ต้องติดตั้งอะไรในเครื่อง
- ✅ รองรับผู้ใช้หลายคนพร้อมกัน

#### 🐍 Run บน Google Colab (แบบชั่วคราว | Temporary)
สำหรับการทดลองใช้งานและการพัฒนา | For testing and development

[![🔬 Open in Colab](https://colab.research.google.com/assets/colab-badge.svg)](https://colab.research.google.com/github/athipan1/AI_Assistant_PaiNaiDee/blob/main/PaiNaiDee_Colab_Deploy.ipynb)

**ขั้นตอนการใช้งาน | Usage Steps:**
1. คลิกปุ่ม "Open in Colab" ด้านบน
2. สมัครบัญชี [ngrok](https://ngrok.com/) (ฟรี) เพื่อรับ auth token
3. คัดลอก auth token จาก [ngrok dashboard](https://dashboard.ngrok.com/get-started/your-authtoken)
4. ใน Colab: เลือก Runtime > Change runtime type > GPU (แนะนำ)
5. รันเซลล์ทีละเซลล์ตามลำดับ (กด Shift+Enter)
6. ใส่ ngrok token ในเซลล์ที่ 3 ตัวแปร `NGROK_TOKEN`
7. รอให้ติดตั้งเสร็จและคลิกลิงก์ที่ได้รับ

**วิธีใช้งานหลังจากเริ่มแล้ว:**
- ทดสอบ API endpoints ต่างๆ ผ่าน `/docs`
- ใช้งาน 3D model selection ผ่าน natural language
- ทดลอง emotion analysis ระบบ
- เข้าถึง tourism recommendations

**ข้อดี | Benefits:**
- ✅ ทดลองใช้ได้ทันที
- ✅ ใช้ GPU ฟรีจาก Google
- ✅ ไม่ต้องติดตั้งอะไรในเครื่อง
- ✅ เหมาะสำหรับการเรียนรู้และทดสอบ

**หมายเหตุ | Note:** เซิร์ฟเวอร์จะหยุดทำงานเมื่อปิด Colab หรือไม่ใช้งานเกิน 12 ชั่วโมง

---

### 🔧 การติดตั้งในเครื่อง | Local Installation

### System Requirements | ความต้องการของระบบ
- **Python**: 3.8+ (recommended: 3.9 or 3.10)
- **Memory**: Minimum 4GB RAM (8GB+ recommended for AI models)
- **Storage**: At least 2GB free space for models and dependencies
- **Browser**: Modern browser with WebGL support (Chrome 80+, Firefox 75+, Safari 13+)
- **Internet**: Required for initial setup and AI model downloads

### Prerequisites | ข้อกำหนดเบื้องต้น
- Python 3.8+
- Web browser with WebGL support
- Git for cloning the repository
- pip for package management

### Installation & Setup | การติดตั้งและตั้งค่า

1. **Clone the repository | โคลนโปรเจกต์**
   ```bash
   git clone https://github.com/athipan1/AI_Assistant_PaiNaiDee.git
   cd AI_Assistant_PaiNaiDee/painaidee_ai_assistant
   ```

2. **Create virtual environment (recommended) | สร้าง virtual environment**
   ```bash
   # Windows
   python -m venv venv
   venv\Scripts\activate
   
   # macOS/Linux
   python3 -m venv venv
   source venv/bin/activate
   ```

3. **Install dependencies | ติดตั้ง dependencies**
   ```bash
   pip install -r requirements.txt
   
   # For development with all features
   pip install -r requirements.txt scikit-learn
   ```

4. **Environment Configuration | ตั้งค่าสิ่งแวดล้อม**
   ```bash
   # Copy example environment file
   cp .env.example .env
   
   # Edit .env file with your preferences
   # nano .env  # Linux/macOS
   # notepad .env  # Windows
   ```

5. **Start the server | เริ่มเซิร์ฟเวอร์**
   ```bash
   # Option 1: FastAPI server (recommended for production)
   python main.py
   
   # Option 2: Simple test server (for development/demo)
   python test_server.py
   
   # Option 3: With specific port
   uvicorn main:app --host 0.0.0.0 --port 8000 --reload
   ```

6. **Open in browser | เปิดในเบราว์เซอร์**
   ```
   http://localhost:8000
   ```

### Quick Health Check | ตรวจสอบการทำงาน
```bash
# Test if server is running
curl http://localhost:8000/performance/system_health

# Test AI model selection
curl -X POST -H "Content-Type: application/json" \
     -d '{"question": "Show me a walking person"}' \
     http://localhost:8000/ai/select_model

# Test emotion analysis
curl -X POST -H "Content-Type: application/json" \
     -d '{"text": "I am excited about my trip!"}' \
     http://localhost:8000/emotion/analyze_emotion
```

## 📚 Usage Examples

### Natural Language Queries

```javascript
// Example API calls for model selection
const response = await fetch('/ai/select_model', {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({ 
        question: "Show me a walking person",
        language: "en" 
    })
});

// Enhanced model selection with emotion analysis
const emotionResponse = await fetch('/ai/select_model_with_emotion', {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({ 
        question: "I'm excited to see walking animations!",
        analyze_emotion: true
    })
});

// Emotion analysis only
const emotionOnly = await fetch('/emotion/analyze_emotion', {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({ 
        text: "I'm worried about my trip",
        language: "en" 
    })
});

// Response includes emotion and gesture data:
{
    "model_selection": {
        "selected_model": "Walking.fbx",
        "confidence": 0.8,
        "description": "Character animation showing walking motion"
    },
    "emotion_analysis": {
        "primary_emotion": "excited",
        "suggested_gesture": "excited_jump",
        "tone_adjustment": "energetic and enthusiastic"
    },
    "status": "success"
}
```

### Supported Question Types

| Question Examples | Selected Model | Emotion Detection | Gesture Recommendation |
|------------------|----------------|-------------------|------------------------|
| "Show me a person", "Display a character" | Man.fbx | neutral | neutral_idle |
| "I'm excited to see walking!" | Walking.fbx | excited | excited_jump |
| "I'm worried about running", "Show running" | Running.fbx | worried | reassuring_gesture |
| "Calm standing pose", "Peaceful character" | Idle.fbx | calm | calm_standing |
| "I'm curious about rigged models" | Man_Rig.fbx | curious | thoughtful_pose |

## 🔧 Technical Architecture | สถาปัตยกรรมเทคนิค

### System Overview | ภาพรวมระบบ
```
┌─────────────────┐    ┌──────────────────┐    ┌─────────────────┐
│   Frontend      │    │   FastAPI        │    │   AI Models     │
│   (3D Viewer)   │◄──►│   Backend        │◄──►│   (BERT, etc.)  │
└─────────────────┘    └──────────────────┘    └─────────────────┘
         │                       │                       │
         │              ┌────────▼────────┐             │
         │              │  Model Storage  │             │
         └──────────────►│   (FBX Files)   │◄────────────┘
                        └─────────────────┘
```

### Core Components | ส่วนประกอบหลัก

#### 1. AI Model Selection Algorithm | อัลกอริทึมการเลือกโมเดล AI
```python
class ModelSelector:
    def analyze_question(self, question: str) -> Dict[str, Any]:
        # 1. Keyword extraction and matching
        # 2. Confidence scoring based on context
        # 3. Model selection with fallback logic
        # 4. Return structured response with metadata
```

#### 2. Emotion Analysis Engine | เครื่องมือวิเคราะห์อารมณ์
```python
class EmotionAnalysisAgent:
    def analyze_emotion(self, text: str) -> EmotionResult:
        # 1. BERT-based sentiment analysis
        # 2. Keyword fallback for reliability
        # 3. Confidence scoring and validation
        # 4. Gesture recommendation mapping
```

#### 3. Tourism Intelligence System | ระบบท่องเที่ยวอัจฉริยะ
```python
class TouristInterestGraph:
    def capture_interest_from_interaction(self, interaction_data: Dict) -> Interest:
        # 1. Extract interests from user interactions
        # 2. Classify interest types and intensities
        # 3. Update user profile and preferences
        # 4. Generate personalized recommendations
```

#### 4. Multimodal Action Coordinator | ระบบประสานงานแอคชั่นหลายรูปแบบ
```python
class ActionPlanExecutor:
    def execute_plan(self, action_plan: ActionPlan) -> ExecutionResult:
        # 1. Coordinate speech, gesture, and UI actions
        # 2. Handle timing and synchronization
        # 3. Manage 3D scene interactions
        # 4. Generate structured frontend responses
```

### Frontend Integration | การรวมระบบส่วนหน้า
```javascript
// 3D viewer initialization
function initializeViewer() {
    scene = new THREE.Scene();
    camera = new THREE.PerspectiveCamera(75, width/height, 0.1, 1000);
    renderer = new THREE.WebGLRenderer({ antialias: true });
    controls = new THREE.OrbitControls(camera, renderer.domElement);
}

// Enhanced model loading with emotion and context
async function loadSelectedModelWithContext() {
    // 1. Analyze user input for emotion and intent
    const analysis = await analyzeUserInput(userText);
    
    // 2. Get AI model recommendation
    const modelResponse = await fetch('/ai/select_model_with_emotion', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
            question: userText,
            analyze_emotion: true,
            context: getCurrentContext()
        })
    });
    
    // 3. Load model with appropriate gestures
    const result = await modelResponse.json();
    await loadModel(result.model_selection.selected_model);
    applyEmotionGestures(result.emotion_analysis);
    
    // 4. Execute multimodal action plan
    if (result.action_plan) {
        executeActionPlan(result.action_plan);
    }
}

// Context-aware tourism recommendations
async function getTourismRecommendations() {
    const context = {
        weather: await getWeatherData(),
        time: new Date(),
        user_preferences: getUserPreferences()
    };
    
    const response = await fetch('/tourism/recommendations/integrated', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
            user_id: getCurrentUserId(),
            query: getCurrentQuery(),
            context: context
        })
    });
    
    return await response.json();
}
```

### File Structure | โครงสร้างไฟล์
```
AI_Assistant_PaiNaiDee/
├── painaidee_ai_assistant/           # Main application directory
│   ├── main.py                       # FastAPI application entry point
│   ├── test_server.py               # Development server
│   ├── requirements.txt             # Python dependencies
│   ├── .env.example                 # Environment configuration template
│   ├── Dockerfile                   # Container deployment
│   │
│   ├── api/                         # API routes and endpoints
│   │   ├── ai_routes.py            # Core AI model selection
│   │   ├── emotion_routes.py       # Emotion analysis endpoints
│   │   ├── tourism_routes.py       # Tourism intelligence APIs
│   │   ├── action_plan_routes.py   # Multimodal action plans
│   │   ├── gesture_routes.py       # Gesture recognition APIs
│   │   ├── model_routes.py         # 3D model management
│   │   ├── performance_routes.py   # System monitoring
│   │   └── admin_routes.py         # Administrative functions
│   │
│   ├── agents/                      # AI agents and core logic
│   │   ├── model_selector.py       # AI model selection logic
│   │   ├── emotion_analysis.py     # Emotion detection system
│   │   ├── action_plan_system.py   # Multimodal coordination
│   │   └── gesture_recognition.py  # Gesture processing
│   │
│   ├── models/                      # Data models and utilities
│   │   ├── tourist_interest_graph.py    # User interest tracking
│   │   ├── contextual_recommendations.py # Context-aware suggestions
│   │   ├── cache_manager.py        # Performance optimization
│   │   └── external_apis.py        # External service integrations
│   │
│   ├── static/                      # Frontend files
│   │   ├── index.html              # Main 3D viewer interface
│   │   ├── demo.html               # Demo version (offline)
│   │   ├── css/                    # Styling files
│   │   └── js/                     # JavaScript logic
│   │
│   ├── assets/                      # Static assets
│   │   └── models/Fbx/             # 3D model files
│   │       ├── Man.fbx             # Basic character
│   │       ├── Idle.fbx            # Standing pose
│   │       ├── Walking.fbx         # Walking animation
│   │       ├── Running.fbx         # Running animation
│   │       └── Man_Rig.fbx         # Rigged for animations
│   │
│   ├── tests/                       # Test suites
│   │   ├── test_ai_selection.py    # AI model selection tests
│   │   ├── test_emotion_analysis.py # Emotion system tests
│   │   ├── test_tourism_features.py # Tourism intelligence tests
│   │   └── test_integration.py     # Integration test suite
│   │
│   ├── tools/                       # Development utilities
│   ├── scripts/                     # Automation scripts
│   └── cache/                       # Runtime cache directory
│
├── README.md                        # This documentation
├── .gitignore                       # Git ignore rules
└── Dockerfile                       # Container configuration
```

## 🎯 Model Mapping Logic

The AI uses keyword-based analysis with confidence scoring:

```python
model_mapping = {
    # Person/Character keywords
    "person": "Man.fbx",
    "human": "Man.fbx", 
    "character": "Man.fbx",
    
    # Animation keywords
    "walking": "Walking.fbx",
    "running": "Running.fbx",
    "idle": "Idle.fbx",
    
    # Technical keywords
    "rig": "Man_Rig.fbx",
    "animation": "Man_Rig.fbx"
}
```

Confidence is calculated based on:
- Number of matching keywords
- Context relevance
- Question complexity

## 🌟 Future Enhancements | แผนการพัฒนาต่อไป

### Planned Features | ฟีเจอร์ที่วางแผนไว้

#### Phase 1: Enhanced AI & Language Support | ขั้นตอนที่ 1: AI และการรองรับภาษาที่ดีขึ้น
- [ ] **Advanced AI Models**: Integration with llama.cpp, OpenChat, OpenHermes
- [ ] **Thai Language Processing**: Full Thai language support for emotion analysis and NLP
- [ ] **Voice Commands**: Speech-to-text integration with emotion detection
- [ ] **Thai Cultural Context**: Enhanced understanding of Thai cultural preferences
- [ ] **Multilingual Tourism**: Support for major tourist languages (Chinese, Japanese, Korean)

#### Phase 2: Expanded 3D & Interaction | ขั้นตอนที่ 2: 3D และการโต้ตอบที่ขยายผล
- [ ] **More 3D Formats**: Support for GLB, OBJ, GLTF files
- [ ] **Animation Controls**: Play/pause/speed controls for animations
- [ ] **Custom Gestures**: User-defined gesture library
- [ ] **AR/VR Support**: WebXR compatibility for immersive experiences
- [ ] **Real-time Collaboration**: Multi-user 3D sessions
- [ ] **Enhanced Gestures**: More sophisticated 3D gesture library with Thai cultural gestures

#### Phase 3: Advanced Tourism Intelligence | ขั้นตอนที่ 3: ระบบท่องเที่ยวอัจฉริยะขั้นสูง
- [ ] **Real-time Weather Integration**: Live weather API for accurate recommendations
- [ ] **Location-based Services**: GPS integration for precise location recommendations
- [ ] **Social Features**: Group recommendations and social clustering
- [ ] **Personalized Learning**: AI that learns individual user preferences over time
- [ ] **Tourism Database Integration**: Connection with official Thai tourism databases
- [ ] **Review System Integration**: Incorporate real user reviews and ratings

#### Phase 4: Performance & Enterprise Features | ขั้นตอนที่ 4: ประสิทธิภาพและฟีเจอร์องค์กร
- [ ] **Model Caching**: Faster loading for frequently used models
- [ ] **Progressive Loading**: Streaming for large model files
- [ ] **Analytics Dashboard**: Usage statistics and popular models
- [ ] **A/B Testing Framework**: Testing different recommendation algorithms
- [ ] **Enterprise API**: Scalable API for tourism businesses
- [ ] **Mobile SDK**: Native mobile app integration

### Technical Improvements | การปรับปรุงเทคนิค

#### Architecture Enhancements | การปรับปรุงสถาปัตยกรรม
- [ ] **Microservices Architecture**: Break down into smaller, scalable services
- [ ] **Container Orchestration**: Kubernetes deployment support
- [ ] **Database Integration**: PostgreSQL/MongoDB for persistent data storage
- [ ] **Redis Caching**: Distributed caching for improved performance
- [ ] **Load Balancing**: Support for high-traffic deployments
- [ ] **CDN Integration**: Global content delivery for 3D assets

#### AI & ML Improvements | การปรับปรุง AI และ Machine Learning
- [ ] **Custom Model Training**: Train models on Thai tourism data
- [ ] **Reinforcement Learning**: AI that improves from user interactions
- [ ] **Computer Vision**: Image-based tourism recommendations
- [ ] **Natural Language Generation**: Dynamic Thai language responses
- [ ] **Recommendation Engine**: Advanced collaborative filtering
- [ ] **Sentiment Analysis**: More nuanced emotion detection

#### Developer Experience | ประสบการณ์นักพัฒนา
- [ ] **TypeScript Support**: Full type safety for frontend development
- [ ] **GraphQL API**: More flexible API queries
- [ ] **SDK Development**: Python, JavaScript, and mobile SDKs
- [ ] **Documentation**: Interactive API documentation with examples
- [ ] **Testing Framework**: Comprehensive automated testing
- [ ] **CI/CD Pipeline**: Automated deployment and testing

### Integration Opportunities | โอกาสการรวมระบบ

#### Tourism Industry Partners | พันธมิตรอุตสาหกรรมท่องเที่ยว
- [ ] **Hotel Booking Systems**: Integration with major booking platforms
- [ ] **Transportation APIs**: Connect with flight, train, and bus booking
- [ ] **Tour Operators**: Partnership with local tour companies
- [ ] **Restaurant Platforms**: Food and dining recommendations
- [ ] **Cultural Sites**: Integration with museums and cultural attractions

#### Government & Official Sources | แหล่งข้อมูลราชการและทางการ
- [ ] **Tourism Authority of Thailand (TAT)**: Official tourism data integration
- [ ] **Weather Department**: Real-time weather and safety information
- [ ] **Transportation Ministry**: Public transport schedules and updates
- [ ] **Cultural Heritage**: Historic site information and cultural context
- [ ] **Emergency Services**: Safety alerts and emergency contact integration

#### Technology Ecosystem | ระบบนิเวศเทคโนโลยี
- [ ] **Google Maps Integration**: Enhanced location services
- [ ] **Social Media APIs**: Integration with Facebook, Instagram, TikTok
- [ ] **Payment Gateways**: Seamless booking and payment processing
- [ ] **Analytics Platforms**: Advanced user behavior tracking
- [ ] **Cloud Services**: AWS, Google Cloud, Azure deployment options

## 🛠️ Development | การพัฒนา

### Development Environment Setup | ตั้งค่าสภาพแวดล้อมการพัฒนา

#### Prerequisites for Developers | ข้อกำหนดสำหรับนักพัฒนา
```bash
# Required tools
python --version  # Should be 3.8+
git --version
node --version    # Optional, for frontend development
```

#### Setting up Development Environment | ตั้งค่าสภาพแวดล้อมการพัฒนา
```bash
# 1. Clone and setup
git clone https://github.com/athipan1/AI_Assistant_PaiNaiDee.git
cd AI_Assistant_PaiNaiDee/painaidee_ai_assistant

# 2. Create virtual environment
python -m venv venv
source venv/bin/activate  # Linux/macOS
# or
venv\Scripts\activate     # Windows

# 3. Install development dependencies
pip install -r requirements.txt
pip install pytest pytest-asyncio black flake8  # Development tools

# 4. Setup pre-commit hooks (optional)
pip install pre-commit
pre-commit install
```

### Adding New Features | การเพิ่มฟีเจอร์ใหม่

#### Adding New 3D Models | การเพิ่มโมเดล 3D ใหม่
```bash
# 1. Add FBX files to assets directory
cp your_model.fbx assets/models/Fbx/

# 2. Update model descriptions in model_routes.py
# Edit: painaidee_ai_assistant/api/model_routes.py
```

```python
# 3. Add model information to the models dictionary
MODELS = {
    "your_model.fbx": {
        "name": "Your Model",
        "description": "Description of your model",
        "size": "file_size_in_bytes",
        "category": "animation|character|prop",
        "keywords": ["keyword1", "keyword2"],
        "emotion_compatibility": ["happy", "excited"]
    }
}

# 4. Add keyword mappings for AI selection
model_mapping = {
    "your_keyword": "your_model.fbx",
    # ... existing mappings
}
```

#### Adding New Emotions | การเพิ่มอารมณ์ใหม่
```python
# 1. Edit emotion analysis agent
# File: painaidee_ai_assistant/agents/emotion_analysis.py

class EmotionAnalysisAgent:
    def __init__(self):
        self.emotion_gesture_mappings = {
            # Add new emotion-gesture pair
            "new_emotion": {
                "gesture": "new_gesture_name",
                "expression": "facial_expression",
                "animation_style": "gentle|energetic|smooth"
            }
        }

# 2. Update keyword patterns
emotion_keywords = {
    "new_emotion": ["keyword1", "keyword2", "pattern"]
}
```

#### Adding New API Endpoints | การเพิ่ม API endpoint ใหม่
```python
# 1. Create new route file
# File: painaidee_ai_assistant/api/new_feature_routes.py

from fastapi import APIRouter, HTTPException
from pydantic import BaseModel

router = APIRouter(prefix="/new_feature", tags=["new_feature"])

class NewFeatureRequest(BaseModel):
    input_data: str
    optional_param: str = "default"

@router.post("/endpoint")
async def new_endpoint(request: NewFeatureRequest):
    try:
        # Your logic here
        result = process_request(request)
        return {"status": "success", "data": result}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

# 2. Register route in main.py
# Add to main.py imports and include_router calls
```

#### Adding Tourism Features | การเพิ่มฟีเจอร์ท่องเที่ยว
```python
# 1. Extend tourist interest categories
# File: painaidee_ai_assistant/models/tourist_interest_graph.py

class TouristInterestGraph:
    def __init__(self):
        self.interest_categories = {
            "new_category": {
                "keywords": ["keyword1", "keyword2"],
                "weight": 1.0,
                "related_models": ["model1.fbx", "model2.fbx"]
            }
        }

# 2. Add contextual factors
# File: painaidee_ai_assistant/models/contextual_recommendations.py

class ContextualRecommendationEngine:
    def add_contextual_factor(self, factor_name: str, 
                            calculation_function: callable):
        self.contextual_factors[factor_name] = calculation_function
```

### Testing | การทดสอบ

#### Running Tests | การรันการทดสอบ
```bash
# Run all tests
python -m pytest tests/

# Run specific test file
python -m pytest tests/test_ai_selection.py

# Run with coverage
python -m pytest tests/ --cov=painaidee_ai_assistant

# Run integration tests
python test_multimodal_integration.py
```

#### Writing New Tests | การเขียนการทดสอบใหม่
```python
# File: tests/test_new_feature.py
import pytest
from fastapi.testclient import TestClient
from main import app

client = TestClient(app)

def test_new_feature_endpoint():
    response = client.post("/new_feature/endpoint", 
                          json={"input_data": "test"})
    assert response.status_code == 200
    assert response.json()["status"] == "success"

@pytest.mark.asyncio
async def test_async_function():
    result = await your_async_function("test_input")
    assert result is not None
```

### Performance Optimization | การเพิ่มประสิทธิภาพ

#### Monitoring Performance | การติดตามประสิทธิภาพ
```bash
# Check system health
curl http://localhost:8000/performance/system_health

# Monitor model performance
curl http://localhost:8000/performance/model_performance

# Get detailed analytics
curl http://localhost:8000/tourism/analytics/tourist_graph
```

#### Optimization Guidelines | แนวทางการเพิ่มประสิทธิภาพ
1. **Model Loading**: Use lazy loading for large 3D models
2. **Caching**: Implement Redis for frequently accessed data
3. **Database Queries**: Optimize database queries with indexing
4. **API Response**: Use async/await for non-blocking operations
5. **Memory Management**: Clean up unused models and cache

### API Testing | การทดสอบ API

#### Core Functionality Tests | การทดสอบฟังก์ชันหลัก
```bash
# Test AI model selection
curl -X POST -H "Content-Type: application/json" \
     -d '{"question": "Show me a walking person"}' \
     http://localhost:8000/ai/select_model

# Test emotion analysis
curl -X POST -H "Content-Type: application/json" \
     -d '{"text": "I am so excited about my trip!"}' \
     http://localhost:8000/emotion/analyze_emotion

# Test tourism recommendations
curl -X POST -H "Content-Type: application/json" \
     -d '{"user_id": "test_user", "query": "indoor cafes"}' \
     http://localhost:8000/tourism/recommendations/contextual

# Test combined emotion and model selection
curl -X POST -H "Content-Type: application/json" \
     -d '{"question": "I am worried about walking alone"}' \
     http://localhost:8000/ai/select_model_with_emotion

# Test multimodal action plans
curl -X POST -H "Content-Type: application/json" \
     -d '{"intent": "welcome_user", "context": {}}' \
     http://localhost:8000/action_plan/generate_plan
```

#### Load Testing | การทดสอบภาระงาน
```bash
# Install testing tools
pip install locust

# Create load test script
# File: tests/load_test.py
from locust import HttpUser, task, between

class APITestUser(HttpUser):
    wait_time = between(1, 3)
    
    @task
    def test_model_selection(self):
        self.client.post("/ai/select_model",
                        json={"question": "Show me walking"})
    
    @task
    def test_emotion_analysis(self):
        self.client.post("/emotion/analyze_emotion",
                        json={"text": "I'm excited!"})

# Run load test
locust -f tests/load_test.py --host=http://localhost:8000
```

## 🔍 Troubleshooting & FAQ | การแก้ไขปัญหาและคำถามที่พบบ่อย

### Common Issues | ปัญหาที่พบบ่อย

#### Installation Problems | ปัญหาการติดตั้ง

**Q: ModuleNotFoundError when starting the server**
```bash
# Issue: Missing dependencies
ModuleNotFoundError: No module named 'fastapi'

# Solution: Install requirements
pip install -r requirements.txt
# If still failing, try upgrading pip
pip install --upgrade pip
pip install -r requirements.txt
```

**Q: Python version compatibility issues**
```bash
# Issue: Older Python version
ERROR: Package requires Python >=3.8

# Solution: Check and upgrade Python
python --version
# Install Python 3.8+ from python.org
# Or use pyenv for version management
pyenv install 3.9.0
pyenv local 3.9.0
```

**Q: Virtual environment issues**
```bash
# Issue: Virtual environment not activating
# Solution for different operating systems:

# Windows
python -m venv venv
venv\Scripts\activate.bat

# macOS/Linux
python3 -m venv venv
source venv/bin/activate

# If using conda
conda create -n painaidee python=3.9
conda activate painaidee
```

#### Server Startup Issues | ปัญหาการเริ่มเซิร์ฟเวอร์

**Q: Port already in use**
```bash
# Issue: Port 8000 is busy
OSError: [Errno 48] Address already in use

# Solution: Use different port or kill existing process
python main.py --port 8001
# Or find and kill the process
lsof -i :8000  # Find process ID
kill -9 <PID>  # Kill the process
```

**Q: AI models not loading**
```bash
# Issue: BERT models fail to download
# Solution: Manual model installation
python -c "
from transformers import pipeline
pipeline('sentiment-analysis', 
         model='cardiffnlp/twitter-roberta-base-sentiment-latest')
"

# Alternative: Use offline mode
export TRANSFORMERS_OFFLINE=1
```

#### 3D Model Issues | ปัญหาโมเดล 3D

**Q: Models not displaying in browser**
```javascript
// Issue: WebGL not supported
// Solution: Check browser compatibility
function checkWebGLSupport() {
    const canvas = document.createElement('canvas');
    const gl = canvas.getContext('webgl') || canvas.getContext('experimental-webgl');
    return !!gl;
}

// Upgrade browser or enable WebGL in settings
```

**Q: Slow model loading**
```bash
# Issue: Large model files loading slowly
# Solution: Enable model compression or use CDN

# Check model sizes
ls -lh assets/models/Fbx/

# Optimize models using Blender or other tools
# Or implement progressive loading
```

#### API Response Issues | ปัญหาการตอบสนอง API

**Q: Emotion analysis returning low confidence**
```python
# Issue: Emotion detection accuracy is low
# Solution: Improve text preprocessing

def preprocess_text(text: str) -> str:
    # Remove special characters
    import re
    text = re.sub(r'[^\w\s]', '', text)
    # Handle Thai text properly
    if contains_thai(text):
        # Use Thai-specific preprocessing
        return preprocess_thai_text(text)
    return text.lower().strip()
```

**Q: Tourism recommendations not relevant**
```python
# Issue: Contextual recommendations are off
# Solution: Check context data quality

# Verify context input
context = {
    "weather": "rainy",  # Should be: sunny|rainy|cloudy
    "time": "evening",   # Should be: morning|afternoon|evening|night
    "temperature": 25,   # Should be numeric
    "season": "rainy"    # Should be: hot|rainy|cool
}
```

### Performance Issues | ปัญหาประสิทธิภาพ

#### Memory Usage | การใช้หน่วยความจำ
```bash
# Monitor memory usage
python -c "
import psutil
import os
process = psutil.Process(os.getpid())
print(f'Memory usage: {process.memory_info().rss / 1024 / 1024:.2f} MB')
"

# Reduce memory usage
# 1. Clear model cache periodically
curl -X POST http://localhost:8000/admin/cache/clear

# 2. Use model quantization
export TRANSFORMERS_CACHE=/tmp/cache
```

#### Response Time Optimization | การเพิ่มประสิทธิภาพเวลาตอบสนอง
```python
# Use async/await for better performance
import asyncio
import aiohttp

async def optimized_api_call():
    async with aiohttp.ClientSession() as session:
        tasks = [
            session.post('/ai/select_model', json=request1),
            session.post('/emotion/analyze_emotion', json=request2)
        ]
        results = await asyncio.gather(*tasks)
    return results
```

### Debug Mode | โหมดดีบัก

#### Enable Detailed Logging | เปิดใช้งานการบันทึกแบบละเอียด
```python
# Add to .env file
DEBUG=true
LOG_LEVEL=DEBUG

# Or set environment variables
export DEBUG=true
export LOG_LEVEL=DEBUG
python main.py
```

#### API Debugging | การดีบัก API
```bash
# Test specific endpoints with verbose output
curl -v -X POST -H "Content-Type: application/json" \
     -d '{"question": "test"}' \
     http://localhost:8000/ai/select_model

# Check server logs
tail -f logs/painaidee.log

# Enable FastAPI debug mode
uvicorn main:app --reload --log-level debug
```

### Browser Compatibility | ความเข้ากันได้ของเบราว์เซอร์

#### Supported Browsers | เบราว์เซอร์ที่รองรับ
| Browser | Minimum Version | 3D Support | Recommended |
|---------|----------------|------------|-------------|
| Chrome | 80+ | ✅ Full | ✅ Yes |
| Firefox | 75+ | ✅ Full | ✅ Yes |
| Safari | 13+ | ⚠️ Limited | ⚠️ Partial |
| Edge | 80+ | ✅ Full | ✅ Yes |
| Opera | 67+ | ✅ Full | ✅ Yes |

#### WebGL Troubleshooting | การแก้ไขปัญหา WebGL
```javascript
// Check WebGL capabilities
function diagnoseWebGL() {
    const canvas = document.createElement('canvas');
    const gl = canvas.getContext('webgl');
    
    if (!gl) {
        console.error('WebGL not supported');
        return false;
    }
    
    const info = {
        vendor: gl.getParameter(gl.VENDOR),
        renderer: gl.getParameter(gl.RENDERER),
        version: gl.getParameter(gl.VERSION),
        extensions: gl.getSupportedExtensions()
    };
    
    console.log('WebGL Info:', info);
    return true;
}
```

### Development Tips | เคล็ดลับการพัฒนา

#### Hot Reload for Development | การโหลดซ้ำแบบทันทีสำหรับการพัฒนา
```bash
# Start with auto-reload
uvicorn main:app --reload --host 0.0.0.0 --port 8000

# Watch for file changes
pip install watchdog
python scripts/dev_watch.py
```

#### API Documentation | เอกสาร API
```bash
# Access interactive API docs
# Start server and visit:
http://localhost:8000/docs          # Swagger UI
http://localhost:8000/redoc         # ReDoc UI

# Generate OpenAPI schema
curl http://localhost:8000/openapi.json > api_schema.json
```

### Getting Help | การขอความช่วยเหลือ

#### Community Support | การสนับสนุนจากชุมชน
- **GitHub Issues**: Report bugs and request features
- **Discussions**: Join community discussions
- **Thai Developer Community**: เข้าร่วมชุมชนนักพัฒนาไทย

#### Professional Support | การสนับสนุนระดับมืออาชีพ
- **Enterprise Support**: Contact for enterprise deployment
- **Custom Development**: Request custom features
- **Training Services**: Thai language training available

#### Useful Resources | แหล่งข้อมูลที่เป็นประโยชน์
- [FastAPI Documentation](https://fastapi.tiangolo.com/)
- [Three.js Documentation](https://threejs.org/docs/)
- [Python Virtual Environments](https://docs.python.org/3/tutorial/venv.html)
- [Thai NLP Resources](https://github.com/PyThaiNLP/pythainlp)

## 🚀 Deployment | การปรับใช้งาน

### Production Deployment | การปรับใช้งานสำหรับการใช้งานจริง

#### Docker Deployment | การปรับใช้ด้วย Docker
```bash
# Build Docker image
docker build -t painaidee-ai-assistant .

# Run container
docker run -d -p 8000:8000 --name painaidee-app painaidee-ai-assistant

# With environment variables
docker run -d -p 8000:8000 \
  -e DEBUG=false \
  -e LOG_LEVEL=INFO \
  --name painaidee-app \
  painaidee-ai-assistant

# Using docker-compose
docker-compose up -d
```

#### Cloud Deployment | การปรับใช้บนคลาวด์

**AWS Deployment**
```bash
# Using AWS ECS
aws ecs create-cluster --cluster-name painaidee-cluster

# Deploy with Fargate
aws ecs run-task --cluster painaidee-cluster \
  --task-definition painaidee-task \
  --launch-type FARGATE
```

**Google Cloud Platform**
```bash
# Deploy to Cloud Run
gcloud run deploy painaidee-ai-assistant \
  --source . \
  --platform managed \
  --region asia-southeast1 \
  --allow-unauthenticated
```

**Heroku Deployment**
```bash
# Create Heroku app
heroku create painaidee-ai-assistant

# Deploy
git push heroku main

# Set environment variables
heroku config:set DEBUG=false
heroku config:set LOG_LEVEL=INFO
```

#### Production Configuration | การตั้งค่าสำหรับการใช้งานจริง
```bash
# Environment variables for production
export DEBUG=false
export LOG_LEVEL=INFO
export WORKERS=4
export MAX_REQUEST_SIZE=10000000
export TIMEOUT=300

# Run with Gunicorn
pip install gunicorn
gunicorn main:app -w 4 -k uvicorn.workers.UvicornWorker --bind 0.0.0.0:8000
```

### Monitoring & Maintenance | การติดตามและบำรุงรักษา

#### Health Checks | การตรวจสอบสุขภาพระบบ
```bash
# System health endpoint
curl http://localhost:8000/performance/system_health

# Detailed health check
curl http://localhost:8000/performance/detailed_health

# Monitor specific components
curl http://localhost:8000/emotion/health
curl http://localhost:8000/tourism/health/tourism
```

#### Logging & Analytics | การบันทึกและการวิเคราะห์
```python
# Setup structured logging
import logging
import json

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('logs/painaidee.log'),
        logging.StreamHandler()
    ]
)

# Usage analytics
def log_api_usage(endpoint: str, user_id: str, response_time: float):
    analytics_data = {
        "timestamp": datetime.now().isoformat(),
        "endpoint": endpoint,
        "user_id": user_id,
        "response_time": response_time
    }
    logging.info(f"API_USAGE: {json.dumps(analytics_data)}")
```

### Security | ความปลอดภัย

#### API Security | ความปลอดภัย API
```python
# Add API key authentication
from fastapi import Depends, HTTPException, status
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials

security = HTTPBearer()

async def verify_api_key(credentials: HTTPAuthorizationCredentials = Depends(security)):
    if credentials.credentials != os.getenv("API_KEY"):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid API key"
        )
    return credentials.credentials

# Use in routes
@router.post("/protected-endpoint")
async def protected_route(api_key: str = Depends(verify_api_key)):
    return {"message": "Access granted"}
```

#### CORS Configuration | การตั้งค่า CORS
```python
# Configure CORS for production
from fastapi.middleware.cors import CORSMiddleware

app.add_middleware(
    CORSMiddleware,
    allow_origins=["https://yourdomain.com"],  # Specific domains only
    allow_credentials=True,
    allow_methods=["GET", "POST"],
    allow_headers=["*"],
)
```

#### Rate Limiting | การจำกัดอัตราการเรียกใช้
```python
# Implement rate limiting
from slowapi import Limiter, _rate_limit_exceeded_handler
from slowapi.util import get_remote_address
from slowapi.errors import RateLimitExceeded

limiter = Limiter(key_func=get_remote_address)
app.state.limiter = limiter
app.add_exception_handler(RateLimitExceeded, _rate_limit_exceeded_handler)

@router.post("/ai/select_model")
@limiter.limit("10/minute")
async def select_model(request: Request, ...):
    # API logic
```

## 🤝 Contributing | การมีส่วนร่วม

### For Thai Developers | สำหรับนักพัฒนาชาวไทย

#### Getting Started | เริ่มต้นการมีส่วนร่วม
1. **Fork โปรเจกต์** - คลิก Fork ที่มุมขวาบนของหน้า GitHub
2. **Clone โปรเจกต์** - โคลนโปรเจกต์มายังเครื่องของคุณ
3. **สร้าง Branch ใหม่** - สร้าง branch สำหรับฟีเจอร์ใหม่
4. **พัฒนาและทดสอบ** - เพิ่มฟีเจอร์ใหม่และเขียนการทดสอบ
5. **ส่ง Pull Request** - ส่งการเปลี่ยนแปลงกลับมายังโปรเจกต์หลัก

#### Code Style Guidelines | แนวทางการเขียนโค้ด
```python
# Python code style (PEP 8)
# Use Black formatter
pip install black
black painaidee_ai_assistant/

# Use flake8 for linting
pip install flake8
flake8 painaidee_ai_assistant/

# Type hints are encouraged
def analyze_emotion(text: str, language: str = "th") -> EmotionResult:
    pass
```

#### Thai Language Contributions | การมีส่วนร่วมด้านภาษาไทย
- **การแปล**: ช่วยแปลเอกสารและข้อความในระบบ
- **ข้อมูลวัฒนธรรม**: เพิ่มข้อมูลเกี่ยวกับวัฒนธรรมไทยและท่องเที่ยว
- **การทดสอบภาษาไทย**: ทดสอบความสามารถในการประมวลผลภาษาไทย
- **ฐานข้อมูลท่องเที่ยว**: เพิ่มข้อมูลสถานที่ท่องเที่ยวในประเทศไทย

### Contribution Areas | ด้านที่สามารถมีส่วนร่วม

#### 1. AI & Machine Learning | AI และการเรียนรู้ของเครื่อง
- Improve emotion analysis accuracy for Thai language
- Add new gesture recognition algorithms
- Enhance tourism recommendation algorithms
- Implement Thai cultural context understanding

#### 2. 3D Graphics & Animation | กราฟิก 3D และแอนิเมชั่น
- Add new 3D models with Thai cultural themes
- Improve animation quality and smoothness
- Optimize 3D rendering performance
- Create Thai traditional gesture animations

#### 3. Tourism Domain Knowledge | ความรู้ด้านการท่องเที่ยว
- Add comprehensive Thai tourism database
- Implement seasonal tourism recommendations
- Create location-based services
- Add cultural and historical context

#### 4. Frontend Development | การพัฒนาส่วนหน้า
- Improve 3D viewer user interface
- Add Thai language UI support
- Enhance mobile responsiveness
- Create better user experience flows

#### 5. Documentation | เอกสารประกอบ
- Translate documentation to Thai
- Create video tutorials
- Write developer guides
- Add API usage examples

### Development Workflow | ขั้นตอนการพัฒนา

```bash
# 1. Setup development environment
git clone https://github.com/your-username/AI_Assistant_PaiNaiDee.git
cd AI_Assistant_PaiNaiDee
git remote add upstream https://github.com/athipan1/AI_Assistant_PaiNaiDee.git

# 2. Create feature branch
git checkout -b feature/new-thai-feature

# 3. Make changes and commit
git add .
git commit -m "Add new Thai tourism feature"

# 4. Push and create pull request
git push origin feature/new-thai-feature
```

### Code Review Process | กระบวนการตรวจสอบโค้ด

#### Review Checklist | รายการตรวจสอบ
- [ ] **Functionality**: Does the code work as intended?
- [ ] **Tests**: Are there adequate tests covering the new code?
- [ ] **Documentation**: Is the new feature properly documented?
- [ ] **Performance**: Does the change impact system performance?
- [ ] **Thai Language Support**: Does it work correctly with Thai text?
- [ ] **Cultural Sensitivity**: Is it appropriate for Thai cultural context?

#### Pull Request Template | แม่แบบ Pull Request
```markdown
## Description | คำอธิบาย
Brief description of changes in Thai and English

## Type of Change | ประเภทของการเปลี่ยนแปลง
- [ ] Bug fix | การแก้ไขบัก
- [ ] New feature | ฟีเจอร์ใหม่
- [ ] Documentation | เอกสาร
- [ ] Performance improvement | การปรับปรุงประสิทธิภาพ

## Testing | การทดสอบ
- [ ] Unit tests pass
- [ ] Integration tests pass
- [ ] Manual testing completed
- [ ] Thai language testing (if applicable)

## Screenshots | ภาพหน้าจอ
(If applicable, especially for UI changes)
```

## 📄 License | ใบอนุญาต

This project is part of the PaiNaiDee tourism assistant initiative, developed for the benefit of Thai tourism industry and open-source community.

### Open Source License
This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.

### Usage Rights | สิทธิ์การใช้งาน
- ✅ **Commercial Use** | การใช้งานเชิงพาณิชย์
- ✅ **Modification** | การดัดแปลง
- ✅ **Distribution** | การแจกจ่าย
- ✅ **Private Use** | การใช้งานส่วนตัว

### Responsibilities | ความรับผิดชอบ
- 📝 **Include License** | รวมใบอนุญาต
- 📝 **Include Copyright** | รวมลิขสิทธิ์

## 🙏 Acknowledgments | กิตติกรรมประกาศ

### Contributors | ผู้ร่วมพัฒนา
- Thai Tourism Authority for domain expertise
- Open source community for libraries and tools
- Thai developer community for cultural insights

### Technologies Used | เทคโนโลยีที่ใช้
- **FastAPI** - Modern Python web framework
- **Three.js** - 3D graphics library
- **Transformers** - Hugging Face NLP models
- **scikit-learn** - Machine learning library
- **Docker** - Containerization platform

### Special Thanks | ขอบคุณเป็นพิเศษ
- Tourism Authority of Thailand (TAT)
- Thai software developer community
- Open source contributors worldwide
- Beta testers and early adopters

---

**Made with ❤️ for Thai tourism and AI innovation**
**สร้างด้วยความรักเพื่อการท่องเที่ยวไทยและนวัตกรรม AI**

---

### Quick Links | ลิงก์ด่วน
- [📖 Full Documentation](docs/)
- [🎯 API Reference](http://localhost:8000/docs)
- [🎨 3D Model Gallery](assets/models/)
- [🧪 Live Demo](http://localhost:8000)
- [🐛 Report Issues](https://github.com/athipan1/AI_Assistant_PaiNaiDee/issues)
- [💬 Discussions](https://github.com/athipan1/AI_Assistant_PaiNaiDee/discussions)