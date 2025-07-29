"""
Action Plan API Routes
Provides endpoints for generating and executing multimodal action plans
"""

from fastapi import APIRouter, HTTPException, BackgroundTasks
from pydantic import BaseModel
from typing import List, Optional, Dict, Any
import logging

from agents.action_plan_system import intent_mapper, action_registry
from agents.action_plan_executor import action_plan_executor

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Create router
router = APIRouter()

# Request/Response models
class ActionPlanRequest(BaseModel):
    intent: str
    parameters: Optional[Dict[str, Any]] = {}
    confidence: Optional[float] = 1.0
    user_context: Optional[Dict[str, Any]] = {}

class QuickActionRequest(BaseModel):
    user_input: str
    language: Optional[str] = "th"
    context: Optional[Dict[str, Any]] = {}

class ActionPlanResponse(BaseModel):
    intent: str
    confidence: float
    speech_actions: List[Dict[str, Any]]
    gesture_actions: List[Dict[str, Any]]
    scene_actions: List[Dict[str, Any]]
    ui_actions: List[Dict[str, Any]]
    execution_order: List[str]
    estimated_duration_ms: int
    metadata: Dict[str, Any]

class ExecutionRequest(BaseModel):
    plan: ActionPlanRequest
    execution_mode: Optional[str] = "immediate"  # immediate, scheduled, preview

class ExecutionResponse(BaseModel):
    execution_id: str
    status: str
    started_at: str
    outputs: Dict[str, List[Dict[str, Any]]]
    estimated_completion: Optional[str] = None

class IntentRegistrationRequest(BaseModel):
    intent: str
    mapping: Dict[str, Any]
    description: Optional[str] = ""

class TemplateRegistrationRequest(BaseModel):
    category: str  # speech, gesture, scene, ui, composite
    name: str
    template: Dict[str, Any]
    description: Optional[str] = ""

@router.post("/generate_plan", response_model=ActionPlanResponse)
async def generate_action_plan(request: ActionPlanRequest):
    """
    Generate a multimodal action plan for the given intent
    """
    try:
        logger.info(f"Generating action plan for intent: {request.intent}")
        
        # Generate action plan using the intent mapper
        plan = intent_mapper.get_action_plan(
            intent=request.intent,
            parameters=request.parameters,
            confidence=request.confidence
        )
        
        # Calculate estimated duration
        estimated_duration = _calculate_plan_duration(plan)
        
        # Convert to response format
        response = ActionPlanResponse(
            intent=plan.intent,
            confidence=plan.confidence,
            speech_actions=[_speech_action_to_dict(action) for action in plan.speech_actions],
            gesture_actions=[_gesture_action_to_dict(action) for action in plan.gesture_actions],
            scene_actions=[_scene_action_to_dict(action) for action in plan.scene_actions],
            ui_actions=[_ui_action_to_dict(action) for action in plan.ui_actions],
            execution_order=plan.execution_order,
            estimated_duration_ms=estimated_duration,
            metadata=plan.metadata
        )
        
        logger.info(f"Generated action plan with {len(plan.speech_actions)} speech, "
                   f"{len(plan.gesture_actions)} gesture, {len(plan.scene_actions)} scene, "
                   f"and {len(plan.ui_actions)} UI actions")
        
        return response
        
    except Exception as e:
        logger.error(f"Error generating action plan: {str(e)}")
        raise HTTPException(
            status_code=500,
            detail=f"Failed to generate action plan: {str(e)}"
        )

@router.post("/quick_action", response_model=ActionPlanResponse)
async def quick_action_plan(request: QuickActionRequest):
    """
    Generate and preview an action plan from natural language input
    Uses intent recognition to map user input to actions
    """
    try:
        logger.info(f"Processing quick action for input: {request.user_input[:50]}...")
        
        # Simple intent recognition (can be enhanced with ML models)
        recognized_intent = _recognize_intent_from_text(request.user_input, request.language)
        
        # Extract parameters from user input
        extracted_params = _extract_parameters_from_text(request.user_input, recognized_intent)
        
        # Merge with provided context
        merged_params = {**extracted_params, **request.context}
        
        # Generate action plan
        plan = intent_mapper.get_action_plan(
            intent=recognized_intent["intent"],
            parameters=merged_params,
            confidence=recognized_intent["confidence"]
        )
        
        # Calculate estimated duration
        estimated_duration = _calculate_plan_duration(plan)
        
        response = ActionPlanResponse(
            intent=plan.intent,
            confidence=plan.confidence,
            speech_actions=[_speech_action_to_dict(action) for action in plan.speech_actions],
            gesture_actions=[_gesture_action_to_dict(action) for action in plan.gesture_actions],
            scene_actions=[_scene_action_to_dict(action) for action in plan.scene_actions],
            ui_actions=[_ui_action_to_dict(action) for action in plan.ui_actions],
            execution_order=plan.execution_order,
            estimated_duration_ms=estimated_duration,
            metadata={
                **plan.metadata,
                "recognized_from": request.user_input,
                "recognition_confidence": recognized_intent["confidence"]
            }
        )
        
        return response
        
    except Exception as e:
        logger.error(f"Error processing quick action: {str(e)}")
        raise HTTPException(
            status_code=500,
            detail=f"Failed to process quick action: {str(e)}"
        )

