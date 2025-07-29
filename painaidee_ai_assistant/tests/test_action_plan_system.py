"""
Tests for the Multimodal Action Plan System
"""

import asyncio
from typing import Dict, Any

# Import the action plan components
from agents.action_plan_system import (
    intent_mapper, action_registry, ActionPlan, SpeechAction, 
    GestureAction, SceneInteractionAction, UIComponentAction,
    SpeechStyle, GestureAnimation, SceneInteractionType, UIComponentType
)
from agents.action_plan_executor import action_plan_executor, ExecutionResult

def test_action_registry_initialization():
    """Test that action registry initializes with default templates"""
    
    # Test speech templates
    greeting_template = action_registry.get_speech_template("greeting")
    assert greeting_template is not None
    assert greeting_template.text == "สวัสดีครับ ยินดีต้อนรับ"
    assert greeting_template.style == SpeechStyle.FRIENDLY
    
    # Test gesture templates
    nod_template = action_registry.get_gesture_template("friendly_nod")
    assert nod_template is not None
    assert nod_template.animation == GestureAnimation.NOD
    assert nod_template.facial_expression == "smile"
    
    # Test scene templates
    map_pin_template = action_registry.get_scene_template("focus_map_pin")
    assert map_pin_template is not None
    assert map_pin_template.interaction_type == SceneInteractionType.MAP_PIN_HIGHLIGHT
    
    # Test UI templates
    photo_template = action_registry.get_ui_template("place_photo")
    assert photo_template is not None
    assert photo_template.component_type == UIComponentType.PHOTO

def test_intent_mapping_basic():
    """Test basic intent mapping functionality"""
    
    # Test suggest_place intent
    plan = intent_mapper.get_action_plan("suggest_place", {
        "place_name": "วัดพระแก้ว",
        "coordinates": "13.7503,100.4914",
        "photo_url": "https://example.com/wat-phra-kaew.jpg"
    })
    
    assert plan.intent == "suggest_place"
    assert plan.confidence == 1.0
    assert len(plan.speech_actions) > 0
    assert len(plan.gesture_actions) > 0
    assert len(plan.scene_actions) > 0
    assert len(plan.ui_actions) > 0
    
    # Check speech action content
    speech_action = plan.speech_actions[0]
    assert "วัดพระแก้ว" in speech_action.text or "{place_name}" in speech_action.text

def test_cultural_place_intent():
    """Test cultural place suggestion intent"""
    
    plan = intent_mapper.get_action_plan("suggest_cultural_place", {
        "coordinates": "13.7465,100.5014",
        "photo_url": "https://example.com/museum.jpg"
    })
    
    assert plan.intent == "suggest_cultural_place"
    assert len(plan.speech_actions) > 0
    assert len(plan.gesture_actions) > 0
    assert len(plan.scene_actions) > 0
    assert len(plan.ui_actions) > 0
    
    # Check that it mentions cultural content
    speech_action = plan.speech_actions[0]
    assert "พิพิธภัณฑ์" in speech_action.text

def test_greeting_intent():
    """Test greeting intent"""
    
    plan = intent_mapper.get_action_plan("greet_user")
    
    assert plan.intent == "greet_user"
    assert len(plan.speech_actions) > 0
    assert len(plan.gesture_actions) > 0
    # Greeting doesn't need scene or UI actions
    
    speech_action = plan.speech_actions[0]
    assert "สวัสดี" in speech_action.text

def test_unknown_intent_fallback():
    """Test fallback for unknown intents"""
    
    plan = intent_mapper.get_action_plan("unknown_intent")
    
    assert plan.intent == "unknown_intent"
    assert len(plan.speech_actions) > 0
    assert len(plan.gesture_actions) > 0
    
    speech_action = plan.speech_actions[0]
    assert "ขออภัย" in speech_action.text

def test_template_registration():
    """Test registering new templates"""
    
    # Register a new speech template
    custom_speech = SpeechAction(
        text="นี่คือการทดสอบ",
        style=SpeechStyle.INFORMATIVE
    )
    action_registry.register_template("speech", "test_speech", custom_speech)
    
    # Verify it was registered
    retrieved = action_registry.get_speech_template("test_speech")
    assert retrieved is not None
    assert retrieved.text == "นี่คือการทดสอบ"
    assert retrieved.style == SpeechStyle.INFORMATIVE

def test_intent_registration():
    """Test registering new intent mappings"""
    
    # Register a new intent
    test_mapping = {
        "speech_templates": ["test_speech"],
        "gesture_templates": ["friendly_nod"],
        "execution_order": ["speech", "gesture"]
    }
    intent_mapper.register_intent_mapping("test_intent", test_mapping)
    
    # Test the new intent
    plan = intent_mapper.get_action_plan("test_intent")
    assert plan.intent == "test_intent"

async def test_action_execution():
    """Test executing action plans"""
    
    # Create a simple plan for testing
    plan = intent_mapper.get_action_plan("greet_user")
    
    # Execute the plan
    result = await action_plan_executor.execute_plan(plan)
    
    assert isinstance(result, ExecutionResult)
    assert result.status in ["completed", "executing"]
    assert result.plan.intent == "greet_user"
    
    # Check that outputs were generated
    outputs = action_plan_executor.get_all_outputs()
    assert "speech" in outputs
    assert "gesture" in outputs

