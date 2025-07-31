"""
Multi-user 3D Collaboration API Routes
Provides WebSocket-based real-time collaboration for 3D scenes
"""

from fastapi import APIRouter, WebSocket, WebSocketDisconnect, HTTPException, Depends
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from pydantic import BaseModel
from typing import List, Dict, Any, Optional, Set
import logging
import json
import time
import uuid
from dataclasses import dataclass, asdict
from enum import Enum

logger = logging.getLogger(__name__)
security = HTTPBearer()

class MessageType(Enum):
    USER_JOIN = "user_join"
    USER_LEAVE = "user_leave" 
    AVATAR_MOVE = "avatar_move"
    GESTURE_PERFORM = "gesture_perform"
    CHAT_MESSAGE = "chat_message"
    VOICE_MESSAGE = "voice_message"
    MODEL_CHANGE = "model_change"
    SCENE_UPDATE = "scene_update"
    PING = "ping"
    PONG = "pong"

@dataclass
class User:
    """Represents a connected user"""
    user_id: str
    username: str
    avatar_color: str
    position: List[float] = None
    rotation: List[float] = None
    current_gesture: str = None
    last_activity: float = None
    
    def __post_init__(self):
        if self.position is None:
            self.position = [0, 0, 0]
        if self.rotation is None:
            self.rotation = [0, 0, 0]
        if self.last_activity is None:
            self.last_activity = time.time()

@dataclass
class CollaborationMessage:
    """WebSocket message structure"""
    type: MessageType
    user_id: str
    data: Dict[str, Any]
    timestamp: float = None
    room_id: str = None
    
    def __post_init__(self):
        if self.timestamp is None:
            self.timestamp = time.time()

class ConnectionManager:
    """Manages WebSocket connections for multi-user sessions"""
    
    def __init__(self):
        # Room ID -> Set of WebSocket connections
        self.active_connections: Dict[str, Set[WebSocket]] = {}
        # Room ID -> Dict of User ID -> User
        self.room_users: Dict[str, Dict[str, User]] = {}
        # WebSocket -> (room_id, user_id) mapping
        self.connection_mapping: Dict[WebSocket, tuple] = {}
        
    async def connect(self, websocket: WebSocket, room_id: str, user: User):
        """Connect user to a collaboration room"""
        await websocket.accept()
        
        # Initialize room if needed
        if room_id not in self.active_connections:
            self.active_connections[room_id] = set()
            self.room_users[room_id] = {}
        
        # Add connection and user
        self.active_connections[room_id].add(websocket)
        self.room_users[room_id][user.user_id] = user
        self.connection_mapping[websocket] = (room_id, user.user_id)
        
        # Notify other users of new user joining
        join_message = CollaborationMessage(
            type=MessageType.USER_JOIN,
            user_id=user.user_id,
            data={
                "username": user.username,
                "avatar_color": user.avatar_color,
                "position": user.position,
                "rotation": user.rotation
            },
            room_id=room_id
        )
        
        await self.broadcast_to_room(room_id, join_message, exclude_user=user.user_id)
        
        # Send current room state to new user
        room_state = {
            "users": [asdict(u) for u in self.room_users[room_id].values() if u.user_id != user.user_id],
            "room_id": room_id,
            "total_users": len(self.room_users[room_id])
        }
        
        await websocket.send_text(json.dumps({
            "type": "room_state",
            "data": room_state
        }))
        
        logger.info(f"User {user.user_id} joined room {room_id}")
    
    async def disconnect(self, websocket: WebSocket):
        """Disconnect user from collaboration room"""
        if websocket not in self.connection_mapping:
            return
        
        room_id, user_id = self.connection_mapping[websocket]
        
        # Remove connection
        self.active_connections[room_id].discard(websocket)
        del self.connection_mapping[websocket]
        
        # Remove user and notify others
        if user_id in self.room_users[room_id]:
            user = self.room_users[room_id][user_id]
            del self.room_users[room_id][user_id]
            
            leave_message = CollaborationMessage(
                type=MessageType.USER_LEAVE,
                user_id=user_id,
                data={"username": user.username},
                room_id=room_id
            )
            
            await self.broadcast_to_room(room_id, leave_message)
        
        # Clean up empty rooms
        if not self.active_connections[room_id]:
            del self.active_connections[room_id]
            del self.room_users[room_id]
        
        logger.info(f"User {user_id} left room {room_id}")
    
    async def broadcast_to_room(self, room_id: str, message: CollaborationMessage, exclude_user: str = None):
        """Broadcast message to all users in room"""
        if room_id not in self.active_connections:
            return
        
        message_data = asdict(message)
        message_json = json.dumps(message_data)
        
        # Send to all connections in room
        disconnected = []
        for websocket in self.active_connections[room_id].copy():
            try:
                # Skip excluded user
                if exclude_user and websocket in self.connection_mapping:
                    _, ws_user_id = self.connection_mapping[websocket]
                    if ws_user_id == exclude_user:
                        continue
                
                await websocket.send_text(message_json)
            except Exception as e:
                logger.error(f"Error broadcasting to websocket: {e}")
                disconnected.append(websocket)
        
        # Clean up disconnected websockets
        for ws in disconnected:
            await self.disconnect(ws)
    
    def get_room_users(self, room_id: str) -> List[User]:
        """Get all users in a room"""
        if room_id not in self.room_users:
            return []
        return list(self.room_users[room_id].values())
    
    def update_user_avatar(self, room_id: str, user_id: str, position: List[float], rotation: List[float]):
        """Update user avatar position and rotation"""
        if room_id in self.room_users and user_id in self.room_users[room_id]:
            user = self.room_users[room_id][user_id]
            user.position = position
            user.rotation = rotation
            user.last_activity = time.time()