@router.post("/execute_plan", response_model=ExecutionResponse)
async def execute_action_plan(request: ExecutionRequest, background_tasks: BackgroundTasks):
    """
    Execute a multimodal action plan
    """
    try:
        logger.info(f"Executing action plan for intent: {request.plan.intent}")
        
        # Generate the action plan
        plan = intent_mapper.get_action_plan(
            intent=request.plan.intent,
            parameters=request.plan.parameters,
            confidence=request.plan.confidence
        )
        
        if request.execution_mode == "preview":
            # Return preview without execution
            return ExecutionResponse(
                execution_id="preview",
                status="preview",
                started_at="",
                outputs={
                    "speech": [_speech_action_to_dict(action) for action in plan.speech_actions],
                    "gesture": [_gesture_action_to_dict(action) for action in plan.gesture_actions],
                    "scene": [_scene_action_to_dict(action) for action in plan.scene_actions],
                    "ui": [_ui_action_to_dict(action) for action in plan.ui_actions]
                }
            )
        
        # Execute the plan
        execution_result = await action_plan_executor.execute_plan(plan)
        
        return ExecutionResponse(
            execution_id=f"exec_{execution_result.started_at.timestamp()}",
            status=execution_result.status,
            started_at=execution_result.started_at.isoformat(),
            outputs=execution_result.results
        )
        
    except Exception as e:
        logger.error(f"Error executing action plan: {str(e)}")
        raise HTTPException(
            status_code=500,
            detail=f"Failed to execute action plan: {str(e)}"
        )

@router.get("/execution_status/{execution_id}")
async def get_execution_status(execution_id: str):
    """
    Get the status of an active execution
    """
    try:
        status = action_plan_executor.get_execution_status(execution_id)
        
        if status is None:
            raise HTTPException(
                status_code=404,
                detail=f"Execution {execution_id} not found"
            )
        
        return status
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error getting execution status: {str(e)}")
        raise HTTPException(
            status_code=500,
            detail=f"Failed to get execution status: {str(e)}"
        )

@router.get("/outputs")
async def get_all_outputs():
    """
    Get all generated outputs from recent executions
    """
    try:
        outputs = action_plan_executor.get_all_outputs()
        return {
            "outputs": outputs,
            "total_items": sum(len(output_list) for output_list in outputs.values()),
            "categories": list(outputs.keys())
        }
        
    except Exception as e:
        logger.error(f"Error getting outputs: {str(e)}")
        raise HTTPException(
            status_code=500,
            detail=f"Failed to get outputs: {str(e)}"
        )

@router.delete("/outputs")
async def clear_outputs():
    """
    Clear all accumulated outputs
    """
    try:
        action_plan_executor.clear_outputs()
        return {"message": "All outputs cleared successfully"}
        
    except Exception as e:
        logger.error(f"Error clearing outputs: {str(e)}")
        raise HTTPException(
            status_code=500,
            detail=f"Failed to clear outputs: {str(e)}"
        )

@router.get("/execution_history")
async def get_execution_history(limit: int = 10):
    """
    Get recent execution history
    """
    try:
        history = action_plan_executor.get_execution_history(limit)
        return {
            "history": history,
            "total_items": len(history)
        }
        
    except Exception as e:
        logger.error(f"Error getting execution history: {str(e)}")
        raise HTTPException(
            status_code=500,
            detail=f"Failed to get execution history: {str(e)}"
        )

@router.post("/register_intent")
async def register_intent_mapping(request: IntentRegistrationRequest):
    """
    Register a new intent mapping
    """
    try:
        intent_mapper.register_intent_mapping(request.intent, request.mapping)
        return {
            "message": f"Intent '{request.intent}' registered successfully",
            "intent": request.intent,
            "description": request.description
        }
        
    except Exception as e:
        logger.error(f"Error registering intent: {str(e)}")
        raise HTTPException(
            status_code=500,
            detail=f"Failed to register intent: {str(e)}"
        )

@router.post("/register_template")
async def register_action_template(request: TemplateRegistrationRequest):
    """
    Register a new action template
    """
    try:
        # Convert template dict to appropriate object (simplified here)
        action_registry.register_template(request.category, request.name, request.template)
        
        return {
            "message": f"Template '{request.name}' registered in category '{request.category}'",
            "category": request.category,
            "name": request.name,
            "description": request.description
        }
        
    except Exception as e:
        logger.error(f"Error registering template: {str(e)}")
        raise HTTPException(
            status_code=500,
            detail=f"Failed to register template: {str(e)}"
        )

