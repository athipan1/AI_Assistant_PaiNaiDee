"""
Enhanced 3D Gesture Recognition Agent
Implements real-time hand tracking with 21+ keypoints detection and ML-based gesture classification
"""

import cv2
import numpy as np
import mediapipe as mp
import logging
from typing import Dict, List, Optional, Tuple, Any
from dataclasses import dataclass
from enum import Enum
import json
import pickle
import os
from pathlib import Path
import time
import asyncio
from concurrent.futures import ThreadPoolExecutor

logger = logging.getLogger(__name__)

class HandLandmarks(Enum):
    """MediaPipe hand landmark indices"""
    WRIST = 0
    THUMB_CMC = 1
    THUMB_MCP = 2
    THUMB_IP = 3
    THUMB_TIP = 4
    INDEX_FINGER_MCP = 5
    INDEX_FINGER_PIP = 6
    INDEX_FINGER_DIP = 7
    INDEX_FINGER_TIP = 8
    MIDDLE_FINGER_MCP = 9
    MIDDLE_FINGER_PIP = 10
    MIDDLE_FINGER_DIP = 11
    MIDDLE_FINGER_TIP = 12
    RING_FINGER_MCP = 13
    RING_FINGER_PIP = 14
    RING_FINGER_DIP = 15
    RING_FINGER_TIP = 16
    PINKY_MCP = 17
    PINKY_PIP = 18
    PINKY_DIP = 19
    PINKY_TIP = 20

class GestureType(Enum):
    """Enhanced gesture types for 3D interaction"""
    # Basic gestures
    OPEN_HAND = "open_hand"
    CLOSED_FIST = "closed_fist"
    POINTING = "pointing"
    THUMBS_UP = "thumbs_up"
    THUMBS_DOWN = "thumbs_down"
    PEACE_SIGN = "peace_sign"
    OK_SIGN = "ok_sign"
    
    # Navigation gestures
    SWIPE_LEFT = "swipe_left"
    SWIPE_RIGHT = "swipe_right"
    SWIPE_UP = "swipe_up"
    SWIPE_DOWN = "swipe_down"
    GRAB = "grab"
    RELEASE = "release"
    PINCH = "pinch"
    SPREAD = "spread"
    
    # 3D manipulation gestures
    ROTATE_CLOCKWISE = "rotate_clockwise"
    ROTATE_COUNTERCLOCKWISE = "rotate_counterclockwise"
    ZOOM_IN = "zoom_in"
    ZOOM_OUT = "zoom_out"
    SELECT = "select"
    DESELECT = "deselect"
    
    # Custom gestures
    CUSTOM = "custom"
    UNKNOWN = "unknown"

@dataclass
class HandKeypoint:
    """3D hand keypoint data"""
    x: float
    y: float
    z: float
    visibility: float
    landmark_id: int
    landmark_name: str

@dataclass
class GestureResult:
    """Gesture recognition result"""
    gesture_type: GestureType
    confidence: float
    hand_landmarks: List[HandKeypoint]
    bounding_box: Tuple[float, float, float, float]  # x, y, width, height
    timestamp: float
    processing_time_ms: float
    hand_type: str  # "Left" or "Right"
    gesture_data: Dict[str, Any]  # Additional gesture-specific data

@dataclass
class CustomGesture:
    """Custom user-defined gesture"""
    name: str
    gesture_id: str
    landmarks_sequence: List[List[HandKeypoint]]
    confidence_threshold: float
    description: str
    created_timestamp: float
    training_samples: int

