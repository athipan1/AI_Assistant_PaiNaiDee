# PaiNaiDee AI Assistant Backend

A FastAPI-based AI assistant backend for the PaiNaiDee tourism app, featuring Thai-style greetings and intelligent place information search using state-of-the-art language models.

## Features

### 🤖 AI Capabilities
- **Thai-style Greetings**: Personalized greetings using Falcon-7B-Instruct model
- **Place Information Search**: Intelligent summarization using BART-large-CNN
- **Multi-language Support**: English and Thai language options
- **Fallback Responses**: Robust error handling with mock data

### 🚀 API Endpoints
- `POST /ai/greet` - Generate warm Thai-style greetings
- `POST /ai/search_info` - Search and summarize place information
- `GET /health` - Health check endpoint

### 🛠 Technical Stack
- **FastAPI** - Modern, fast web framework
- **HuggingFace Transformers** - State-of-the-art NLP models
- **PyTorch** - Deep learning framework
- **Docker** - Containerized deployment
- **CORS** - Cross-origin resource sharing support

## Project Structure

```
painaidee_ai_assistant/
├── agents/                 # AI agent logic
│   ├── greeting_agent.py   # Falcon-7B greeting generation
│   └── search_agent.py     # BART-powered search & summarization
├── api/                    # API route definitions
│   └── ai_routes.py        # Main AI endpoints
├── scraping/               # Data fetching utilities
│   ├── wikipedia_scraper.py # Wikipedia integration
│   └── maps_scraper.py     # Google Maps integration
├── models/                 # Model storage and utilities
├── scripts/                # Training and utility scripts
│   └── download_models.py  # Pre-download models
├── tests/                  # Test suites
├── main.py                 # FastAPI application entry point
├── requirements.txt        # Python dependencies
├── Dockerfile              # Docker configuration
└── .env.example           # Environment configuration template
```

## Quick Start

### 1. Local Development

```bash
# Clone the repository
git clone <repository-url>
cd painaidee_ai_assistant

# Create virtual environment
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate

# Install dependencies
pip install -r requirements.txt

# Copy environment configuration
cp .env.example .env
# Edit .env with your configuration

# Run the application
python main.py
```

### 2. Docker Deployment

```bash
# Build the image
docker build -t painaidee-ai-assistant .

# Run the container
docker run -p 8000:8000 painaidee-ai-assistant

# Or with GPU support (if available)
docker run --gpus all -p 8000:8000 painaidee-ai-assistant
```

### 3. API Usage

#### Generate Greeting
```bash
curl -X POST "http://localhost:8000/ai/greet" \
     -H "Content-Type: application/json" \
     -d '{"name": "John", "language": "en"}'
```

Response:
```json
{
    "greeting": "Hello John! Sawasdee! Welcome to Thailand, the Land of Smiles! 🇹🇭",
    "language": "en",
    "status": "success"
}
```

#### Search Place Information
```bash
curl -X POST "http://localhost:8000/ai/search_info" \
     -H "Content-Type: application/json" \
     -d '{"place_name": "Bangkok", "language": "en"}'
```

Response:
```json
{
    "images": ["https://example.com/bangkok1.jpg", "https://example.com/bangkok2.jpg"],
    "map_link": "https://www.google.com/maps/search/Bangkok",
    "description": "Bangkok, Thailand's capital, is a large city known for ornate shrines and vibrant street life...",
    "rating": 4.5,
    "status": "success"
}
```

## Configuration

### Environment Variables

Copy `.env.example` to `.env` and configure:

```env
# Server Configuration
HOST=0.0.0.0
PORT=8000

# AI Models
GREETING_MODEL=tiiuae/falcon-7b-instruct
SUMMARIZATION_MODEL=facebook/bart-large-cnn

# Optional API Keys
GOOGLE_PLACES_API_KEY=your_key_here
HUGGINGFACE_API_TOKEN=your_token_here
```

### Model Configuration

The application supports different models for different tasks:

- **Greeting Generation**: Falcon-7B-Instruct (default) or any compatible causal LM
- **Text Summarization**: BART-large-CNN (default) or any compatible seq2seq model

## Production Deployment

### Docker Production

```bash
# Build production image
docker build -t painaidee-ai-assistant:prod .

# Run with production settings
docker run -d \
  --name painaidee-ai \
  -p 8000:8000 \
  -e DEBUG=false \
  -e LOG_LEVEL=INFO \
  -v $(pwd)/models:/app/models \
  painaidee-ai-assistant:prod
```

### Pre-downloading Models

For faster startup in production:

```bash
# Pre-download models
python scripts/download_models.py
```

### GPU Support

The application automatically detects and uses GPU if available:

```bash
# Check GPU availability
python -c "import torch; print(torch.cuda.is_available())"

# Run with GPU
docker run --gpus all -p 8000:8000 painaidee-ai-assistant
```

## API Documentation

Once running, visit:
- **Swagger UI**: http://localhost:8000/docs
- **ReDoc**: http://localhost:8000/redoc

## Development

### Adding New Agents

1. Create agent class in `agents/`
2. Implement required methods
3. Add route in `api/ai_routes.py`
4. Update imports in `main.py`

### Testing

```bash
# Install test dependencies
pip install pytest pytest-asyncio

# Run tests
pytest tests/

# Run with coverage
pytest --cov=.
```

## Troubleshooting

### Common Issues

1. **Model Download Errors**: Ensure stable internet connection and sufficient disk space
2. **Memory Issues**: Use CPU-only mode or smaller models for limited resources
3. **API Timeouts**: Increase timeout values for model loading

### Performance Optimization

- Pre-download models using `scripts/download_models.py`
- Use GPU acceleration when available
- Enable model caching in production
- Configure appropriate worker counts

## Contributing

1. Fork the repository
2. Create feature branch
3. Make changes with tests
4. Submit pull request

## License

[Add your license information here]

## Support

For issues and questions:
- Create GitHub issues for bugs
- Check documentation for common problems
- Review logs for error details