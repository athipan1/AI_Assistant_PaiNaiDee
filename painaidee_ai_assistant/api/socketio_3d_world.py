"""
Socket.IO integration for 3D World multi-user support
Handles real-time communication between users in the 3D world
"""

import socketio
from fastapi import FastAPI
import asyncio
import json
import logging
from datetime import datetime
from typing import Dict, List, Any, Optional

logger = logging.getLogger(__name__)

# Create Socket.IO server
sio = socketio.AsyncServer(
    cors_allowed_origins="*",
    logger=True,
    engineio_logger=True
)

# Global state for 3D world users
connected_users: Dict[str, Dict[str, Any]] = {}
user_rooms: Dict[str, str] = {}  # user_id -> room_id
room_users: Dict[str, List[str]] = {}  # room_id -> [user_ids]
ai_states: Dict[str, Dict[str, Any]] = {}  # room_id -> ai_state

class World3DSocketManager:
    def __init__(self):
        self.sio = sio
        self.setup_events()
    
    def setup_events(self):
        """Setup Socket.IO event handlers"""
        
        @sio.event
        async def connect(sid, environ):
            """Handle user connection"""
            logger.info(f"User connected: {sid}")
            await sio.emit('connection_established', {
                'user_id': sid,
                'message': 'Connected to 3D World',
                'timestamp': datetime.now().isoformat()
            }, room=sid)
        
        @sio.event
        async def disconnect(sid):
            """Handle user disconnection"""
            logger.info(f"User disconnected: {sid}")
            
            # Remove user from room
            if sid in user_rooms:
                room_id = user_rooms[sid]
                if room_id in room_users and sid in room_users[room_id]:
                    room_users[room_id].remove(sid)
                    
                    # Notify other users in the room
                    await sio.emit('user_left', {
                        'user_id': sid,
                        'room_id': room_id,
                        'remaining_users': len(room_users[room_id]),
                        'timestamp': datetime.now().isoformat()
                    }, room=room_id)
                    
                    # Remove empty rooms
                    if len(room_users[room_id]) == 0:
                        del room_users[room_id]
                        if room_id in ai_states:
                            del ai_states[room_id]
                
                del user_rooms[sid]
            
            # Remove from connected users
            if sid in connected_users:
                del connected_users[sid]
        
        @sio.event
        async def join_3d_world(sid, data=None):
            """Handle user joining the 3D world"""
            try:
                # Extract user info
                user_data = data or {}
                username = user_data.get('username', f'User_{sid[:8]}')
                language = user_data.get('language', 'en')
                room_preference = user_data.get('room', 'default')
                
                # Add user to connected users
                connected_users[sid] = {
                    'user_id': sid,
                    'username': username,
                    'language': language,
                    'position': {'x': 0, 'y': 1, 'z': -5},
                    'joined_at': datetime.now().isoformat(),
                    'last_active': datetime.now().isoformat()
                }
                
                # Assign to room
                room_id = await self.assign_to_room(sid, room_preference)
                
                # Send room info to user
                await sio.emit('room_joined', {
                    'room_id': room_id,
                    'user_count': len(room_users.get(room_id, [])),
                    'ai_state': ai_states.get(room_id, self.get_default_ai_state()),
                    'other_users': [connected_users[uid] for uid in room_users.get(room_id, []) if uid != sid]
                }, room=sid)
                
                # Notify other users in the room
                await sio.emit('user_joined', {
                    'user': connected_users[sid],
                    'user_count': len(room_users[room_id]),
                    'timestamp': datetime.now().isoformat()
                }, room=room_id)
                
                logger.info(f"User {username} ({sid}) joined room {room_id}")
                
            except Exception as e:
                logger.error(f"Error in join_3d_world: {str(e)}")
                await sio.emit('error', {'message': str(e)}, room=sid)
        
        @sio.event
        async def ai_navigate_request(sid, data):
            """Handle AI navigation request from user"""
            try:
                if sid not in user_rooms:
                    await sio.emit('error', {'message': 'Not in a room'}, room=sid)
                    return
                
                room_id = user_rooms[sid]
                location_id = data.get('location_id')
                language = data.get('language', 'en')
                
                if not location_id:
                    await sio.emit('error', {'message': 'Location ID required'}, room=sid)
                    return
                
                # Update AI state for the room
                ai_state = ai_states.get(room_id, self.get_default_ai_state())
                ai_state['current_action'] = {
                    'type': 'navigate',
                    'target_location': location_id,
                    'requested_by': sid,
                    'language': language,
                    'timestamp': datetime.now().isoformat()
                }
                ai_states[room_id] = ai_state
                
                # Broadcast AI navigation to all users in the room
                await sio.emit('ai_navigation_started', {
                    'location_id': location_id,
                    'requested_by': connected_users[sid]['username'],
                    'language': language,
                    'ai_state': ai_state,
                    'timestamp': datetime.now().isoformat()
                }, room=room_id)
                
                logger.info(f"AI navigation to {location_id} requested by {sid} in room {room_id}")
                
            except Exception as e:
                logger.error(f"Error in ai_navigate_request: {str(e)}")
                await sio.emit('error', {'message': str(e)}, room=sid)
        
        @sio.event
        async def ai_action_request(sid, data):
            """Handle AI action request (greet, dance, etc.)"""
            try:
                if sid not in user_rooms:
                    await sio.emit('error', {'message': 'Not in a room'}, room=sid)
                    return
                
                room_id = user_rooms[sid]
                action_type = data.get('action_type', 'greet')
                language = data.get('language', 'en')
                
                # Update AI state
                ai_state = ai_states.get(room_id, self.get_default_ai_state())
                ai_state['current_action'] = {
                    'type': action_type,
                    'requested_by': sid,
                    'language': language,
                    'timestamp': datetime.now().isoformat()
                }
                ai_states[room_id] = ai_state
                
                # Broadcast AI action to all users in the room
                await sio.emit('ai_action_started', {
                    'action_type': action_type,
                    'requested_by': connected_users[sid]['username'],
                    'language': language,
                    'ai_state': ai_state,
                    'timestamp': datetime.now().isoformat()
                }, room=room_id)
                
                logger.info(f"AI action {action_type} requested by {sid} in room {room_id}")
                
            except Exception as e:
                logger.error(f"Error in ai_action_request: {str(e)}")
                await sio.emit('error', {'message': str(e)}, room=sid)
        
        @sio.event
        async def user_position_update(sid, data):
            """Handle user position updates"""
            try:
                if sid not in connected_users:
                    return
                
                # Update user position
                position = data.get('position', {'x': 0, 'y': 1, 'z': -5})
                connected_users[sid]['position'] = position
                connected_users[sid]['last_active'] = datetime.now().isoformat()
                
                # Broadcast to other users in the same room
                if sid in user_rooms:
                    room_id = user_rooms[sid]
                    await sio.emit('user_moved', {
                        'user_id': sid,
                        'username': connected_users[sid]['username'],
                        'position': position,
                        'timestamp': datetime.now().isoformat()
                    }, room=room_id, skip_sid=sid)
                
            except Exception as e:
                logger.error(f"Error in user_position_update: {str(e)}")
        
        @sio.event
        async def chat_message(sid, data):
            """Handle chat messages between users"""
            try:
                if sid not in connected_users or sid not in user_rooms:
                    return
                
                room_id = user_rooms[sid]
                message = data.get('message', '')
                language = data.get('language', 'en')
                
                if not message.strip():
                    return
                
                # Broadcast chat message to all users in the room
                await sio.emit('chat_message_received', {
                    'user_id': sid,
                    'username': connected_users[sid]['username'],
                    'message': message,
                    'language': language,
                    'timestamp': datetime.now().isoformat()
                }, room=room_id)
                
                logger.info(f"Chat message from {sid} in room {room_id}: {message}")
                
            except Exception as e:
                logger.error(f"Error in chat_message: {str(e)}")
        
        @sio.event
        async def get_room_status(sid, data=None):
            """Get current room status and user list"""
            try:
                if sid not in user_rooms:
                    await sio.emit('room_status', {'error': 'Not in a room'}, room=sid)
                    return
                
                room_id = user_rooms[sid]
                room_users_list = room_users.get(room_id, [])
                
                status = {
                    'room_id': room_id,
                    'user_count': len(room_users_list),
                    'users': [connected_users[uid] for uid in room_users_list if uid in connected_users],
                    'ai_state': ai_states.get(room_id, self.get_default_ai_state()),
                    'timestamp': datetime.now().isoformat()
                }
                
                await sio.emit('room_status', status, room=sid)
                
            except Exception as e:
                logger.error(f"Error in get_room_status: {str(e)}")
                await sio.emit('error', {'message': str(e)}, room=sid)
    
    async def assign_to_room(self, user_id: str, room_preference: str = 'default') -> str:
        """Assign user to a room (create new room if needed)"""
        room_id = room_preference
        
        # Initialize room if it doesn't exist
        if room_id not in room_users:
            room_users[room_id] = []
            ai_states[room_id] = self.get_default_ai_state()
        
        # Add user to room
        room_users[room_id].append(user_id)
        user_rooms[user_id] = room_id
        
        return room_id
    
    def get_default_ai_state(self) -> Dict[str, Any]:
        """Get default AI state for a new room"""
        return {
            'position': {'x': 0, 'y': 1, 'z': 0},
            'current_action': None,
            'last_location': None,
            'active_users': 0,
            'created_at': datetime.now().isoformat()
        }
    
    async def broadcast_ai_update(self, room_id: str, ai_update: Dict[str, Any]):
        """Broadcast AI state update to all users in a room"""
        try:
            await sio.emit('ai_state_update', ai_update, room=room_id)
        except Exception as e:
            logger.error(f"Error broadcasting AI update: {str(e)}")
    
    async def get_room_stats(self) -> Dict[str, Any]:
        """Get statistics about all rooms"""
        return {
            'total_rooms': len(room_users),
            'total_users': len(connected_users),
            'rooms': {
                room_id: {
                    'user_count': len(users),
                    'ai_state': ai_states.get(room_id, {}),
                    'users': [connected_users.get(uid, {}).get('username', uid) for uid in users]
                }
                for room_id, users in room_users.items()
            },
            'timestamp': datetime.now().isoformat()
        }

# Create global socket manager instance
socket_manager = World3DSocketManager()

def get_socket_app() -> socketio.ASGIApp:
    """Get Socket.IO ASGI app for integration with FastAPI"""
    return socketio.ASGIApp(sio)

def init_socketio_with_fastapi(app: FastAPI):
    """Initialize Socket.IO with FastAPI application"""
    # Mount Socket.IO app
    socket_app = get_socket_app()
    app.mount('/socket.io', socket_app)
    
    # Add Socket.IO endpoints
    @app.get("/3d_world/socket/stats")
    async def get_socket_stats():
        """Get Socket.IO connection statistics"""
        return await socket_manager.get_room_stats()
    
    @app.post("/3d_world/socket/broadcast")
    async def broadcast_to_room(room_id: str, message: Dict[str, Any]):
        """Broadcast message to specific room"""
        try:
            await sio.emit('server_broadcast', message, room=room_id)
            return {"status": "success", "room_id": room_id}
        except Exception as e:
            return {"status": "error", "message": str(e)}
    
    logger.info("Socket.IO initialized with FastAPI")
    return socket_manager

# Export the socket instance for use in other modules
__all__ = ['sio', 'socket_manager', 'get_socket_app', 'init_socketio_with_fastapi']