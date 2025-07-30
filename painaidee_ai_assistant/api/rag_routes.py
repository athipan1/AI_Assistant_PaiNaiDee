"""
RAG (Retrieval-Augmented Generation) API Routes for PaiNaiDee AI Assistant

Provides endpoints for RAG-based question answering and knowledge base management.
"""

import asyncio
import logging
from typing import Dict, Any, List, Optional
from datetime import datetime

from fastapi import APIRouter, HTTPException, BackgroundTasks, Depends
from pydantic import BaseModel, Field

from rag.core import RAGSystem

logger = logging.getLogger(__name__)

# Initialize RAG system (will be done once)
rag_system = None

def get_rag_system() -> RAGSystem:
    """Get or initialize the RAG system."""
    global rag_system
    if rag_system is None:
        rag_system = RAGSystem()
    return rag_system

# Pydantic models for API
class RAGSearchRequest(BaseModel):
    question: str = Field(..., description="User's question about Thai tourism")
    language: str = Field("en", description="Response language: 'en' or 'th'")
    include_sources: bool = Field(True, description="Include source URLs in response")
    max_context_length: int = Field(2000, description="Maximum context length for generation")

class RAGSearchResponse(BaseModel):
    answer: str
    sources: List[Dict[str, str]]
    metadata: Dict[str, Any]

class DataSourceConfig(BaseModel):
    type: str = Field(..., description="Source type: 'rss', 'web', or 'api'")
    url: str = Field(..., description="Source URL")
    name: str = Field(..., description="Human-readable source name")
    enabled: bool = Field(True, description="Whether source is enabled")
    headers: Optional[Dict[str, str]] = Field(None, description="HTTP headers for requests")
    params: Optional[Dict[str, str]] = Field(None, description="Query parameters for requests")

class UpdateSourcesRequest(BaseModel):
    action: str = Field(..., description="Action: 'add', 'remove', 'enable', 'disable'")
    source_id: str = Field(..., description="Unique identifier for the source")
    config: Optional[DataSourceConfig] = Field(None, description="Source configuration (required for 'add')")

class KnowledgeBaseUpdateResponse(BaseModel):
    status: str
    documents_added: Optional[int] = None
    total_documents: Optional[int] = None
    update_time_seconds: Optional[float] = None
    timestamp: str
    message: Optional[str] = None
    error: Optional[str] = None

# Create router
router = APIRouter(prefix="/rag", tags=["RAG (Retrieval-Augmented Generation)"])

@router.post("/search", response_model=RAGSearchResponse)
async def rag_search(request: RAGSearchRequest, rag: RAGSystem = Depends(get_rag_system)):
    """
    Search for information and generate AI-powered answers based on retrieved context.
    
    This endpoint uses retrieval-augmented generation to answer questions about Thai tourism
    by finding relevant information from crawled sources and generating contextual responses.
    """
    try:
        if not request.question.strip():
            raise HTTPException(status_code=400, detail="Question cannot be empty")
        
        if request.language not in ["en", "th"]:
            raise HTTPException(status_code=400, detail="Language must be 'en' or 'th'")
        
        # Generate answer using RAG
        result = await rag.answer_question(
            question=request.question,
            language=request.language,
            include_sources=request.include_sources,
            max_context_length=request.max_context_length
        )
        
        return RAGSearchResponse(**result)
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error in RAG search: {e}")
        raise HTTPException(status_code=500, detail=f"Internal server error: {str(e)}")