class GestureRecognitionAgent:
    """Enhanced 3D gesture recognition with real-time hand tracking"""
    
    def __init__(self, model_confidence=0.7, tracking_confidence=0.7):
        """
        Initialize the gesture recognition agent
        
        Args:
            model_confidence: Minimum confidence for hand detection
            tracking_confidence: Minimum confidence for hand tracking
        """
        self.mp_hands = mp.solutions.hands
        self.mp_draw = mp.solutions.drawing_utils
        self.mp_drawing_styles = mp.solutions.drawing_styles
        
        # Initialize MediaPipe hands
        self.hands = self.mp_hands.Hands(
            static_image_mode=False,
            max_num_hands=2,
            min_detection_confidence=model_confidence,
            min_tracking_confidence=tracking_confidence,
            model_complexity=1
        )
        
        # Performance tracking
        self.processing_times = []
        self.max_processing_times = 100
        
        # Custom gesture storage
        self.custom_gestures_dir = Path("cache/custom_gestures")
        self.custom_gestures_dir.mkdir(parents=True, exist_ok=True)
        self.custom_gestures: Dict[str, CustomGesture] = {}
        self.load_custom_gestures()
        
        # Gesture history for sequence detection
        self.gesture_history = []
        self.max_history_length = 10
        
        # Threading for performance
        self.executor = ThreadPoolExecutor(max_workers=2)
        
        logger.info("Enhanced 3D Gesture Recognition Agent initialized")
    
    def detect_hand_landmarks(self, image: np.ndarray) -> Dict[str, Any]:
        """
        Detect hand landmarks from image
        
        Args:
            image: Input image as numpy array (RGB format)
            
        Returns:
            Dictionary containing detection results
        """
        start_time = time.time()
        
        # Convert BGR to RGB if needed
        if len(image.shape) == 3 and image.shape[2] == 3:
            rgb_image = cv2.cvtColor(image, cv2.COLOR_BGR2RGB)
        else:
            rgb_image = image
        
        # Process the image
        results = self.hands.process(rgb_image)
        
        processing_time = (time.time() - start_time) * 1000
        self._update_processing_times(processing_time)
        
        detected_hands = []
        
        if results.multi_hand_landmarks:
            for hand_idx, (hand_landmarks, handedness) in enumerate(
                zip(results.multi_hand_landmarks, results.multi_handedness)
            ):
                # Extract hand keypoints
                keypoints = []
                for landmark_idx, landmark in enumerate(hand_landmarks.landmark):
                    keypoint = HandKeypoint(
                        x=landmark.x,
                        y=landmark.y,
                        z=landmark.z,
                        visibility=getattr(landmark, 'visibility', 1.0),
                        landmark_id=landmark_idx,
                        landmark_name=list(HandLandmarks)[landmark_idx].name
                    )
                    keypoints.append(keypoint)
                
                # Calculate bounding box
                x_coords = [kp.x for kp in keypoints]
                y_coords = [kp.y for kp in keypoints]
                bbox = (
                    min(x_coords),
                    min(y_coords),
                    max(x_coords) - min(x_coords),
                    max(y_coords) - min(y_coords)
                )
                
                hand_data = {
                    'keypoints': keypoints,
                    'bounding_box': bbox,
                    'handedness': handedness.classification[0].label,
                    'handedness_confidence': handedness.classification[0].score
                }
                detected_hands.append(hand_data)
        
        return {
            'hands': detected_hands,
            'processing_time_ms': processing_time,
            'timestamp': time.time(),
            'image_shape': image.shape
        }
    
    def classify_gesture(self, hand_keypoints: List[HandKeypoint]) -> GestureResult:
        """
        Classify gesture from hand keypoints
        
        Args:
            hand_keypoints: List of hand keypoints
            
        Returns:
            GestureResult with classification
        """
        start_time = time.time()
        
        # Extract finger positions for gesture classification
        gesture_features = self._extract_gesture_features(hand_keypoints)
        
        # Classify basic gestures
        gesture_type, confidence = self._classify_basic_gesture(gesture_features)
        
        # Check custom gestures
        custom_gesture_result = self._check_custom_gestures(hand_keypoints)
        if custom_gesture_result and custom_gesture_result[1] > confidence:
            gesture_type, confidence = custom_gesture_result
        
        processing_time = (time.time() - start_time) * 1000
        
        # Calculate bounding box
        x_coords = [kp.x for kp in hand_keypoints]
        y_coords = [kp.y for kp in hand_keypoints]
        bbox = (
            min(x_coords),
            min(y_coords),
            max(x_coords) - min(x_coords),
            max(y_coords) - min(y_coords)
        )
        
        result = GestureResult(
            gesture_type=gesture_type,
            confidence=confidence,
            hand_landmarks=hand_keypoints,
            bounding_box=bbox,
            timestamp=time.time(),
            processing_time_ms=processing_time,
            hand_type="Unknown",  # Will be updated by caller
            gesture_data=gesture_features
        )
        
        return result
    
    def _extract_gesture_features(self, keypoints: List[HandKeypoint]) -> Dict[str, Any]:
        """Extract features for gesture classification"""
        if len(keypoints) != 21:
            return {}
        
        # Convert to numpy array for easier processing
        points = np.array([[kp.x, kp.y, kp.z] for kp in keypoints])
        
        # Finger tip and base indices
        finger_tips = [4, 8, 12, 16, 20]  # Thumb, Index, Middle, Ring, Pinky
        finger_bases = [2, 5, 9, 13, 17]
        
        # Calculate finger extensions
        finger_extensions = []
        for tip_idx, base_idx in zip(finger_tips, finger_bases):
            tip = points[tip_idx]
            base = points[base_idx]
            extension = np.linalg.norm(tip - base)
            finger_extensions.append(extension)
        
        # Calculate angles between fingers
        finger_angles = []
        for i in range(len(finger_tips) - 1):
            v1 = points[finger_tips[i]] - points[0]  # Vector from wrist to finger tip
            v2 = points[finger_tips[i + 1]] - points[0]
            angle = np.arccos(np.clip(np.dot(v1, v2) / (np.linalg.norm(v1) * np.linalg.norm(v2)), -1.0, 1.0))
            finger_angles.append(angle)
        
        # Hand orientation (palm normal)
        palm_points = [points[0], points[5], points[9], points[13], points[17]]
        palm_center = np.mean(palm_points, axis=0)
        
        return {
            'finger_extensions': finger_extensions,
            'finger_angles': finger_angles,
            'palm_center': palm_center.tolist(),
            'hand_openness': np.mean(finger_extensions),
            'wrist_position': points[0].tolist(),
            'finger_spread': np.std(finger_angles) if finger_angles else 0
        }
    
    def _classify_basic_gesture(self, features: Dict[str, Any]) -> Tuple[GestureType, float]:
        """Classify basic gestures using heuristic rules"""
        if not features:
            return GestureType.UNKNOWN, 0.0
        
        finger_extensions = features.get('finger_extensions', [])
        finger_angles = features.get('finger_angles', [])
        hand_openness = features.get('hand_openness', 0)
        finger_spread = features.get('finger_spread', 0)
        
        if len(finger_extensions) != 5:
            return GestureType.UNKNOWN, 0.0
        
        # Normalize finger extensions
        max_extension = max(finger_extensions) if finger_extensions else 1.0
        normalized_extensions = [ext / max_extension for ext in finger_extensions]
        
        # Define gesture patterns
        open_hand_threshold = 0.7
        closed_fist_threshold = 0.3
        pointing_threshold = 0.6
        
        # Open hand detection
        if all(ext > open_hand_threshold for ext in normalized_extensions):
            confidence = min(normalized_extensions) + finger_spread * 0.2
            return GestureType.OPEN_HAND, min(confidence, 1.0)
        
        # Closed fist detection
        if all(ext < closed_fist_threshold for ext in normalized_extensions):
            confidence = 1.0 - max(normalized_extensions)
            return GestureType.CLOSED_FIST, min(confidence, 1.0)
        
        # Pointing gesture (index finger extended, others closed)
        if (normalized_extensions[1] > pointing_threshold and 
            all(ext < closed_fist_threshold for i, ext in enumerate(normalized_extensions) if i != 1)):
            confidence = normalized_extensions[1] - max(ext for i, ext in enumerate(normalized_extensions) if i != 1)
            return GestureType.POINTING, min(confidence, 1.0)
        
        # Thumbs up (thumb extended, others closed)
        if (normalized_extensions[0] > pointing_threshold and 
            all(ext < closed_fist_threshold for i, ext in enumerate(normalized_extensions) if i != 0)):
            confidence = normalized_extensions[0] - max(ext for i, ext in enumerate(normalized_extensions) if i != 0)
            return GestureType.THUMBS_UP, min(confidence, 1.0)
        
        # Peace sign (index and middle finger extended)
        if (normalized_extensions[1] > pointing_threshold and 
            normalized_extensions[2] > pointing_threshold and
            all(ext < closed_fist_threshold for i, ext in enumerate(normalized_extensions) if i not in [1, 2])):
            confidence = min(normalized_extensions[1], normalized_extensions[2])
            return GestureType.PEACE_SIGN, min(confidence, 1.0)
        
        # OK sign (thumb and index finger form circle, others extended)
        thumb_index_distance = abs(normalized_extensions[0] - normalized_extensions[1])
        if (thumb_index_distance < 0.3 and 
            all(ext > open_hand_threshold for i, ext in enumerate(normalized_extensions) if i > 1)):
            confidence = 1.0 - thumb_index_distance
            return GestureType.OK_SIGN, min(confidence, 1.0)
        
        return GestureType.UNKNOWN, 0.1
    
    def _check_custom_gestures(self, keypoints: List[HandKeypoint]) -> Optional[Tuple[GestureType, float]]:
        """Check against custom trained gestures"""
        # Implement custom gesture matching logic
        # This would compare current keypoints against stored custom gesture patterns
        # For now, return None (no custom gesture detected)
        return None
    
    def add_custom_gesture(self, name: str, keypoints_sequence: List[List[HandKeypoint]], 
                          description: str = "", confidence_threshold: float = 0.8) -> str:
        """
        Add a new custom gesture
        
        Args:
            name: Gesture name
            keypoints_sequence: Sequence of hand keypoint frames
            description: Gesture description
            confidence_threshold: Minimum confidence for detection
            
        Returns:
            Gesture ID
        """
        gesture_id = f"custom_{len(self.custom_gestures)}_{int(time.time())}"
        
        custom_gesture = CustomGesture(
            name=name,
            gesture_id=gesture_id,
            landmarks_sequence=keypoints_sequence,
            confidence_threshold=confidence_threshold,
            description=description,
            created_timestamp=time.time(),
            training_samples=len(keypoints_sequence)
        )
        
        self.custom_gestures[gesture_id] = custom_gesture
        self.save_custom_gesture(custom_gesture)
        
        logger.info(f"Added custom gesture: {name} (ID: {gesture_id})")
        return gesture_id
    
    def save_custom_gesture(self, gesture: CustomGesture):
        """Save custom gesture to disk"""
        filepath = self.custom_gestures_dir / f"{gesture.gesture_id}.pkl"
        with open(filepath, 'wb') as f:
            pickle.dump(gesture, f)
    
    def load_custom_gestures(self):
        """Load custom gestures from disk"""
        if not self.custom_gestures_dir.exists():
            return
        
        for gesture_file in self.custom_gestures_dir.glob("*.pkl"):
            try:
                with open(gesture_file, 'rb') as f:
                    gesture = pickle.load(f)
                    self.custom_gestures[gesture.gesture_id] = gesture
                    logger.info(f"Loaded custom gesture: {gesture.name}")
            except Exception as e:
                logger.error(f"Error loading custom gesture {gesture_file}: {e}")
    
    def get_custom_gestures(self) -> List[Dict[str, Any]]:
        """Get list of custom gestures"""
        return [
            {
                'id': gesture.gesture_id,
                'name': gesture.name,
                'description': gesture.description,
                'training_samples': gesture.training_samples,
                'confidence_threshold': gesture.confidence_threshold,
                'created_timestamp': gesture.created_timestamp
            }
            for gesture in self.custom_gestures.values()
        ]
    
    def process_video_frame(self, frame: np.ndarray) -> Dict[str, Any]:
        """
        Process a single video frame for gesture recognition
        
        Args:
            frame: Video frame as numpy array
            
        Returns:
            Dictionary containing all detected gestures and performance metrics
        """
        start_time = time.time()
        
        # Detect hand landmarks
        detection_result = self.detect_hand_landmarks(frame)
        
        gesture_results = []
        for hand_data in detection_result['hands']:
            # Classify gesture for each hand
            gesture_result = self.classify_gesture(hand_data['keypoints'])
            gesture_result.hand_type = hand_data['handedness']
            gesture_results.append(gesture_result)
        
        total_processing_time = (time.time() - start_time) * 1000
        
        return {
            'gesture_results': gesture_results,
            'detection_data': detection_result,
            'total_processing_time_ms': total_processing_time,
            'average_processing_time_ms': self.get_average_processing_time(),
            'frame_timestamp': time.time(),
            'performance_target_met': total_processing_time < 100  # <100ms target
        }
    
    def _update_processing_times(self, processing_time: float):
        """Update processing time history"""
        self.processing_times.append(processing_time)
        if len(self.processing_times) > self.max_processing_times:
            self.processing_times.pop(0)
    
    def get_average_processing_time(self) -> float:
        """Get average processing time"""
        return np.mean(self.processing_times) if self.processing_times else 0.0
    
    def get_performance_stats(self) -> Dict[str, Any]:
        """Get performance statistics"""
        if not self.processing_times:
            return {
                'average_ms': 0,
                'min_ms': 0,
                'max_ms': 0,
                'target_met_percentage': 0,
                'samples': 0
            }
        
        times = np.array(self.processing_times)
        target_met = np.sum(times < 100) / len(times) * 100
        
        return {
            'average_ms': float(np.mean(times)),
            'min_ms': float(np.min(times)),
            'max_ms': float(np.max(times)),
            'target_met_percentage': float(target_met),
            'samples': len(times)
        }
    
    def reset_performance_stats(self):
        """Reset performance statistics"""
        self.processing_times = []
    
    def __del__(self):
        """Cleanup resources"""
        try:
            if hasattr(self, 'hands'):
                self.hands.close()
            if hasattr(self, 'executor'):
                self.executor.shutdown(wait=False)
        except:
            pass

# Utility functions for gesture recognition
def landmarks_to_dict(landmarks: List[HandKeypoint]) -> List[Dict[str, Any]]:
    """Convert landmarks to dictionary format for JSON serialization"""
    return [
        {
            'x': lm.x,
            'y': lm.y,
            'z': lm.z,
            'visibility': lm.visibility,
            'landmark_id': lm.landmark_id,
            'landmark_name': lm.landmark_name
        }
        for lm in landmarks
    ]

def dict_to_landmarks(landmarks_dict: List[Dict[str, Any]]) -> List[HandKeypoint]:
    """Convert dictionary format back to landmarks"""
    return [
        HandKeypoint(
            x=lm['x'],
            y=lm['y'],
            z=lm['z'],
            visibility=lm['visibility'],
            landmark_id=lm['landmark_id'],
            landmark_name=lm['landmark_name']
        )
        for lm in landmarks_dict
    ]