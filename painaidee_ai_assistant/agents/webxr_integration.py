"""
Test WebXR integration for gesture recognition
"""

import asyncio
import json
import logging
from typing import Dict, Any

logger = logging.getLogger(__name__)

class WebXRGestureIntegration:
    """Integration layer for WebXR gesture recognition"""
    
    def __init__(self):
        self.session_active = False
        self.hand_tracking_supported = False
        self.current_session_type = None  # 'vr' or 'ar'
        
    async def init_webxr_session(self, session_type: str) -> Dict[str, Any]:
        """Initialize WebXR session with hand tracking"""
        try:
            # Mock WebXR session initialization
            self.session_active = True
            self.current_session_type = session_type
            self.hand_tracking_supported = True
            
            return {
                "success": True,
                "session_type": session_type,
                "hand_tracking_supported": self.hand_tracking_supported,
                "features": {
                    "hand_tracking": True,
                    "gesture_recognition": True,
                    "3d_interaction": True,
                    "real_time_processing": True
                }
            }
            
        except Exception as e:
            logger.error(f"WebXR session init error: {e}")
            return {
                "success": False,
                "error": str(e)
            }
    
    async def process_webxr_hand_data(self, hand_data: Dict[str, Any]) -> Dict[str, Any]:
        """Process WebXR hand tracking data"""
        try:
            if not self.session_active:
                return {
                    "success": False,
                    "error": "No active WebXR session"
                }
            
            # Extract hand joints from WebXR data
            joints = hand_data.get("joints", [])
            if not joints:
                return {
                    "success": False,
                    "error": "No hand joints data"
                }
            
            # Convert WebXR joints to our landmark format
            landmarks = self._convert_webxr_joints_to_landmarks(joints)
            
            # Simulate gesture recognition
            gesture_result = {
                "gesture_type": "pointing",
                "confidence": 0.85,
                "hand_type": hand_data.get("handedness", "Right"),
                "landmarks": landmarks,
                "world_position": hand_data.get("position", [0, 0, 0]),
                "world_rotation": hand_data.get("rotation", [0, 0, 0, 1]),
                "timestamp": hand_data.get("timestamp", 0)
            }
            
            return {
                "success": True,
                "gesture_result": gesture_result,
                "session_type": self.current_session_type,
                "processing_time_ms": 15.5
            }
            
        except Exception as e:
            logger.error(f"WebXR hand data processing error: {e}")
            return {
                "success": False,
                "error": str(e)
            }
    
    def _convert_webxr_joints_to_landmarks(self, joints: list) -> list:
        """Convert WebXR joint data to our landmark format"""
        # WebXR provides 25 joints, we need to map to our 21 landmarks
        landmarks = []
        
        # Mapping WebXR joints to MediaPipe landmarks
        webxr_to_mediapipe = {
            0: 0,   # Wrist
            1: 1,   # Thumb CMC
            2: 2,   # Thumb MCP  
            3: 3,   # Thumb IP
            4: 4,   # Thumb Tip
            5: 5,   # Index MCP
            6: 6,   # Index PIP
            7: 7,   # Index DIP
            8: 8,   # Index Tip
            9: 9,   # Middle MCP
            10: 10, # Middle PIP
            11: 11, # Middle DIP
            12: 12, # Middle Tip
            13: 13, # Ring MCP
            14: 14, # Ring PIP
            15: 15, # Ring DIP
            16: 16, # Ring Tip
            17: 17, # Pinky MCP
            18: 18, # Pinky PIP
            19: 19, # Pinky DIP
            20: 20, # Pinky Tip
        }
        
        for mediapipe_idx in range(21):
            if mediapipe_idx in webxr_to_mediapipe.values():
                webxr_idx = [k for k, v in webxr_to_mediapipe.items() if v == mediapipe_idx][0]
                if webxr_idx < len(joints):
                    joint = joints[webxr_idx]
                    landmarks.append({
                        "x": joint.get("x", 0.0),
                        "y": joint.get("y", 0.0), 
                        "z": joint.get("z", 0.0),
                        "visibility": 1.0,
                        "landmark_id": mediapipe_idx,
                        "landmark_name": f"landmark_{mediapipe_idx}"
                    })
                else:
                    # Default landmark if not available
                    landmarks.append({
                        "x": 0.0, "y": 0.0, "z": 0.0,
                        "visibility": 0.0,
                        "landmark_id": mediapipe_idx,
                        "landmark_name": f"landmark_{mediapipe_idx}"
                    })
            else:
                # Default landmark
                landmarks.append({
                    "x": 0.0, "y": 0.0, "z": 0.0,
                    "visibility": 0.0,
                    "landmark_id": mediapipe_idx,
                    "landmark_name": f"landmark_{mediapipe_idx}"
                })
        
        return landmarks
    
    async def end_webxr_session(self) -> Dict[str, Any]:
        """End WebXR session"""
        try:
            self.session_active = False
            self.hand_tracking_supported = False
            self.current_session_type = None
            
            return {
                "success": True,
                "message": "WebXR session ended"
            }
            
        except Exception as e:
            logger.error(f"WebXR session end error: {e}")
            return {
                "success": False,
                "error": str(e)
            }

# Global WebXR integration instance
webxr_integration = WebXRGestureIntegration()

# Test the integration
async def test_webxr_integration():
    """Test WebXR gesture integration"""
    print("Testing WebXR Gesture Integration...")
    
    # Initialize VR session
    vr_result = await webxr_integration.init_webxr_session("vr")
    print(f"VR Session Init: {vr_result}")
    
    # Mock hand tracking data
    hand_data = {
        "handedness": "Right",
        "position": [0.1, 0.2, -0.5],
        "rotation": [0, 0, 0, 1],
        "timestamp": 1234567890.123,
        "joints": [
            {"x": 0.0, "y": 0.0, "z": 0.0},  # Wrist
            {"x": 0.1, "y": 0.0, "z": 0.0},  # Thumb CMC
            {"x": 0.15, "y": 0.0, "z": 0.0}, # Thumb MCP
            {"x": 0.2, "y": 0.0, "z": 0.0},  # Thumb IP
            {"x": 0.25, "y": 0.0, "z": 0.0}, # Thumb Tip
            {"x": 0.05, "y": 0.1, "z": 0.0}, # Index MCP
            {"x": 0.05, "y": 0.15, "z": 0.0}, # Index PIP
            {"x": 0.05, "y": 0.2, "z": 0.0}, # Index DIP
            {"x": 0.05, "y": 0.25, "z": 0.0}, # Index Tip
            # ... continue for other joints
        ] + [{"x": 0.0, "y": 0.0, "z": 0.0} for _ in range(12)]  # Fill remaining joints
    }
    
    # Process hand data
    gesture_result = await webxr_integration.process_webxr_hand_data(hand_data)
    print(f"Gesture Recognition: {gesture_result}")
    
    # End session
    end_result = await webxr_integration.end_webxr_session()
    print(f"Session End: {end_result}")

if __name__ == "__main__":
    asyncio.run(test_webxr_integration())