"""
3D World API routes for PaiNaiDee AI Assistant
Handles 3D world interactions, AI movement, and multi-user synchronization
"""

from fastapi import APIRouter, HTTPException, WebSocket, WebSocketDisconnect
from fastapi.responses import JSONResponse
from pydantic import BaseModel
from typing import Dict, List, Optional, Any
import json
import asyncio
import uuid
from datetime import datetime
import logging

logger = logging.getLogger(__name__)

# Router setup
router = APIRouter(prefix="/3d_world", tags=["3D World"])

# Data models
class WorldPosition(BaseModel):
    x: float
    y: float
    z: float

class AIAction(BaseModel):
    type: str  # navigate, greet, dance, point, speak
    target_location: Optional[str] = None
    position: Optional[WorldPosition] = None
    message: Optional[str] = None
    language: Optional[str] = "en"

class LocationVisit(BaseModel):
    location: str
    language: str = "en"
    user_id: Optional[str] = None

class User3D(BaseModel):
    user_id: str
    username: Optional[str] = None
    position: WorldPosition
    language: str = "en"
    last_active: datetime

# Global state for 3D world
active_users: Dict[str, User3D] = {}
active_connections: Dict[str, WebSocket] = {}
ai_current_position = WorldPosition(x=0, y=1, z=0)
ai_current_action = None

# Tourist locations data
TOURIST_LOCATIONS = {
    "koh-samui": {
        "name": {"en": "Koh Samui Island", "th": "เกาะสมุย"},
        "description": {"en": "Beautiful tropical island with pristine beaches", "th": "เกาะเขตร้อนที่สวยงามพร้อมชายหาดบริสุทธิ์"},
        "position": {"x": 10, "y": 0, "z": 5},
        "category": "island",
        "rating": 4.8,
        "activities": ["swimming", "snorkeling", "beach_walking", "sunset_viewing"]
    },
    "temple": {
        "name": {"en": "Buddhist Temple", "th": "วัดพุทธ"},
        "description": {"en": "Sacred Buddhist temple with ancient architecture", "th": "วัดพุทธศักดิ์สิทธิ์พร้อมสถาปัตยกรรมโบราณ"},
        "position": {"x": -10, "y": 0, "z": 5},
        "category": "cultural",
        "rating": 4.9,
        "activities": ["meditation", "prayer", "architecture_viewing", "cultural_learning"]
    },
    "market": {
        "name": {"en": "Floating Market", "th": "ตลาดน้ำ"},
        "description": {"en": "Traditional floating market with local food and crafts", "th": "ตลาดน้ำแบบดั้งเดิมพร้อมอาหารและหัตถกรรมท้องถิ่น"},
        "position": {"x": 0, "y": 0, "z": 15},
        "category": "market",
        "rating": 4.6,
        "activities": ["shopping", "food_tasting", "boat_riding", "photography"]
    },
    "beach": {
        "name": {"en": "Tropical Beach", "th": "ชายหาดเขตร้อน"},
        "description": {"en": "Pristine tropical beach with crystal clear water", "th": "ชายหาดเขตร้อนบริสุทธิ์พร้อมน้ำใสคริสตัล"},
        "position": {"x": 15, "y": 0, "z": -5},
        "category": "beach",
        "rating": 4.7,
        "activities": ["swimming", "sunbathing", "water_sports", "relaxation"]
    },
    "restaurant": {
        "name": {"en": "Thai Restaurant", "th": "ร้านอาหารไทย"},
        "description": {"en": "Authentic Thai restaurant with traditional cuisine", "th": "ร้านอาหารไทยแท้พร้อมอาหารแบบดั้งเดิม"},
        "position": {"x": -5, "y": 0, "z": -10},
        "category": "restaurant",
        "rating": 4.8,
        "activities": ["dining", "cooking_class", "cultural_experience", "food_photography"]
    }
}

@router.get("/locations")
async def get_tourist_locations():
    """Get all tourist locations in the 3D world"""
    return {"status": "success", "locations": TOURIST_LOCATIONS}

@router.get("/locations/{location_id}")
async def get_location_details(location_id: str):
    """Get detailed information about a specific location"""
    if location_id not in TOURIST_LOCATIONS:
        raise HTTPException(status_code=404, detail="Location not found")
    
    location = TOURIST_LOCATIONS[location_id]
    return {
        "status": "success",
        "location_id": location_id,
        "data": location
    }

