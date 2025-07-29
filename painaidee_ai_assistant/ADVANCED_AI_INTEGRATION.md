# Advanced AI Models Integration

This document describes the integration of advanced AI models (llama.cpp, OpenChat, OpenHermes) into the PaiNaiDee AI Assistant.

## Overview

The PaiNaiDee AI Assistant now supports advanced AI models that provide enhanced intelligence, accuracy, and performance for diverse user questions. The integration includes:

- **llama.cpp**: Efficient LLaMA models optimized for edge devices
- **OpenChat**: Open source conversational AI specialized in dialogue  
- **OpenHermes**: Human-like communication models with cultural awareness

## Features

### 🤖 Advanced AI Model Support
- **Multiple Model Types**: Support for llama.cpp GGUF files, OpenChat models, and OpenHermes models
- **Intelligent Model Selection**: Automatic selection of the best model based on capability requirements
- **Fallback Support**: Graceful degradation when advanced models are unavailable
- **Configuration Management**: JSON-based model configuration system

### 🎯 Enhanced Capabilities
- **Conversational AI**: Natural dialogue with context awareness
- **Question Answering**: Factual responses with tourism expertise
- **Tourism Advice**: Specialized recommendations for Thai tourism
- **Text Generation**: Creative and informative content generation
- **Cultural Context**: Thai cultural awareness and sensitivity

### 🔄 Seamless Integration
- **3D Model Enhancement**: Enhanced 3D model selection with AI explanations
- **Backward Compatibility**: Existing features continue to work unchanged
- **API Expansion**: New endpoints while maintaining existing API structure
- **Progressive Enhancement**: Features activate only when models are available

## API Endpoints

### Advanced AI Endpoints

#### `/advanced_ai/generate`
Generate text using advanced AI models

```json
POST /advanced_ai/generate
{
  "prompt": "Tell me about Thai temples",
  "capability": "tourism_advice",
  "language": "en",
  "max_tokens": 500,
  "temperature": 0.7
}
```

#### `/advanced_ai/conversation`
Natural conversation with optional 3D model recommendations

```json
POST /advanced_ai/conversation
{
  "message": "Hello! Can you help me plan a trip to Thailand?",
  "conversation_history": [
    {"role": "user", "content": "Previous message"},
    {"role": "assistant", "content": "Previous response"}
  ],
  "language": "en"
}
```

#### `/advanced_ai/tourism_advisor`
Specialized tourism advice with context awareness

```json
POST /advanced_ai/tourism_advisor
{
  "question": "What are the best temples to visit in Bangkok?",
  "location": "Bangkok, Thailand",
  "preferences": {
    "interests": ["culture", "history"],
    "budget": "moderate",
    "duration": "2 days"
  },
  "language": "en"
}
```

#### `/advanced_ai/models`
List all available advanced AI models

```json
GET /advanced_ai/models
```

#### `/advanced_ai/health`
Health check for advanced AI system

```json
GET /advanced_ai/health
```

### Enhanced AI Endpoints

#### `/ai/select_model_enhanced`
Enhanced 3D model selection with AI analysis

```json
POST /ai/select_model_enhanced
{
  "question": "Show me a walking person",
  "session_id": "user_session_123",
  "use_advanced_ai": true,
  "language": "en"
}
```

#### `/ai/conversation`
AI conversation with 3D model context

```json
POST /ai/conversation
{
  "message": "I want to see traditional Thai dance movements",
  "conversation_history": [],
  "language": "en"
}
```

#### `/ai/tourism_advice`
Tourism advice with 3D model recommendations

```json
POST /ai/tourism_advice
{
  "question": "What cultural experiences should I try in Thailand?",
  "location": "Chiang Mai",
  "preferences": {"type": "cultural"},
  "language": "en"
}
```

## Configuration

### Model Configuration File: `config/ai_models.json`

```json
{
  "llama-2-7b-chat": {
    "name": "llama-2-7b-chat",
    "model_type": "llama_cpp",
    "model_path": "models/llama-2-7b-chat.gguf",
    "capabilities": ["conversation", "question_answering", "text_generation", "tourism_advice"],
    "language_support": ["en", "th"],
    "max_tokens": 2048,
    "temperature": 0.7,
    "is_local": true,
    "requires_gpu": false,
    "load_in_8bit": false,
    "priority": 2
  },
  "openchat-3.5": {
    "name": "openchat-3.5",
    "model_type": "openchat",
    "model_path": "openchat/openchat-3.5-1210",
    "capabilities": ["conversation", "question_answering", "text_generation"],
    "language_support": ["en", "th"],
    "max_tokens": 4096,
    "temperature": 0.7,
    "is_local": true,
    "requires_gpu": true,
    "load_in_8bit": true,
    "priority": 3
  },
  "openhermes-2.5": {
    "name": "openhermes-2.5",
    "model_type": "openhermes",
    "model_path": "NousResearch/Nous-Hermes-2-Mixtral-8x7B-DPO",
    "capabilities": ["conversation", "question_answering", "text_generation", "tourism_advice"],
    "language_support": ["en", "th"],
    "max_tokens": 4096,
    "temperature": 0.7,
    "is_local": true,
    "requires_gpu": true,
    "load_in_8bit": true,
    "priority": 4
  }
}
```

### Configuration Fields

- **name**: Unique identifier for the model
- **model_type**: Type of model (`llama_cpp`, `openchat`, `openhermes`)
- **model_path**: Path to model file or HuggingFace model ID
- **capabilities**: List of supported capabilities
- **language_support**: Supported languages (ISO codes)
- **max_tokens**: Maximum tokens for generation
- **temperature**: Generation temperature (0.0-1.0)
- **is_local**: Whether model runs locally
- **requires_gpu**: GPU requirement flag
- **load_in_8bit**: Use 8-bit quantization
- **priority**: Model selection priority (higher = preferred)