@router.get("/available_intents")
async def get_available_intents():
    """
    Get list of available intents and their descriptions
    """
    try:
        # Get intents from the mapper (simplified access)
        intents = {
            "suggest_place": {
                "description": "Suggest a tourist place with full multimodal presentation",
                "parameters": ["place_name", "coordinates", "photo_url"],
                "actions": ["speech", "gesture", "scene", "ui"]
            },
            "suggest_cultural_place": {
                "description": "Suggest a cultural place like museum with information display",
                "parameters": ["cultural_type", "coordinates", "photo_url"],
                "actions": ["speech", "gesture", "scene", "ui"]
            },
            "greet_user": {
                "description": "Welcome greeting with friendly gesture",
                "parameters": [],
                "actions": ["speech", "gesture"]
            },
            "confirm_action": {
                "description": "Confirm user action with acknowledgment",
                "parameters": [],
                "actions": ["speech", "gesture"]
            }
        }
        
        return {
            "intents": intents,
            "total_count": len(intents)
        }
        
    except Exception as e:
        logger.error(f"Error getting available intents: {str(e)}")
        raise HTTPException(
            status_code=500,
            detail=f"Failed to get available intents: {str(e)}"
        )

@router.get("/health")
async def action_plan_health():
    """Health check for action plan service"""
    try:
        return {
            "service": "action_plan_system",
            "status": "healthy",
            "components": {
                "intent_mapper": "available",
                "action_registry": "available",
                "action_executor": "available"
            },
            "active_executions": len(action_plan_executor.active_executions),
            "execution_history_count": len(action_plan_executor.execution_history)
        }
        
    except Exception as e:
        return {
            "service": "action_plan_system",
            "status": "error",
            "error": str(e)
        }

# Helper functions
def _calculate_plan_duration(plan) -> int:
    """Calculate estimated total duration for the action plan"""
    total_duration = 0
    
    # Get maximum duration from each action type (since they run concurrently within type)
    if plan.speech_actions:
        max_speech = max((action.duration_ms or 3000) for action in plan.speech_actions)
        total_duration += max_speech
    
    if plan.gesture_actions:
        max_gesture = max(action.duration_ms for action in plan.gesture_actions)
        total_duration = max(total_duration, max_gesture)  # Overlap with speech
    
    if plan.scene_actions:
        max_scene = max(action.duration_ms for action in plan.scene_actions)
        total_duration += max_scene
    
    # UI actions are typically instant
    return total_duration

def _speech_action_to_dict(action) -> Dict[str, Any]:
    """Convert SpeechAction to dictionary"""
    return {
        "text": action.text,
        "language": action.language,
        "style": action.style.value,
        "duration_ms": action.duration_ms,
        "voice_params": action.voice_params
    }

def _gesture_action_to_dict(action) -> Dict[str, Any]:
    """Convert GestureAction to dictionary"""
    return {
        "animation": action.animation.value,
        "model_name": action.model_name,
        "duration_ms": action.duration_ms,
        "intensity": action.intensity,
        "loop": action.loop,
        "facial_expression": action.facial_expression
    }

def _scene_action_to_dict(action) -> Dict[str, Any]:
    """Convert SceneInteractionAction to dictionary"""
    return {
        "interaction_type": action.interaction_type.value,
        "target": action.target,
        "duration_ms": action.duration_ms,
        "parameters": action.parameters
    }

def _ui_action_to_dict(action) -> Dict[str, Any]:
    """Convert UIComponentAction to dictionary"""
    return {
        "component_type": action.component_type.value,
        "content": action.content,
        "position": action.position,
        "duration_ms": action.duration_ms,
        "interaction_enabled": action.interaction_enabled
    }

def _recognize_intent_from_text(text: str, language: str) -> Dict[str, Any]:
    """Simple intent recognition from text (can be enhanced with ML)"""
    text_lower = text.lower()
    
    # Simple keyword-based intent recognition
    if any(word in text_lower for word in ["แนะนำ", "suggest", "ไป", "go", "สถานที่", "place"]):
        if any(word in text_lower for word in ["วัฒนธรรม", "cultural", "พิพิธภัณฑ์", "museum"]):
            return {"intent": "suggest_cultural_place", "confidence": 0.8}
        else:
            return {"intent": "suggest_place", "confidence": 0.7}
    
    elif any(word in text_lower for word in ["สวัสดี", "hello", "hi", "ยินดี", "welcome"]):
        return {"intent": "greet_user", "confidence": 0.9}
    
    elif any(word in text_lower for word in ["ตกลง", "ok", "เข้าใจ", "confirm", "yes"]):
        return {"intent": "confirm_action", "confidence": 0.8}
    
    else:
        return {"intent": "suggest_place", "confidence": 0.3}  # Default fallback

def _extract_parameters_from_text(text: str, intent_info: Dict[str, Any]) -> Dict[str, Any]:
    """Extract parameters from user input text"""
    params = {}
    
    # Simple parameter extraction (can be enhanced with NER)
    if intent_info["intent"] in ["suggest_place", "suggest_cultural_place"]:
        # Try to extract place names (this is very basic)
        words = text.split()
        for i, word in enumerate(words):
            if word in ["ไป", "go", "to"] and i + 1 < len(words):
                params["place_name"] = words[i + 1]
                break
    
    return params