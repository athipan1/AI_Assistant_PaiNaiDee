"""
Test suite for RAG (Retrieval-Augmented Generation) functionality.
"""

import asyncio
import sys
import os

# Add the parent directory to sys.path so we can import the RAG modules
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))

from rag.core import RAGSystem
from rag.vector_store import SimpleVectorStore
from rag.retriever import DocumentRetriever
from rag.crawler import TourismCrawler

class TestRAGSystem:
    """Test cases for the RAG system."""
    
    def setup_method(self):
        """Set up test environment."""
        self.rag_system = RAGSystem("cache/test_vector_store")
        
        # Add sample documents for testing
        self.sample_documents = [
            {
                "id": "test_1",
                "content": "Bangkok is Thailand's capital city with amazing temples and street food.",
                "metadata": {
                    "source": "Test Data",
                    "title": "Bangkok Guide",
                    "url": "https://test.com/bangkok",
                    "type": "tourism_info"
                }
            },
            {
                "id": "test_2",
                "content": "Thai food includes Pad Thai, Tom Yum, and Green Curry. Very delicious and spicy.",
                "metadata": {
                    "source": "Test Data", 
                    "title": "Thai Food Guide",
                    "url": "https://test.com/food",
                    "type": "food_info"
                }
            }
        ]
        
        self.rag_system.vector_store.add_documents(self.sample_documents)
    
    def teardown_method(self):
        """Clean up after tests."""
        self.rag_system.vector_store.clear()
    
    def test_vector_store_functionality(self):
        """Test vector store operations."""
        vector_store = SimpleVectorStore("cache/test_vector_store_2")
        
        # Test adding documents
        vector_store.add_documents(self.sample_documents)
        assert vector_store.get_document_count() == 2
        
        # Test search
        results = vector_store.search("Bangkok Thailand", top_k=1)
        assert len(results) > 0
        assert "Bangkok" in results[0]["content"]
        
        # Test clear
        vector_store.clear()
        assert vector_store.get_document_count() == 0
    
    def test_document_retriever(self):
        """Test document retrieval functionality."""
        retriever = DocumentRetriever(self.rag_system.vector_store)
        
        # Test retrieval
        results = retriever.retrieve_documents("Thai food", top_k=2)
        assert len(results) > 0
        
        # Test context preparation
        context = retriever.prepare_context(results)
        assert len(context) > 0
        assert "Thai food" in context or "food" in context
    
    async def test_rag_answer_generation(self):
        """Test RAG answer generation."""
        # Test with existing data
        result = await self.rag_system.answer_question("What is Bangkok like?")
        assert result["answer"] is not None
        assert result["metadata"]["method"] == "rag"
        assert result["metadata"]["documents_used"] > 0
        
        # Test with no relevant data
        result = await self.rag_system.answer_question("What is the weather like on Mars?")
        assert result["answer"] is not None
        assert result["metadata"]["method"] in ["simple_fallback", "ai_fallback"]
        
    async def test_thai_language_support(self):
        """Test Thai language support."""
        result = await self.rag_system.answer_question("อาหารไทยมีอะไรบ้าง", language="th")
        assert result["answer"] is not None
        assert result["metadata"]["language"] == "th"
    
    def test_crawler_configuration(self):
        """Test crawler configuration."""
        crawler = TourismCrawler()
        
        # Test getting sources
        sources = crawler.get_sources()
        assert len(sources) > 0
        
        # Test adding source
        crawler.add_source("test_source", {
            "type": "web",
            "url": "https://test.com",
            "name": "Test Source"
        })
        
        sources_after = crawler.get_sources()
        assert len(sources_after) == len(sources) + 1
        assert "test_source" in sources_after
        
        # Test removing source
        success = crawler.remove_source("test_source")
        assert success == True
    
    def test_rag_system_stats(self):
        """Test RAG system statistics."""
        stats = self.rag_system.get_system_stats()
        
        assert "vector_store" in stats
        assert "retriever" in stats
        assert "crawler_sources" in stats
        assert "supported_languages" in stats
        
        assert stats["vector_store"]["total_documents"] == 2
        assert "en" in stats["supported_languages"]
        assert "th" in stats["supported_languages"]

def run_tests():
    """Run all RAG tests."""
    import subprocess
    
    # Run pytest on this file
    result = subprocess.run([
        sys.executable, "-m", "pytest", __file__, "-v"
    ], capture_output=True, text=True)
    
    print("RAG Test Results:")
    print("=" * 50)
    print(result.stdout)
    if result.stderr:
        print("Errors:")
        print(result.stderr)
    
    return result.returncode == 0

if __name__ == "__main__":
    # Run a simple test without pytest
    print("Running basic RAG functionality test...")
    
    # Test vector store
    vector_store = SimpleVectorStore("cache/test_vector_store_basic")
    sample_doc = [{
        "id": "test_basic",
        "content": "Bangkok is Thailand's capital with great food and temples.",
        "metadata": {"source": "Test", "title": "Bangkok Test"}
    }]
    
    vector_store.add_documents(sample_doc)
    results = vector_store.search("Bangkok Thailand")
    
    print(f"✓ Vector Store: Added 1 document, found {len(results)} results")
    
    # Test RAG system
    rag = RAGSystem("cache/test_rag_basic")
    rag.vector_store.add_documents(sample_doc)
    
    async def test_answer():
        result = await rag.answer_question("Tell me about Bangkok")
        return result
    
    answer_result = asyncio.run(test_answer())
    print(f"✓ RAG Answer: Generated answer with method '{answer_result['metadata']['method']}'")
    
    # Clean up
    vector_store.clear()
    rag.vector_store.clear()
    
    print("\n✅ Basic RAG functionality test completed successfully!")
    print("\nTo run full test suite: python -m pytest tests/test_rag.py -v")