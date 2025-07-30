"""
Simple in-memory vector store for document embeddings.
Lightweight alternative to ChromaDB for development and small-scale usage.
"""

import json
import os
import pickle
from typing import List, Dict, Any, Optional, Tuple
import numpy as np
from sklearn.metrics.pairwise import cosine_similarity
from sklearn.feature_extraction.text import TfidfVectorizer
import logging

logger = logging.getLogger(__name__)

class SimpleVectorStore:
    """Simple in-memory vector store using TF-IDF and cosine similarity."""
    
    def __init__(self, storage_path: str = "cache/vector_store"):
        self.storage_path = storage_path
        self.documents: List[Dict[str, Any]] = []
        self.vectorizer = TfidfVectorizer(max_features=1000, stop_words='english')
        self.document_vectors = None
        self.is_fitted = False
        
        # Create storage directory
        os.makedirs(storage_path, exist_ok=True)
        
        # Load existing data if available
        self._load()
    
    def add_documents(self, documents: List[Dict[str, Any]]) -> None:
        """
        Add documents to the vector store.
        
        Args:
            documents: List of documents with 'content', 'metadata', and optional 'id'
        """
        for doc in documents:
            if 'id' not in doc:
                doc['id'] = f"doc_{len(self.documents)}"
            
            # Ensure required fields
            if 'content' not in doc:
                raise ValueError("Document must have 'content' field")
            if 'metadata' not in doc:
                doc['metadata'] = {}
            
            self.documents.append(doc)
        
        # Re-fit vectorizer with all documents
        self._fit_vectorizer()
        self._save()
        
        logger.info(f"Added {len(documents)} documents. Total: {len(self.documents)}")
    
    def search(self, query: str, top_k: int = 5, min_score: float = 0.1) -> List[Dict[str, Any]]:
        """
        Search for similar documents.
        
        Args:
            query: Search query text
            top_k: Number of top results to return
            min_score: Minimum similarity score threshold
            
        Returns:
            List of documents with similarity scores
        """
        if not self.is_fitted or len(self.documents) == 0:
            return []
        
        try:
            # Vectorize the query
            query_vector = self.vectorizer.transform([query])
            
            # Calculate similarities
            similarities = cosine_similarity(query_vector, self.document_vectors)[0]
            
            # Get top_k results above threshold
            top_indices = np.argsort(similarities)[::-1][:top_k]
            
            results = []
            for idx in top_indices:
                score = similarities[idx]
                if score >= min_score:
                    doc = self.documents[idx].copy()
                    doc['similarity_score'] = float(score)
                    results.append(doc)
            
            logger.info(f"Search query: '{query}' returned {len(results)} results")
            return results
            
        except Exception as e:
            logger.error(f"Error during search: {e}")
            return []
    
    def get_document_count(self) -> int:
        """Get the total number of documents in the store."""
        return len(self.documents)
    
    def clear(self) -> None:
        """Clear all documents from the store."""
        self.documents = []
        self.document_vectors = None
        self.is_fitted = False
        self._save()
        logger.info("Vector store cleared")
    
    def _fit_vectorizer(self) -> None:
        """Fit the TF-IDF vectorizer on all documents."""
        if not self.documents:
            return
        
        # Extract text content from all documents
        texts = [doc['content'] for doc in self.documents]
        
        try:
            # Fit and transform documents
            self.document_vectors = self.vectorizer.fit_transform(texts)
            self.is_fitted = True
            logger.info(f"Vectorizer fitted on {len(texts)} documents")
        except Exception as e:
            logger.error(f"Error fitting vectorizer: {e}")
            self.is_fitted = False
    
    def _save(self) -> None:
        """Save the vector store to disk."""
        try:
            # Save documents as JSON
            docs_path = os.path.join(self.storage_path, "documents.json")
            with open(docs_path, 'w', encoding='utf-8') as f:
                json.dump(self.documents, f, ensure_ascii=False, indent=2)
            
            # Save vectorizer if fitted
            if self.is_fitted:
                vectorizer_path = os.path.join(self.storage_path, "vectorizer.pkl")
                with open(vectorizer_path, 'wb') as f:
                    pickle.dump(self.vectorizer, f)
                
                vectors_path = os.path.join(self.storage_path, "vectors.pkl")
                with open(vectors_path, 'wb') as f:
                    pickle.dump(self.document_vectors, f)
                    
        except Exception as e:
            logger.error(f"Error saving vector store: {e}")
    
    def _load(self) -> None:
        """Load the vector store from disk."""
        try:
            docs_path = os.path.join(self.storage_path, "documents.json")
            if os.path.exists(docs_path):
                with open(docs_path, 'r', encoding='utf-8') as f:
                    self.documents = json.load(f)
                
                # Load vectorizer if available
                vectorizer_path = os.path.join(self.storage_path, "vectorizer.pkl")
                vectors_path = os.path.join(self.storage_path, "vectors.pkl")
                
                if os.path.exists(vectorizer_path) and os.path.exists(vectors_path):
                    with open(vectorizer_path, 'rb') as f:
                        self.vectorizer = pickle.load(f)
                    
                    with open(vectors_path, 'rb') as f:
                        self.document_vectors = pickle.load(f)
                    
                    self.is_fitted = True
                    logger.info(f"Loaded vector store with {len(self.documents)} documents")
                else:
                    # Re-fit if documents exist but no vectorizer
                    if self.documents:
                        self._fit_vectorizer()
                        
        except Exception as e:
            logger.error(f"Error loading vector store: {e}")
            self.documents = []
            self.is_fitted = False

    def get_statistics(self) -> Dict[str, Any]:
        """Get statistics about the vector store."""
        return {
            "total_documents": len(self.documents),
            "is_fitted": self.is_fitted,
            "storage_path": self.storage_path,
            "vectorizer_features": self.vectorizer.max_features if self.is_fitted else 0
        }