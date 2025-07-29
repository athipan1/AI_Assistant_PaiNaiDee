"""
Test suite for Emotion Analysis system
Tests sentiment analysis, emotion detection, and gesture mapping functionality
"""

import unittest
import asyncio
import sys
import os
from pathlib import Path

# Add parent directory to path for imports
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))

try:
    from agents.emotion_analysis import (
        EmotionAnalysisAgent, EmotionType, GestureType, 
        EmotionResult, GestureMapping
    )
    HAS_EMOTION_AGENT = True
except ImportError as e:
    print(f"Warning: Could not import emotion analysis agent: {e}")
    HAS_EMOTION_AGENT = False

class TestEmotionAnalysis(unittest.TestCase):
    """Test the Emotion Analysis Agent"""
    
    def setUp(self):
        if not HAS_EMOTION_AGENT:
            self.skipTest("Emotion analysis agent not available")
        self.agent = EmotionAnalysisAgent()
    
    def test_emotion_detection_happy(self):
        """Test detection of happy emotions"""
        async def run_test():
            result = await self.agent.analyze_emotion("I'm so excited about this trip to Thailand!")
            self.assertIn(result.primary_emotion, [EmotionType.HAPPY, EmotionType.EXCITED])
            self.assertGreater(result.confidence, 0.3)
            return result
        
        result = asyncio.run(run_test())
        self.assertIsNotNone(result.suggested_gesture)
        self.assertIn("excited", result.tone_adjustment.lower())
    
    def test_emotion_detection_worried(self):
        """Test detection of worried/anxious emotions"""
        async def run_test():
            result = await self.agent.analyze_emotion("I'm a bit worried about traveling alone")
            self.assertEqual(result.primary_emotion, EmotionType.WORRIED)
            self.assertGreater(result.confidence, 0.3)
            return result
        
        result = asyncio.run(run_test())
        self.assertEqual(result.suggested_gesture, GestureType.REASSURING_GESTURE)
        self.assertIn("reassuring", result.tone_adjustment.lower())
    
    def test_emotion_detection_curious(self):
        """Test detection of curious emotions"""
        async def run_test():
            result = await self.agent.analyze_emotion("I wonder what the best temples to visit are?")
            self.assertEqual(result.primary_emotion, EmotionType.CURIOUS)
            self.assertGreater(result.confidence, 0.3)
            return result
        
        result = asyncio.run(run_test())
        self.assertEqual(result.suggested_gesture, GestureType.THOUGHTFUL_POSE)
    
    def test_emotion_detection_neutral(self):
        """Test detection of neutral emotions"""
        async def run_test():
            result = await self.agent.analyze_emotion("Please show me information about Bangkok")
            # Should be neutral or have low confidence
            self.assertTrue(
                result.primary_emotion == EmotionType.NEUTRAL or 
                result.confidence < 0.7
            )
            return result
        
        result = asyncio.run(run_test())
        self.assertIsNotNone(result.suggested_gesture)
    
    def test_context_analysis(self):
        """Test context-aware emotion analysis"""
        async def run_test():
            result = await self.agent.analyze_emotion(
                "This is difficult", 
                context="user struggling with travel planning"
            )
            self.assertEqual(result.primary_emotion, EmotionType.FRUSTRATED)
            self.assertIn("context", result.context_analysis.lower())
            return result
        
        result = asyncio.run(run_test())
        self.assertEqual(result.suggested_gesture, GestureType.REASSURING_GESTURE)
    
    def test_gesture_mappings_completeness(self):
        """Test that all emotions have gesture mappings"""
        mappings = self.agent.get_all_gesture_mappings()
        
        # Check that all emotion types have mappings
        for emotion_type in EmotionType:
            self.assertIn(emotion_type, mappings)
            
            mapping = mappings[emotion_type]
            self.assertIsInstance(mapping, GestureMapping)
            self.assertEqual(mapping.emotion, emotion_type)
            self.assertIsInstance(mapping.gesture, GestureType)
            self.assertIsNotNone(mapping.model_expression)
            self.assertIsNotNone(mapping.animation_style)
            self.assertIsNotNone(mapping.description)
    
    def test_gesture_adjustment_suggestions(self):
        """Test gesture adjustment suggestions"""
        suggestions = self.agent.suggest_gesture_adjustments(
            "neutral_idle", EmotionType.EXCITED
        )
        
        self.assertIn("suggested_gesture", suggestions)
        self.assertIn("expression", suggestions)
        self.assertIn("animation_style", suggestions)
        self.assertEqual(suggestions["suggested_gesture"], GestureType.EXCITED_JUMP.value)
    
    def test_tone_adjustment_logic(self):
        """Test tone adjustment based on emotion and confidence"""
        # High confidence happy emotion
        async def test_high_confidence():
            result = await self.agent.analyze_emotion("I absolutely love Thailand! It's amazing!")
            # Should be strongly positive tone
            self.assertIn("warm", result.tone_adjustment.lower())
            return result
        
        # Low confidence emotion
        async def test_low_confidence():
            result = await self.agent.analyze_emotion("okay")
            # Should be mild adjustment
            self.assertTrue(
                "mildly" in result.tone_adjustment.lower() or
                result.confidence < 0.6
            )
            return result
        
        asyncio.run(test_high_confidence())
        asyncio.run(test_low_confidence())
    
    def test_keyword_fallback_system(self):
        """Test that keyword-based emotion detection works as fallback"""
        # Force keyword analysis by testing with simple keywords
        happy_keywords = ["happy", "joy", "wonderful", "amazing"]
        
        for keyword in happy_keywords:
            async def test_keyword():
                result = await self.agent.analyze_emotion(f"This is {keyword}")
                # Should detect positive emotion
                self.assertIn(result.primary_emotion, [EmotionType.HAPPY, EmotionType.EXCITED])
                return result
            
            asyncio.run(test_keyword())
    
    def test_error_handling(self):
        """Test error handling for invalid inputs"""
        async def test_empty_text():
            result = await self.agent.analyze_emotion("")
            # Should return neutral with low confidence
            self.assertEqual(result.primary_emotion, EmotionType.NEUTRAL)
            self.assertLessEqual(result.confidence, 0.5)
            return result
        
        async def test_very_long_text():
            long_text = "This is a very long text. " * 100
            result = await self.agent.analyze_emotion(long_text)
            # Should still return a valid result
            self.assertIsInstance(result, EmotionResult)
            self.assertGreaterEqual(result.confidence, 0.0)
            return result
        
        asyncio.run(test_empty_text())
        asyncio.run(test_very_long_text())

