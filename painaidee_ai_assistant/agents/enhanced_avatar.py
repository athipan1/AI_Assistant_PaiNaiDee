"""
Enhanced 3D Avatar System
Manages realistic facial expressions, eye gaze tracking, and lip syncing for Thai TTS
"""

import logging
import asyncio
import numpy as np
from typing import Dict, List, Optional, Tuple, Any
from dataclasses import dataclass
from enum import Enum
import json
import time
from pathlib import Path

from .emotion_analysis import EmotionAnalysisAgent, EmotionResult, FacialExpression, EyeGazeDirection

logger = logging.getLogger(__name__)

class AvatarAnimationState(Enum):
    """Avatar animation states"""
    IDLE = "idle"
    SPEAKING = "speaking"
    LISTENING = "listening"
    THINKING = "thinking"
    GESTURING = "gesturing"
    TRANSITIONING = "transitioning"

@dataclass
class EyeGazeData:
    """Eye gaze tracking data"""
    target_x: float  # -1.0 to 1.0 (left to right)
    target_y: float  # -1.0 to 1.0 (down to up)
    focus_intensity: float  # 0.0 to 1.0
    blink_rate: float  # blinks per second
    gaze_duration: float  # seconds to maintain gaze
    transition_speed: float  # speed of eye movement

@dataclass
class FacialAnimationData:
    """Facial expression animation data"""
    expression_type: FacialExpression
    intensity: float  # 0.0 to 1.0
    duration: float  # seconds
    transition_in: float  # transition in time
    transition_out: float  # transition out time
    blend_previous: bool  # blend with previous expression

@dataclass
class LipSyncFrame:
    """Single frame of lip sync animation"""
    timestamp: float
    mouth_open: float  # 0.0 to 1.0
    mouth_width: float  # 0.0 to 1.0
    tongue_position: float  # 0.0 to 1.0
    jaw_open: float  # 0.0 to 1.0
    phoneme: str
    viseme: str  # Visual phoneme

@dataclass
class AvatarAnimationFrame:
    """Complete avatar animation frame"""
    timestamp: float
    facial_animation: FacialAnimationData
    eye_gaze: EyeGazeData
    lip_sync: Optional[LipSyncFrame]
    gesture_state: str
    animation_state: AvatarAnimationState

