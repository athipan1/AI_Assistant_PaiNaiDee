"""
Modular Action Plan System for Multimodal 3D Assistant
Converts parsed NLP intents into coordinated multimodal action plans
"""

import logging
from typing import Dict, List, Optional, Any, Union
from dataclasses import dataclass, field
from enum import Enum
import asyncio
from abc import ABC, abstractmethod

logger = logging.getLogger(__name__)

class ActionType(Enum):
    """Types of actions in the multimodal system"""
    SPEECH = "speech"
    GESTURE = "gesture"  
    SCENE_INTERACTION = "scene_interaction"
    UI_COMPONENT = "ui_component"

class SpeechStyle(Enum):
    """Speech output styles"""
    FORMAL = "formal"
    FRIENDLY = "friendly"
    ENTHUSIASTIC = "enthusiastic"
    CALM = "calm"
    INFORMATIVE = "informative"

class GestureAnimation(Enum):
    """Available gesture animations for 3D models"""
    NOD = "nod"
    POINT = "point"
    WAVE = "wave"
    NOD_AND_POINT = "nod_and_point"
    WELCOME_GESTURE = "welcome_gesture"
    THINKING_POSE = "thinking_pose"
    EXCITED_GESTURE = "excited_gesture"
    REASSURING_NOD = "reassuring_nod"
    # Enhanced animations from problem statement
    POINT_RIGHT_THEN_SMILE = "point_right_then_smile"
    POINT_MAP_LEFT = "point_map_left"
    EXCITED_JUMP = "excited_jump"
    INVITE_FORWARD = "invite_forward"
    POINT_UPWARD = "point_upward"
    SMILE_AND_WAVE = "smile_and_wave"

class SceneInteractionType(Enum):
    """Types of 3D scene interactions"""
    CAMERA_MOVE = "camera_move"
    FOCUS_OBJECT = "focus_object"
    MAP_PIN_HIGHLIGHT = "map_pin_highlight"
    ZOOM_TO_LOCATION = "zoom_to_location"
    ROTATE_VIEW = "rotate_view"

class UIComponentType(Enum):
    """Types of UI components to display"""
    PHOTO = "photo"
    BUTTON = "button"
    INFO_PANEL = "info_panel"
    MAP_OVERLAY = "map_overlay"
    RATING_DISPLAY = "rating_display"
    # Enhanced UI components from problem statement
    SHOW_LOCATION_POPUP = "show_location_popup"
    MAP_PIN_MARKER = "map_pin_marker"
    REVIEW_PANEL = "review_panel"
    ROUTE_PANEL = "route_panel"
    IMAGE_GALLERY = "image_gallery"
    BILLBOARD = "billboard"

@dataclass
class SpeechAction:
    """Speech output action"""
    text: str
    language: str = "th"  # Thai by default
    style: SpeechStyle = SpeechStyle.FRIENDLY
    duration_ms: Optional[int] = None
    voice_params: Dict[str, Any] = field(default_factory=dict)

@dataclass
class GestureAction:
    """Gesture animation action"""
    animation: GestureAnimation
    model_name: str = "Man_Rig.fbx"
    duration_ms: int = 2000
    intensity: float = 1.0  # 0.0 to 1.0
    loop: bool = False
    facial_expression: str = "neutral"

@dataclass
class SceneInteractionAction:
    """3D scene interaction action"""
    interaction_type: SceneInteractionType
    target: str  # Object, location, or coordinate
    duration_ms: int = 3000
    parameters: Dict[str, Any] = field(default_factory=dict)
    
@dataclass
class UIComponentAction:
    """UI component display action"""
    component_type: UIComponentType
    content: Dict[str, Any]  # Component-specific content
    position: str = "overlay"  # overlay, sidebar, fullscreen
    duration_ms: Optional[int] = None  # None means persistent
    interaction_enabled: bool = True

@dataclass
class ActionPlan:
    """Complete multimodal action plan"""
    intent: str
    confidence: float
    speech_actions: List[SpeechAction] = field(default_factory=list)
    gesture_actions: List[GestureAction] = field(default_factory=list)
    scene_actions: List[SceneInteractionAction] = field(default_factory=list)
    ui_actions: List[UIComponentAction] = field(default_factory=list)
    metadata: Dict[str, Any] = field(default_factory=dict)
    execution_order: List[str] = field(default_factory=list)  # Order of action types
    
