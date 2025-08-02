"""
Smart AI API Routes
Provides intelligent AI assistance with automatic model selection
Integrates OpenThaiGPT with existing PaiNaiDee AI system
"""

from fastapi import APIRouter, HTTPException, WebSocket, WebSocketDisconnect
from pydantic import BaseModel, Field
from typing import List, Optional, Dict, Any
import logging
import asyncio
import json
import time

# Import the AI orchestrator
from ai.orchestrator.ai_orchestrator import get_ai_orchestrator, AIResponse

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Create router
router = APIRouter()

# Request/Response models
class SmartAIRequest(BaseModel):
    """Request model for smart AI endpoint"""
    message: str = Field(..., description="User message/query")
    language: Optional[str] = Field("auto", description="Language preference: 'th', 'en', or 'auto'")
    source: Optional[str] = Field("web", description="Source of request (web, mobile, 3D-assistant, etc.)")
    context: Optional[Dict[str, Any]] = Field(None, description="Additional context information")
    user_profile: Optional[Dict[str, Any]] = Field(None, description="User profile for personalization")

class SmartAIResponse(BaseModel):
    """Response model for smart AI endpoint"""
    content: str = Field(..., description="Generated response content")
    intent_type: str = Field(..., description="Detected intent type")
    language: str = Field(..., description="Detected/used language")
    model_used: str = Field(..., description="AI model that generated the response")
    confidence: float = Field(..., description="Confidence score for intent classification")
    response_time: float = Field(..., description="Response generation time in seconds")
    metadata: Optional[Dict[str, Any]] = Field(None, description="Additional metadata")
    status: str = Field("success", description="Response status")

class ChatHistoryRequest(BaseModel):
    """Request model for multi-turn chat"""
    messages: List[Dict[str, str]] = Field(..., description="Conversation history")
    language: Optional[str] = Field("auto", description="Language preference")
    source: Optional[str] = Field("web", description="Source of request")
    context: Optional[Dict[str, Any]] = Field(None, description="Additional context")

class ModelStatusResponse(BaseModel):
    """Response model for AI system status"""
    status: str = Field(..., description="Overall system status")
    components: Dict[str, Any] = Field(..., description="Status of individual components")
    thai_llm_enabled: bool = Field(..., description="Whether Thai LLM is enabled")
    openai_fallback_enabled: bool = Field(..., description="Whether OpenAI fallback is enabled")
    agents_available: bool = Field(..., description="Whether existing agents are available")

# WebSocket connection manager for streaming
class ConnectionManager:
    def __init__(self):
        self.active_connections: List[WebSocket] = []

    async def connect(self, websocket: WebSocket):
        await websocket.accept()
        self.active_connections.append(websocket)

    def disconnect(self, websocket: WebSocket):
        self.active_connections.remove(websocket)

    async def send_personal_message(self, message: str, websocket: WebSocket):
        await websocket.send_text(message)

manager = ConnectionManager()

@router.post("/ask-smart", response_model=SmartAIResponse)
async def ask_smart_ai(request: SmartAIRequest):
    """
    Smart AI endpoint that automatically selects the best model for the request
    
    This endpoint:
    - Analyzes user intent and language
    - Routes to appropriate AI components (Thai LLM, existing agents, etc.)
    - Provides intelligent responses with fallback handling
    - Supports both Thai and English languages
    """
    try:
        logger.info(f"Smart AI request: {request.message[:100]}... (lang: {request.language}, source: {request.source})")
        
        # Get the AI orchestrator
        orchestrator = get_ai_orchestrator()
        
        # Prepare context with user profile if provided
        context = request.context or {}
        if request.user_profile:
            context["user_profile"] = request.user_profile
        
        # Handle the input through orchestrator
        ai_response: AIResponse = await orchestrator.handle_input(
            user_input=request.message,
            lang=request.language,
            source=request.source,
            context=context
        )
        
        # Convert to API response format
        response = SmartAIResponse(
            content=ai_response.content,
            intent_type=ai_response.intent_type.value,
            language=ai_response.language.value,
            model_used=ai_response.model_used,
            confidence=ai_response.confidence,
            response_time=ai_response.response_time,
            metadata=ai_response.metadata,
            status="success"
        )
        
        logger.info(f"Smart AI response generated: {ai_response.model_used} ({ai_response.response_time:.2f}s)")
        return response
        
    except Exception as e:
        logger.error(f"Error in smart AI endpoint: {str(e)}")
        raise HTTPException(
            status_code=500,
            detail={
                "error": "Internal server error",
                "message": str(e),
                "fallback_response": _get_fallback_response(request.language)
            }
        )

@router.post("/chat-multi-turn", response_model=SmartAIResponse)
async def chat_multi_turn(request: ChatHistoryRequest):
    """
    Multi-turn chat endpoint for conversational AI
    Maintains conversation context and history
    """
    try:
        logger.info(f"Multi-turn chat request with {len(request.messages)} messages")
        
        if not request.messages:
            raise HTTPException(status_code=400, detail="No messages provided")
        
        # Get the last user message
        last_message = request.messages[-1]
        if last_message.get("role") != "user":
            raise HTTPException(status_code=400, detail="Last message must be from user")
        
        # Get the AI orchestrator
        orchestrator = get_ai_orchestrator()
        
        # For multi-turn chat, we can enhance the context with conversation history
        context = request.context or {}
        context["conversation_history"] = request.messages[:-1]  # All but the last message
        
        # Handle the input
        ai_response: AIResponse = await orchestrator.handle_input(
            user_input=last_message["content"],
            lang=request.language,
            source=request.source,
            context=context
        )
        
        # Convert to API response format
        response = SmartAIResponse(
            content=ai_response.content,
            intent_type=ai_response.intent_type.value,
            language=ai_response.language.value,
            model_used=ai_response.model_used,
            confidence=ai_response.confidence,
            response_time=ai_response.response_time,
            metadata=ai_response.metadata,
            status="success"
        )
        
        return response
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error in multi-turn chat: {str(e)}")
        raise HTTPException(
            status_code=500,
            detail={
                "error": "Internal server error",
                "message": str(e)
            }
        )