class EnhancedAvatarSystem:
    """Enhanced 3D Avatar System with realistic animations"""
    
    def __init__(self):
        self.emotion_agent = EmotionAnalysisAgent()
        self.current_state = AvatarAnimationState.IDLE
        self.animation_queue = []
        self.current_frame = None
        
        # Initialize eye gaze patterns
        self.gaze_patterns = self._initialize_gaze_patterns()
        
        # Initialize facial expression library
        self.expression_library = self._initialize_expression_library()
        
        # Initialize Thai phoneme to viseme mapping
        self.thai_viseme_mapping = self._initialize_thai_visemes()
        
    def _initialize_gaze_patterns(self) -> Dict[str, EyeGazeData]:
        """Initialize different eye gaze patterns"""
        return {
            "natural_conversation": EyeGazeData(
                target_x=0.0, target_y=0.1,
                focus_intensity=0.8, blink_rate=0.3,
                gaze_duration=2.5, transition_speed=0.8
            ),
            "thinking": EyeGazeData(
                target_x=-0.3, target_y=0.4,
                focus_intensity=0.4, blink_rate=0.2,
                gaze_duration=1.8, transition_speed=0.5
            ),
            "excited_engagement": EyeGazeData(
                target_x=0.0, target_y=0.0,
                focus_intensity=1.0, blink_rate=0.4,
                gaze_duration=3.0, transition_speed=1.2
            ),
            "respectful_attention": EyeGazeData(
                target_x=0.0, target_y=-0.2,
                focus_intensity=0.9, blink_rate=0.25,
                gaze_duration=4.0, transition_speed=0.6
            ),
            "curious_exploration": EyeGazeData(
                target_x=0.2, target_y=0.3,
                focus_intensity=0.7, blink_rate=0.35,
                gaze_duration=1.5, transition_speed=1.0
            )
        }
    
    def _initialize_expression_library(self) -> Dict[FacialExpression, Dict[str, float]]:
        """Initialize facial expression parameters"""
        return {
            FacialExpression.SMILE_GENTLE: {
                "mouth_corner_lift": 0.4,
                "cheek_raise": 0.3,
                "eye_squint": 0.2,
                "eyebrow_lift": 0.1
            },
            FacialExpression.SMILE_BIG: {
                "mouth_corner_lift": 0.8,
                "cheek_raise": 0.7,
                "eye_squint": 0.4,
                "eyebrow_lift": 0.2
            },
            FacialExpression.SMILE_EXCITED: {
                "mouth_corner_lift": 0.9,
                "cheek_raise": 0.8,
                "eye_squint": 0.3,
                "eyebrow_lift": 0.6,
                "mouth_open": 0.3
            },
            FacialExpression.CONFUSED_SLIGHT: {
                "eyebrow_furrow": 0.3,
                "eyebrow_asymmetry": 0.4,
                "mouth_corner_down": 0.2,
                "head_tilt": 0.3
            },
            FacialExpression.CONFUSED_PUZZLED: {
                "eyebrow_furrow": 0.6,
                "eyebrow_asymmetry": 0.7,
                "mouth_corner_down": 0.3,
                "head_tilt": 0.5,
                "mouth_slightly_open": 0.2
            },
            FacialExpression.EXCITED_EYES_WIDE: {
                "eye_wide": 0.8,
                "eyebrow_lift": 0.7,
                "mouth_corner_lift": 0.6,
                "nostril_flare": 0.2
            },
            FacialExpression.WORRIED_SLIGHT: {
                "eyebrow_furrow": 0.4,
                "eyebrow_inner_up": 0.5,
                "mouth_corner_down": 0.3,
                "lip_press": 0.2
            },
            FacialExpression.CALM_PEACEFUL: {
                "eye_soft": 0.6,
                "mouth_neutral": 0.8,
                "jaw_relax": 0.7,
                "overall_relaxation": 0.9
            },
            FacialExpression.CONFIDENT_ASSURED: {
                "chin_up": 0.3,
                "eye_focus": 0.8,
                "mouth_slight_smile": 0.4,
                "posture_straight": 0.9
            }
        }
    
    def _initialize_thai_visemes(self) -> Dict[str, str]:
        """Initialize Thai phoneme to viseme mapping for lip sync"""
        return {
            # Thai consonants
            'ก': 'k_sound',     # velar stop
            'ข': 'k_aspirated', # aspirated velar
            'ค': 'k_sound',     # velar stop
            'ง': 'ng_sound',    # nasal
            'จ': 'ch_sound',    # affricate
            'ช': 'ch_aspirated',# aspirated affricate
            'ซ': 's_sound',     # fricative
            'ด': 'd_sound',     # dental stop
            'ต': 't_sound',     # dental stop
            'ท': 't_aspirated', # aspirated dental
            'น': 'n_sound',     # nasal
            'บ': 'b_sound',     # bilabial stop
            'ป': 'p_sound',     # bilabial stop
            'ผ': 'p_aspirated', # aspirated bilabial
            'ฝ': 'f_sound',     # fricative
            'พ': 'p_aspirated', # aspirated bilabial
            'ฟ': 'f_sound',     # fricative
            'ม': 'm_sound',     # bilabial nasal
            'ย': 'y_sound',     # approximant
            'ร': 'r_sound',     # trill
            'ล': 'l_sound',     # lateral
            'ว': 'w_sound',     # approximant
            'ส': 's_sound',     # fricative
            'ห': 'h_sound',     # fricative
            'อ': 'glottal_stop',# glottal stop
            
            # Thai vowels
            'า': 'aa_long',     # long a
            'ิ': 'i_short',     # short i
            'ี': 'ii_long',     # long i
            'ุ': 'u_short',     # short u
            'ู': 'uu_long',     # long u
            'เ': 'e_mid',       # mid e
            'แ': 'ae_open',     # open e
            'โ': 'o_close',     # close o
            'ใ': 'ai_diphthong',# diphthong
            'ไ': 'ai_diphthong',# diphthong
            'ำ': 'am_sound',    # am sound
            
            # English phonemes for mixed content
            'a': 'ah_sound',
            'e': 'eh_sound',
            'i': 'ih_sound',
            'o': 'oh_sound',
            'u': 'uh_sound'
        }
    
    async def generate_avatar_animation(self, emotion_result: EmotionResult, 
                                      text: str, language: str = "thai") -> List[AvatarAnimationFrame]:
        """
        Generate complete avatar animation sequence
        
        Args:
            emotion_result: Result from emotion analysis
            text: Text being spoken
            language: Language for lip sync
            
        Returns:
            List of animation frames for the avatar
        """
        try:
            # Generate facial animation
            facial_animation = self._generate_facial_animation(emotion_result.facial_expression)
            
            # Generate eye gaze sequence
            eye_gaze_sequence = self._generate_eye_gaze_sequence(
                emotion_result.eye_gaze_direction, 
                emotion_result.primary_emotion
            )
            
            # Generate lip sync animation
            lip_sync_sequence = await self._generate_lip_sync_sequence(
                emotion_result.lip_sync_data, text, language
            )
            
            # Combine into animation frames
            frames = self._combine_animation_elements(
                facial_animation, eye_gaze_sequence, lip_sync_sequence,
                emotion_result.suggested_gesture, emotion_result.gesture_context
            )
            
            return frames
            
        except Exception as e:
            logger.error(f"Failed to generate avatar animation: {e}")
            return self._create_fallback_animation()
    
    def _generate_facial_animation(self, expression: FacialExpression) -> FacialAnimationData:
        """Generate facial expression animation"""
        expression_params = self.expression_library.get(
            expression, self.expression_library[FacialExpression.NEUTRAL_RELAXED]
        )
        
        return FacialAnimationData(
            expression_type=expression,
            intensity=0.8,
            duration=2.0,
            transition_in=0.3,
            transition_out=0.5,
            blend_previous=True
        )
    
    def _generate_eye_gaze_sequence(self, gaze_direction: EyeGazeDirection, 
                                   emotion) -> List[EyeGazeData]:
        """Generate eye gaze animation sequence"""
        # Map gaze direction to pattern
        pattern_mapping = {
            EyeGazeDirection.LOOKING_AT_USER: "natural_conversation",
            EyeGazeDirection.LOOKING_AWAY_THOUGHTFUL: "thinking",
            EyeGazeDirection.LOOKING_UP: "curious_exploration",
            EyeGazeDirection.LOOKING_DOWN: "respectful_attention",
            EyeGazeDirection.FOLLOWING_GESTURE: "excited_engagement"
        }
        
        pattern_name = pattern_mapping.get(gaze_direction, "natural_conversation")
        base_gaze = self.gaze_patterns[pattern_name]
        
        # Create sequence with natural variations
        sequence = []
        total_duration = 3.0
        frame_duration = 0.1
        
        for i in range(int(total_duration / frame_duration)):
            # Add subtle natural variations
            variation_x = np.random.normal(0, 0.05)
            variation_y = np.random.normal(0, 0.03)
            
            gaze_frame = EyeGazeData(
                target_x=base_gaze.target_x + variation_x,
                target_y=base_gaze.target_y + variation_y,
                focus_intensity=base_gaze.focus_intensity,
                blink_rate=base_gaze.blink_rate,
                gaze_duration=frame_duration,
                transition_speed=base_gaze.transition_speed
            )
            sequence.append(gaze_frame)
        
        return sequence
    
    async def _generate_lip_sync_sequence(self, lip_sync_data: Optional[Dict[str, Any]], 
                                        text: str, language: str) -> List[LipSyncFrame]:
        """Generate lip sync animation frames"""
        if not lip_sync_data or not lip_sync_data.get('phoneme_sequence'):
            return self._create_basic_lip_sync(text)
        
        frames = []
        for phoneme_data in lip_sync_data['phoneme_sequence']:
            # Convert phoneme to viseme
            character = phoneme_data['character']
            viseme = self.thai_viseme_mapping.get(character, 'neutral')
            
            # Calculate mouth parameters based on viseme
            mouth_params = self._calculate_mouth_parameters(viseme)
            
            frame = LipSyncFrame(
                timestamp=phoneme_data['start_time'],
                mouth_open=mouth_params['mouth_open'],
                mouth_width=mouth_params['mouth_width'],
                tongue_position=mouth_params['tongue_position'],
                jaw_open=mouth_params['jaw_open'],
                phoneme=character,
                viseme=viseme
            )
            frames.append(frame)
        
        return frames
    
    def _calculate_mouth_parameters(self, viseme: str) -> Dict[str, float]:
        """Calculate mouth animation parameters for viseme"""
        viseme_params = {
            'neutral': {'mouth_open': 0.0, 'mouth_width': 0.5, 'tongue_position': 0.5, 'jaw_open': 0.0},
            'aa_long': {'mouth_open': 0.8, 'mouth_width': 0.7, 'tongue_position': 0.3, 'jaw_open': 0.6},
            'i_short': {'mouth_open': 0.2, 'mouth_width': 0.9, 'tongue_position': 0.8, 'jaw_open': 0.1},
            'ii_long': {'mouth_open': 0.3, 'mouth_width': 0.9, 'tongue_position': 0.8, 'jaw_open': 0.2},
            'u_short': {'mouth_open': 0.3, 'mouth_width': 0.2, 'tongue_position': 0.6, 'jaw_open': 0.2},
            'uu_long': {'mouth_open': 0.4, 'mouth_width': 0.1, 'tongue_position': 0.6, 'jaw_open': 0.3},
            'o_close': {'mouth_open': 0.5, 'mouth_width': 0.3, 'tongue_position': 0.4, 'jaw_open': 0.4},
            'm_sound': {'mouth_open': 0.0, 'mouth_width': 0.5, 'tongue_position': 0.5, 'jaw_open': 0.0},
            'b_sound': {'mouth_open': 0.0, 'mouth_width': 0.5, 'tongue_position': 0.5, 'jaw_open': 0.0},
            'p_sound': {'mouth_open': 0.1, 'mouth_width': 0.5, 'tongue_position': 0.5, 'jaw_open': 0.0},
            'f_sound': {'mouth_open': 0.2, 'mouth_width': 0.6, 'tongue_position': 0.3, 'jaw_open': 0.1},
            's_sound': {'mouth_open': 0.3, 'mouth_width': 0.8, 'tongue_position': 0.9, 'jaw_open': 0.1},
            't_sound': {'mouth_open': 0.2, 'mouth_width': 0.6, 'tongue_position': 0.9, 'jaw_open': 0.1},
            'd_sound': {'mouth_open': 0.3, 'mouth_width': 0.6, 'tongue_position': 0.9, 'jaw_open': 0.2},
            'k_sound': {'mouth_open': 0.4, 'mouth_width': 0.5, 'tongue_position': 0.1, 'jaw_open': 0.3},
            'g_sound': {'mouth_open': 0.4, 'mouth_width': 0.5, 'tongue_position': 0.1, 'jaw_open': 0.3},
            'ng_sound': {'mouth_open': 0.3, 'mouth_width': 0.5, 'tongue_position': 0.1, 'jaw_open': 0.2},
            'ch_sound': {'mouth_open': 0.4, 'mouth_width': 0.6, 'tongue_position': 0.7, 'jaw_open': 0.3},
            'r_sound': {'mouth_open': 0.4, 'mouth_width': 0.6, 'tongue_position': 0.8, 'jaw_open': 0.3},
            'l_sound': {'mouth_open': 0.3, 'mouth_width': 0.6, 'tongue_position': 0.9, 'jaw_open': 0.2},
            'w_sound': {'mouth_open': 0.4, 'mouth_width': 0.2, 'tongue_position': 0.4, 'jaw_open': 0.3},
            'y_sound': {'mouth_open': 0.2, 'mouth_width': 0.8, 'tongue_position': 0.8, 'jaw_open': 0.1},
            'h_sound': {'mouth_open': 0.5, 'mouth_width': 0.6, 'tongue_position': 0.3, 'jaw_open': 0.4}
        }
        
        return viseme_params.get(viseme, viseme_params['neutral'])
    
    def _create_basic_lip_sync(self, text: str) -> List[LipSyncFrame]:
        """Create basic lip sync animation as fallback"""
        frames = []
        duration_per_char = 0.1
        
        for i, char in enumerate(text):
            if char.isspace():
                continue
                
            # Basic mouth movement
            mouth_open = 0.3 + 0.2 * np.sin(i * 0.5)  # Natural variation
            
            frame = LipSyncFrame(
                timestamp=i * duration_per_char,
                mouth_open=mouth_open,
                mouth_width=0.6,
                tongue_position=0.5,
                jaw_open=mouth_open * 0.7,
                phoneme=char,
                viseme='generic'
            )
            frames.append(frame)
        
        return frames
    
    def _combine_animation_elements(self, facial_animation: FacialAnimationData,
                                  eye_gaze_sequence: List[EyeGazeData],
                                  lip_sync_sequence: List[LipSyncFrame],
                                  gesture_type: str,
                                  gesture_context: Dict[str, Any]) -> List[AvatarAnimationFrame]:
        """Combine all animation elements into synchronized frames"""
        frames = []
        max_duration = max(
            facial_animation.duration,
            len(eye_gaze_sequence) * 0.1,
            lip_sync_sequence[-1].timestamp if lip_sync_sequence else 0
        )
        
        total_frames = int(max_duration * 30)  # 30 FPS
        
        for frame_idx in range(total_frames):
            timestamp = frame_idx / 30.0
            
            # Get eye gaze for this timestamp
            gaze_idx = min(int(timestamp * 10), len(eye_gaze_sequence) - 1)
            current_gaze = eye_gaze_sequence[gaze_idx] if eye_gaze_sequence else self._default_gaze()
            
            # Get lip sync for this timestamp
            current_lip_sync = None
            for lip_frame in lip_sync_sequence:
                if abs(lip_frame.timestamp - timestamp) < 0.033:  # Within one frame
                    current_lip_sync = lip_frame
                    break
            
            # Determine animation state
            if current_lip_sync and current_lip_sync.mouth_open > 0.1:
                anim_state = AvatarAnimationState.SPEAKING
            elif timestamp < 0.5:
                anim_state = AvatarAnimationState.TRANSITIONING
            else:
                anim_state = AvatarAnimationState.IDLE
            
            frame = AvatarAnimationFrame(
                timestamp=timestamp,
                facial_animation=facial_animation,
                eye_gaze=current_gaze,
                lip_sync=current_lip_sync,
                gesture_state=gesture_type,
                animation_state=anim_state
            )
            frames.append(frame)
        
        return frames
    
    def _default_gaze(self) -> EyeGazeData:
        """Return default eye gaze data"""
        return self.gaze_patterns["natural_conversation"]
    
    def _create_fallback_animation(self) -> List[AvatarAnimationFrame]:
        """Create basic fallback animation"""
        return [
            AvatarAnimationFrame(
                timestamp=0.0,
                facial_animation=FacialAnimationData(
                    expression_type=FacialExpression.NEUTRAL_RELAXED,
                    intensity=0.5,
                    duration=1.0,
                    transition_in=0.2,
                    transition_out=0.2,
                    blend_previous=False
                ),
                eye_gaze=self._default_gaze(),
                lip_sync=None,
                gesture_state="neutral",
                animation_state=AvatarAnimationState.IDLE
            )
        ]
    
    def export_animation_data(self, frames: List[AvatarAnimationFrame]) -> Dict[str, Any]:
        """Export animation data for 3D viewer"""
        return {
            "total_frames": len(frames),
            "duration": frames[-1].timestamp if frames else 0,
            "fps": 30,
            "frames": [
                {
                    "timestamp": frame.timestamp,
                    "facial_expression": {
                        "type": frame.facial_animation.expression_type.value,
                        "intensity": frame.facial_animation.intensity
                    },
                    "eye_gaze": {
                        "target_x": frame.eye_gaze.target_x,
                        "target_y": frame.eye_gaze.target_y,
                        "focus_intensity": frame.eye_gaze.focus_intensity,
                        "blink_rate": frame.eye_gaze.blink_rate
                    },
                    "lip_sync": {
                        "mouth_open": frame.lip_sync.mouth_open if frame.lip_sync else 0,
                        "mouth_width": frame.lip_sync.mouth_width if frame.lip_sync else 0.5,
                        "jaw_open": frame.lip_sync.jaw_open if frame.lip_sync else 0
                    } if frame.lip_sync else None,
                    "animation_state": frame.animation_state.value
                }
                for frame in frames
            ]
        }