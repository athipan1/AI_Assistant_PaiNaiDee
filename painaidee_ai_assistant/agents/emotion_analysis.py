"""
Emotion Analysis Agent
Analyzes user sentiments and maps emotions to 3D model gestures and expressions
Uses BERT-based sentiment analysis for emotion detection
"""

import logging
from typing import Dict, List, Optional, Tuple, Any
import torch
from transformers import AutoTokenizer, AutoModelForSequenceClassification, pipeline
from dataclasses import dataclass
from enum import Enum
import asyncio
import json

logger = logging.getLogger(__name__)

class EmotionType(Enum):
    """Supported emotion types"""
    HAPPY = "happy"
    EXCITED = "excited"
    CALM = "calm"
    CURIOUS = "curious"
    FRUSTRATED = "frustrated"
    WORRIED = "worried"
    NEUTRAL = "neutral"
    CONFIDENT = "confident"
    ENTHUSIASTIC = "enthusiastic"

class GestureType(Enum):
    """3D model gesture types"""
    FRIENDLY_WAVE = "friendly_wave"
    EXCITED_JUMP = "excited_jump"
    CALM_STANDING = "calm_standing"
    THOUGHTFUL_POSE = "thoughtful_pose"
    REASSURING_GESTURE = "reassuring_gesture"
    WELCOMING_ARMS = "welcoming_arms"
    NEUTRAL_IDLE = "neutral_idle"
    CONFIDENT_POSE = "confident_pose"
    ENERGETIC_MOVEMENT = "energetic_movement"
    
    # Thai Cultural Gestures
    THAI_WAI = "thai_wai"           # Traditional Thai greeting with palms together
    THAI_SMILE = "thai_smile"       # Thai-style gentle smile with slight bow
    THAI_POINT = "thai_point"       # Thai-style pointing (with open hand, not finger)
    THAI_WELCOME = "thai_welcome"   # Traditional Thai welcoming gesture
    THAI_RESPECT = "thai_respect"   # Deep wai for showing respect
    THAI_BOW = "thai_bow"          # Traditional Thai bow
    
    # Context-aware AI Gestures
    POINTING_GESTURE = "pointing_gesture"       # AI-based pointing based on content
    EXPLAINING_GESTURE = "explaining_gesture"   # Hand movements for explanations
    EMPHASIZING_GESTURE = "emphasizing_gesture" # Emphasis gestures
    COUNTING_GESTURE = "counting_gesture"       # Counting with fingers

class FacialExpression(Enum):
    """Detailed facial expressions for 3D avatars"""
    SMILE_GENTLE = "smile_gentle"
    SMILE_BIG = "smile_big" 
    SMILE_EXCITED = "smile_excited"
    CONFUSED_SLIGHT = "confused_slight"
    CONFUSED_PUZZLED = "confused_puzzled"
    EXCITED_EYES_WIDE = "excited_eyes_wide"
    EXCITED_ANTICIPATION = "excited_anticipation"
    CALM_PEACEFUL = "calm_peaceful"
    CALM_CONTENT = "calm_content"
    WORRIED_SLIGHT = "worried_slight"
    WORRIED_CONCERNED = "worried_concerned"
    THOUGHTFUL_CONTEMPLATIVE = "thoughtful_contemplative"
    CONFIDENT_ASSURED = "confident_assured"
    NEUTRAL_RELAXED = "neutral_relaxed"

class EyeGazeDirection(Enum):
    """Eye gaze directions for realistic interaction"""
    LOOKING_AT_USER = "looking_at_user"
    LOOKING_LEFT = "looking_left"
    LOOKING_RIGHT = "looking_right"  
    LOOKING_UP = "looking_up"
    LOOKING_DOWN = "looking_down"
    LOOKING_AWAY_THOUGHTFUL = "looking_away_thoughtful"
    FOLLOWING_GESTURE = "following_gesture"

@dataclass
class EmotionResult:
    """Result of emotion analysis"""
    primary_emotion: EmotionType
    confidence: float
    emotion_scores: Dict[str, float]
    suggested_gesture: GestureType
    tone_adjustment: str
    context_analysis: str
    # Enhanced avatar features
    facial_expression: FacialExpression
    eye_gaze_direction: EyeGazeDirection
    lip_sync_data: Optional[Dict[str, Any]] = None
    gesture_context: Optional[Dict[str, Any]] = None