@router.post("/ai/navigate")
async def navigate_ai_to_location(action: AIAction):
    """Make AI navigate to a specific location"""
    global ai_current_position, ai_current_action
    
    try:
        if action.target_location and action.target_location in TOURIST_LOCATIONS:
            location_data = TOURIST_LOCATIONS[action.target_location]
            target_pos = location_data["position"]
            
            # Update AI position
            ai_current_position = WorldPosition(
                x=target_pos["x"], 
                y=1, 
                z=target_pos["z"] - 2
            )
            ai_current_action = {
                "type": "navigate",
                "target": action.target_location,
                "position": ai_current_position.dict(),
                "timestamp": datetime.now().isoformat()
            }
            
            # Broadcast to all connected users
            await broadcast_ai_action(ai_current_action)
            
            # Generate AI response based on location
            ai_response = generate_location_response(action.target_location, action.language)
            
            return {
                "status": "success",
                "ai_position": ai_current_position.dict(),
                "action": ai_current_action,
                "ai_response": ai_response
            }
        else:
            raise HTTPException(status_code=400, detail="Invalid location")
            
    except Exception as e:
        logger.error(f"Error navigating AI: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Navigation failed: {str(e)}")

@router.post("/ai/action")
async def execute_ai_action(action: AIAction):
    """Execute various AI actions (greet, dance, point, etc.)"""
    global ai_current_action
    
    try:
        ai_current_action = {
            "type": action.type,
            "message": action.message,
            "language": action.language,
            "timestamp": datetime.now().isoformat()
        }
        
        # Generate appropriate response based on action type
        response_data = generate_action_response(action)
        
        # Broadcast to all users
        await broadcast_ai_action({**ai_current_action, **response_data})
        
        return {
            "status": "success",
            "action": ai_current_action,
            "response": response_data
        }
        
    except Exception as e:
        logger.error(f"Error executing AI action: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Action failed: {str(e)}")

@router.post("/process_location_visit")
async def process_location_visit(visit: LocationVisit):
    """Process when AI visits a location and generate contextual response"""
    try:
        # This endpoint is called from the frontend when AI reaches a location
        location_info = None
        for loc_id, loc_data in TOURIST_LOCATIONS.items():
            if (loc_data["name"]["en"].lower() == visit.location.lower() or 
                loc_data["name"]["th"] == visit.location):
                location_info = loc_data
                break
        
        if location_info:
            response = {
                "status": "success",
                "location_analysis": {
                    "name": location_info["name"],
                    "description": location_info["description"],
                    "category": location_info["category"],
                    "rating": location_info["rating"],
                    "recommended_activities": location_info["activities"]
                },
                "ai_response": generate_detailed_location_info(location_info, visit.language)
            }
        else:
            response = {
                "status": "success",
                "message": f"Information about {visit.location} processed",
                "ai_response": {
                    "en": f"Thank you for visiting {visit.location}!",
                    "th": f"ขอบคุณที่มาเยี่ยมชม {visit.location}!"
                }
            }
        
        return response
        
    except Exception as e:
        logger.error(f"Error processing location visit: {str(e)}")
        return {"status": "error", "message": str(e)}

@router.get("/ai/status")
async def get_ai_status():
    """Get current AI status and position"""
    return {
        "status": "success",
        "ai_position": ai_current_position.dict(),
        "current_action": ai_current_action,
        "active_users": len(active_users)
    }

@router.get("/users/active")
async def get_active_users():
    """Get list of active users in the 3D world"""
    return {
        "status": "success",
        "user_count": len(active_users),
        "users": [user.dict() for user in active_users.values()]
    }

# WebSocket endpoint for real-time multi-user support
@router.websocket("/ws/{user_id}")
async def websocket_endpoint(websocket: WebSocket, user_id: str):
    """WebSocket connection for real-time 3D world synchronization"""
    await websocket.accept()
    
    # Add user to active connections
    active_connections[user_id] = websocket
    
    # Create user object
    user = User3D(
        user_id=user_id,
        position=WorldPosition(x=0, y=1, z=-5),  # Starting position
        last_active=datetime.now()
    )
    active_users[user_id] = user
    
    # Notify all users about new user
    await broadcast_user_update()
    
    try:
        while True:
            # Receive messages from client
            data = await websocket.receive_text()
            message = json.loads(data)
            
            # Handle different message types
            if message["type"] == "position_update":
                # Update user position
                active_users[user_id].position = WorldPosition(**message["position"])
                active_users[user_id].last_active = datetime.now()
                
            elif message["type"] == "ai_request":
                # Handle AI interaction request
                await handle_ai_request(user_id, message)
                
            elif message["type"] == "chat_message":
                # Broadcast chat message to all users
                await broadcast_message({
                    "type": "chat",
                    "user_id": user_id,
                    "message": message["message"],
                    "timestamp": datetime.now().isoformat()
                })
                
    except WebSocketDisconnect:
        # Remove user from active connections
        if user_id in active_connections:
            del active_connections[user_id]
        if user_id in active_users:
            del active_users[user_id]
        
        # Notify remaining users
        await broadcast_user_update()

