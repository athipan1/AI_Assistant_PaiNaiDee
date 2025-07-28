"""
Semantic Search Engine for 3D Model Selection
Implements embeddings-based search for semantic meaning rather than just keywords
"""

import numpy as np
import json
import re
from typing import Dict, List, Any, Optional, Tuple
from dataclasses import dataclass
from pathlib import Path
import logging
import math

logger = logging.getLogger(__name__)

@dataclass
class ModelEmbedding:
    """Model with its semantic embedding"""
    name: str
    description: str
    keywords: List[str]
    embedding: np.ndarray
    metadata: Dict[str, Any]

@dataclass
class SearchResult:
    """Search result with similarity score"""
    model_name: str
    similarity_score: float
    description: str
    matched_concepts: List[str]
    semantic_reasoning: str

class SimpleWordEmbeddings:
    """
    Lightweight word embedding implementation for offline semantic search
    Uses pre-computed word vectors and TF-IDF weighting
    """
    
    def __init__(self):
        # Simple pre-computed embeddings for 3D model domain
        # In a full implementation, these would be learned from larger corpora
        self.word_vectors = {
            # Person/Character words
            "person": np.array([1.0, 0.8, 0.2, 0.1, 0.5, 0.3]),
            "human": np.array([1.0, 0.9, 0.1, 0.1, 0.4, 0.2]),
            "character": np.array([0.9, 0.7, 0.3, 0.2, 0.6, 0.4]),
            "figure": np.array([0.8, 0.6, 0.2, 0.1, 0.3, 0.1]),
            "man": np.array([1.0, 0.8, 0.0, 0.1, 0.3, 0.1]),
            "woman": np.array([1.0, 0.8, 0.0, 0.2, 0.3, 0.1]),
            
            # Animation/Motion words
            "walking": np.array([0.3, 0.2, 1.0, 0.8, 0.1, 0.1]),
            "running": np.array([0.2, 0.1, 1.0, 0.9, 0.1, 0.1]),
            "moving": np.array([0.3, 0.2, 0.9, 0.7, 0.2, 0.1]),
            "animation": np.array([0.2, 0.3, 0.9, 0.8, 0.5, 0.6]),
            "motion": np.array([0.1, 0.2, 1.0, 0.8, 0.3, 0.2]),
            "idle": np.array([0.5, 0.4, 0.1, 0.1, 0.8, 0.3]),
            "standing": np.array([0.6, 0.5, 0.2, 0.1, 0.9, 0.2]),
            "still": np.array([0.4, 0.3, 0.1, 0.1, 0.9, 0.1]),
            
            # Style words
            "realistic": np.array([0.8, 0.9, 0.2, 0.3, 0.1, 0.8]),
            "stylized": np.array([0.6, 0.7, 0.3, 0.4, 0.2, 0.9]),
            "cartoon": np.array([0.5, 0.6, 0.4, 0.5, 0.3, 1.0]),
            "basic": np.array([0.7, 0.5, 0.2, 0.2, 0.5, 0.3]),
            "simple": np.array([0.6, 0.4, 0.2, 0.1, 0.6, 0.2]),
            
            # Purpose words
            "display": np.array([0.4, 0.5, 0.1, 0.2, 0.7, 0.5]),
            "show": np.array([0.4, 0.5, 0.1, 0.2, 0.6, 0.4]),
            "demo": np.array([0.3, 0.4, 0.2, 0.3, 0.7, 0.6]),
            "rigged": np.array([0.5, 0.6, 0.7, 0.8, 0.3, 0.7]),
            "skeleton": np.array([0.6, 0.7, 0.6, 0.7, 0.2, 0.6]),
            "bones": np.array([0.6, 0.7, 0.5, 0.6, 0.2, 0.5]),
            
            # Activity words
            "game": np.array([0.3, 0.4, 0.5, 0.6, 0.3, 0.8]),
            "visualization": np.array([0.4, 0.5, 0.2, 0.3, 0.8, 0.6]),
            "render": np.array([0.2, 0.3, 0.1, 0.2, 0.7, 0.8]),
            "3d": np.array([0.5, 0.6, 0.4, 0.5, 0.6, 0.7]),
            "model": np.array([0.7, 0.8, 0.3, 0.4, 0.4, 0.5]),
        }
        
        # Dimension meanings (for interpretability):
        # 0: Human-likeness, 1: Character-ness, 2: Motion, 3: Speed
        # 4: Staticness, 5: Artistic/Technical
        
        self.embedding_dim = 6
        
        # Synonyms and related terms
        self.synonyms = {
            "person": ["human", "figure", "character"],
            "walk": ["walking", "stroll", "step"],
            "run": ["running", "sprint", "jog"],
            "stand": ["standing", "idle", "still"],
            "animate": ["animation", "animated", "motion"],
            "rig": ["rigged", "skeleton", "bones"]
        }
    
    def get_word_embedding(self, word: str) -> np.ndarray:
        """Get embedding for a single word"""
        word = word.lower().strip()
        
        if word in self.word_vectors:
            return self.word_vectors[word]
        
        # Check for synonyms
        for base_word, synonyms in self.synonyms.items():
            if word in synonyms and base_word in self.word_vectors:
                return self.word_vectors[base_word]
        
        # Return neutral embedding for unknown words
        return np.zeros(self.embedding_dim)
    
    def get_text_embedding(self, text: str) -> np.ndarray:
        """Get embedding for a text by averaging word embeddings"""
        words = re.findall(r'\b\w+\b', text.lower())
        
        if not words:
            return np.zeros(self.embedding_dim)
        
        embeddings = []
        for word in words:
            embedding = self.get_word_embedding(word)
            if np.any(embedding):  # Only include non-zero embeddings
                embeddings.append(embedding)
        
        if not embeddings:
            return np.zeros(self.embedding_dim)
        
        # Weighted average (could be improved with TF-IDF)
        return np.mean(embeddings, axis=0)

