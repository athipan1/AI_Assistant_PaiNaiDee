"""
Core RAG system that orchestrates retrieval and generation.
Integrates with existing AI models and provides fallback mechanisms.
"""

import logging
from typing import List, Dict, Any, Optional, Tuple
from datetime import datetime
import asyncio

from .vector_store import SimpleVectorStore
from .retriever import DocumentRetriever
from .crawler import TourismCrawler

# Try to import existing AI components
try:
    from agents.model_selector import ModelSelector
    from agents.emotion_analysis import EmotionAnalysisAgent
    HAS_EXISTING_AI = True
except ImportError:
    HAS_EXISTING_AI = False

logger = logging.getLogger(__name__)

class RAGSystem:
    """Main RAG system that handles retrieval-augmented generation."""
    
    def __init__(self, vector_store_path: str = "cache/vector_store"):
        self.vector_store = SimpleVectorStore(vector_store_path)
        self.retriever = DocumentRetriever(self.vector_store)
        self.crawler = TourismCrawler()
        
        # Initialize existing AI components if available
        if HAS_EXISTING_AI:
            try:
                self.model_selector = ModelSelector()
                self.emotion_analyzer = EmotionAnalysisAgent()
                self.has_ai_fallback = True
                logger.info("Initialized RAG with existing AI components")
            except Exception as e:
                logger.warning(f"Could not initialize AI components: {e}")
                self.has_ai_fallback = False
        else:
            logger.warning("Could not import existing AI agents. RAG will work in standalone mode.")
            self.has_ai_fallback = False
        
        # Default prompt templates
        self.prompt_templates = {
            "default": """Based on the following context about Thailand tourism, please answer the user's question.

Context:
{context}

Question: {question}

Please provide a helpful and accurate answer based on the context. If the context doesn't contain enough information to answer the question, please say so and provide general guidance if possible.

Answer:""",
            
            "thai": """ตามข้อมูลท่องเที่ยวในประเทศไทยต่อไปนี้ กรุณาตอบคำถามของผู้ใช้

บริบท:
{context}

คำถาม: {question}

กรุณาให้คำตอบที่เป็นประโยชน์และถูกต้องตามบริบทที่ให้มา หากบริบทไม่มีข้อมูลเพียงพอที่จะตอบคำถาม กรุณาบอกและให้คำแนะนำทั่วไปหากเป็นไปได้

คำตอบ:""",
            
            "with_sources": """Based on the following context about Thailand tourism, please answer the user's question and cite your sources.

Context:
{context}

Question: {question}

Please provide a helpful answer and list the sources you used. Format your response as:

Answer: [Your answer here]

Sources used:
- [Source 1]
- [Source 2]
etc.

Response:"""
        }
    
    async def answer_question(self, question: str, language: str = "en", 
                            include_sources: bool = True, 
                            max_context_length: int = 2000) -> Dict[str, Any]:
        """
        Answer a question using RAG approach.
        
        Args:
            question: User's question
            language: Language for response ("en" or "th")
            include_sources: Whether to include source URLs
            max_context_length: Maximum context length for generation
            
        Returns:
            Dictionary with answer, sources, and metadata
        """
        try:
            start_time = datetime.now()
            
            # Step 1: Retrieve relevant documents
            documents = self.retriever.retrieve_documents(question, top_k=5)
            
            if not documents:
                # No relevant documents found, use fallback
                logger.info("No relevant documents found, using fallback")
                return await self._generate_fallback_answer(question, language)
            
            # Step 2: Prepare context
            context = self.retriever.prepare_context(documents, max_context_length)
            
            # Step 3: Generate answer
            answer = await self._generate_answer(question, context, language, include_sources)
            
            # Step 4: Extract sources
            sources = self._extract_sources(documents) if include_sources else []
            
            # Step 5: Calculate processing time
            processing_time = (datetime.now() - start_time).total_seconds()
            
            result = {
                "answer": answer,
                "sources": sources,
                "metadata": {
                    "method": "rag",
                    "documents_used": len(documents),
                    "processing_time_seconds": processing_time,
                    "language": language,
                    "has_context": bool(context),
                    "context_length": len(context)
                }
            }
            
            logger.info(f"Generated RAG answer in {processing_time:.2f}s using {len(documents)} documents")
            return result
            
        except Exception as e:
            logger.error(f"Error in RAG answer generation: {e}")
            return await self._generate_fallback_answer(question, language)
    
    async def _generate_answer(self, question: str, context: str, 
                             language: str, include_sources: bool) -> str:
        """Generate answer using the context."""
        
        # Select appropriate prompt template
        if language == "th":
            template_key = "thai"
        elif include_sources:
            template_key = "with_sources"
        else:
            template_key = "default"
        
        prompt = self.prompt_templates[template_key].format(
            context=context,
            question=question
        )
        
        # For now, return a structured response based on context
        # In a production system, this would use an LLM
        return self._create_structured_answer(question, context, language, include_sources)
    
    def _create_structured_answer(self, question: str, context: str, 
                                language: str, include_sources: bool) -> str:
        """Create a structured answer from context (placeholder for LLM)."""
        
        # Simple keyword-based response generation as placeholder
        context_lower = context.lower()
        question_lower = question.lower()
        
        # Extract relevant information from context
        context_parts = context.split('\n\n')
        relevant_parts = []
        
        for part in context_parts:
            if any(word in part.lower() for word in question_lower.split()):
                relevant_parts.append(part)
        
        if relevant_parts:
            if language == "th":
                answer = "ตามข้อมูลที่พบ:\n\n"
                answer += "\n\n".join(relevant_parts[:3])  # Limit to top 3 relevant parts
                answer += "\n\nข้อมูลนี้มาจากแหล่งที่เชื่อถือได้เกี่ยวกับการท่องเที่ยวในประเทศไทย"
            else:
                answer = "Based on the available information:\n\n"
                answer += "\n\n".join(relevant_parts[:3])
                answer += "\n\nThis information comes from reliable Thai tourism sources."
        else:
            if language == "th":
                answer = "ขออธิษฐาน ไม่พบข้อมูลที่เฉพาะเจาะจงสำหรับคำถามของคุณในข้อมูลปัจจุบัน กรุณาลองถามในรูปแบบอื่นหรือติดต่อ Tourism Authority of Thailand สำหรับข้อมูลล่าสุด"
            else:
                answer = "I couldn't find specific information for your question in the current data. Please try rephrasing your question or contact the Tourism Authority of Thailand for the most up-to-date information."
        
        return answer
    
    async def _generate_fallback_answer(self, question: str, language: str) -> Dict[str, Any]:
        """Generate fallback answer when no relevant documents are found."""
        
        # Try to use existing AI system if available
        if self.has_ai_fallback:
            try:
                # Use existing model selector for 3D model suggestions
                model_response = self.model_selector.select_model_with_context(question, {})
                
                # Use emotion analysis for better response
                emotion_result = self.emotion_analyzer.analyze_emotion(question, language)
                
                fallback_answer = self._create_ai_fallback_response(
                    question, model_response, emotion_result, language
                )
                
                return {
                    "answer": fallback_answer,
                    "sources": [],
                    "metadata": {
                        "method": "ai_fallback",
                        "has_model_suggestion": bool(model_response),
                        "emotion_detected": emotion_result.get('primary_emotion') if emotion_result else None,
                        "language": language
                    }
                }
                
            except Exception as e:
                logger.error(f"Error in AI fallback: {e}")
        
        # Simple fallback response
        if language == "th":
            fallback_answer = """ขออภัย ไม่พบข้อมูลที่เกี่ยวข้องในฐานข้อมูลปัจจุบัน

สำหรับข้อมูลการท่องเที่ยวในประเทศไทย แนะนำให้ติดต่อ:
- การท่องเที่ยวแห่งประเทศไทย (TAT): www.tourismthailand.org
- หรือสอบถามข้อมูลเพิ่มเติมผ่านช่องทางอื่น

คุณสามารถลองถามคำถามในรูปแบบอื่นได้"""
        else:
            fallback_answer = """I apologize, but I couldn't find relevant information in the current database.

For Thailand tourism information, I recommend contacting:
- Tourism Authority of Thailand (TAT): www.tourismthailand.org
- Or seeking additional information through other channels

You can try rephrasing your question differently."""
        
        return {
            "answer": fallback_answer,
            "sources": [],
            "metadata": {
                "method": "simple_fallback",
                "language": language
            }
        }
    
    def _create_ai_fallback_response(self, question: str, model_response: Optional[Dict], 
                                   emotion_result: Optional[Dict], language: str) -> str:
        """Create AI-enhanced fallback response."""
        
        response_parts = []
        
        if language == "th":
            response_parts.append("แม้ว่าจะไม่พบข้อมูลที่เฉพาะเจาะจงในฐานข้อมูลปัจจุบัน แต่ฉันสามารถช่วยคุณได้ด้วยวิธีอื่น:")
        else:
            response_parts.append("While I couldn't find specific information in the current database, I can help you in other ways:")
        
        # Add model suggestion if available
        if model_response and model_response.get('selected_model'):
            if language == "th":
                response_parts.append(f"แนะนำให้ดูโมเดล 3D: {model_response['selected_model']}")
            else:
                response_parts.append(f"Suggested 3D model: {model_response['selected_model']}")
        
        # Add emotion-based guidance
        if emotion_result and emotion_result.get('primary_emotion'):
            emotion = emotion_result['primary_emotion']
            if language == "th":
                if emotion in ['excited', 'happy']:
                    response_parts.append("เห็นว่าคุณมีความกระตือรือร้น! การท่องเที่ยวไทยมีกิจกรรมสนุกๆ มากมาย")
                elif emotion in ['worried', 'anxious']:
                    response_parts.append("หากมีความกังวล แนะนำให้ตรวจสอบข้อมูลล่าสุดจากแหล่งราชการ")
            else:
                if emotion in ['excited', 'happy']:
                    response_parts.append("I can see you're excited! Thailand has many amazing activities to offer.")
                elif emotion in ['worried', 'anxious']:
                    response_parts.append("If you have concerns, I recommend checking official sources for the latest information.")
        
        return "\n\n".join(response_parts)
    
    def _extract_sources(self, documents: List[Dict[str, Any]]) -> List[Dict[str, str]]:
        """Extract source information from documents."""
        sources = []
        seen_urls = set()
        
        for doc in documents:
            metadata = doc.get('metadata', {})
            url = metadata.get('url', '')
            source_name = metadata.get('source', 'Unknown Source')
            title = metadata.get('title', '')
            
            if url and url not in seen_urls:
                sources.append({
                    "name": source_name,
                    "title": title,
                    "url": url
                })
                seen_urls.add(url)
        
        return sources
    
    async def update_knowledge_base(self) -> Dict[str, Any]:
        """Update the knowledge base by crawling sources."""
        try:
            start_time = datetime.now()
            
            # Crawl all sources
            logger.info("Starting knowledge base update...")
            documents = await self.crawler.crawl_all_sources()
            
            if documents:
                # Add documents to vector store
                self.vector_store.add_documents(documents)
                
                update_time = (datetime.now() - start_time).total_seconds()
                
                result = {
                    "status": "success",
                    "documents_added": len(documents),
                    "total_documents": self.vector_store.get_document_count(),
                    "update_time_seconds": update_time,
                    "timestamp": datetime.now().isoformat()
                }
                
                logger.info(f"Knowledge base updated: {len(documents)} new documents in {update_time:.2f}s")
                return result
            else:
                return {
                    "status": "no_new_documents",
                    "message": "No new documents were found during crawling",
                    "timestamp": datetime.now().isoformat()
                }
                
        except Exception as e:
            logger.error(f"Error updating knowledge base: {e}")
            return {
                "status": "error",
                "error": str(e),
                "timestamp": datetime.now().isoformat()
            }
    
    def get_system_stats(self) -> Dict[str, Any]:
        """Get comprehensive system statistics."""
        return {
            "vector_store": self.vector_store.get_statistics(),
            "retriever": self.retriever.get_retrieval_stats(),
            "crawler_sources": len(self.crawler.get_sources()),
            "has_ai_fallback": self.has_ai_fallback,
            "supported_languages": ["en", "th"]
        }
    
    def add_data_source(self, source_id: str, config: Dict[str, Any]) -> bool:
        """Add a new data source for crawling."""
        try:
            self.crawler.add_source(source_id, config)
            return True
        except Exception as e:
            logger.error(f"Error adding data source: {e}")
            return False
    
    def remove_data_source(self, source_id: str) -> bool:
        """Remove a data source."""
        return self.crawler.remove_source(source_id)
    
    def get_data_sources(self) -> Dict[str, Any]:
        """Get all configured data sources."""
        return self.crawler.get_sources()