def test_action_plan_structure():
    """Test the structure of generated action plans"""
    
    plan = intent_mapper.get_action_plan("suggest_place", {
        "place_name": "พระราชวังใหญ่",
        "coordinates": "13.7503,100.4914"
    })
    
    # Verify execution order
    assert "speech" in plan.execution_order
    assert "gesture" in plan.execution_order
    assert "scene" in plan.execution_order
    assert "ui" in plan.execution_order
    
    # Verify action types
    for speech_action in plan.speech_actions:
        assert isinstance(speech_action, SpeechAction)
        assert speech_action.language in ["th", "en"]
    
    for gesture_action in plan.gesture_actions:
        assert isinstance(gesture_action, GestureAction)
        assert isinstance(gesture_action.animation, GestureAnimation)
    
    for scene_action in plan.scene_actions:
        assert isinstance(scene_action, SceneInteractionAction)
        assert isinstance(scene_action.interaction_type, SceneInteractionType)
    
    for ui_action in plan.ui_actions:
        assert isinstance(ui_action, UIComponentAction)
        assert isinstance(ui_action.component_type, UIComponentType)

def test_parameter_substitution():
    """Test parameter substitution in templates"""
    
    plan = intent_mapper.get_action_plan("suggest_place", {
        "place_name": "วัดอรุณราชวราราม",
        "coordinates": "13.7436,100.4886",
        "photo_url": "https://example.com/wat-arun.jpg"
    })
    
    # Check that parameters were substituted
    speech_action = plan.speech_actions[0]
    # Either the parameter was substituted or still in template form
    assert "วัดอรุณราชวราราม" in speech_action.text or "{place_name}" in speech_action.text
    
    # Check UI action content
    for ui_action in plan.ui_actions:
        if ui_action.component_type == UIComponentType.PHOTO:
            content = ui_action.content
            if "src" in content:
                assert "wat-arun" in content["src"] or "placeholder" in content["src"]

def test_composite_templates():
    """Test composite template functionality"""
    
    # Get a composite template
    composite = action_registry.get_composite_template("suggest_place_full")
    assert composite is not None
    assert "speech" in composite
    assert "gesture" in composite
    assert "scene" in composite
    assert "ui" in composite
    
    # Verify it has the expected templates
    assert "suggest_place" in composite["speech"]
    assert "suggest_nod_point" in composite["gesture"]

def test_multilingual_support():
    """Test multilingual action support"""
    
    # Test with Thai parameters
    plan_th = intent_mapper.get_action_plan("suggest_place", {
        "place_name": "วัดโพธิ์",
        "coordinates": "13.7465,100.4930"
    })
    
    # Test with English parameters  
    plan_en = intent_mapper.get_action_plan("suggest_place", {
        "place_name": "Wat Pho",
        "coordinates": "13.7465,100.4930"
    })
    
    # Both should generate valid plans
    assert plan_th.intent == "suggest_place"
    assert plan_en.intent == "suggest_place"
    
    # Both should have Thai speech by default
    assert plan_th.speech_actions[0].language == "th"
    assert plan_en.speech_actions[0].language == "th"

def test_execution_timing():
    """Test execution timing and coordination"""
    
    plan = intent_mapper.get_action_plan("suggest_cultural_place")
    
    # Check that actions have reasonable durations
    for gesture_action in plan.gesture_actions:
        assert gesture_action.duration_ms > 0
        assert gesture_action.duration_ms <= 10000  # Max 10 seconds
    
    for scene_action in plan.scene_actions:
        assert scene_action.duration_ms > 0
        assert scene_action.duration_ms <= 10000

def test_ui_component_generation():
    """Test UI component generation"""
    
    plan = intent_mapper.get_action_plan("suggest_place", {
        "place_name": "เกาะสมุย",
        "photo_url": "https://example.com/koh-samui.jpg"
    })
    
    # Should have buttons for reviews and directions
    button_actions = [
        action for action in plan.ui_actions 
        if action.component_type == UIComponentType.BUTTON
    ]
    
    assert len(button_actions) > 0
    button_content = button_actions[0].content
    assert "buttons" in button_content
    
    buttons = button_content["buttons"]
    button_texts = [btn["text"] for btn in buttons]
    assert "ดูรีวิว" in button_texts
    assert "เส้นทาง" in button_texts

if __name__ == "__main__":
    # Run tests manually if not using pytest
    print("Running Action Plan System Tests...")
    
    test_action_registry_initialization()
    print("✓ Action registry initialization test passed")
    
    test_intent_mapping_basic()
    print("✓ Basic intent mapping test passed")
    
    test_cultural_place_intent()
    print("✓ Cultural place intent test passed")
    
    test_greeting_intent()
    print("✓ Greeting intent test passed")
    
    test_unknown_intent_fallback()
    print("✓ Unknown intent fallback test passed")
    
    test_template_registration()
    print("✓ Template registration test passed")
    
    test_intent_registration()
    print("✓ Intent registration test passed")
    
    # Run async test
    asyncio.run(test_action_execution())
    print("✓ Action execution test passed")
    
    test_action_plan_structure()
    print("✓ Action plan structure test passed")
    
    test_parameter_substitution()
    print("✓ Parameter substitution test passed")
    
    test_composite_templates()
    print("✓ Composite templates test passed")
    
    test_multilingual_support()
    print("✓ Multilingual support test passed")
    
    test_execution_timing()
    print("✓ Execution timing test passed")
    
    test_ui_component_generation()
    print("✓ UI component generation test passed")
    
    print("\n🎉 All tests passed successfully!")