@router.post("/update_sources", response_model=Dict[str, Any])
async def update_sources(request: UpdateSourcesRequest, rag: RAGSystem = Depends(get_rag_system)):
    """
    Add, remove, enable, or disable data sources for the RAG system.
    
    Allows dynamic management of data sources that the system crawls for information.
    """
    try:
        if request.action == "add":
            if not request.config:
                raise HTTPException(status_code=400, detail="Config is required for 'add' action")
            
            success = rag.add_data_source(request.source_id, request.config.dict())
            if success:
                return {
                    "status": "success",
                    "message": f"Source '{request.source_id}' added successfully",
                    "source_id": request.source_id
                }
            else:
                raise HTTPException(status_code=400, detail="Failed to add source")
        
        elif request.action == "remove":
            success = rag.remove_data_source(request.source_id)
            if success:
                return {
                    "status": "success",
                    "message": f"Source '{request.source_id}' removed successfully",
                    "source_id": request.source_id
                }
            else:
                raise HTTPException(status_code=404, detail="Source not found")
        
        elif request.action == "enable":
            success = rag.crawler.enable_source(request.source_id)
            if success:
                return {
                    "status": "success", 
                    "message": f"Source '{request.source_id}' enabled",
                    "source_id": request.source_id
                }
            else:
                raise HTTPException(status_code=404, detail="Source not found")
        
        elif request.action == "disable":
            success = rag.crawler.disable_source(request.source_id)
            if success:
                return {
                    "status": "success",
                    "message": f"Source '{request.source_id}' disabled", 
                    "source_id": request.source_id
                }
            else:
                raise HTTPException(status_code=404, detail="Source not found")
        
        else:
            raise HTTPException(status_code=400, detail="Invalid action. Must be 'add', 'remove', 'enable', or 'disable'")
            
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error updating sources: {e}")
        raise HTTPException(status_code=500, detail=f"Internal server error: {str(e)}")

@router.post("/update_knowledge_base", response_model=KnowledgeBaseUpdateResponse)
async def update_knowledge_base(background_tasks: BackgroundTasks, rag: RAGSystem = Depends(get_rag_system)):
    """
    Trigger a manual update of the knowledge base by crawling all enabled sources.
    
    This will fetch new content from all configured sources and add it to the vector store.
    The operation runs in the background for better performance.
    """
    try:
        # Run update in background for better performance
        result = await rag.update_knowledge_base()
        return KnowledgeBaseUpdateResponse(**result)
        
    except Exception as e:
        logger.error(f"Error updating knowledge base: {e}")
        return KnowledgeBaseUpdateResponse(
            status="error",
            error=str(e),
            timestamp=datetime.now().isoformat()
        )

@router.get("/sources", response_model=Dict[str, Any])
async def get_data_sources(rag: RAGSystem = Depends(get_rag_system)):
    """
    Get all configured data sources and their status.
    """
    try:
        sources = rag.get_data_sources()
        return {
            "sources": sources,
            "total_sources": len(sources),
            "enabled_sources": len([s for s in sources.values() if s.get('enabled', False)])
        }
    except Exception as e:
        logger.error(f"Error getting data sources: {e}")
        raise HTTPException(status_code=500, detail=f"Internal server error: {str(e)}")

@router.get("/stats", response_model=Dict[str, Any])
async def get_rag_stats(rag: RAGSystem = Depends(get_rag_system)):
    """
    Get comprehensive statistics about the RAG system.
    """
    try:
        stats = rag.get_system_stats()
        return stats
    except Exception as e:
        logger.error(f"Error getting RAG stats: {e}")
        raise HTTPException(status_code=500, detail=f"Internal server error: {str(e)}")

@router.get("/health")
async def rag_health_check(rag: RAGSystem = Depends(get_rag_system)):
    """
    Check the health status of the RAG system.
    """
    try:
        stats = rag.get_system_stats()
        
        # Determine health status
        is_healthy = True
        issues = []
        
        if stats["vector_store"]["total_documents"] == 0:
            issues.append("No documents in vector store")
            is_healthy = False
        
        if stats["crawler_sources"] == 0:
            issues.append("No data sources configured")
            is_healthy = False
        
        return {
            "status": "healthy" if is_healthy else "unhealthy",
            "timestamp": datetime.now().isoformat(),
            "issues": issues,
            "details": {
                "total_documents": stats["vector_store"]["total_documents"],
                "data_sources": stats["crawler_sources"],
                "has_ai_fallback": stats["has_ai_fallback"]
            }
        }
        
    except Exception as e:
        logger.error(f"Error in RAG health check: {e}")
        return {
            "status": "error",
            "timestamp": datetime.now().isoformat(),
            "error": str(e)
        }

