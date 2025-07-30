# RAG (Retrieval-Augmented Generation) Module

## Overview

The RAG module extends the PaiNaiDee AI Assistant with retrieval-augmented generation capabilities, allowing it to answer user questions based on up-to-date information from external tourism sources.

## Features

- 🔍 **Vector-based Document Retrieval**: TF-IDF vectorization with cosine similarity
- 🕷️ **Tourism Content Crawler**: Respectful web scraping with robots.txt compliance
- 🌏 **Multi-language Support**: English and Thai language processing
- 📅 **Background Scheduling**: Automatic knowledge base updates
- 🛡️ **Fallback Mechanisms**: Graceful degradation when no relevant documents are found
- 🔧 **Dynamic Source Management**: Add/remove data sources via API

## Architecture

```
┌─────────────────┐    ┌──────────────────┐    ┌─────────────────┐
│   User Query    │───►│   RAG System     │───►│   AI Response   │
└─────────────────┘    └──────────────────┘    └─────────────────┘
                                │
                    ┌───────────▼───────────┐
                    │   Document Retriever  │
                    └───────────┬───────────┘
                                │
                    ┌───────────▼───────────┐
                    │   Vector Store        │
                    └───────────┬───────────┘
                                │
                    ┌───────────▼───────────┐
                    │   Tourism Crawler    │
                    └───────────────────────┘
```

## API Endpoints

### Core RAG Functionality

#### `POST /rag/search`
Search for information and generate AI-powered answers.

**Request:**
```json
{
  "question": "What are the best places to visit in Bangkok?",
  "language": "en",
  "include_sources": true,
  "max_context_length": 2000
}
```

**Response:**
```json
{
  "answer": "Based on the available information...",
  "sources": [
    {
      "name": "Tourism Authority of Thailand",
      "title": "Bangkok Guide",
      "url": "https://example.com/bangkok"
    }
  ],
  "metadata": {
    "method": "rag",
    "documents_used": 2,
    "processing_time_seconds": 0.15,
    "language": "en"
  }
}
```

### Source Management

#### `POST /rag/update_sources`
Add, remove, enable, or disable data sources.

**Add Source:**
```json
{
  "action": "add",
  "source_id": "new_source",
  "config": {
    "type": "web",
    "url": "https://example.com/tourism",
    "name": "Tourism Site",
    "enabled": true
  }
}
```

#### `GET /rag/sources`
List all configured data sources.

### Knowledge Base Management

#### `POST /rag/update_knowledge_base`
Manually trigger knowledge base update.

#### `GET /rag/stats`
Get comprehensive system statistics.

#### `GET /rag/health`
Check system health status.

### Scheduler Management

#### `POST /rag/scheduler/start?interval_hours=6`
Start background updates with specified interval.

#### `GET /rag/scheduler/status`
Get scheduler status and timing information.

#### `POST /rag/scheduler/stop`
Stop background scheduler.

## Usage Examples

### Basic Tourism Query
```bash
curl -X POST "http://localhost:8000/rag/search" \
  -H "Content-Type: application/json" \
  -d '{"question": "What Thai food should I try?", "language": "en"}'
```

### Thai Language Query
```bash
curl -X POST "http://localhost:8000/rag/search" \
  -H "Content-Type: application/json" \
  -d '{"question": "อาหารไทยอะไรอร่อย", "language": "th"}'
```

### Add New Data Source
```bash
curl -X POST "http://localhost:8000/rag/update_sources" \
  -H "Content-Type: application/json" \
  -d '{
    "action": "add",
    "source_id": "tat_official",
    "config": {
      "type": "web",
      "url": "https://www.tourismthailand.org/",
      "name": "TAT Official Website"
    }
  }'
```

### Start Background Updates
```bash
curl -X POST "http://localhost:8000/rag/scheduler/start?interval_hours=6"
```

## Components

### 1. Vector Store (`SimpleVectorStore`)
- Lightweight TF-IDF based vector storage
- Persistent storage with JSON and pickle files
- Configurable similarity thresholds
- Memory-efficient for small to medium datasets