class TestEmotionAPIIntegration(unittest.TestCase):
    """Test emotion analysis API integration"""
    
    def setUp(self):
        if not HAS_EMOTION_AGENT:
            self.skipTest("Emotion analysis agent not available")
    
    def test_api_request_response_models(self):
        """Test that API models can be instantiated correctly"""
        try:
            from api.emotion_routes import (
                EmotionAnalysisRequest, EmotionAnalysisResponse,
                GestureRecommendationRequest, GestureRecommendationResponse
            )
            
            # Test request model
            request = EmotionAnalysisRequest(
                text="I'm excited about my trip!",
                context="travel planning",
                language="en",
                user_id="test_user"
            )
            self.assertEqual(request.text, "I'm excited about my trip!")
            self.assertEqual(request.context, "travel planning")
            
            # Test response model structure
            response_data = {
                "primary_emotion": "excited",
                "confidence": 0.8,
                "emotion_scores": {"excited": 0.8},
                "suggested_gesture": "excited_jump",
                "tone_adjustment": "energetic and enthusiastic",
                "context_analysis": "Test analysis",
                "status": "success"
            }
            response = EmotionAnalysisResponse(**response_data)
            self.assertEqual(response.primary_emotion, "excited")
            self.assertEqual(response.confidence, 0.8)
            
        except ImportError:
            self.skipTest("API routes not available")
    
    def test_gesture_recommendation_workflow(self):
        """Test the complete gesture recommendation workflow"""
        agent = EmotionAnalysisAgent()
        
        # Test getting gesture for specific emotion
        gesture_mapping = agent.get_gesture_for_emotion(EmotionType.HAPPY)
        self.assertIsNotNone(gesture_mapping)
        self.assertEqual(gesture_mapping.emotion, EmotionType.HAPPY)
        
        # Test gesture adjustment suggestions
        adjustments = agent.suggest_gesture_adjustments("neutral_idle", EmotionType.HAPPY)
        self.assertIn("suggested_gesture", adjustments)
        self.assertEqual(adjustments["suggested_gesture"], GestureType.FRIENDLY_WAVE.value)