# Helper functions
def generate_location_response(location_id: str, language: str = "en") -> Dict[str, Any]:
    """Generate AI response for location visit"""
    location = TOURIST_LOCATIONS[location_id]
    
    responses = {
        "koh-samui": {
            "en": "Welcome to the beautiful Koh Samui! This tropical paradise offers pristine beaches, crystal clear waters, and amazing sunset views. Would you like to know about the best beaches or activities here?",
            "th": "ยินดีต้อนรับสู่เกาะสมุยที่สวยงาม! เกาะเขตร้อนแห่งนี้มีชายหาดบริสุทธิ์ น้ำใสคริสตัล และวิวพระอาทิตย์ตกที่สวยงาม อยากทราบเกี่ยวกับชายหาดที่ดีที่สุดหรือกิจกรรมที่นี่ไหม?"
        },
        "temple": {
            "en": "Here is a sacred Buddhist temple, a place of peace and spiritual reflection. Thai temples are architectural marvels with intricate designs and golden decorations. You can meditate here or learn about Buddhist culture.",
            "th": "นี่คือวัดพุทธศักดิ์สิทธิ์ สถานที่แห่งความสงบและการไตร่ตรอง วัดไทยเป็นสิ่งมหัศจรรย์ทางสถาปัตยกรรมที่มีการออกแบบที่ซับซ้อนและการตукраशения ทอง คุณสามารถนั่งสมาธิที่นี่หรือเรียนรู้เกี่ยวกับวัฒนธรรมพุทธ"
        },
        "market": {
            "en": "This is a traditional floating market where you can experience authentic Thai culture! Try delicious local food, buy handmade crafts, and enjoy a unique boat ride through the market.",
            "th": "นี่คือตลาดน้ำแบบดั้งเดิมที่คุณสามารถสัมผัสวัฒนธรรมไทยแท้! ลิ้มรสอาหารท้องถิ่นอร่อยๆ ซื้อหัตถกรรมทำมือ และเพลิดเพลินกับการนั่งเรือผ่านตลาดอย่างมีเอกลักษณ์"
        },
        "beach": {
            "en": "What a perfect tropical beach! The sand is soft, the water is warm and crystal clear. Perfect for swimming, sunbathing, or just relaxing while listening to the gentle waves.",
            "th": "ชายหาดเขตร้อนที่สมบูรณ์แบบ! ทรายนุ่ม น้ำอุ่นและใสคริสตัล เหมาะสำหรับการว่ายน้ำ อาบแดด หรือแค่ผ่อนคลายไปกับเสียงคลื่นเบาๆ"
        },
        "restaurant": {
            "en": "Welcome to an authentic Thai restaurant! Here you can taste traditional Thai cuisine with its amazing flavors - sweet, sour, salty, and spicy all perfectly balanced. Would you like menu recommendations?",
            "th": "ยินดีต้อนรับสู่ร้านอาหารไทยแท้! ที่นี่คุณสามารถลิ้มรสอาหารไทยแบบดั้งเดิมที่มีรสชาติที่น่าทึ่ง - หวาน เปรี้ยว เค็ม และเผ็ดที่สมดุลอย่างสมบูรณ์แบบ อยากได้คำแนะนำเมนูไหม?"
        }
    }
    
    return {
        "message": responses.get(location_id, {}).get(language, "Welcome to this location!"),
        "location_data": location,
        "suggested_activities": location["activities"]
    }

def generate_action_response(action: AIAction) -> Dict[str, Any]:
    """Generate response for AI actions"""
    responses = {
        "greet": {
            "en": "Hello! I'm your AI tourism assistant. How can I help you explore Thailand today?",
            "th": "สวัสดีค่ะ! ฉันเป็นผู้ช่วย AI ด้านการท่องเที่ยว วันนี้ช่วยให้คุณสำรวจประเทศไทยได้อย่างไร?"
        },
        "dance": {
            "en": "Let me show you a traditional Thai dance! This represents the graceful movements of Thai classical culture.",
            "th": "ให้ฉันแสดงการเต้นรำแบบไทยให้ดูนะ! นี่แสดงถึงการเคลื่อนไหวที่สง่างามของวัฒนธรรมไทยคลาสสิก"
        },
        "point": {
            "en": "I'm pointing to show you this interesting location. Each place in Thailand has its own unique story and beauty.",
            "th": "ฉันชี้เพื่อแสดงให้คุณเห็นสถานที่น่าสนใจนี้ แต่ละสถานที่ในประเทศไทยมีเรื่องราวและความงามที่เป็นเอกลักษณ์"
        }
    }
    
    return {
        "message": responses.get(action.type, {}).get(action.language, "Action completed!"),
        "animation": action.type,
        "duration": 3.0  # seconds
    }