## Setup Instructions

### 1. Install Dependencies

```bash
# Basic dependencies (already included)
pip install fastapi uvicorn transformers torch

# Advanced AI dependencies
pip install llama-cpp-python  # For llama.cpp models
pip install bitsandbytes      # For model quantization
```

### 2. Download Models

#### For llama.cpp models:
```bash
# Create models directory
mkdir -p models

# Download GGUF model files (example)
wget https://huggingface.co/TheBloke/Llama-2-7B-Chat-GGUF/resolve/main/llama-2-7b-chat.q4_0.gguf \
  -O models/llama-2-7b-chat.gguf
```

#### For OpenChat/OpenHermes models:
Models are automatically downloaded from HuggingFace when first used.

### 3. Configure Models

Edit `config/ai_models.json` to match your model paths and preferences.

### 4. Test Integration

```bash
# Run the integration test
python test_advanced_ai_integration.py

# Start the server
python main.py
```

## Usage Examples

### Basic Conversation

```python
import requests

response = requests.post("http://localhost:8000/advanced_ai/conversation", json={
    "message": "Hello! I'm planning a trip to Thailand. Can you help?",
    "language": "en"
})

result = response.json()
print(f"AI Response: {result['response']}")
if result.get('suggested_3d_model'):
    print(f"Suggested 3D Model: {result['suggested_3d_model']}")
```

### Tourism Advice

```python
response = requests.post("http://localhost:8000/advanced_ai/tourism_advisor", json={
    "question": "What are the must-visit temples in Bangkok?",
    "location": "Bangkok, Thailand",
    "preferences": {
        "interests": ["culture", "history", "architecture"],
        "time_available": "1 day",
        "transportation": "public"
    },
    "language": "en"
})

result = response.json()
print(f"Tourism Advice: {result['advice']}")
```

### Enhanced Model Selection

```python
response = requests.post("http://localhost:8000/ai/select_model_enhanced", json={
    "question": "Show me traditional Thai dance movements",
    "use_advanced_ai": True,
    "language": "en"
})

result = response.json()
print(f"Selected 3D Model: {result['model_selection']['selected_model']}")
print(f"AI Enhancement: {result['ai_enhancement']['ai_explanation']}")
```

## Architecture

### Components

1. **AdvancedAIManager**: Core manager for AI models
2. **Model Wrappers**: Specific implementations for each model type
3. **EnhancedModelSelector**: Bridges 3D models with AI capabilities
4. **API Routes**: RESTful endpoints for all functionality
5. **Configuration System**: JSON-based model management

### Model Selection Logic

1. **Capability Matching**: Find models supporting required capabilities
2. **Language Support**: Filter by language requirements
3. **Availability Check**: Verify model files and dependencies
4. **Priority Ranking**: Select highest priority available model
5. **Fallback Handling**: Graceful degradation when models unavailable

### Integration Flow

1. User makes request → API endpoint
2. Enhanced selector analyzes request
3. 3D model selected using existing logic
4. Advanced AI provides enhancement/explanation
5. Combined response returned to user

## Performance Considerations

### Model Loading
- **Lazy Loading**: Models loaded only when first requested
- **Memory Management**: Models cached for subsequent requests
- **GPU Optimization**: Automatic GPU utilization when available

### Response Times
- **Model Selection**: ~100ms for 3D model selection
- **AI Generation**: Variable based on model size and complexity
- **Caching**: Frequent queries cached for faster responses

### Resource Usage
- **Memory**: 2-8GB depending on loaded models
- **GPU**: Optional but recommended for larger models
- **Storage**: 1-20GB for model files

## Troubleshooting

### Common Issues

#### Models Not Loading
```
Error: Model xyz is not available (missing files or dependencies)
```
**Solution**: Check model paths and install required dependencies

#### CUDA/GPU Issues
```
Error: CUDA out of memory
```
**Solution**: Use smaller models or enable 8-bit quantization

#### Network Connectivity
```
Error: We couldn't connect to 'https://huggingface.co'
```
**Solution**: Check internet connection or use offline mode

### Debug Mode

Enable detailed logging:
```bash
export DEBUG=true
export LOG_LEVEL=DEBUG
python main.py
```

### Health Checks

Check system status:
```bash
curl http://localhost:8000/advanced_ai/health
curl http://localhost:8000/health
```

## Future Enhancements

### Planned Features
- **More Model Types**: Support for additional AI architectures
- **Fine-tuning**: Custom training on Thai tourism data
- **Voice Integration**: Speech-to-text and text-to-speech
- **Real-time Learning**: Continuous improvement from user interactions
- **Multi-modal**: Integration with image and video understanding

### Performance Improvements
- **Model Quantization**: Smaller, faster model variants
- **Distributed Inference**: Load balancing across multiple models
- **Edge Deployment**: Optimized models for mobile devices
- **Caching Strategies**: Intelligent response caching

## Support

For issues and questions:
- GitHub Issues: [Repository Issues](https://github.com/athipan1/AI_Assistant_PaiNaiDee/issues)
- Documentation: [Full Documentation](https://github.com/athipan1/AI_Assistant_PaiNaiDee)
- Thai Community: ชุมชนนักพัฒนาไทย

## License

This advanced AI integration is part of the PaiNaiDee AI Assistant project and follows the same MIT License terms.