class TestEmotionGestureMapping(unittest.TestCase):
    """Test emotion to gesture mapping system"""
    
    def setUp(self):
        if not HAS_EMOTION_AGENT:
            self.skipTest("Emotion analysis agent not available")
        self.agent = EmotionAnalysisAgent()
    
    def test_all_emotions_have_gestures(self):
        """Test that all emotions map to valid gestures"""
        mappings = self.agent.get_all_gesture_mappings()
        
        for emotion_type in EmotionType:
            self.assertIn(emotion_type, mappings)
            mapping = mappings[emotion_type]
            
            # Verify gesture is valid
            self.assertIsInstance(mapping.gesture, GestureType)
            
            # Verify description is meaningful
            self.assertTrue(len(mapping.description) > 10)
            
            # Verify expression and animation style are specified
            self.assertIsNotNone(mapping.model_expression)
            self.assertIsNotNone(mapping.animation_style)
    
    def test_gesture_model_compatibility(self):
        """Test that gestures are compatible with available 3D models"""
        mappings = self.agent.get_all_gesture_mappings()
        available_models = ["Man.fbx", "Idle.fbx", "Walking.fbx", "Running.fbx", "Man_Rig.fbx"]
        
        for emotion_type, mapping in mappings.items():
            # Check that gesture can be implemented with available models
            if mapping.animation_style == "dynamic":
                # Dynamic gestures should work with rigged model
                self.assertIn("Man_Rig.fbx", available_models)
            
            # All gestures should have fallback to basic models
            self.assertTrue(
                mapping.animation_style in ["standard", "smooth", "upbeat", "energetic", 
                                           "contemplative", "supportive", "gentle", 
                                           "assertive", "dynamic"]
            )
    
    def test_emotion_intensity_mapping(self):
        """Test that gesture intensity matches emotion intensity"""
        mappings = self.agent.get_all_gesture_mappings()
        
        # High energy emotions should have energetic gestures
        high_energy_emotions = [EmotionType.EXCITED, EmotionType.ENTHUSIASTIC]
        for emotion in high_energy_emotions:
            if emotion in mappings:
                mapping = mappings[emotion]
                self.assertIn(mapping.animation_style, ["energetic", "dynamic"])
        
        # Calm emotions should have calm gestures
        calm_emotions = [EmotionType.CALM, EmotionType.NEUTRAL]
        for emotion in calm_emotions:
            if emotion in mappings:
                mapping = mappings[emotion]
                self.assertIn(mapping.animation_style, ["smooth", "standard"])

class TestEmotionSystemPerformance(unittest.TestCase):
    """Test performance aspects of emotion analysis"""
    
    def setUp(self):
        if not HAS_EMOTION_AGENT:
            self.skipTest("Emotion analysis agent not available")
        self.agent = EmotionAnalysisAgent()
    
    def test_analysis_speed(self):
        """Test that emotion analysis completes in reasonable time"""
        import time
        
        async def measure_analysis_time():
            test_texts = [
                "I'm excited about my trip!",
                "I'm worried about the weather",
                "This is amazing!",
                "Can you help me?",
                "I don't understand"
            ]
            
            start_time = time.time()
            
            for text in test_texts:
                await self.agent.analyze_emotion(text)
            
            end_time = time.time()
            avg_time = (end_time - start_time) / len(test_texts)
            
            # Should complete within reasonable time (adjust based on hardware)
            self.assertLess(avg_time, 5.0)  # 5 seconds per analysis max
            
            return avg_time
        
        avg_time = asyncio.run(measure_analysis_time())
        print(f"Average emotion analysis time: {avg_time:.3f} seconds")
    
    def test_memory_usage(self):
        """Test that emotion analysis doesn't consume excessive memory"""
        # Simple test - just ensure multiple analyses don't crash
        async def run_multiple_analyses():
            texts = ["Test text " + str(i) for i in range(10)]
            results = []
            
            for text in texts:
                result = await self.agent.analyze_emotion(text)
                results.append(result)
            
            return results
        
        results = asyncio.run(run_multiple_analyses())
        self.assertEqual(len(results), 10)
        
        # All results should be valid
        for result in results:
            self.assertIsInstance(result, EmotionResult)
            self.assertGreaterEqual(result.confidence, 0.0)
            self.assertLessEqual(result.confidence, 1.0)

def run_emotion_analysis_demo():
    """Demo function to showcase emotion analysis capabilities"""
    if not HAS_EMOTION_AGENT:
        print("Emotion analysis agent not available for demo")
        return
    
    print("\n" + "="*60)
    print("EMOTION ANALYSIS SYSTEM DEMO")
    print("="*60)
    
    agent = EmotionAnalysisAgent()
    
    demo_texts = [
        "I'm so excited to explore Thailand!",
        "I'm a bit worried about the language barrier",
        "This temple is absolutely amazing!",
        "Can you recommend some good restaurants?",
        "I'm feeling overwhelmed with all the options",
        "Thank you for your help, I feel much better now"
    ]
    
    async def run_demo():
        for text in demo_texts:
            print(f"\nText: '{text}'")
            result = await agent.analyze_emotion(text)
            
            print(f"  Emotion: {result.primary_emotion.value}")
            print(f"  Confidence: {result.confidence:.2f}")
            print(f"  Suggested Gesture: {result.suggested_gesture.value}")
            print(f"  Tone Adjustment: {result.tone_adjustment}")
            print(f"  Context: {result.context_analysis}")
    
    asyncio.run(run_demo())
    print("\n" + "="*60)

if __name__ == "__main__":
    # Run unit tests
    unittest.main(verbosity=2, exit=False)
    
    # Run demo
    run_emotion_analysis_demo()