@router.delete("/clear_knowledge_base")
async def clear_knowledge_base(rag: RAGSystem = Depends(get_rag_system)):
    """
    Clear all documents from the knowledge base.
    
    WARNING: This will remove all crawled documents. Use with caution.
    """
    try:
        rag.vector_store.clear()
        return {
            "status": "success",
            "message": "Knowledge base cleared successfully",
            "timestamp": datetime.now().isoformat()
        }
    except Exception as e:
        logger.error(f"Error clearing knowledge base: {e}")
        raise HTTPException(status_code=500, detail=f"Internal server error: {str(e)}")

# Add sample data for testing
@router.post("/add_sample_data")
async def add_sample_data(rag: RAGSystem = Depends(get_rag_system)):
    """
    Add sample tourism data for testing the RAG system.
    """
    try:
        sample_documents = [
            {
                "id": "sample_1",
                "content": "Bangkok is the capital and largest city of Thailand. It's known for its vibrant street life, cultural landmarks, and amazing food. Popular attractions include the Grand Palace, Wat Pho temple, and Chatuchak Weekend Market. The city offers excellent shopping, from luxury malls to street markets.",
                "metadata": {
                    "source": "Sample Tourism Data",
                    "title": "Bangkok - Thailand's Capital City",
                    "url": "https://example.com/bangkok",
                    "type": "tourism_info",
                    "crawled_at": datetime.now().isoformat()
                }
            },
            {
                "id": "sample_2", 
                "content": "Chiang Mai is Thailand's cultural capital in the north. Famous for its ancient temples, night markets, and traditional crafts. The city is surrounded by mountains and is a gateway to trekking and elephant sanctuaries. Best visited during cool season (November to February).",
                "metadata": {
                    "source": "Sample Tourism Data",
                    "title": "Chiang Mai - Cultural Capital of Northern Thailand",
                    "url": "https://example.com/chiangmai",
                    "type": "tourism_info",
                    "crawled_at": datetime.now().isoformat()
                }
            },
            {
                "id": "sample_3",
                "content": "Thai cuisine is world-renowned for its balance of sweet, sour, salty, and spicy flavors. Must-try dishes include Pad Thai, Tom Yum Goong, Green Curry, and Mango Sticky Rice. Street food is excellent and affordable. Vegetarian and vegan options are widely available.",
                "metadata": {
                    "source": "Sample Tourism Data",
                    "title": "Thai Cuisine Guide",
                    "url": "https://example.com/thai-food",
                    "type": "food_info",
                    "crawled_at": datetime.now().isoformat()
                }
            },
            {
                "id": "sample_4",
                "content": "Phuket is Thailand's largest island and most popular beach destination. Known for beautiful beaches like Patong, Kata, and Karon. Offers water sports, diving, island hopping tours. The old town has Sino-Portuguese architecture and great restaurants.",
                "metadata": {
                    "source": "Sample Tourism Data", 
                    "title": "Phuket - Thailand's Premier Beach Destination",
                    "url": "https://example.com/phuket",
                    "type": "beach_info",
                    "crawled_at": datetime.now().isoformat()
                }
            }
        ]
        
        rag.vector_store.add_documents(sample_documents)
        
        return {
            "status": "success",
            "message": f"Added {len(sample_documents)} sample documents",
            "documents_added": len(sample_documents),
            "total_documents": rag.vector_store.get_document_count()
        }
        
    except Exception as e:
        logger.error(f"Error adding sample data: {e}")
        raise HTTPException(status_code=500, detail=f"Internal server error: {str(e)}")

# Make router creation function for main.py
def create_rag_routes() -> APIRouter:
    """Create and return the RAG router."""
    return router