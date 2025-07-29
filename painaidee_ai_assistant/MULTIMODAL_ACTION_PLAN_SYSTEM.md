# Multimodal Action Plan System Documentation

## Overview

The Multimodal Action Plan System converts parsed NLP intents into coordinated multimodal action plans for the 3D assistant. Each intent triggers a combination of:

- **Speech output** (text-to-speech or dialogue in Thai/English)
- **Gesture animation** (nod, point, wave, etc.)
- **3D scene interaction** (camera movement, focus on map pin)
- **Optional UI components** (display photo, buttons: 'ดูรีวิว', 'เส้นทาง')

## Architecture

### Core Components

1. **Action Plan System** (`agents/action_plan_system.py`)
   - Defines action types and data structures
   - Manages action registry with reusable templates
   - Maps intents to action plans

2. **Action Plan Executor** (`agents/action_plan_executor.py`)
   - Coordinates execution of multimodal outputs
   - Handles timing and synchronization
   - Generates structured outputs for frontend consumption

3. **API Routes** (`api/action_plan_routes.py`)
   - REST endpoints for generating and executing plans
   - Natural language processing for quick actions
   - Template and intent registration

## Data Structures

### Action Types

```python
class ActionType(Enum):
    SPEECH = "speech"
    GESTURE = "gesture"  
    SCENE_INTERACTION = "scene_interaction"
    UI_COMPONENT = "ui_component"
```

### Speech Actions

```python
@dataclass
class SpeechAction:
    text: str
    language: str = "th"  # Thai by default
    style: SpeechStyle = SpeechStyle.FRIENDLY
    duration_ms: Optional[int] = None
    voice_params: Dict[str, Any] = field(default_factory=dict)
```

### Gesture Actions

```python
@dataclass
class GestureAction:
    animation: GestureAnimation
    model_name: str = "Man_Rig.fbx"
    duration_ms: int = 2000
    intensity: float = 1.0  # 0.0 to 1.0
    loop: bool = False
    facial_expression: str = "neutral"
```

### Scene Interaction Actions

```python
@dataclass
class SceneInteractionAction:
    interaction_type: SceneInteractionType
    target: str  # Object, location, or coordinate
    duration_ms: int = 3000
    parameters: Dict[str, Any] = field(default_factory=dict)
```

### UI Component Actions

```python
@dataclass
class UIComponentAction:
    component_type: UIComponentType
    content: Dict[str, Any]  # Component-specific content
    position: str = "overlay"  # overlay, sidebar, fullscreen
    duration_ms: Optional[int] = None  # None means persistent
    interaction_enabled: bool = True
```

## API Endpoints

### Generate Action Plan

```http
POST /action/generate_plan
```

**Request:**
```json
{
  "intent": "suggest_cultural_place",
  "parameters": {
    "place_name": "พิพิธภัณฑ์กรุงเทพ",
    "coordinates": "13.7465,100.5014",
    "photo_url": "https://example.com/bangkok-museum.jpg"
  },
  "confidence": 0.9
}
```

**Response:**
```json
{
  "intent": "suggest_cultural_place",
  "confidence": 0.9,
  "speech_actions": [
    {
      "text": "ลองไปพิพิธภัณฑ์พื้นบ้านดูไหมครับ?",
      "language": "th",
      "style": "informative",
      "duration_ms": null,
      "voice_params": {}
    }
  ],
  "gesture_actions": [
    {
      "animation": "nod",
      "model_name": "Man_Rig.fbx",
      "duration_ms": 1500,
      "intensity": 1.0,
      "loop": false,
      "facial_expression": "smile"
    }
  ],
  "scene_actions": [
    {
      "interaction_type": "map_pin_highlight",
      "target": "13.7465,100.5014",
      "duration_ms": 2000,
      "parameters": {
        "highlight_color": "#FF6B35",
        "pulse": true
      }
    }
  ],
  "ui_actions": [
    {
      "component_type": "photo",
      "content": {
        "src": "https://example.com/bangkok-museum.jpg",
        "alt": "รูปภาพของพิพิธภัณฑ์กรุงเทพ"
      },
      "position": "overlay",
      "duration_ms": null,
      "interaction_enabled": true
    },
    {
      "component_type": "button",
      "content": {
        "buttons": [
          {
            "text": "ดูรีวิว",
            "action": "view_reviews",
            "style": "primary"
          },
          {
            "text": "เส้นทาง",
            "action": "get_directions",
            "style": "secondary"
          }
        ]
      },
      "position": "overlay",
      "duration_ms": null,
      "interaction_enabled": true
    }
  ],
  "execution_order": ["speech", "gesture", "scene", "ui"],
  "estimated_duration_ms": 5000,
  "metadata": {}
}
```

