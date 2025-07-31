"""
WebXR/AR integration for the 3D World
Provides AR/VR capabilities for mobile and VR headsets
"""

from fastapi import APIRouter, HTTPException
from fastapi.responses import JSONResponse
from pydantic import BaseModel
from typing import Dict, List, Optional, Any
import json
import logging

logger = logging.getLogger(__name__)

# Router setup
router = APIRouter(prefix="/webxr", tags=["WebXR/AR"])

class XRSession(BaseModel):
    session_id: str
    mode: str  # "immersive-ar", "immersive-vr", "inline"
    user_id: str
    device_info: Optional[Dict[str, Any]] = None

class XRPose(BaseModel):
    position: Dict[str, float]  # x, y, z
    orientation: Dict[str, float]  # x, y, z, w quaternion
    timestamp: float

# Global XR sessions
active_xr_sessions: Dict[str, XRSession] = {}

@router.post("/session/start")
async def start_xr_session(session: XRSession):
    """Start a new WebXR session"""
    try:
        active_xr_sessions[session.session_id] = session
        
        # Configure session based on mode
        session_config = {
            "immersive-ar": {
                "required_features": ["local", "bounded-floor"],
                "optional_features": ["hand-tracking", "anchors", "plane-detection"],
                "reference_space": "local-floor"
            },
            "immersive-vr": {
                "required_features": ["local"],
                "optional_features": ["bounded-floor", "hand-tracking"],
                "reference_space": "local-floor"
            },
            "inline": {
                "required_features": [],
                "optional_features": ["viewer"],
                "reference_space": "viewer"
            }
        }
        
        config = session_config.get(session.mode, session_config["inline"])
        
        return {
            "status": "success",
            "session_id": session.session_id,
            "mode": session.mode,
            "config": config,
            "message": f"WebXR session started in {session.mode} mode"
        }
        
    except Exception as e:
        logger.error(f"Error starting XR session: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Failed to start XR session: {str(e)}")

@router.post("/session/end/{session_id}")
async def end_xr_session(session_id: str):
    """End a WebXR session"""
    try:
        if session_id in active_xr_sessions:
            del active_xr_sessions[session_id]
            
        return {
            "status": "success",
            "session_id": session_id,
            "message": "WebXR session ended"
        }
        
    except Exception as e:
        logger.error(f"Error ending XR session: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Failed to end XR session: {str(e)}")

@router.post("/pose/update")
async def update_xr_pose(session_id: str, pose: XRPose):
    """Update user pose in XR session"""
    try:
        if session_id not in active_xr_sessions:
            raise HTTPException(status_code=404, detail="XR session not found")
        
        # Here you would typically update the user's position in the 3D world
        # and synchronize with other users
        
        return {
            "status": "success",
            "session_id": session_id,
            "pose": pose.dict(),
            "timestamp": pose.timestamp
        }
        
    except Exception as e:
        logger.error(f"Error updating XR pose: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Failed to update XR pose: {str(e)}")

@router.get("/capabilities")
async def get_xr_capabilities():
    """Get WebXR capabilities and supported features"""
    return {
        "status": "success",
        "capabilities": {
            "supported_modes": ["immersive-ar", "immersive-vr", "inline"],
            "features": {
                "ar": {
                    "plane_detection": True,
                    "anchors": True,
                    "hit_testing": True,
                    "light_estimation": True,
                    "hand_tracking": True
                },
                "vr": {
                    "room_scale": True,
                    "hand_tracking": True,
                    "eye_tracking": False,
                    "bounded_floor": True
                }
            },
            "reference_spaces": ["viewer", "local", "local-floor", "bounded-floor", "unbounded"]
        }
    }

@router.get("/sessions/active")
async def get_active_xr_sessions():
    """Get list of active XR sessions"""
    return {
        "status": "success",
        "session_count": len(active_xr_sessions),
        "sessions": [session.dict() for session in active_xr_sessions.values()]
    }

def create_webxr_routes():
    """Factory function to create WebXR routes"""
    return router