### 2. Document Retriever (`DocumentRetriever`)
- Tourism-focused keyword enhancement
- Re-ranking based on recency, authority, and relevance
- Context preparation with length limits
- Metadata filtering capabilities

### 3. Tourism Crawler (`TourismCrawler`)
- Respectful web scraping with robots.txt compliance
- Support for RSS feeds, web pages, and APIs
- Rate limiting and error handling
- Configurable source management

### 4. RAG System (`RAGSystem`)
- Orchestrates retrieval and generation
- Fallback mechanisms for missing data
- Integration with existing AI components
- Multi-language response generation

### 5. Background Scheduler (`RAGScheduler`)
- Automatic knowledge base updates
- Configurable update intervals
- Manual trigger capability
- Status monitoring and logging

## Configuration

### Data Sources
Sources are configured in the crawler with the following structure:

```python
{
  "source_id": {
    "type": "web|rss|api",
    "url": "https://example.com",
    "name": "Human-readable name",
    "enabled": true,
    "headers": {},  # Optional HTTP headers
    "params": {}    # Optional query parameters
  }
}
```

### Vector Store Settings
- **Storage Path**: `cache/vector_store`
- **Max Features**: 1000 TF-IDF features
- **Similarity Threshold**: 0.1 (configurable)
- **Max Results**: 5 documents per query

## Supported Languages

- **English (en)**: Full support with tourism keyword enhancement
- **Thai (th)**: Response generation with fallback mechanisms

## Error Handling

The RAG system includes comprehensive error handling:

1. **Document Retrieval Failures**: Falls back to existing AI responses
2. **Network Errors**: Graceful degradation with cached data
3. **Parsing Errors**: Logs issues and continues with available data
4. **Storage Errors**: Automatic recovery and rebuild mechanisms

## Performance Considerations

- **Memory Usage**: Optimized TF-IDF vectorization
- **Response Time**: Typically < 0.5 seconds for queries
- **Scalability**: Designed for 1K-10K documents
- **Caching**: Persistent vector storage reduces initialization time

## Testing

Run the RAG test suite:

```bash
cd painaidee_ai_assistant
python tests/test_rag.py
```

Example test output:
```
✓ Vector Store: Added 1 document, found 1 results
✓ RAG Answer: Generated answer with method 'rag'
✅ Basic RAG functionality test completed successfully!
```

## Integration with Existing System

The RAG module integrates seamlessly with existing PaiNaiDee features:

- **Emotion Analysis**: Enhanced responses based on user sentiment
- **3D Model Selection**: Tourism-aware model recommendations
- **Multi-modal Actions**: Coordinated responses with gestures and UI
- **Thai Cultural Context**: Culturally appropriate recommendations

## Future Enhancements

- [ ] **Advanced Vector Stores**: ChromaDB, Pinecone integration
- [ ] **LLM Integration**: GPT/Claude/Llama for better generation
- [ ] **Real-time Updates**: WebSocket-based live data feeds
- [ ] **Advanced Crawling**: RSS feed parsing, API integrations
- [ ] **Analytics**: Usage patterns and performance metrics
- [ ] **Caching**: Redis integration for improved performance

## Troubleshooting

### Common Issues

1. **No documents found**: Add sample data using `/rag/add_sample_data`
2. **Slow responses**: Check vector store fit status in `/rag/stats`
3. **Scheduler not working**: Verify status with `/rag/scheduler/status`
4. **Network errors**: Check robots.txt compliance and rate limits

### Debug Mode

Enable debug logging by setting:
```bash
export LOG_LEVEL=DEBUG
```

## Security Considerations

- **Robots.txt Compliance**: Respects website crawling policies
- **Rate Limiting**: Configurable delays between requests
- **Input Validation**: Sanitized user inputs and queries
- **Error Exposure**: Controlled error messages to prevent information leakage

---

**The RAG module successfully extends PaiNaiDee AI Assistant with modern retrieval-augmented generation capabilities, enabling it to provide up-to-date, contextual tourism information while maintaining the existing 3D visualization and cultural features.**