### Quick Action (Natural Language)

```http
POST /action/quick_action
```

**Request:**
```json
{
  "user_input": "แนะนำสถานที่ท่องเที่ยวให้หน่อย",
  "language": "th",
  "context": {
    "user_location": "กรุงเทพ"
  }
}
```

### Execute Action Plan

```http
POST /action/execute_plan
```

**Request:**
```json
{
  "plan": {
    "intent": "greet_user",
    "parameters": {},
    "confidence": 1.0
  },
  "execution_mode": "immediate"
}
```

**Response:**
```json
{
  "execution_id": "exec_1753761225.523236",
  "status": "completed",
  "started_at": "2025-07-29T03:53:45.523236",
  "outputs": {
    "speech": [
      {
        "type": "speech",
        "text": "สวัสดีครับ ยินดีต้อนรับ",
        "language": "th",
        "style": "friendly",
        "duration_ms": 800,
        "voice_params": {},
        "audio_url": "/audio/tts?text=สวัสดีครับ ยินดีต้อนรับ&lang=th&style=friendly",
        "timestamp": "2025-07-29T03:53:45.523360"
      }
    ],
    "gesture": [
      {
        "type": "gesture",
        "animation": "wave",
        "model_name": "Man_Rig.fbx",
        "duration_ms": 2500,
        "intensity": 1.0,
        "loop": false,
        "facial_expression": "happy",
        "animation_params": {
          "start_time": 0,
          "end_time": 2500,
          "easing": "ease-in-out",
          "blend_weight": 1.0
        },
        "timestamp": "2025-07-29T03:53:45.523463"
      }
    ]
  }
}
```

## Built-in Intents

### suggest_place
Suggests a tourist place with full multimodal presentation.

**Parameters:**
- `place_name`: Name of the place
- `coordinates`: GPS coordinates
- `photo_url`: URL to place photo

**Action Plan:**
- Speech: "ลองไป{place_name}ดูไหมครับ?"
- Gesture: nod_and_point
- Scene: Map pin highlight + zoom to location
- UI: Photo + action buttons ('ดูรีวิว', 'เส้นทาง')

### suggest_cultural_place
Suggests a cultural place like museum with information display.

**Parameters:**
- `cultural_type`: Type of cultural site
- `coordinates`: GPS coordinates  
- `photo_url`: URL to place photo

**Action Plan:**
- Speech: "ลองไปพิพิธภัณฑ์พื้นบ้านดูไหมครับ?"
- Gesture: friendly_nod
- Scene: Map pin highlight
- UI: Photo + action buttons + info panel

### greet_user
Welcome greeting with friendly gesture.

**Action Plan:**
- Speech: "สวัสดีครับ ยินดีต้อนรับ"
- Gesture: welcoming_wave

### confirm_action
Confirms user action with acknowledgment.

**Action Plan:**
- Speech: "เข้าใจแล้วครับ"
- Gesture: friendly_nod

## Extending the System

### Adding New Intents

```python
# 1. Register new intent mapping
intent_mapping = {
    "speech_templates": ["custom_speech"],
    "gesture_templates": ["custom_gesture"],
    "scene_templates": ["focus_map_pin"],
    "ui_templates": ["place_photo", "action_buttons"],
    "parameters": {
        "param_name": "{param_value}"
    },
    "execution_order": ["speech", "gesture", "scene", "ui"]
}

# 2. Register via API
POST /action/register_intent
{
  "intent": "new_intent_name",
  "mapping": intent_mapping,
  "description": "Description of the new intent"
}
```

### Adding Custom Templates

```python
# Speech template
custom_speech = {
    "text": "Custom speech text with {parameter}",
    "language": "th",
    "style": "friendly",
    "duration_ms": None,
    "voice_params": {}
}

# Register via API
POST /action/register_template
{
  "category": "speech",
  "name": "custom_speech",
  "template": custom_speech,
  "description": "Custom speech template"
}
```