# Global connection manager
connection_manager = ConnectionManager()

def create_multiuser_routes(app):
    """Add multi-user collaboration routes to FastAPI app"""
    
    @app.websocket("/ws/collaboration/{room_id}")
    async def websocket_collaboration(websocket: WebSocket, room_id: str):
        """WebSocket endpoint for real-time collaboration"""
        user = None
        try:
            # Wait for user authentication message
            auth_data = await websocket.receive_text()
            auth_message = json.loads(auth_data)
            
            if auth_message.get("type") != "auth":
                await websocket.close(code=4000, reason="Authentication required")
                return
            
            # Create user from auth data
            user_data = auth_message.get("user", {})
            user = User(
                user_id=user_data.get("user_id", str(uuid.uuid4())),
                username=user_data.get("username", "Anonymous"),
                avatar_color=user_data.get("avatar_color", "#4CAF50"),
                position=user_data.get("position", [0, 0, 0]),
                rotation=user_data.get("rotation", [0, 0, 0])
            )
            
            # Connect user to room
            await connection_manager.connect(websocket, room_id, user)
            
            # Message handling loop
            while True:
                try:
                    data = await websocket.receive_text()
                    message_data = json.loads(data)
                    
                    message_type = MessageType(message_data.get("type"))
                    
                    # Handle different message types
                    if message_type == MessageType.AVATAR_MOVE:
                        position = message_data.get("position", [0, 0, 0])
                        rotation = message_data.get("rotation", [0, 0, 0])
                        
                        connection_manager.update_user_avatar(room_id, user.user_id, position, rotation)
                        
                        move_message = CollaborationMessage(
                            type=MessageType.AVATAR_MOVE,
                            user_id=user.user_id,
                            data={
                                "position": position,
                                "rotation": rotation
                            },
                            room_id=room_id
                        )
                        await connection_manager.broadcast_to_room(room_id, move_message, exclude_user=user.user_id)
                    
                    elif message_type == MessageType.GESTURE_PERFORM:
                        gesture_data = message_data.get("gesture", {})
                        
                        gesture_message = CollaborationMessage(
                            type=MessageType.GESTURE_PERFORM,
                            user_id=user.user_id,
                            data={
                                "gesture_name": gesture_data.get("name", ""),
                                "gesture_type": gesture_data.get("type", ""),
                                "duration": gesture_data.get("duration", 2.0),
                                "cultural_context": gesture_data.get("cultural_context", "")
                            },
                            room_id=room_id
                        )
                        await connection_manager.broadcast_to_room(room_id, gesture_message, exclude_user=user.user_id)
                    
                    elif message_type == MessageType.CHAT_MESSAGE:
                        chat_data = message_data.get("message", {})
                        
                        chat_message = CollaborationMessage(
                            type=MessageType.CHAT_MESSAGE,
                            user_id=user.user_id,
                            data={
                                "text": chat_data.get("text", ""),
                                "username": user.username,
                                "language": chat_data.get("language", "en")
                            },
                            room_id=room_id
                        )
                        await connection_manager.broadcast_to_room(room_id, chat_message)
                    
                    elif message_type == MessageType.MODEL_CHANGE:
                        model_data = message_data.get("model", {})
                        
                        model_message = CollaborationMessage(
                            type=MessageType.MODEL_CHANGE,
                            user_id=user.user_id,
                            data={
                                "model_name": model_data.get("name", ""),
                                "model_format": model_data.get("format", ""),
                                "position": model_data.get("position", [0, 0, 0]),
                                "scale": model_data.get("scale", [1, 1, 1])
                            },
                            room_id=room_id
                        )
                        await connection_manager.broadcast_to_room(room_id, model_message)
                    
                    elif message_type == MessageType.PING:
                        # Respond with pong
                        await websocket.send_text(json.dumps({
                            "type": "pong",
                            "timestamp": time.time()
                        }))
                
                except WebSocketDisconnect:
                    break
                except json.JSONDecodeError:
                    logger.error("Invalid JSON received")
                    continue
                except ValueError as e:
                    logger.error(f"Invalid message type: {e}")
                    continue
                except Exception as e:
                    logger.error(f"Error handling WebSocket message: {e}")
                    continue
                    
        except WebSocketDisconnect:
            pass
        except Exception as e:
            logger.error(f"WebSocket error: {e}")
        finally:
            if user:
                await connection_manager.disconnect(websocket)
    
    @app.get("/api/collaboration/rooms")
    async def list_active_rooms():
        """List all active collaboration rooms"""
        try:
            rooms = []
            for room_id, users in connection_manager.room_users.items():
                room_info = {
                    "room_id": room_id,
                    "user_count": len(users),
                    "users": [
                        {
                            "user_id": user.user_id,
                            "username": user.username,
                            "avatar_color": user.avatar_color,
                            "last_activity": user.last_activity
                        }
                        for user in users.values()
                    ],
                    "created_time": min(user.last_activity for user in users.values()) if users else time.time()
                }
                rooms.append(room_info)
            
            return {
                "success": True,
                "rooms": rooms,
                "total_rooms": len(rooms),
                "total_users": sum(len(users) for users in connection_manager.room_users.values())
            }
        
        except Exception as e:
            logger.error(f"Error listing rooms: {e}")
            return {"success": False, "message": str(e)}
    
    @app.post("/api/collaboration/room/create")
    async def create_collaboration_room(request: dict):
        """Create a new collaboration room"""
        try:
            room_name = request.get("room_name", f"Room_{int(time.time())}")
            max_users = request.get("max_users", 10)
            is_private = request.get("is_private", False)
            room_settings = request.get("settings", {})
            
            room_id = str(uuid.uuid4())
            
            # Room settings
            default_settings = {
                "max_users": max_users,
                "is_private": is_private,
                "allow_voice": True,
                "allow_gestures": True,
                "thai_cultural_mode": True,
                "auto_translate": False,
                "scene_permissions": "all_users"  # who can change 3D models
            }
            
            room_settings.update(default_settings)
            
            return {
                "success": True,
                "room_id": room_id,
                "room_name": room_name,
                "websocket_url": f"/ws/collaboration/{room_id}",
                "settings": room_settings,
                "invite_link": f"/3d-collaboration?room={room_id}",
                "qr_code_url": f"/api/collaboration/room/{room_id}/qr"
            }
        
        except Exception as e:
            logger.error(f"Error creating room: {e}")
            return {"success": False, "message": str(e)}
    
    @app.get("/api/collaboration/room/{room_id}/info")
    async def get_room_info(room_id: str):
        """Get information about a specific room"""
        try:
            if room_id not in connection_manager.room_users:
                raise HTTPException(status_code=404, detail="Room not found")
            
            users = connection_manager.get_room_users(room_id)
            
            return {
                "success": True,
                "room_id": room_id,
                "user_count": len(users),
                "users": [
                    {
                        "user_id": user.user_id,
                        "username": user.username,
                        "avatar_color": user.avatar_color,
                        "position": user.position,
                        "rotation": user.rotation,
                        "current_gesture": user.current_gesture,
                        "last_activity": user.last_activity
                    }
                    for user in users
                ],
                "room_active": len(users) > 0
            }
        
        except HTTPException:
            raise
        except Exception as e:
            logger.error(f"Error getting room info: {e}")
            return {"success": False, "message": str(e)}

    logger.info("Multi-user collaboration API routes added")