class ActionRegistry:
    """Registry for reusable action templates"""
    
    def __init__(self):
        self._speech_templates = {}
        self._gesture_templates = {}
        self._scene_templates = {}
        self._ui_templates = {}
        self._composite_templates = {}
        self._initialize_default_templates()
    
    def _initialize_default_templates(self):
        """Initialize default action templates"""
        
        # Speech templates
        self._speech_templates.update({
            "greeting": SpeechAction(
                text="สวัสดีครับ ยินดีต้อนรับ",
                style=SpeechStyle.FRIENDLY
            ),
            "suggest_place": SpeechAction(
                text="ลองไป{place_name}ดูไหมครับ?",
                style=SpeechStyle.ENTHUSIASTIC
            ),
            "cultural_suggestion": SpeechAction(
                text="ลองไปพิพิธภัณฑ์พื้นบ้านดูไหมครับ?",
                style=SpeechStyle.INFORMATIVE
            ),
            "confirmation": SpeechAction(
                text="เข้าใจแล้วครับ",
                style=SpeechStyle.CALM
            ),
            # Enhanced speech templates from problem statement
            "phu_chi_fa_suggest": SpeechAction(
                text="ลองไปภูชี้ฟ้าดูไหมครับ?",
                style=SpeechStyle.ENTHUSIASTIC,
                duration_ms=3000
            ),
            "weather_nature_suggest": SpeechAction(
                text="อากาศแบบนี้ เหมาะไปป่ามาก",
                style=SpeechStyle.ENTHUSIASTIC
            ),
            "excited_expression": SpeechAction(
                text="ดีใจจัง",
                style=SpeechStyle.ENTHUSIASTIC
            )
        })
        
        # Gesture templates
        self._gesture_templates.update({
            "friendly_nod": GestureAction(
                animation=GestureAnimation.NOD,
                facial_expression="smile",
                duration_ms=1500
            ),
            "pointing_gesture": GestureAction(
                animation=GestureAnimation.POINT,
                facial_expression="focused",
                duration_ms=2000
            ),
            "welcoming_wave": GestureAction(
                animation=GestureAnimation.WAVE,
                facial_expression="happy",
                duration_ms=2500
            ),
            "suggest_nod_point": GestureAction(
                animation=GestureAnimation.NOD_AND_POINT,
                facial_expression="encouraging",
                duration_ms=3000
            ),
            # Enhanced gesture templates from problem statement
            "point_right_then_smile": GestureAction(
                animation=GestureAnimation.POINT_RIGHT_THEN_SMILE,
                facial_expression="friendly",
                duration_ms=3500
            ),
            "thinking_pose": GestureAction(
                animation=GestureAnimation.THINKING_POSE,
                facial_expression="contemplative",
                duration_ms=2500
            ),
            "point_map_left": GestureAction(
                animation=GestureAnimation.POINT_MAP_LEFT,
                facial_expression="informative",
                duration_ms=2500
            ),
            "excited_jump": GestureAction(
                animation=GestureAnimation.EXCITED_JUMP,
                facial_expression="excited",
                duration_ms=2000
            ),
            "invite_forward": GestureAction(
                animation=GestureAnimation.INVITE_FORWARD,
                facial_expression="welcoming",
                duration_ms=2500
            ),
            "smile_and_wave": GestureAction(
                animation=GestureAnimation.SMILE_AND_WAVE,
                facial_expression="joyful",
                duration_ms=3000
            )
        })
        
        # Scene interaction templates
        self._scene_templates.update({
            "focus_map_pin": SceneInteractionAction(
                interaction_type=SceneInteractionType.MAP_PIN_HIGHLIGHT,
                target="location_pin",
                duration_ms=2000,
                parameters={"highlight_color": "#FF6B35", "pulse": True}
            ),
            "zoom_to_location": SceneInteractionAction(
                interaction_type=SceneInteractionType.ZOOM_TO_LOCATION,
                target="coordinates",
                duration_ms=3000,
                parameters={"zoom_level": 15, "smooth_transition": True}
            ),
            "camera_follow": SceneInteractionAction(
                interaction_type=SceneInteractionType.CAMERA_MOVE,
                target="follow_target",
                duration_ms=2000,
                parameters={"follow_smooth": True}
            )
        })
        
        # UI component templates
        self._ui_templates.update({
            "place_photo": UIComponentAction(
                component_type=UIComponentType.PHOTO,
                content={"src": "placeholder.jpg", "alt": "สถานที่ท่องเที่ยว"},
                position="overlay"
            ),
            "action_buttons": UIComponentAction(
                component_type=UIComponentType.BUTTON,
                content={
                    "buttons": [
                        {"text": "ดูรีวิว", "action": "view_reviews", "style": "primary"},
                        {"text": "เส้นทาง", "action": "get_directions", "style": "secondary"}
                    ]
                },
                position="overlay"
            ),
            # Enhanced UI templates from problem statement
            "location_popup": UIComponentAction(
                component_type=UIComponentType.SHOW_LOCATION_POPUP,
                content={
                    "name": "สถานที่ท่องเที่ยว",
                    "img": "placeholder.jpg",
                    "buttons": ["เปิดแผนที่", "ดูรีวิว"]
                },
                position="overlay",
                interaction_enabled=True
            ),
            "map_pin_display": UIComponentAction(
                component_type=UIComponentType.MAP_PIN_MARKER,
                content={
                    "location": {"lat": 0, "lng": 0},
                    "title": "สถานที่ท่องเที่ยว",
                    "animation": "blink"
                },
                position="scene"
            ),
            "review_display": UIComponentAction(
                component_type=UIComponentType.REVIEW_PANEL,
                content={
                    "reviews": [],
                    "rating": 4.5,
                    "total_reviews": 0
                },
                position="sidebar"
            ),
            "route_display": UIComponentAction(
                component_type=UIComponentType.ROUTE_PANEL,
                content={
                    "from": "ตำแหน่งปัจจุบัน",
                    "to": "สถานที่ท่องเที่ยว",
                    "buttons": ["เริ่มนำทาง", "ดูรายละเอียด"]
                },
                position="overlay"
            )
        })
        
        # Composite action templates (combinations)
        self._composite_templates.update({
            "suggest_place_full": {
                "speech": ["suggest_place"],
                "gesture": ["point_right_then_smile"],
                "scene": ["focus_map_pin", "zoom_to_location"],
                "ui": ["location_popup", "map_pin_display"]
            },
            "cultural_place_suggestion": {
                "speech": ["cultural_suggestion"],
                "gesture": ["friendly_nod"],
                "scene": ["focus_map_pin"],
                "ui": ["location_popup", "review_display"]
            },
            "greeting_welcome": {
                "speech": ["greeting"],
                "gesture": ["welcoming_wave"],
                "scene": [],
                "ui": []
            },
            # Enhanced composite from problem statement
            "phu_chi_fa_suggestion": {
                "speech": ["phu_chi_fa_suggest"],
                "gesture": ["point_right_then_smile"],
                "scene": ["focus_map_pin"],
                "ui": ["location_popup"]
            }
        })
    
    def get_speech_template(self, name: str) -> Optional[SpeechAction]:
        """Get a speech action template by name"""
        return self._speech_templates.get(name)
    
    def get_gesture_template(self, name: str) -> Optional[GestureAction]:
        """Get a gesture action template by name"""
        return self._gesture_templates.get(name)
    
    def get_scene_template(self, name: str) -> Optional[SceneInteractionAction]:
        """Get a scene interaction template by name"""
        return self._scene_templates.get(name)
    
    def get_ui_template(self, name: str) -> Optional[UIComponentAction]:
        """Get a UI component template by name"""
        return self._ui_templates.get(name)
    
    def get_composite_template(self, name: str) -> Optional[Dict[str, List[str]]]:
        """Get a composite action template by name"""
        return self._composite_templates.get(name)
    
    def register_template(self, category: str, name: str, template: Any):
        """Register a new template"""
        registry_map = {
            "speech": self._speech_templates,
            "gesture": self._gesture_templates,
            "scene": self._scene_templates,
            "ui": self._ui_templates,
            "composite": self._composite_templates
        }
        
        if category in registry_map:
            registry_map[category][name] = template
            logger.info(f"Registered {category} template: {name}")
        else:
            raise ValueError(f"Unknown template category: {category}")

