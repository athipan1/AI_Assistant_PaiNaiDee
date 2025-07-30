"""
Document retriever for RAG system.
Handles document search, ranking, and context preparation.
"""

import logging
from typing import List, Dict, Any, Optional, Tuple
from datetime import datetime, timedelta
import re

from .vector_store import SimpleVectorStore

logger = logging.getLogger(__name__)

class DocumentRetriever:
    """Document retriever for RAG-based question answering."""
    
    def __init__(self, vector_store: SimpleVectorStore):
        self.vector_store = vector_store
        
        # Thai tourism-related keywords for query enhancement
        self.tourism_keywords = {
            'thai': ['thailand', 'thai', 'ไทย', 'ประเทศไทย'],
            'places': ['place', 'destination', 'location', 'สถานที่', 'จุดหมาย'],
            'travel': ['travel', 'trip', 'tour', 'visit', 'เดินทาง', 'ท่องเที่ยว', 'เที่ยว'],
            'food': ['food', 'restaurant', 'eat', 'dining', 'อาหาร', 'ร้านอาหาร', 'กิน'],
            'hotel': ['hotel', 'accommodation', 'stay', 'resort', 'โรงแรม', 'ที่พัก'],
            'activity': ['activity', 'attraction', 'things to do', 'กิจกรรม', 'สถานที่ท่องเที่ยว'],
            'culture': ['culture', 'temple', 'tradition', 'วัฒนธรรม', 'วัด', 'ประเพณี'],
            'beach': ['beach', 'island', 'sea', 'ชายหาด', 'เกาะ', 'ทะเล'],
            'shopping': ['shopping', 'market', 'mall', 'buy', 'ช้อปปิ้ง', 'ตลาด', 'ห้าง'],
            'transport': ['transport', 'bus', 'train', 'flight', 'การเดินทาง', 'รถบัส', 'รถไฟ', 'เครื่องบิน']
        }
    
    def retrieve_documents(self, query: str, top_k: int = 5, 
                          min_relevance_score: float = 0.1,
                          filters: Optional[Dict[str, Any]] = None) -> List[Dict[str, Any]]:
        """
        Retrieve relevant documents for a query.
        
        Args:
            query: User query text
            top_k: Maximum number of documents to retrieve
            min_relevance_score: Minimum relevance score threshold
            filters: Optional filters for document metadata
            
        Returns:
            List of relevant documents with scores
        """
        try:
            # Enhance query with tourism context
            enhanced_query = self._enhance_query(query)
            
            # Search vector store
            results = self.vector_store.search(
                enhanced_query, 
                top_k=top_k * 2,  # Get more results for filtering
                min_score=min_relevance_score
            )
            
            # Apply filters if specified
            if filters:
                results = self._apply_filters(results, filters)
            
            # Re-rank and limit results
            results = self._rerank_results(results, query)[:top_k]
            
            logger.info(f"Retrieved {len(results)} documents for query: '{query}'")
            return results
            
        except Exception as e:
            logger.error(f"Error retrieving documents: {e}")
            return []
    
    def prepare_context(self, documents: List[Dict[str, Any]], 
                       max_context_length: int = 2000) -> str:
        """
        Prepare context text from retrieved documents.
        
        Args:
            documents: List of relevant documents
            max_context_length: Maximum length of context text
            
        Returns:
            Formatted context string
        """
        if not documents:
            return ""
        
        context_parts = []
        current_length = 0
        
        for doc in documents:
            content = doc.get('content', '')
            metadata = doc.get('metadata', {})
            score = doc.get('similarity_score', 0)
            
            # Format document with source information
            doc_text = f"Source: {metadata.get('source', 'Unknown')}\n"
            if metadata.get('title'):
                doc_text += f"Title: {metadata['title']}\n"
            doc_text += f"Content: {content}\n"
            doc_text += f"Relevance: {score:.2f}\n\n"
            
            # Check if adding this document would exceed length limit
            if current_length + len(doc_text) > max_context_length:
                # Try to fit partial content
                remaining_length = max_context_length - current_length
                if remaining_length > 200:  # Only if there's meaningful space left
                    truncated_content = content[:remaining_length-100] + "..."
                    doc_text = f"Source: {metadata.get('source', 'Unknown')}\n"
                    if metadata.get('title'):
                        doc_text += f"Title: {metadata['title']}\n"
                    doc_text += f"Content: {truncated_content}\n\n"
                    context_parts.append(doc_text)
                break
            
            context_parts.append(doc_text)
            current_length += len(doc_text)
        
        return "".join(context_parts).strip()
    
    def _enhance_query(self, query: str) -> str:
        """Enhance query with tourism-related context."""
        query_lower = query.lower()
        
        # Check if query already contains tourism keywords
        has_tourism_context = any(
            keyword in query_lower 
            for keywords in self.tourism_keywords.values() 
            for keyword in keywords
        )
        
        # If no tourism context detected, add general tourism terms
        if not has_tourism_context:
            query += " thailand tourism travel"
        
        return query
    
    def _apply_filters(self, documents: List[Dict[str, Any]], 
                      filters: Dict[str, Any]) -> List[Dict[str, Any]]:
        """Apply metadata filters to documents."""
        filtered_docs = []
        
        for doc in documents:
            metadata = doc.get('metadata', {})
            include_doc = True
            
            for filter_key, filter_value in filters.items():
                if filter_key in metadata:
                    if isinstance(filter_value, list):
                        if metadata[filter_key] not in filter_value:
                            include_doc = False
                            break
                    else:
                        if metadata[filter_key] != filter_value:
                            include_doc = False
                            break
            
            if include_doc:
                filtered_docs.append(doc)
        
        return filtered_docs
    
    def _rerank_results(self, documents: List[Dict[str, Any]], 
                       original_query: str) -> List[Dict[str, Any]]:
        """Re-rank documents based on additional criteria."""
        for doc in documents:
            base_score = doc.get('similarity_score', 0)
            metadata = doc.get('metadata', {})
            
            # Boost recent documents
            recency_boost = self._calculate_recency_boost(metadata.get('crawled_at'))
            
            # Boost documents from authoritative sources
            authority_boost = self._calculate_authority_boost(metadata.get('source', ''))
            
            # Boost documents with tourism keywords in title
            title_boost = self._calculate_title_boost(metadata.get('title', ''), original_query)
            
            # Calculate final score
            final_score = base_score * (1 + recency_boost + authority_boost + title_boost)
            doc['final_score'] = final_score
        
        # Sort by final score
        return sorted(documents, key=lambda x: x.get('final_score', 0), reverse=True)
    
    def _calculate_recency_boost(self, crawled_at: Optional[str]) -> float:
        """Calculate boost based on document recency."""
        if not crawled_at:
            return 0.0
        
        try:
            crawl_date = datetime.fromisoformat(crawled_at.replace('Z', '+00:00'))
            days_old = (datetime.now() - crawl_date.replace(tzinfo=None)).days
            
            if days_old <= 1:
                return 0.3  # Very recent
            elif days_old <= 7:
                return 0.2  # Recent
            elif days_old <= 30:
                return 0.1  # Somewhat recent
            else:
                return 0.0  # Older
                
        except Exception:
            return 0.0
    
    def _calculate_authority_boost(self, source: str) -> float:
        """Calculate boost based on source authority."""
        authoritative_sources = {
            'Tourism Authority of Thailand': 0.4,
            'TAT News': 0.4,
            'Thai PBS': 0.3,
            'Government': 0.3,
            'Official': 0.2
        }
        
        source_lower = source.lower()
        for auth_source, boost in authoritative_sources.items():
            if auth_source.lower() in source_lower:
                return boost
        
        return 0.0
    
    def _calculate_title_boost(self, title: str, query: str) -> float:
        """Calculate boost based on title relevance."""
        if not title:
            return 0.0
        
        title_lower = title.lower()
        query_lower = query.lower()
        
        # Simple keyword matching in title
        query_words = query_lower.split()
        title_matches = sum(1 for word in query_words if word in title_lower)
        
        if title_matches > 0:
            return min(0.2, title_matches * 0.05)  # Up to 0.2 boost
        
        return 0.0
    
    def get_retrieval_stats(self) -> Dict[str, Any]:
        """Get statistics about the retrieval system."""
        return {
            "total_documents": self.vector_store.get_document_count(),
            "vector_store_stats": self.vector_store.get_statistics(),
            "tourism_keyword_categories": len(self.tourism_keywords)
        }