def generate_detailed_location_info(location_info: Dict, language: str = "en") -> Dict[str, str]:
    """Generate detailed information about a location"""
    category_descriptions = {
        "island": {
            "en": "This beautiful island destination offers tropical paradise experiences with pristine beaches and clear waters.",
            "th": "เกาะปลายทางที่สวยงามแห่งนี้มอบประสบการณ์สวรรค์เขตร้อนพร้อมชายหาดบริสุทธิ์และน้ำใส"
        },
        "cultural": {
            "en": "This cultural site represents Thailand's rich heritage and spiritual traditions.",
            "th": "แหล่งวัฒนธรรมแห่งนี้แสดงถึงมรดกอันยิ่งใหญ่และประเพณีทางจิตวิญญาณของไทย"
        },
        "market": {
            "en": "Experience authentic Thai market culture with local foods, crafts, and traditional commerce.",
            "th": "สัมผัสวัฒนธรรมตลาดไทยแท้พร้อมอาหารท้องถิ่น หัตถกรรม และการค้าแบบดั้งเดิม"
        },
        "beach": {
            "en": "Relax at this stunning beach with soft sand and crystal-clear tropical waters.",
            "th": "ผ่อนคลายที่ชายหาดที่น่าทึ่งแห่งนี้พร้อมทรายนุ่มและน้ำเขตร้อนใสคริสตัล"
        },
        "restaurant": {
            "en": "Discover authentic Thai flavors and culinary traditions at this local dining establishment.",
            "th": "ค้นพบรสชาติไทยแท้และประเพณีการทำอาหารที่สถานที่รับประทานอาหารท้องถิ่นแห่งนี้"
        }
    }
    
    category = location_info.get("category", "general")
    base_description = category_descriptions.get(category, {}).get(language, "A wonderful Thai destination!")
    
    return {
        "en": f"{location_info['description']['en']} {base_description}",
        "th": f"{location_info['description']['th']} {category_descriptions.get(category, {}).get('th', 'สถานที่ท่องเที่ยวไทยที่วิเศษ!')}"
    }

async def broadcast_ai_action(action_data: Dict):
    """Broadcast AI action to all connected users"""
    message = {
        "type": "ai_action",
        "data": action_data
    }
    await broadcast_message(message)

async def broadcast_user_update():
    """Broadcast user count update to all connected users"""
    message = {
        "type": "user_update",
        "user_count": len(active_users),
        "users": [user.dict() for user in active_users.values()]
    }
    await broadcast_message(message)

async def broadcast_message(message: Dict):
    """Broadcast message to all connected WebSocket clients"""
    if not active_connections:
        return
    
    # Send to all active connections
    disconnected_users = []
    for user_id, websocket in active_connections.items():
        try:
            await websocket.send_text(json.dumps(message))
        except Exception as e:
            logger.error(f"Error sending message to user {user_id}: {str(e)}")
            disconnected_users.append(user_id)
    
    # Clean up disconnected users
    for user_id in disconnected_users:
        if user_id in active_connections:
            del active_connections[user_id]
        if user_id in active_users:
            del active_users[user_id]

async def handle_ai_request(user_id: str, message: Dict):
    """Handle AI interaction requests from users"""
    try:
        request_type = message.get("request_type")
        
        if request_type == "navigate":
            # User requesting AI to navigate to location
            location_id = message.get("location_id")
            if location_id in TOURIST_LOCATIONS:
                action = AIAction(
                    type="navigate",
                    target_location=location_id,
                    language=message.get("language", "en")
                )
                await navigate_ai_to_location(action)
        
        elif request_type == "action":
            # User requesting AI action
            action_type = message.get("action_type", "greet")
            action = AIAction(
                type=action_type,
                language=message.get("language", "en")
            )
            await execute_ai_action(action)
            
    except Exception as e:
        logger.error(f"Error handling AI request from user {user_id}: {str(e)}")

# Health check endpoint
@router.get("/health")
async def health_check():
    """Health check for 3D world service"""
    return {
        "status": "healthy",
        "active_users": len(active_users),
        "active_connections": len(active_connections),
        "ai_position": ai_current_position.dict(),
        "locations_available": len(TOURIST_LOCATIONS)
    }

def create_3d_world_routes():
    """Factory function to create and configure 3D world routes"""
    return router