class IntentMapper:
    """Maps intents to action plans using the action registry"""
    
    def __init__(self, action_registry: ActionRegistry):
        self.registry = action_registry
        self._intent_mappings = {}
        self._initialize_default_mappings()
    
    def _initialize_default_mappings(self):
        """Initialize default intent-to-action mappings"""
        
        self._intent_mappings.update({
            "suggest_place": {
                "composite_template": "suggest_place_full",
                "parameters": {
                    "place_name": "{place_name}",
                    "location_coordinates": "{coordinates}",
                    "photo_url": "{photo_url}"
                },
                "execution_order": ["speech", "gesture", "scene", "ui"]
            },
            "suggest_cultural_place": {
                "composite_template": "cultural_place_suggestion",
                "parameters": {
                    "cultural_type": "พิพิธภัณฑ์",
                    "location_coordinates": "{coordinates}",
                    "photo_url": "{photo_url}"
                },
                "execution_order": ["speech", "gesture", "scene", "ui"]
            },
            "greet_user": {
                "composite_template": "greeting_welcome",
                "parameters": {},
                "execution_order": ["speech", "gesture"]
            },
            "confirm_action": {
                "speech_templates": ["confirmation"],
                "gesture_templates": ["friendly_nod"],
                "execution_order": ["speech", "gesture"]
            }
        })
    
    def get_action_plan(self, intent: str, parameters: Dict[str, Any] = None, 
                       confidence: float = 1.0) -> ActionPlan:
        """Generate an action plan for the given intent"""
        
        if intent not in self._intent_mappings:
            logger.warning(f"Unknown intent: {intent}")
            return self._create_fallback_plan(intent, confidence)
        
        mapping = self._intent_mappings[intent]
        parameters = parameters or {}
        
        # Merge default parameters with provided ones
        merged_params = {**mapping.get("parameters", {}), **parameters}
        
        plan = ActionPlan(
            intent=intent,
            confidence=confidence,
            execution_order=mapping.get("execution_order", ["speech", "gesture", "scene", "ui"])
        )
        
        # Handle composite template
        if "composite_template" in mapping:
            composite = self.registry.get_composite_template(mapping["composite_template"])
            if composite:
                plan = self._build_from_composite(plan, composite, merged_params)
        
        # Handle individual templates
        for action_type in ["speech", "gesture", "scene", "ui"]:
            template_key = f"{action_type}_templates"
            if template_key in mapping:
                self._add_templates_to_plan(plan, action_type, mapping[template_key], merged_params)
        
        return plan
    
    def generate_problem_statement_format(self, intent: str, parameters: Dict[str, Any] = None) -> Dict[str, Any]:
        """
        Generate action plan in the exact format specified in the problem statement
        Example: {"intent": "suggest_place", "spoken_text": "...", "animation": "...", "ui_action": {...}}
        """
        plan = self.get_action_plan(intent, parameters)
        
        # Extract primary speech text
        spoken_text = ""
        if plan.speech_actions:
            spoken_text = plan.speech_actions[0].text
            
        # Extract primary animation
        animation = ""
        if plan.gesture_actions:
            animation = plan.gesture_actions[0].animation.value
            
        # Extract UI action data
        ui_action = {}
        if plan.ui_actions:
            ui_component = plan.ui_actions[0]
            if ui_component.component_type == UIComponentType.SHOW_LOCATION_POPUP:
                ui_action = {
                    "type": "show_location_popup",
                    "data": ui_component.content
                }
            else:
                ui_action = {
                    "type": ui_component.component_type.value,
                    "data": ui_component.content
                }
        
        return {
            "intent": intent,
            "spoken_text": spoken_text,
            "animation": animation,
            "ui_action": ui_action
        }
    
    def _build_from_composite(self, plan: ActionPlan, composite: Dict[str, List[str]], 
                            parameters: Dict[str, Any]) -> ActionPlan:
        """Build action plan from composite template"""
        
        # Add speech actions
        for template_name in composite.get("speech", []):
            template = self.registry.get_speech_template(template_name)
            if template:
                speech_action = self._customize_speech_action(template, parameters)
                plan.speech_actions.append(speech_action)
        
        # Add gesture actions
        for template_name in composite.get("gesture", []):
            template = self.registry.get_gesture_template(template_name)
            if template:
                plan.gesture_actions.append(template)
        
        # Add scene actions
        for template_name in composite.get("scene", []):
            template = self.registry.get_scene_template(template_name)
            if template:
                scene_action = self._customize_scene_action(template, parameters)
                plan.scene_actions.append(scene_action)
        
        # Add UI actions
        for template_name in composite.get("ui", []):
            template = self.registry.get_ui_template(template_name)
            if template:
                ui_action = self._customize_ui_action(template, parameters)
                plan.ui_actions.append(ui_action)
        
        return plan
    
    def _customize_speech_action(self, template: SpeechAction, 
                                parameters: Dict[str, Any]) -> SpeechAction:
        """Customize speech action with parameters"""
        text = template.text
        
        # Simple parameter substitution
        for key, value in parameters.items():
            placeholder = f"{{{key}}}"
            if placeholder in text:
                text = text.replace(placeholder, str(value))
        
        return SpeechAction(
            text=text,
            language=template.language,
            style=template.style,
            duration_ms=template.duration_ms,
            voice_params=template.voice_params.copy()
        )
    
    def _customize_scene_action(self, template: SceneInteractionAction,
                              parameters: Dict[str, Any]) -> SceneInteractionAction:
        """Customize scene action with parameters"""
        # Update target and parameters based on provided data
        target = template.target
        action_params = template.parameters.copy()
        
        if "coordinates" in parameters:
            target = parameters["coordinates"]
        
        if "location_pin_id" in parameters:
            action_params["pin_id"] = parameters["location_pin_id"]
        
        return SceneInteractionAction(
            interaction_type=template.interaction_type,
            target=target,
            duration_ms=template.duration_ms,
            parameters=action_params
        )
    
    def _customize_ui_action(self, template: UIComponentAction,
                           parameters: Dict[str, Any]) -> UIComponentAction:
        """Customize UI action with parameters"""
        content = template.content.copy()
        
        # Update content based on parameters
        if template.component_type == UIComponentType.PHOTO and "photo_url" in parameters:
            content["src"] = parameters["photo_url"]
        
        if "place_name" in parameters:
            if "alt" in content:
                content["alt"] = f"รูปภาพของ{parameters['place_name']}"
            if "title" in content:
                content["title"] = parameters["place_name"]
        
        return UIComponentAction(
            component_type=template.component_type,
            content=content,
            position=template.position,
            duration_ms=template.duration_ms,
            interaction_enabled=template.interaction_enabled
        )
    
    def _add_templates_to_plan(self, plan: ActionPlan, action_type: str, 
                             template_names: List[str], parameters: Dict[str, Any]):
        """Add templates of specific type to the plan"""
        
        for template_name in template_names:
            if action_type == "speech":
                template = self.registry.get_speech_template(template_name)
                if template:
                    speech_action = self._customize_speech_action(template, parameters)
                    plan.speech_actions.append(speech_action)
            
            elif action_type == "gesture":
                template = self.registry.get_gesture_template(template_name)
                if template:
                    plan.gesture_actions.append(template)
            
            elif action_type == "scene":
                template = self.registry.get_scene_template(template_name)
                if template:
                    scene_action = self._customize_scene_action(template, parameters)
                    plan.scene_actions.append(scene_action)
            
            elif action_type == "ui":
                template = self.registry.get_ui_template(template_name)
                if template:
                    ui_action = self._customize_ui_action(template, parameters)
                    plan.ui_actions.append(ui_action)
    
    def _create_fallback_plan(self, intent: str, confidence: float) -> ActionPlan:
        """Create a fallback action plan for unknown intents"""
        
        fallback_speech = SpeechAction(
            text="ขออภัยครับ ผมไม่เข้าใจคำขอของคุณ",
            style=SpeechStyle.CALM
        )
        
        fallback_gesture = GestureAction(
            animation=GestureAnimation.THINKING_POSE,
            facial_expression="confused",
            duration_ms=2000
        )
        
        return ActionPlan(
            intent=intent,
            confidence=confidence,
            speech_actions=[fallback_speech],
            gesture_actions=[fallback_gesture],
            execution_order=["speech", "gesture"]
        )
    
    def register_intent_mapping(self, intent: str, mapping: Dict[str, Any]):
        """Register a new intent mapping"""
        self._intent_mappings[intent] = mapping
        logger.info(f"Registered intent mapping: {intent}")

# Global instances
action_registry = ActionRegistry()
intent_mapper = IntentMapper(action_registry)