class SemanticSearchEngine:
    """
    Semantic search engine for 3D models using lightweight embeddings
    """
    
    def __init__(self, models_dir: Optional[Path] = None):
        self.models_dir = models_dir or Path(__file__).parent.parent.parent / "assets" / "models" / "Fbx"
        self.embeddings = SimpleWordEmbeddings()
        self.model_embeddings: List[ModelEmbedding] = []
        self._initialize_model_embeddings()
    
    def _initialize_model_embeddings(self):
        """Initialize embeddings for all available models"""
        # Define detailed model information for semantic search
        model_info = {
            "Man.fbx": {
                "description": "Basic human character figure in neutral pose for general display",
                "keywords": ["person", "human", "man", "character", "figure", "basic", "neutral", "display"],
                "metadata": {
                    "style": "neutral",
                    "motion": "none",
                    "purpose": "display",
                    "complexity": "simple"
                }
            },
            "Idle.fbx": {
                "description": "Human character in idle standing pose for static visualization",
                "keywords": ["idle", "standing", "still", "pose", "static", "waiting", "character", "person"],
                "metadata": {
                    "style": "neutral",
                    "motion": "idle",
                    "purpose": "display",
                    "complexity": "simple"
                }
            },
            "Walking.fbx": {
                "description": "Animated character demonstrating walking motion and movement",
                "keywords": ["walking", "walk", "moving", "step", "stroll", "animation", "motion", "character"],
                "metadata": {
                    "style": "neutral",
                    "motion": "walking",
                    "purpose": "animation",
                    "complexity": "medium"
                }
            },
            "Running.fbx": {
                "description": "Animated character showing running motion at high speed",
                "keywords": ["running", "run", "fast", "sprint", "jogging", "animation", "motion", "speed"],
                "metadata": {
                    "style": "neutral",
                    "motion": "running",
                    "purpose": "animation",
                    "complexity": "medium"
                }
            },
            "Man_Rig.fbx": {
                "description": "Rigged character model with skeleton for custom animations and development",
                "keywords": ["rigged", "rig", "skeleton", "bones", "custom", "animation", "development", "character"],
                "metadata": {
                    "style": "neutral",
                    "motion": "custom",
                    "purpose": "development",
                    "complexity": "high"
                }
            }
        }
        
        for model_name, info in model_info.items():
            # Create combined text for embedding
            combined_text = f"{info['description']} {' '.join(info['keywords'])}"
            embedding = self.embeddings.get_text_embedding(combined_text)
            
            model_embedding = ModelEmbedding(
                name=model_name,
                description=info['description'],
                keywords=info['keywords'],
                embedding=embedding,
                metadata=info['metadata']
            )
            self.model_embeddings.append(model_embedding)
    
    def search(self, query: str, top_k: int = 3) -> List[SearchResult]:
        """
        Perform semantic search for models based on query
        
        Args:
            query: User search query
            top_k: Number of top results to return
            
        Returns:
            List of SearchResult objects sorted by similarity
        """
        query_embedding = self.embeddings.get_text_embedding(query)
        
        if np.all(query_embedding == 0):
            # Fallback to keyword matching if no semantic embedding
            return self._fallback_keyword_search(query, top_k)
        
        results = []
        
        for model in self.model_embeddings:
            similarity = self._calculate_similarity(query_embedding, model.embedding)
            matched_concepts = self._find_matched_concepts(query, model.keywords)
            reasoning = self._generate_semantic_reasoning(query, model, similarity, matched_concepts)
            
            result = SearchResult(
                model_name=model.name,
                similarity_score=similarity,
                description=model.description,
                matched_concepts=matched_concepts,
                semantic_reasoning=reasoning
            )
            results.append(result)
        
        # Sort by similarity score (descending)
        results.sort(key=lambda x: x.similarity_score, reverse=True)
        
        return results[:top_k]
    
    def _calculate_similarity(self, query_embedding: np.ndarray, model_embedding: np.ndarray) -> float:
        """Calculate cosine similarity between embeddings"""
        query_norm = np.linalg.norm(query_embedding)
        model_norm = np.linalg.norm(model_embedding)
        
        if query_norm == 0 or model_norm == 0:
            return 0.0
        
        similarity = np.dot(query_embedding, model_embedding) / (query_norm * model_norm)
        return max(0.0, similarity)  # Ensure non-negative
    
    def _find_matched_concepts(self, query: str, model_keywords: List[str]) -> List[str]:
        """Find conceptually matched keywords"""
        query_words = set(re.findall(r'\b\w+\b', query.lower()))
        matched = []
        
        for keyword in model_keywords:
            if keyword in query_words:
                matched.append(keyword)
            else:
                # Check for semantic similarity
                for word in query_words:
                    if self._words_semantically_similar(word, keyword):
                        matched.append(f"{keyword} (similar to '{word}')")
        
        return matched
    
    def _words_semantically_similar(self, word1: str, word2: str, threshold: float = 0.7) -> bool:
        """Check if two words are semantically similar"""
        emb1 = self.embeddings.get_word_embedding(word1)
        emb2 = self.embeddings.get_word_embedding(word2)
        
        if np.all(emb1 == 0) or np.all(emb2 == 0):
            return False
        
        similarity = self._calculate_similarity(emb1, emb2)
        return similarity >= threshold
    
    def _generate_semantic_reasoning(self, query: str, model: ModelEmbedding, 
                                   similarity: float, matched_concepts: List[str]) -> str:
        """Generate explanation for the semantic match"""
        reasoning_parts = []
        
        if similarity > 0.8:
            reasoning_parts.append("Strong semantic match")
        elif similarity > 0.6:
            reasoning_parts.append("Good semantic similarity")
        elif similarity > 0.4:
            reasoning_parts.append("Moderate semantic relevance")
        else:
            reasoning_parts.append("Weak semantic connection")
        
        if matched_concepts:
            reasoning_parts.append(f"Matched concepts: {', '.join(matched_concepts[:3])}")
        
        # Add metadata-based reasoning
        if "motion" in query.lower() and model.metadata.get("motion") != "none":
            reasoning_parts.append(f"Motion requirement satisfied ({model.metadata['motion']})")
        
        if any(word in query.lower() for word in ["rig", "skeleton", "custom"]) and model.metadata.get("purpose") == "development":
            reasoning_parts.append("Suitable for development/customization")
        
        return "; ".join(reasoning_parts)
    
    def _fallback_keyword_search(self, query: str, top_k: int) -> List[SearchResult]:
        """Fallback to simple keyword matching when embeddings fail"""
        query_words = set(re.findall(r'\b\w+\b', query.lower()))
        results = []
        
        for model in self.model_embeddings:
            score = 0
            matched = []
            
            for keyword in model.keywords:
                if keyword in query_words:
                    score += 1
                    matched.append(keyword)
            
            if score > 0:
                normalized_score = score / len(model.keywords)
                result = SearchResult(
                    model_name=model.name,
                    similarity_score=normalized_score,
                    description=model.description,
                    matched_concepts=matched,
                    semantic_reasoning=f"Keyword match: {', '.join(matched)}"
                )
                results.append(result)
        
        results.sort(key=lambda x: x.similarity_score, reverse=True)
        return results[:top_k]
    
    def explain_search(self, query: str) -> Dict[str, Any]:
        """
        Provide detailed explanation of how the search works for a query
        """
        query_embedding = self.embeddings.get_text_embedding(query)
        query_words = re.findall(r'\b\w+\b', query.lower())
        
        explanation = {
            "query": query,
            "query_words": query_words,
            "query_embedding": query_embedding.tolist() if query_embedding is not None else None,
            "embedding_interpretation": self._interpret_embedding(query_embedding),
            "word_embeddings": {},
            "search_results": []
        }
        
        # Show individual word embeddings
        for word in query_words:
            word_emb = self.embeddings.get_word_embedding(word)
            if np.any(word_emb):
                explanation["word_embeddings"][word] = {
                    "embedding": word_emb.tolist(),
                    "interpretation": self._interpret_embedding(word_emb)
                }
        
        # Get and explain search results
        results = self.search(query)
        for result in results:
            explanation["search_results"].append({
                "model": result.model_name,
                "similarity": result.similarity_score,
                "reasoning": result.semantic_reasoning,
                "matched_concepts": result.matched_concepts
            })
        
        return explanation
    
    def _interpret_embedding(self, embedding: np.ndarray) -> Dict[str, str]:
        """Interpret embedding dimensions for human understanding"""
        if embedding is None or np.all(embedding == 0):
            return {"interpretation": "No semantic information"}
        
        dimensions = {
            0: ("Human-likeness", embedding[0]),
            1: ("Character-ness", embedding[1]),
            2: ("Motion", embedding[2]),
            3: ("Speed", embedding[3]),
            4: ("Staticness", embedding[4]),
            5: ("Artistic/Technical", embedding[5])
        }
        
        # Find strongest dimensions
        strong_dims = [(name, value) for name, value in dimensions.values() if value > 0.5]
        strong_dims.sort(key=lambda x: x[1], reverse=True)
        
        if strong_dims:
            interpretation = f"Strong in: {', '.join([name for name, _ in strong_dims[:3]])}"
        else:
            interpretation = "Neutral/balanced semantic profile"
        
        return {
            "interpretation": interpretation,
            "strongest_dimensions": strong_dims[:3]
        }

# Global instance
semantic_search_engine = SemanticSearchEngine()

def test_semantic_search():
    """Test the semantic search engine"""
    engine = SemanticSearchEngine()
    
    test_queries = [
        "Show me a walking person",
        "I need something for animation",
        "Display a human character",
        "I want to see running motion",
        "Show me a rigged model",
        "I need an idle pose",
        "Can you show me movement?",
        "I want a character for my game",
        "Show me a figure standing still",
        "I need custom animation capability"
    ]
    
    print("Testing Semantic Search Engine:")
    print("=" * 60)
    
    for query in test_queries:
        print(f"Query: '{query}'")
        results = engine.search(query, top_k=3)
        
        for i, result in enumerate(results, 1):
            print(f"  {i}. {result.model_name} (similarity: {result.similarity_score:.3f})")
            print(f"     Reasoning: {result.semantic_reasoning}")
            if result.matched_concepts:
                print(f"     Matched: {', '.join(result.matched_concepts)}")
        print("-" * 40)

if __name__ == "__main__":
    test_semantic_search()