@router.get("/status", response_model=ModelStatusResponse)
async def get_ai_status():
    """
    Get the status of AI system components
    Returns information about available models and agents
    """
    try:
        orchestrator = get_ai_orchestrator()
        status_info = orchestrator.get_status()
        
        return ModelStatusResponse(
            status="operational",
            components=status_info["components"],
            thai_llm_enabled=status_info["thai_llm_enabled"],
            openai_fallback_enabled=status_info["openai_fallback_enabled"],
            agents_available=status_info["agents_available"]
        )
        
    except Exception as e:
        logger.error(f"Error getting AI status: {str(e)}")
        return ModelStatusResponse(
            status="error",
            components={},
            thai_llm_enabled=False,
            openai_fallback_enabled=False,
            agents_available=False
        )

@router.websocket("/chat-stream")
async def websocket_chat_stream(websocket: WebSocket):
    """
    WebSocket endpoint for streaming chat responses
    Provides real-time AI responses with streaming capability
    """
    await manager.connect(websocket)
    try:
        orchestrator = get_ai_orchestrator()
        
        while True:
            # Receive message from client
            data = await websocket.receive_text()
            
            try:
                # Parse JSON message
                message_data = json.loads(data)
                user_message = message_data.get("message", "")
                language = message_data.get("language", "auto")
                source = message_data.get("source", "websocket")
                
                if not user_message:
                    await manager.send_personal_message(
                        json.dumps({"error": "Empty message"}),
                        websocket
                    )
                    continue
                
                # Send processing status
                await manager.send_personal_message(
                    json.dumps({"status": "processing", "message": "กำลังประมวลผล..."}),
                    websocket
                )
                
                # Get AI response
                ai_response = await orchestrator.handle_input(
                    user_input=user_message,
                    lang=language,
                    source=source
                )
                
                # Send the response
                response_data = {
                    "content": ai_response.content,
                    "intent_type": ai_response.intent_type.value,
                    "language": ai_response.language.value,
                    "model_used": ai_response.model_used,
                    "confidence": ai_response.confidence,
                    "response_time": ai_response.response_time,
                    "status": "success"
                }
                
                await manager.send_personal_message(
                    json.dumps(response_data, ensure_ascii=False),
                    websocket
                )
                
            except json.JSONDecodeError:
                await manager.send_personal_message(
                    json.dumps({"error": "Invalid JSON format"}),
                    websocket
                )
            except Exception as e:
                logger.error(f"Error in WebSocket chat: {str(e)}")
                await manager.send_personal_message(
                    json.dumps({
                        "error": "Processing error",
                        "message": str(e),
                        "fallback": _get_fallback_response("th")
                    }),
                    websocket
                )
                
    except WebSocketDisconnect:
        manager.disconnect(websocket)
        logger.info("WebSocket client disconnected")
    except Exception as e:
        logger.error(f"WebSocket error: {str(e)}")
        manager.disconnect(websocket)

@router.post("/test-models")
async def test_ai_models():
    """
    Test endpoint to verify all AI models are working
    Useful for debugging and health checks
    """
    try:
        orchestrator = get_ai_orchestrator()
        
        test_results = {}
        
        # Test Thai LLM
        try:
            thai_llm = orchestrator._get_thai_llm()
            thai_response = await thai_llm.chat("สวัสดี", "greeting")
            test_results["thai_llm"] = {
                "status": "working",
                "response": thai_response[:100] + "..." if len(thai_response) > 100 else thai_response
            }
        except Exception as e:
            test_results["thai_llm"] = {
                "status": "error",
                "error": str(e)
            }
        
        # Test OpenAI fallback
        try:
            openai_llm = orchestrator._get_openai_llm()
            openai_response = await openai_llm.chat("Hello", "greeting")
            test_results["openai_fallback"] = {
                "status": "working",
                "response": openai_response[:100] + "..." if len(openai_response) > 100 else openai_response
            }
        except Exception as e:
            test_results["openai_fallback"] = {
                "status": "error",
                "error": str(e)
            }
        
        # Test orchestrator
        try:
            test_response = await orchestrator.handle_input("Test message", "en", "test")
            test_results["orchestrator"] = {
                "status": "working",
                "intent": test_response.intent_type.value,
                "model_used": test_response.model_used
            }
        except Exception as e:
            test_results["orchestrator"] = {
                "status": "error",
                "error": str(e)
            }
        
        return {
            "test_results": test_results,
            "timestamp": time.time(),
            "overall_status": "working" if all(
                result.get("status") == "working" 
                for result in test_results.values()
            ) else "partial"
        }
        
    except Exception as e:
        logger.error(f"Error in model testing: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))

def _get_fallback_response(language: str) -> str:
    """Get fallback response when all else fails"""
    if language == "th":
        return "ขออภัยครับ ระบบขัดข้องชั่วคราว กรุณาลองใหม่อีกครั้งครับ"
    else:
        return "Sorry, the system is temporarily unavailable. Please try again later."

# Helper function to get router for main app
def create_smart_ai_routes() -> APIRouter:
    """Create and return the smart AI router"""
    return router