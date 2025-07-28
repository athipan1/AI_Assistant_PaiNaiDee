# AI_Assistant_PaiNaiDee

## 🎯 Overview

PaiNaiDee AI Assistant is an intelligent Thai tourism assistant that now features **3D model visualization** with AI-powered question analysis. Users can ask questions in natural language and the AI will automatically select and display relevant 3D models to enhance the user experience.

![PaiNaiDee 3D Demo](https://github.com/user-attachments/assets/36c99aa7-4aa5-4df7-9f9c-bcf94e4d5e8d)

## ✨ Features

### 🤖 AI-Powered 3D Model Selection
- **Natural Language Processing**: Ask questions like "Show me a walking person" or "Display running animation"
- **Smart Model Mapping**: AI analyzes keywords and context to select appropriate 3D models
- **Confidence Scoring**: Each selection includes confidence percentage for transparency

### 🎮 Interactive 3D Viewer
- **Mouse Controls**: Rotate, zoom, and pan around 3D models
- **Click Interactions**: Click on models to view detailed information
- **Real-time Updates**: Seamless model switching based on user queries

### 📦 Available 3D Models
- **Man.fbx**: Basic human character model (296 KB)
- **Idle.fbx**: Character in standing/idle pose (1.09 MB)
- **Walking.fbx**: Walking animation sequence (743 KB)
- **Running.fbx**: Running animation sequence (734 KB)
- **Man_Rig.fbx**: Rigged character for custom animations (698 KB)

### 🌐 API Endpoints
- `POST /ai/select_model` - AI model selection based on questions
- `GET /ai/models` - List all available 3D models
- `GET /ai/models/{model_name}` - Get specific model information
- `GET /models/{model_name}` - Download 3D model files

## 🚀 Quick Start

### Prerequisites
- Python 3.8+
- Web browser with WebGL support

### Installation & Setup

1. **Clone the repository**
   ```bash
   git clone https://github.com/athipan1/AI_Assistant_PaiNaiDee.git
   cd AI_Assistant_PaiNaiDee/painaidee_ai_assistant
   ```

2. **Install dependencies**
   ```bash
   pip install -r requirements.txt
   ```

3. **Start the server**
   ```bash
   # Option 1: FastAPI server (recommended for production)
   python main.py
   
   # Option 2: Simple test server (for development/demo)
   python test_server.py
   ```

4. **Open in browser**
   ```
   http://localhost:8000
   ```

## 📚 Usage Examples

### Natural Language Queries

```javascript
// Example API calls
const response = await fetch('/ai/select_model', {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({ 
        question: "Show me a walking person",
        language: "en" 
    })
});

// Response:
{
    "model_selection": {
        "selected_model": "Walking.fbx",
        "confidence": 0.8,
        "description": "Character animation showing walking motion"
    },
    "status": "success"
}
```

### Supported Question Types

| Question Examples | Selected Model | Use Case |
|------------------|----------------|----------|
| "Show me a person", "Display a character" | Man.fbx | Basic character representation |
| "Walking animation", "Show walking" | Walking.fbx | Walking demonstrations |
| "Running person", "Show running" | Running.fbx | Running/sports content |
| "Idle pose", "Standing character" | Idle.fbx | Static character display |
| "Rigged model", "Animation ready" | Man_Rig.fbx | Development/customization |

## 🔧 Technical Architecture

### AI Model Selection Algorithm
```python
class ModelSelector:
    def analyze_question(self, question: str) -> Dict[str, Any]:
        # 1. Keyword extraction and matching
        # 2. Confidence scoring based on context
        # 3. Model selection with fallback logic
        # 4. Return structured response with metadata
```

### Frontend Integration
```javascript
// 3D viewer initialization
function initializeViewer() {
    scene = new THREE.Scene();
    camera = new THREE.PerspectiveCamera(75, width/height, 0.1, 1000);
    renderer = new THREE.WebGLRenderer({ antialias: true });
    controls = new THREE.OrbitControls(camera, renderer.domElement);
}

// Model loading and interaction
function loadSelectedModel() {
    // Remove existing model
    // Load new FBX model using FBXLoader
    // Add interaction handlers
    // Update UI with model info
}
```

### File Structure
```
painaidee_ai_assistant/
├── main.py                 # FastAPI application
├── test_server.py         # Development server
├── api/
│   ├── ai_routes.py       # Original AI endpoints
│   └── model_routes.py    # 3D model API endpoints
├── static/
│   ├── index.html         # Full 3D viewer (requires CDN)
│   └── demo.html          # Demo version (offline)
└── assets/models/Fbx/     # 3D model files
    ├── Man.fbx
    ├── Idle.fbx
    ├── Walking.fbx
    ├── Running.fbx
    └── Man_Rig.fbx
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

## 🌟 Future Enhancements

### Planned Features
- [ ] **Advanced AI Models**: Integration with llama.cpp, OpenChat, OpenHermes
- [ ] **More 3D Formats**: Support for GLB, OBJ, GLTF files
- [ ] **Animation Controls**: Play/pause/speed controls for animations
- [ ] **Multi-language Support**: Thai language question processing
- [ ] **Voice Commands**: Speech-to-text integration
- [ ] **AR/VR Support**: WebXR compatibility

### Technical Improvements
- [ ] **Model Caching**: Faster loading for frequently used models
- [ ] **Progressive Loading**: Streaming for large model files
- [ ] **Real-time Collaboration**: Multi-user 3D sessions
- [ ] **Analytics Dashboard**: Usage statistics and popular models

## 🛠️ Development

### Adding New Models
1. Add FBX files to `assets/models/Fbx/`
2. Update model descriptions in `model_routes.py`
3. Add keyword mappings for AI selection
4. Test with sample questions

### API Testing
```bash
# List available models
curl http://localhost:8000/ai/models

# Test AI selection
curl -X POST -H "Content-Type: application/json" \
     -d '{"question": "Show me a walking person"}' \
     http://localhost:8000/ai/select_model
```

## 📄 License

This project is part of the PaiNaiDee tourism assistant initiative.

## 🤝 Contributing

1. Fork the repository
2. Create a feature branch
3. Add tests for new functionality
4. Submit a pull request

---

**Made with ❤️ for Thai tourism and AI innovation**