## Available Gestures

- `nod`: Simple head nod
- `point`: Pointing gesture
- `wave`: Friendly wave
- `nod_and_point`: Combined nod and point
- `welcome_gesture`: Welcoming arms gesture
- `thinking_pose`: Thoughtful pose
- `excited_gesture`: Energetic movement
- `reassuring_nod`: Calm, reassuring nod

## Scene Interactions

- `camera_move`: Move camera to target
- `focus_object`: Focus on specific object
- `map_pin_highlight`: Highlight map pin with color/pulse
- `zoom_to_location`: Zoom to GPS coordinates
- `rotate_view`: Rotate camera view

## UI Components

- `photo`: Display image with alt text
- `button`: Interactive buttons with actions
- `info_panel`: Information display panel
- `map_overlay`: Map overlay components
- `rating_display`: Rating and review display

## Example Usage

```python
import requests

# Generate action plan
response = requests.post(
    "http://localhost:8000/action/generate_plan",
    json={
        "intent": "suggest_cultural_place",
        "parameters": {
            "place_name": "วัดพระแก้ว",
            "coordinates": "13.7503,100.4914",
            "photo_url": "https://example.com/wat-phra-kaew.jpg"
        },
        "confidence": 0.9
    }
)

plan = response.json()

# Execute the plan
response = requests.post(
    "http://localhost:8000/action/execute_plan", 
    json={
        "plan": {
            "intent": "suggest_cultural_place",
            "parameters": plan["parameters"],
            "confidence": 0.9
        },
        "execution_mode": "immediate"
    }
)

execution_result = response.json()
```

## Integration with Frontend

The action plan executor generates structured outputs that can be consumed by the frontend:

```javascript
// Example frontend integration
async function executeActionPlan(intent, parameters) {
    const response = await fetch('/action/execute_plan', {
        method: 'POST',
        headers: {
            'Content-Type': 'application/json'
        },
        body: JSON.stringify({
            plan: {
                intent: intent,
                parameters: parameters,
                confidence: 1.0
            },
            execution_mode: 'immediate'
        })
    });
    
    const result = await response.json();
    
    // Handle speech output
    if (result.outputs.speech) {
        result.outputs.speech.forEach(speech => {
            playTextToSpeech(speech.text, speech.language, speech.style);
        });
    }
    
    // Handle gesture animations
    if (result.outputs.gesture) {
        result.outputs.gesture.forEach(gesture => {
            animate3DModel(
                gesture.model_name,
                gesture.animation,
                gesture.duration_ms,
                gesture.facial_expression
            );
        });
    }
    
    // Handle scene interactions
    if (result.outputs.scene) {
        result.outputs.scene.forEach(scene => {
            if (scene.camera_commands) {
                scene.camera_commands.forEach(cmd => {
                    executeCamera Command(cmd);
                });
            }
            if (scene.scene_updates) {
                scene.scene_updates.forEach(update => {
                    updateSceneObject(update);
                });
            }
        });
    }
    
    // Handle UI components
    if (result.outputs.ui) {
        result.outputs.ui.forEach(ui => {
            renderUIComponent(
                ui.component_type,
                ui.content,
                ui.position,
                ui.interaction_enabled
            );
        });
    }
}
```

## Testing

Run the comprehensive test suite:

```bash
cd /home/runner/work/AI_Assistant_PaiNaiDee/AI_Assistant_PaiNaiDee/painaidee_ai_assistant
PYTHONPATH=/home/runner/work/AI_Assistant_PaiNaiDee/AI_Assistant_PaiNaiDee/painaidee_ai_assistant python tests/test_action_plan_system.py
```

Run the comprehensive demo:

```bash
python examples/comprehensive_action_plan_demo.py
```

## Health Check

```http
GET /action/health
```

Returns system status and available components.

## API Documentation

Full interactive API documentation is available at:
```
http://localhost:8000/docs
```

## Performance Considerations

- Actions within the same type (e.g., multiple speech actions) execute concurrently
- Scene interactions are optimized for smooth transitions
- UI components are rendered asynchronously
- Speech duration is estimated automatically if not specified
- Gesture animations include easing and blending parameters for smooth execution