@dataclass
class GestureMapping:
    """Mapping between emotion and 3D gesture"""
    emotion: EmotionType
    gesture: GestureType
    model_expression: str
    animation_style: str
    description: str
    # Enhanced avatar features
    facial_expression: FacialExpression
    eye_gaze_direction: EyeGazeDirection
    gesture_intensity: float = 1.0  # 0.0 to 1.0
    context_sensitivity: bool = True

class EmotionAnalysisAgent:
    """Advanced emotion analysis using BERT-based sentiment analysis"""
    
    def __init__(self):
        self.device = "cuda" if torch.cuda.is_available() else "cpu"
        self.sentiment_pipeline = None
        self.emotion_classifier = None
        self._models_loaded = False
        
        # Initialize emotion-to-gesture mappings
        self.emotion_gesture_mappings = self._initialize_emotion_mappings()
        
        # Emotion keywords for enhanced detection
        self.emotion_keywords = {
            EmotionType.HAPPY: ["happy", "joy", "great", "wonderful", "amazing", "fantastic", "love", "excited"],
            EmotionType.EXCITED: ["excited", "thrilled", "can't wait", "eager", "pumped", "awesome", "incredible"],
            EmotionType.CALM: ["calm", "peaceful", "relaxed", "serene", "quiet", "tranquil", "gentle"],
            EmotionType.CURIOUS: ["curious", "wonder", "interested", "explore", "discover", "learn", "know more"],
            EmotionType.FRUSTRATED: ["frustrated", "annoyed", "difficult", "hard", "struggle", "problem"],
            EmotionType.WORRIED: ["worried", "concerned", "anxious", "nervous", "unsure", "afraid"],
            EmotionType.CONFIDENT: ["confident", "sure", "certain", "ready", "determined", "strong"],
            EmotionType.ENTHUSIASTIC: ["enthusiastic", "passionate", "energetic", "motivated", "inspiring"]
        }
    
    def _initialize_emotion_mappings(self) -> Dict[EmotionType, GestureMapping]:
        """Initialize emotion to gesture mappings with enhanced avatar features"""
        return {
            EmotionType.HAPPY: GestureMapping(
                emotion=EmotionType.HAPPY,
                gesture=GestureType.FRIENDLY_WAVE,
                model_expression="smile",
                animation_style="upbeat",
                description="Friendly wave with warm smile for happy emotions",
                facial_expression=FacialExpression.SMILE_GENTLE,
                eye_gaze_direction=EyeGazeDirection.LOOKING_AT_USER,
                gesture_intensity=0.8
            ),
            EmotionType.EXCITED: GestureMapping(
                emotion=EmotionType.EXCITED,
                gesture=GestureType.EXCITED_JUMP,
                model_expression="big_smile",
                animation_style="energetic",
                description="Energetic jump with enthusiastic expression",
                facial_expression=FacialExpression.EXCITED_EYES_WIDE,
                eye_gaze_direction=EyeGazeDirection.LOOKING_AT_USER,
                gesture_intensity=1.0
            ),
            EmotionType.CALM: GestureMapping(
                emotion=EmotionType.CALM,
                gesture=GestureType.CALM_STANDING,
                model_expression="peaceful",
                animation_style="smooth",
                description="Calm standing pose with peaceful expression",
                facial_expression=FacialExpression.CALM_PEACEFUL,
                eye_gaze_direction=EyeGazeDirection.LOOKING_AT_USER,
                gesture_intensity=0.5
            ),
            EmotionType.CURIOUS: GestureMapping(
                emotion=EmotionType.CURIOUS,
                gesture=GestureType.THOUGHTFUL_POSE,
                model_expression="inquisitive",
                animation_style="contemplative",
                description="Thoughtful pose showing curiosity and interest",
                facial_expression=FacialExpression.THOUGHTFUL_CONTEMPLATIVE,
                eye_gaze_direction=EyeGazeDirection.LOOKING_AWAY_THOUGHTFUL,
                gesture_intensity=0.6
            ),
            EmotionType.FRUSTRATED: GestureMapping(
                emotion=EmotionType.FRUSTRATED,
                gesture=GestureType.REASSURING_GESTURE,
                model_expression="understanding",
                animation_style="supportive",
                description="Reassuring gesture with understanding expression",
                facial_expression=FacialExpression.CONFUSED_SLIGHT,
                eye_gaze_direction=EyeGazeDirection.LOOKING_AT_USER,
                gesture_intensity=0.7
            ),
            EmotionType.WORRIED: GestureMapping(
                emotion=EmotionType.WORRIED,
                gesture=GestureType.REASSURING_GESTURE,
                model_expression="comforting",
                animation_style="gentle",
                description="Gentle reassuring gesture with comforting expression",
                facial_expression=FacialExpression.WORRIED_SLIGHT,
                eye_gaze_direction=EyeGazeDirection.LOOKING_AT_USER,
                gesture_intensity=0.6
            ),
            EmotionType.NEUTRAL: GestureMapping(
                emotion=EmotionType.NEUTRAL,
                gesture=GestureType.NEUTRAL_IDLE,
                model_expression="neutral",
                animation_style="standard",
                description="Standard idle pose with neutral expression",
                facial_expression=FacialExpression.NEUTRAL_RELAXED,
                eye_gaze_direction=EyeGazeDirection.LOOKING_AT_USER,
                gesture_intensity=0.5
            ),
            EmotionType.CONFIDENT: GestureMapping(
                emotion=EmotionType.CONFIDENT,
                gesture=GestureType.CONFIDENT_POSE,
                model_expression="confident",
                animation_style="assertive",
                description="Confident pose with assertive expression",
                facial_expression=FacialExpression.CONFIDENT_ASSURED,
                eye_gaze_direction=EyeGazeDirection.LOOKING_AT_USER,
                gesture_intensity=0.9
            ),
            EmotionType.ENTHUSIASTIC: GestureMapping(
                emotion=EmotionType.ENTHUSIASTIC,
                gesture=GestureType.ENERGETIC_MOVEMENT,
                model_expression="enthusiastic",
                animation_style="dynamic",
                description="Dynamic energetic movement with enthusiastic expression",
                facial_expression=FacialExpression.EXCITED_ANTICIPATION,
                eye_gaze_direction=EyeGazeDirection.LOOKING_AT_USER,
                gesture_intensity=1.0
            )
        }
    
    def get_thai_cultural_gesture(self, context: str) -> GestureMapping:
        """Get appropriate Thai cultural gesture based on context"""
        context_lower = context.lower()
        
        # Thai tourism context mappings
        thai_gesture_contexts = {
            "greeting": GestureMapping(
                emotion=EmotionType.HAPPY,
                gesture=GestureType.THAI_WAI,
                model_expression="respectful_smile",
                animation_style="traditional",
                description="Traditional Thai wai greeting (สวัสดี) - palms together with gentle bow",
                facial_expression=FacialExpression.SMILE_GENTLE,
                eye_gaze_direction=EyeGazeDirection.LOOKING_AT_USER,
                gesture_intensity=0.8
            ),
            "welcome": GestureMapping(
                emotion=EmotionType.HAPPY,
                gesture=GestureType.THAI_WELCOME,
                model_expression="welcoming_smile",
                animation_style="graceful",
                description="Thai welcoming gesture with open arms and warm smile",
                facial_expression=FacialExpression.SMILE_BIG,
                eye_gaze_direction=EyeGazeDirection.LOOKING_AT_USER,
                gesture_intensity=0.9
            ),
            "direction": GestureMapping(
                emotion=EmotionType.NEUTRAL,
                gesture=GestureType.THAI_POINT,
                model_expression="helpful",
                animation_style="polite",
                description="Thai-style pointing with open hand (not finger) for giving directions",
                facial_expression=FacialExpression.NEUTRAL_RELAXED,
                eye_gaze_direction=EyeGazeDirection.FOLLOWING_GESTURE,
                gesture_intensity=0.7
            ),
            "respect": GestureMapping(
                emotion=EmotionType.CALM,
                gesture=GestureType.THAI_RESPECT,
                model_expression="reverent",
                animation_style="ceremonial",
                description="Deep wai gesture showing high respect (for temples, elderly)",
                facial_expression=FacialExpression.CALM_PEACEFUL,
                eye_gaze_direction=EyeGazeDirection.LOOKING_DOWN,
                gesture_intensity=1.0
            ),
            "smile": GestureMapping(
                emotion=EmotionType.HAPPY,
                gesture=GestureType.THAI_SMILE,
                model_expression="gentle_smile",
                animation_style="serene",
                description="Genuine Thai smile with slight head nod",
                facial_expression=FacialExpression.SMILE_GENTLE,
                eye_gaze_direction=EyeGazeDirection.LOOKING_AT_USER,
                gesture_intensity=0.6
            ),
            "gratitude": GestureMapping(
                emotion=EmotionType.HAPPY,
                gesture=GestureType.THAI_BOW,
                model_expression="grateful",
                animation_style="appreciative",
                description="Traditional Thai bow showing gratitude (ขอบคุณ)",
                facial_expression=FacialExpression.SMILE_GENTLE,
                eye_gaze_direction=EyeGazeDirection.LOOKING_DOWN,
                gesture_intensity=0.8
            )
        }
        
        # Context matching
        for context_key, gesture_mapping in thai_gesture_contexts.items():
            if context_key in context_lower:
                return gesture_mapping
        
        # Default to Thai wai for tourism interactions
        return thai_gesture_contexts["greeting"]
    
    async def _load_models(self):
        """Load emotion analysis models (lazy loading)"""
        if self._models_loaded:
            return
            
        try:
            logger.info("Loading emotion analysis models...")
            
            # Load sentiment analysis pipeline with a BERT-based model
            self.sentiment_pipeline = pipeline(
                "sentiment-analysis", 
                model="cardiffnlp/twitter-roberta-base-sentiment-latest",
                device=0 if self.device == "cuda" else -1
            )
            
            # Load emotion classification model
            self.emotion_classifier = pipeline(
                "text-classification",
                model="j-hartmann/emotion-english-distilroberta-base",
                device=0 if self.device == "cuda" else -1
            )
            
            self._models_loaded = True
            logger.info("Emotion analysis models loaded successfully")
            
        except Exception as e:
            logger.warning(f"Failed to load advanced models: {e}")
            logger.info("Using fallback keyword-based emotion detection")
            # Fallback to keyword-based detection
            self._models_loaded = False
    
    async def analyze_emotion(self, text: str, context: Optional[str] = None) -> EmotionResult:
        """
        Analyze emotion from user text input
        
        Args:
            text: User input text to analyze
            context: Optional context for better analysis
            
        Returns:
            EmotionResult with detected emotion and suggested gesture
        """
        try:
            await self._load_models()
            
            if self._models_loaded:
                return await self._analyze_with_ai_models(text, context)
            else:
                return await self._analyze_with_keywords(text, context)
                
        except Exception as e:
            logger.error(f"Error in emotion analysis: {e}")
            # Return neutral fallback
            mapping = self.emotion_gesture_mappings[EmotionType.NEUTRAL]
            return EmotionResult(
                primary_emotion=EmotionType.NEUTRAL,
                confidence=0.5,
                emotion_scores={"neutral": 0.5},
                suggested_gesture=GestureType.NEUTRAL_IDLE,
                tone_adjustment="neutral",
                context_analysis=f"Fallback analysis due to error: {str(e)}",
                facial_expression=mapping.facial_expression,
                eye_gaze_direction=mapping.eye_gaze_direction,
                lip_sync_data=None,
                gesture_context={"error": True, "fallback": True}
            )
    
    async def _analyze_with_ai_models(self, text: str, context: Optional[str] = None) -> EmotionResult:
        """Analyze emotion using AI models"""
        # Get sentiment analysis
        sentiment_result = self.sentiment_pipeline(text)[0]
        
        # Get emotion classification
        emotion_result = self.emotion_classifier(text)[0]
        
        # Map to our emotion types
        primary_emotion = self._map_to_emotion_type(emotion_result['label'])
        confidence = max(sentiment_result['score'], emotion_result['score'])
        
        # Create emotion scores dictionary
        emotion_scores = {
            emotion_result['label'].lower(): emotion_result['score'],
            sentiment_result['label'].lower(): sentiment_result['score']
        }
        
        # Enhance with keyword analysis
        keyword_emotion, keyword_confidence = self._analyze_keywords(text)
        if keyword_confidence > 0.7:
            primary_emotion = keyword_emotion
            confidence = max(confidence, keyword_confidence)
        
        # Get gesture mapping
        gesture_mapping = self.emotion_gesture_mappings.get(primary_emotion)
        if not gesture_mapping:
            gesture_mapping = self.emotion_gesture_mappings[EmotionType.NEUTRAL]
        
        suggested_gesture = gesture_mapping.gesture
        
        # Determine tone adjustment
        tone_adjustment = self._determine_tone_adjustment(primary_emotion, confidence)
        
        # Create context analysis
        context_analysis = self._create_context_analysis(text, primary_emotion, context)
        
        # Generate lip sync data for Thai TTS
        lip_sync_data = await self._generate_lip_sync_data(text, primary_emotion)
        
        # Create gesture context for AI-based animations
        gesture_context = self._analyze_gesture_context(text, primary_emotion)
        
        return EmotionResult(
            primary_emotion=primary_emotion,
            confidence=confidence,
            emotion_scores=emotion_scores,
            suggested_gesture=suggested_gesture,
            tone_adjustment=tone_adjustment,
            context_analysis=context_analysis,
            facial_expression=gesture_mapping.facial_expression,
            eye_gaze_direction=gesture_mapping.eye_gaze_direction,
            lip_sync_data=lip_sync_data,
            gesture_context=gesture_context
        )
    
    async def _analyze_with_keywords(self, text: str, context: Optional[str] = None) -> EmotionResult:
        """Analyze emotion using keyword-based approach (fallback)"""
        text_lower = text.lower()
        emotion_scores = {}
        
        # Score each emotion based on keyword matches
        for emotion, keywords in self.emotion_keywords.items():
            score = sum(1 for keyword in keywords if keyword in text_lower)
            if score > 0:
                emotion_scores[emotion.value] = min(score / len(keywords), 1.0)
        
        # Determine primary emotion
        if emotion_scores:
            primary_emotion_str = max(emotion_scores.keys(), key=emotion_scores.get)
            primary_emotion = EmotionType(primary_emotion_str)
            confidence = emotion_scores[primary_emotion_str]
        else:
            primary_emotion = EmotionType.NEUTRAL
            confidence = 0.5
            emotion_scores = {"neutral": 0.5}
        
        # Get gesture mapping
        gesture_mapping = self.emotion_gesture_mappings.get(primary_emotion)
        if not gesture_mapping:
            gesture_mapping = self.emotion_gesture_mappings[EmotionType.NEUTRAL]
        
        suggested_gesture = gesture_mapping.gesture
        
        # Determine tone adjustment
        tone_adjustment = self._determine_tone_adjustment(primary_emotion, confidence)
        
        # Create context analysis
        context_analysis = self._create_context_analysis(text, primary_emotion, context)
        
        # Generate lip sync data for Thai TTS (keyword-based fallback)
        lip_sync_data = await self._generate_lip_sync_data(text, primary_emotion)
        
        # Create gesture context for AI-based animations
        gesture_context = self._analyze_gesture_context(text, primary_emotion)
        
        return EmotionResult(
            primary_emotion=primary_emotion,
            confidence=confidence,
            emotion_scores=emotion_scores,
            suggested_gesture=suggested_gesture,
            tone_adjustment=tone_adjustment,
            context_analysis=context_analysis,
            facial_expression=gesture_mapping.facial_expression,
            eye_gaze_direction=gesture_mapping.eye_gaze_direction,
            lip_sync_data=lip_sync_data,
            gesture_context=gesture_context
        )
    
    def _analyze_keywords(self, text: str) -> Tuple[EmotionType, float]:
        """Analyze keywords for emotion detection"""
        text_lower = text.lower()
        emotion_scores = {}
        
        for emotion, keywords in self.emotion_keywords.items():
            score = sum(1 for keyword in keywords if keyword in text_lower)
            if score > 0:
                emotion_scores[emotion] = score / len(keywords)
        
        if emotion_scores:
            primary_emotion = max(emotion_scores.keys(), key=emotion_scores.get)
            confidence = emotion_scores[primary_emotion]
            return primary_emotion, confidence
        
        return EmotionType.NEUTRAL, 0.0
    
    def _map_to_emotion_type(self, model_emotion: str) -> EmotionType:
        """Map model emotion labels to our emotion types"""
        emotion_mapping = {
            # Sentiment model labels
            'LABEL_2': EmotionType.HAPPY,  # Positive
            'LABEL_1': EmotionType.NEUTRAL,  # Neutral
            'LABEL_0': EmotionType.FRUSTRATED,  # Negative
            'positive': EmotionType.HAPPY,
            'negative': EmotionType.FRUSTRATED,
            'neutral': EmotionType.NEUTRAL,
            
            # Emotion model labels
            'joy': EmotionType.HAPPY,
            'sadness': EmotionType.WORRIED,
            'anger': EmotionType.FRUSTRATED,
            'fear': EmotionType.WORRIED,
            'surprise': EmotionType.EXCITED,
            'disgust': EmotionType.FRUSTRATED,
            'love': EmotionType.HAPPY,
            'optimism': EmotionType.CONFIDENT,
            'pessimism': EmotionType.WORRIED,
        }
        
        return emotion_mapping.get(model_emotion.lower(), EmotionType.NEUTRAL)
    
    def _determine_tone_adjustment(self, emotion: EmotionType, confidence: float) -> str:
        """Determine tone adjustment based on emotion"""
        tone_mappings = {
            EmotionType.HAPPY: "warm and friendly",
            EmotionType.EXCITED: "energetic and enthusiastic",
            EmotionType.CALM: "gentle and peaceful",
            EmotionType.CURIOUS: "engaging and informative",
            EmotionType.FRUSTRATED: "patient and helpful",
            EmotionType.WORRIED: "reassuring and supportive",
            EmotionType.NEUTRAL: "professional and balanced",
            EmotionType.CONFIDENT: "encouraging and positive",
            EmotionType.ENTHUSIASTIC: "dynamic and inspiring"
        }
        
        base_tone = tone_mappings.get(emotion, "neutral")
        
        # Adjust intensity based on confidence
        if confidence > 0.8:
            return f"strongly {base_tone}"
        elif confidence > 0.6:
            return base_tone
        else:
            return f"mildly {base_tone}"
    
    def _create_context_analysis(self, text: str, emotion: EmotionType, context: Optional[str]) -> str:
        """Create context analysis description"""
        analysis_parts = [
            f"Detected primary emotion: {emotion.value}",
            f"Text analyzed: '{text[:50]}{'...' if len(text) > 50 else ''}'"
        ]
        
        if context:
            analysis_parts.append(f"Context considered: {context}")
        
        # Add specific insights based on emotion
        if emotion == EmotionType.EXCITED:
            analysis_parts.append("User shows high enthusiasm - recommend energetic gestures")
        elif emotion == EmotionType.WORRIED:
            analysis_parts.append("User may need reassurance - recommend supportive gestures")
        elif emotion == EmotionType.CURIOUS:
            analysis_parts.append("User is exploring - recommend engaging educational gestures")
        
        return " | ".join(analysis_parts)
    
    def get_gesture_for_emotion(self, emotion: EmotionType) -> Optional[GestureMapping]:
        """Get gesture mapping for a specific emotion"""
        return self.emotion_gesture_mappings.get(emotion)
    
    def get_all_gesture_mappings(self) -> Dict[EmotionType, GestureMapping]:
        """Get all emotion-to-gesture mappings"""
        return self.emotion_gesture_mappings.copy()
    
    def suggest_gesture_adjustments(self, current_gesture: str, target_emotion: EmotionType) -> Dict[str, str]:
        """Suggest adjustments to current gesture based on target emotion"""
        gesture_mapping = self.emotion_gesture_mappings.get(target_emotion)
        
        if not gesture_mapping:
            return {"suggestion": "No specific adjustment needed", "reason": "Emotion not recognized"}
        
        return {
            "suggested_gesture": gesture_mapping.gesture.value,
            "expression": gesture_mapping.model_expression,
            "animation_style": gesture_mapping.animation_style,
            "description": gesture_mapping.description,
            "adjustment_reason": f"Optimized for {target_emotion.value} emotion"
        }
    
    async def _generate_lip_sync_data(self, text: str, emotion: EmotionType) -> Dict[str, Any]:
        """Generate lip sync data for Thai TTS integration"""
        try:
            # Analyze text for Thai phonemes and timing
            thai_phoneme_mapping = {
                'ก': {'duration': 0.12, 'mouth_shape': 'open_mid'},
                'ข': {'duration': 0.15, 'mouth_shape': 'aspirated'},
                'ค': {'duration': 0.13, 'mouth_shape': 'closed_plosive'},
                'ง': {'duration': 0.10, 'mouth_shape': 'nasal'},
                'จ': {'duration': 0.14, 'mouth_shape': 'affricate'},
                'ช': {'duration': 0.16, 'mouth_shape': 'fricative'},
                'ส': {'duration': 0.18, 'mouth_shape': 'sibilant'},
                'ห': {'duration': 0.20, 'mouth_shape': 'aspirated_h'},
                'อ': {'duration': 0.22, 'mouth_shape': 'open_vowel'},
                'า': {'duration': 0.25, 'mouth_shape': 'long_a'},
                'ิ': {'duration': 0.15, 'mouth_shape': 'close_i'},
                'ี': {'duration': 0.20, 'mouth_shape': 'long_i'},
                'ุ': {'duration': 0.15, 'mouth_shape': 'close_u'},
                'ู': {'duration': 0.20, 'mouth_shape': 'long_u'},
                'เ': {'duration': 0.18, 'mouth_shape': 'mid_e'},
                'แ': {'duration': 0.20, 'mouth_shape': 'open_e'},
                'โ': {'duration': 0.22, 'mouth_shape': 'close_o'},
                'ใ': {'duration': 0.18, 'mouth_shape': 'diphthong_ai'},
                'ไ': {'duration': 0.18, 'mouth_shape': 'diphthong_ai'}
            }
            
            # Generate phoneme sequence
            phoneme_sequence = []
            total_duration = 0.0
            
            for char in text:
                if char in thai_phoneme_mapping:
                    phoneme_data = thai_phoneme_mapping[char].copy()
                    phoneme_data['start_time'] = total_duration
                    phoneme_data['character'] = char
                    phoneme_sequence.append(phoneme_data)
                    total_duration += phoneme_data['duration']
                elif char.isalpha():  # English characters
                    duration = 0.12  # Default duration for English phonemes
                    phoneme_sequence.append({
                        'character': char,
                        'duration': duration,
                        'mouth_shape': 'english_generic',
                        'start_time': total_duration
                    })
                    total_duration += duration
            
            # Adjust timing based on emotion
            emotion_speed_modifier = {
                EmotionType.EXCITED: 1.2,
                EmotionType.HAPPY: 1.1,
                EmotionType.CALM: 0.8,
                EmotionType.WORRIED: 0.9,
                EmotionType.CONFIDENT: 1.0,
                EmotionType.FRUSTRATED: 1.1,
                EmotionType.CURIOUS: 1.0,
                EmotionType.ENTHUSIASTIC: 1.3,
                EmotionType.NEUTRAL: 1.0
            }
            
            speed_modifier = emotion_speed_modifier.get(emotion, 1.0)
            for phoneme in phoneme_sequence:
                phoneme['duration'] *= speed_modifier
            
            return {
                'phoneme_sequence': phoneme_sequence,
                'total_duration': total_duration * speed_modifier,
                'language': 'thai_english_mixed',
                'emotion_modifier': speed_modifier,
                'mouth_animation_intensity': self.emotion_gesture_mappings.get(emotion, 
                    self.emotion_gesture_mappings[EmotionType.NEUTRAL]).gesture_intensity
            }
            
        except Exception as e:
            logger.warning(f"Failed to generate lip sync data: {e}")
            return {
                'phoneme_sequence': [],
                'total_duration': len(text) * 0.15,  # Fallback timing
                'language': 'generic',
                'emotion_modifier': 1.0,
                'mouth_animation_intensity': 0.5
            }
    
    def _analyze_gesture_context(self, text: str, emotion: EmotionType) -> Dict[str, Any]:
        """Analyze text for context-aware AI gesture generation"""
        text_lower = text.lower()
        
        # Gesture keywords for different actions
        gesture_keywords = {
            'pointing': ['ที่นั่น', 'ตรงนั้น', 'ทางนั้น', 'here', 'there', 'over there', 'this way', 'that way'],
            'explaining': ['เพราะว่า', 'ดังนั้น', 'เหตุผล', 'because', 'therefore', 'so', 'the reason', 'explanation'],
            'counting': ['หนึ่ง', 'สอง', 'สาม', 'สี่', 'ห้า', 'one', 'two', 'three', 'four', 'five', 'first', 'second'],
            'emphasizing': ['สำคัญ', 'จริงๆ', 'มากๆ', 'very', 'really', 'important', 'definitely', 'absolutely'],
            'welcoming': ['ยินดีต้อนรับ', 'สวัสดี', 'ครับ', 'ค่ะ', 'welcome', 'hello', 'hi', 'greetings'],
            'showing_respect': ['เสด็จ', 'ท่าน', 'คุณ', 'พระ', 'วัด', 'temple', 'monk', 'respect', 'honor'],
            'describing_size': ['ใหญ่', 'เล็ก', 'สูง', 'เตี้ย', 'big', 'small', 'large', 'tiny', 'huge', 'tall', 'short'],
            'showing_direction': ['ซ้าย', 'ขวา', 'ตรง', 'หลัง', 'หน้า', 'left', 'right', 'straight', 'back', 'front']
        }
        
        # Detect context
        detected_contexts = []
        for context, keywords in gesture_keywords.items():
            if any(keyword in text_lower for keyword in keywords):
                detected_contexts.append(context)
        
        # Determine primary gesture context
        primary_context = detected_contexts[0] if detected_contexts else 'general'
        
        # Map context to gesture types
        context_gesture_mapping = {
            'pointing': GestureType.POINTING_GESTURE,
            'explaining': GestureType.EXPLAINING_GESTURE,
            'counting': GestureType.COUNTING_GESTURE,
            'emphasizing': GestureType.EMPHASIZING_GESTURE,
            'welcoming': GestureType.THAI_WELCOME,
            'showing_respect': GestureType.THAI_RESPECT,
            'describing_size': GestureType.EXPLAINING_GESTURE,
            'showing_direction': GestureType.THAI_POINT,
            'general': None  # Use emotion-based gesture
        }
        
        suggested_gesture = context_gesture_mapping.get(primary_context)
        
        return {
            'detected_contexts': detected_contexts,
            'primary_context': primary_context,
            'context_confidence': len(detected_contexts) / len(gesture_keywords),
            'suggested_context_gesture': suggested_gesture.value if suggested_gesture else None,
            'gesture_priority': 'context' if suggested_gesture else 'emotion',
            'animation_modifiers': {
                'intensity': self._calculate_gesture_intensity(text, emotion),
                'speed': self._calculate_gesture_speed(text, emotion),
                'repetition': self._should_repeat_gesture(text, emotion)
            }
        }
    
    def _calculate_gesture_intensity(self, text: str, emotion: EmotionType) -> float:
        """Calculate gesture intensity based on text content and emotion"""
        base_intensity = self.emotion_gesture_mappings.get(emotion, 
            self.emotion_gesture_mappings[EmotionType.NEUTRAL]).gesture_intensity
        
        # Intensity modifiers
        intensity_keywords = {
            'high': ['มาก', 'มากๆ', 'จริงๆ', 'สุดๆ', 'very', 'really', 'extremely', 'absolutely'],
            'medium': ['ค่อนข้าง', 'พอสมควร', 'quite', 'fairly', 'somewhat'],
            'low': ['นิดหน่อย', 'เล็กน้อย', 'a little', 'slightly', 'a bit']
        }
        
        text_lower = text.lower()
        if any(keyword in text_lower for keyword in intensity_keywords['high']):
            return min(base_intensity * 1.3, 1.0)
        elif any(keyword in text_lower for keyword in intensity_keywords['low']):
            return max(base_intensity * 0.7, 0.3)
        else:
            return base_intensity
    
    def _calculate_gesture_speed(self, text: str, emotion: EmotionType) -> float:
        """Calculate gesture speed based on emotion and text urgency"""
        base_speed = 1.0
        
        speed_emotions = {
            EmotionType.EXCITED: 1.4,
            EmotionType.ENTHUSIASTIC: 1.3,
            EmotionType.HAPPY: 1.2,
            EmotionType.FRUSTRATED: 1.1,
            EmotionType.CALM: 0.8,
            EmotionType.WORRIED: 0.9,
            EmotionType.CURIOUS: 0.7
        }
        
        return speed_emotions.get(emotion, base_speed)
    
    def _should_repeat_gesture(self, text: str, emotion: EmotionType) -> bool:
        """Determine if gesture should be repeated for emphasis"""
        repeat_keywords = ['again', 'repeat', 'once more', 'อีกครั้ง', 'ซ้ำ', 'อีกรอบ']
        text_lower = text.lower()
        
        # Repeat for emphasis words or excited emotions
        has_repeat_keywords = any(keyword in text_lower for keyword in repeat_keywords)
        is_emphatic_emotion = emotion in [EmotionType.EXCITED, EmotionType.ENTHUSIASTIC, EmotionType.CONFIDENT]
        
        return has_repeat_keywords or is_emphatic_emotion