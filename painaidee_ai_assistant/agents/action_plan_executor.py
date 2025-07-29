"""
Action Plan Executor - Coordinates execution of multimodal action plans
Handles timing, synchronization, and output generation for the 3D assistant
"""

import logging
import asyncio
from typing import Dict, List, Optional, Any, Callable
from datetime import datetime, timedelta
import json
from dataclasses import asdict

from .action_plan_system import (
    ActionPlan, SpeechAction, GestureAction, 
    SceneInteractionAction, UIComponentAction,
    ActionType
)

logger = logging.getLogger(__name__)

class ExecutionResult:
    """Result of action plan execution"""
    
    def __init__(self, plan: ActionPlan):
        self.plan = plan
        self.started_at = datetime.now()
        self.completed_at = None
        self.status = "executing"
        self.results = {}
        self.errors = []
    
    def mark_completed(self):
        """Mark execution as completed"""
        self.completed_at = datetime.now()
        self.status = "completed"
    
    def mark_failed(self, error: str):
        """Mark execution as failed"""
        self.completed_at = datetime.now()
        self.status = "failed"
        self.errors.append(error)
    
    def add_result(self, action_type: str, result: Dict[str, Any]):
        """Add result from specific action type"""
        if action_type not in self.results:
            self.results[action_type] = []
        self.results[action_type].append(result)
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for API responses"""
        return {
            "intent": self.plan.intent,
            "status": self.status,
            "started_at": self.started_at.isoformat(),
            "completed_at": self.completed_at.isoformat() if self.completed_at else None,
            "execution_time_ms": (
                (self.completed_at - self.started_at).total_seconds() * 1000
                if self.completed_at else None
            ),
            "results": self.results,
            "errors": self.errors
        }

class ActionExecutor:
    """Executes individual actions and manages their outputs"""
    
    def __init__(self):
        self.speech_outputs = []
        self.gesture_outputs = []
        self.scene_outputs = []
        self.ui_outputs = []
    
    async def execute_speech_action(self, action: SpeechAction) -> Dict[str, Any]:
        """Execute a speech action"""
        try:
            # Generate speech output data
            speech_output = {
                "type": "speech",
                "text": action.text,
                "language": action.language,
                "style": action.style.value,
                "duration_ms": action.duration_ms or self._estimate_speech_duration(action.text),
                "voice_params": action.voice_params,
                "audio_url": self._generate_audio_url(action),
                "timestamp": datetime.now().isoformat()
            }
            
            self.speech_outputs.append(speech_output)
            logger.info(f"Executed speech action: {action.text[:50]}...")
            
            return speech_output
            
        except Exception as e:
            logger.error(f"Failed to execute speech action: {e}")
            raise
    
    async def execute_gesture_action(self, action: GestureAction) -> Dict[str, Any]:
        """Execute a gesture action"""
        try:
            # Generate gesture animation data
            gesture_output = {
                "type": "gesture",
                "animation": action.animation.value,
                "model_name": action.model_name,
                "duration_ms": action.duration_ms,
                "intensity": action.intensity,
                "loop": action.loop,
                "facial_expression": action.facial_expression,
                "animation_params": {
                    "start_time": 0,
                    "end_time": action.duration_ms,
                    "easing": "ease-in-out",
                    "blend_weight": action.intensity
                },
                "timestamp": datetime.now().isoformat()
            }
            
            self.gesture_outputs.append(gesture_output)
            logger.info(f"Executed gesture action: {action.animation.value} on {action.model_name}")
            
            return gesture_output
            
        except Exception as e:
            logger.error(f"Failed to execute gesture action: {e}")
            raise
    
    async def execute_scene_action(self, action: SceneInteractionAction) -> Dict[str, Any]:
        """Execute a scene interaction action"""
        try:
            # Generate scene interaction data
            scene_output = {
                "type": "scene_interaction",
                "interaction_type": action.interaction_type.value,
                "target": action.target,
                "duration_ms": action.duration_ms,
                "parameters": action.parameters,
                "camera_commands": self._generate_camera_commands(action),
                "scene_updates": self._generate_scene_updates(action),
                "timestamp": datetime.now().isoformat()
            }
            
            self.scene_outputs.append(scene_output)
            logger.info(f"Executed scene action: {action.interaction_type.value} targeting {action.target}")
            
            return scene_output
            
        except Exception as e:
            logger.error(f"Failed to execute scene action: {e}")
            raise
    
    async def execute_ui_action(self, action: UIComponentAction) -> Dict[str, Any]:
        """Execute a UI component action"""
        try:
            # Generate UI component data
            ui_output = {
                "type": "ui_component",
                "component_type": action.component_type.value,
                "content": action.content,
                "position": action.position,
                "duration_ms": action.duration_ms,
                "interaction_enabled": action.interaction_enabled,
                "element_id": f"ui_{action.component_type.value}_{datetime.now().timestamp()}",
                "css_classes": self._generate_css_classes(action),
                "event_handlers": self._generate_event_handlers(action),
                "timestamp": datetime.now().isoformat()
            }
            
            self.ui_outputs.append(ui_output)
            logger.info(f"Executed UI action: {action.component_type.value} at {action.position}")
            
            return ui_output
            
        except Exception as e:
            logger.error(f"Failed to execute UI action: {e}")
            raise
    
    def _estimate_speech_duration(self, text: str) -> int:
        """Estimate speech duration in milliseconds"""
        # Rough estimation: 150 words per minute for Thai
        word_count = len(text.split())
        duration_seconds = (word_count / 150) * 60
        return int(duration_seconds * 1000)
    
    def _generate_audio_url(self, action: SpeechAction) -> str:
        """Generate audio URL for speech action (placeholder)"""
        # In a real implementation, this would generate TTS audio
        return f"/audio/tts?text={action.text}&lang={action.language}&style={action.style.value}"
    
    def _generate_camera_commands(self, action: SceneInteractionAction) -> List[Dict[str, Any]]:
        """Generate camera commands for scene interactions"""
        commands = []
        
        if action.interaction_type.value == "camera_move":
            commands.append({
                "command": "move_to",
                "target": action.target,
                "duration": action.duration_ms,
                "easing": action.parameters.get("easing", "ease-in-out")
            })
        
        elif action.interaction_type.value == "zoom_to_location":
            commands.append({
                "command": "zoom_to",
                "coordinates": action.target,
                "zoom_level": action.parameters.get("zoom_level", 15),
                "duration": action.duration_ms
            })
        
        elif action.interaction_type.value == "focus_object":
            commands.append({
                "command": "focus_on",
                "object_id": action.target,
                "duration": action.duration_ms,
                "offset": action.parameters.get("camera_offset", [0, 2, 5])
            })
        
        return commands
    
    def _generate_scene_updates(self, action: SceneInteractionAction) -> List[Dict[str, Any]]:
        """Generate scene updates for interactions"""
        updates = []
        
        if action.interaction_type.value == "map_pin_highlight":
            updates.append({
                "object_type": "map_pin",
                "object_id": action.target,
                "highlight": True,
                "color": action.parameters.get("highlight_color", "#FF6B35"),
                "pulse": action.parameters.get("pulse", True),
                "duration": action.duration_ms
            })
        
        elif action.interaction_type.value == "rotate_view":
            updates.append({
                "object_type": "camera",
                "rotation": action.parameters.get("rotation", [0, 45, 0]),
                "duration": action.duration_ms
            })
        
        return updates
    
    def _generate_css_classes(self, action: UIComponentAction) -> List[str]:
        """Generate CSS classes for UI components"""
        classes = [f"action-{action.component_type.value}"]
        
        if action.position:
            classes.append(f"position-{action.position}")
        
        if action.interaction_enabled:
            classes.append("interactive")
        
        return classes
    
    def _generate_event_handlers(self, action: UIComponentAction) -> Dict[str, str]:
        """Generate event handlers for UI components"""
        handlers = {}
        
        if action.component_type.value == "button" and "buttons" in action.content:
            for button in action.content["buttons"]:
                if "action" in button:
                    handlers[f"click_{button['action']}"] = f"handleAction('{button['action']}')"
        
        if action.interaction_enabled:
            handlers["click"] = "handleComponentClick(event)"
            handlers["hover"] = "handleComponentHover(event)"
        
        return handlers

class ActionPlanExecutor:
    """Main executor for coordinating multimodal action plans"""
    
    def __init__(self):
        self.action_executor = ActionExecutor()
        self.active_executions = {}
        self.execution_history = []
    
    async def execute_plan(self, plan: ActionPlan, execution_id: Optional[str] = None) -> ExecutionResult:
        """Execute a complete action plan with proper timing and coordination"""
        
        if not execution_id:
            execution_id = f"exec_{datetime.now().timestamp()}"
        
        result = ExecutionResult(plan)
        self.active_executions[execution_id] = result
        
        try:
            logger.info(f"Starting execution of action plan for intent: {plan.intent}")
            
            # Execute actions according to the specified order
            for action_type in plan.execution_order:
                await self._execute_action_group(plan, action_type, result)
            
            result.mark_completed()
            logger.info(f"Completed execution of action plan for intent: {plan.intent}")
            
        except Exception as e:
            error_msg = f"Failed to execute action plan: {e}"
            logger.error(error_msg)
            result.mark_failed(error_msg)
        
        finally:
            self.execution_history.append(result)
            if execution_id in self.active_executions:
                del self.active_executions[execution_id]
        
        return result
    
    async def _execute_action_group(self, plan: ActionPlan, action_type: str, result: ExecutionResult):
        """Execute all actions of a specific type"""
        
        if action_type == "speech":
            tasks = [
                self.action_executor.execute_speech_action(action)
                for action in plan.speech_actions
            ]
        elif action_type == "gesture":
            tasks = [
                self.action_executor.execute_gesture_action(action)
                for action in plan.gesture_actions
            ]
        elif action_type == "scene":
            tasks = [
                self.action_executor.execute_scene_action(action)
                for action in plan.scene_actions
            ]
        elif action_type == "ui":
            tasks = [
                self.action_executor.execute_ui_action(action)
                for action in plan.ui_actions
            ]
        else:
            logger.warning(f"Unknown action type: {action_type}")
            return
        
        if tasks:
            # Execute all actions of this type concurrently
            action_results = await asyncio.gather(*tasks, return_exceptions=True)
            
            for action_result in action_results:
                if isinstance(action_result, Exception):
                    error_msg = f"Action execution failed: {action_result}"
                    result.errors.append(error_msg)
                    logger.error(error_msg)
                else:
                    result.add_result(action_type, action_result)
    
    def get_execution_status(self, execution_id: str) -> Optional[Dict[str, Any]]:
        """Get status of an active execution"""
        if execution_id in self.active_executions:
            return self.active_executions[execution_id].to_dict()
        return None
    
    def get_all_outputs(self) -> Dict[str, List[Dict[str, Any]]]:
        """Get all generated outputs for frontend consumption"""
        return {
            "speech": self.action_executor.speech_outputs,
            "gesture": self.action_executor.gesture_outputs,
            "scene": self.action_executor.scene_outputs,
            "ui": self.action_executor.ui_outputs
        }
    
    def clear_outputs(self):
        """Clear all accumulated outputs"""
        self.action_executor.speech_outputs.clear()
        self.action_executor.gesture_outputs.clear()
        self.action_executor.scene_outputs.clear()
        self.action_executor.ui_outputs.clear()
    
    def get_execution_history(self, limit: int = 10) -> List[Dict[str, Any]]:
        """Get recent execution history"""
        return [result.to_dict() for result in self.execution_history[-limit:]]

# Global executor instance
action_plan_executor = ActionPlanExecutor()