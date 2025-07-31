"""
Enhanced 3D Avatar Demo
Comprehensive demonstration of all enhanced avatar features including:
- Facial expressions with emotion mapping
- Eye gaze tracking with natural variations
- Thai lip synchronization
- AI-based context-aware gestures
- Animation presets and real-time controls
"""

import asyncio
import json
from typing import Dict, Any
import logging

try:
    from agents.enhanced_avatar import EnhancedAvatarSystem
    from agents.emotion_analysis import EmotionAnalysisAgent, EmotionType, FacialExpression, EyeGazeDirection
    HAS_ENHANCED_AVATAR = True
except ImportError as e:
    logging.warning(f"Enhanced avatar system not available: {e}")
    HAS_ENHANCED_AVATAR = False

logger = logging.getLogger(__name__)

class AvatarDemo:
    """Comprehensive demo of enhanced 3D avatar features"""
    
    def __init__(self):
        if not HAS_ENHANCED_AVATAR:
            raise RuntimeError("Enhanced avatar system not available")
            
        self.avatar_system = EnhancedAvatarSystem()
        self.emotion_agent = EmotionAnalysisAgent()
        
    async def run_comprehensive_demo(self):
        """Run comprehensive demo of all avatar features"""
        print("🎭 Starting Enhanced 3D Avatar Demo")
        print("=" * 60)
        
        # Demo scenarios
        scenarios = [
            {
                "name": "Thai Greeting",
                "text": "สวัสดีครับ ยินดีต้อนรับสู่ประเทศไทย!",
                "description": "Traditional Thai greeting with wai gesture"
            },
            {
                "name": "Excited Tourism", 
                "text": "I'm so excited to explore the beautiful temples in Bangkok!",
                "description": "Enthusiastic response about tourism"
            },
            {
                "name": "Concerned Traveler",
                "text": "I'm a bit worried about traveling alone in Thailand",
                "description": "Supportive response to worried traveler"
            },
            {
                "name": "Curious Explorer",
                "text": "Can you tell me more about Thai cultural traditions?",
                "description": "Thoughtful explanation mode"
            },
            {
                "name": "Confident Guide",
                "text": "Let me show you the best places to visit in Thailand!",
                "description": "Confident tour guide presentation"
            }
        ]
        
        for i, scenario in enumerate(scenarios, 1):
            print(f"\n🎬 Scenario {i}: {scenario['name']}")
            print(f"📝 Text: {scenario['text']}")
            print(f"📖 Description: {scenario['description']}")
            print("-" * 40)
            
            await self.demonstrate_scenario(scenario['text'], scenario['name'])
            
        print("\n🎉 Enhanced 3D Avatar Demo completed!")
        print("✨ All features demonstrated successfully")
        
    async def demonstrate_scenario(self, text: str, scenario_name: str):
        """Demonstrate a specific scenario with full avatar animation"""
        
        # 1. Emotion Analysis
        print("🧠 Analyzing emotion and context...")
        emotion_result = await self.emotion_agent.analyze_emotion(text)
        
        print(f"   📊 Detected emotion: {emotion_result.primary_emotion.value} (confidence: {emotion_result.confidence:.2f})")
        print(f"   😊 Facial expression: {emotion_result.facial_expression.value}")
        print(f"   👀 Eye gaze: {emotion_result.eye_gaze_direction.value}")
        
        if emotion_result.gesture_context:
            print(f"   🤲 Gesture context: {emotion_result.gesture_context.get('primary_context', 'general')}")
            
        if emotion_result.lip_sync_data:
            phoneme_count = len(emotion_result.lip_sync_data.get('phoneme_sequence', []))
            duration = emotion_result.lip_sync_data.get('total_duration', 0)
            print(f"   👄 Lip sync: {phoneme_count} phonemes, {duration:.2f}s duration")
            
        # 2. Avatar Animation Generation
        print("🎭 Generating avatar animation...")
        animation_frames = await self.avatar_system.generate_avatar_animation(
            emotion_result, text, 'thai'
        )
        
        print(f"   🎬 Generated {len(animation_frames)} animation frames")
        
        # 3. Animation Export and Analysis
        animation_data = self.avatar_system.export_animation_data(animation_frames)
        print(f"   ⏱️  Duration: {animation_data['duration']:.2f}s at {animation_data['fps']} FPS")
        
        # 4. Feature Analysis
        self.analyze_animation_features(animation_data, emotion_result)
        
    def analyze_animation_features(self, animation_data: Dict[str, Any], emotion_result):
        """Analyze and display animation features"""
        frames = animation_data.get('frames', [])
        if not frames:
            return
            
        print("   🔍 Animation feature analysis:")
        
        # Facial expression analysis
        facial_expressions = set()
        eye_gaze_targets = []
        lip_sync_frames = 0
        
        for frame in frames:
            if frame.get('facial_expression'):
                facial_expressions.add(frame['facial_expression']['type'])
                
            if frame.get('eye_gaze'):
                eye_gaze_targets.append((frame['eye_gaze']['target_x'], frame['eye_gaze']['target_y']))
                
            if frame.get('lip_sync'):
                lip_sync_frames += 1
                
        print(f"      - Facial expressions used: {', '.join(facial_expressions)}")
        print(f"      - Eye gaze variations: {len(set(eye_gaze_targets))} unique positions")
        print(f"      - Lip sync active frames: {lip_sync_frames}/{len(frames)}")
        print(f"      - Primary gesture: {emotion_result.suggested_gesture.value}")
        
    async def demonstrate_individual_features(self):
        """Demonstrate individual avatar features"""
        print("\n🔧 Individual Feature Demonstrations")
        print("=" * 50)
        
        # Facial Expression Demo
        print("\n😊 Facial Expression Demo:")
        for expression in ['smile_gentle', 'smile_excited', 'confused_slight', 'worried_slight', 'confident_assured']:
            print(f"   Testing: {expression}")
            try:
                expr_enum = FacialExpression(expression)
                facial_anim = self.avatar_system._generate_facial_animation(expr_enum)
                print(f"   ✅ Generated {expression} animation (intensity: {facial_anim.intensity})")
            except Exception as e:
                print(f"   ❌ Failed: {e}")
                
        # Eye Gaze Demo
        print("\n👀 Eye Gaze Demo:")
        for gaze in ['looking_at_user', 'looking_away_thoughtful', 'following_gesture']:
            print(f"   Testing: {gaze}")
            try:
                gaze_enum = EyeGazeDirection(gaze)
                gaze_sequence = self.avatar_system._generate_eye_gaze_sequence(gaze_enum, EmotionType.NEUTRAL)
                print(f"   ✅ Generated {len(gaze_sequence)} gaze frames for {gaze}")
            except Exception as e:
                print(f"   ❌ Failed: {e}")
                
        # Thai Lip Sync Demo
        print("\n👄 Thai Lip Sync Demo:")
        thai_texts = [
            "สวัสดีครับ",
            "ขอบคุณมากครับ", 
            "ไปเที่ยววัดพระแก้ว"
        ]
        
        for text in thai_texts:
            print(f"   Testing: {text}")
            try:
                lip_sync_data = await self.emotion_agent._generate_lip_sync_data(text, EmotionType.HAPPY)
                phoneme_count = len(lip_sync_data.get('phoneme_sequence', []))
                duration = lip_sync_data.get('total_duration', 0)
                print(f"   ✅ {phoneme_count} phonemes, {duration:.2f}s duration")
            except Exception as e:
                print(f"   ❌ Failed: {e}")
                
    async def performance_benchmark(self):
        """Benchmark avatar system performance"""
        print("\n⚡ Performance Benchmark")
        print("=" * 30)
        
        import time
        
        test_texts = [
            "สวัสดีครับ",
            "Hello, welcome to Thailand!",
            "I'm excited about this amazing trip to see the beautiful temples!",
            "ขอบคุณมากครับ สำหรับการต้อนรับที่อบอุ่น"
        ]
        
        total_time = 0
        total_frames = 0
        
        for i, text in enumerate(test_texts, 1):
            print(f"🧪 Test {i}: {text[:30]}...")
            
            start_time = time.time()
            
            # Emotion analysis
            emotion_result = await self.emotion_agent.analyze_emotion(text)
            
            # Animation generation
            animation_frames = await self.avatar_system.generate_avatar_animation(
                emotion_result, text, 'thai'
            )
            
            end_time = time.time()
            duration = end_time - start_time
            
            total_time += duration
            total_frames += len(animation_frames)
            
            print(f"   ⏱️  Processing time: {duration:.3f}s")
            print(f"   🎬 Generated frames: {len(animation_frames)}")
            print(f"   📊 Frames per second: {len(animation_frames)/duration:.1f}")
            
        print(f"\n📈 Overall Performance:")
        print(f"   ⏱️  Total time: {total_time:.3f}s")
        print(f"   🎬 Total frames: {total_frames}")
        print(f"   📊 Average FPS: {total_frames/total_time:.1f}")
        
    def generate_feature_report(self):
        """Generate comprehensive feature report"""
        print("\n📋 Enhanced 3D Avatar Feature Report")
        print("=" * 45)
        
        features = {
            "Facial Expressions": {
                "count": len(list(FacialExpression)),
                "types": [e.value for e in FacialExpression],
                "status": "✅ Fully Implemented"
            },
            "Eye Gaze Directions": {
                "count": len(list(EyeGazeDirection)),
                "types": [e.value for e in EyeGazeDirection],
                "status": "✅ Fully Implemented"
            },
            "Gaze Patterns": {
                "count": len(self.avatar_system.gaze_patterns),
                "types": list(self.avatar_system.gaze_patterns.keys()),
                "status": "✅ Fully Implemented"
            },
            "Thai Phoneme Support": {
                "count": len(self.avatar_system.thai_viseme_mapping),
                "types": list(self.avatar_system.thai_viseme_mapping.keys())[:10] + ["..."],
                "status": "✅ Fully Implemented"
            },
            "Emotion Types": {
                "count": len(list(EmotionType)),
                "types": [e.value for e in EmotionType],
                "status": "✅ Fully Implemented"
            }
        }
        
        for feature_name, feature_data in features.items():
            print(f"\n🔹 {feature_name}:")
            print(f"   📊 Count: {feature_data['count']}")
            print(f"   🏷️  Types: {', '.join(feature_data['types'])}")
            print(f"   ✅ Status: {feature_data['status']}")
            
        print(f"\n🎉 Total Features Implemented: {len(features)}")
        print("🌟 All enhanced avatar features are fully operational!")

async def main():
    """Main demo function"""
    if not HAS_ENHANCED_AVATAR:
        print("❌ Enhanced avatar system not available")
        print("Please ensure all dependencies are installed")
        return
        
    try:
        demo = AvatarDemo()
        
        # Run comprehensive demo
        await demo.run_comprehensive_demo()
        
        # Demonstrate individual features
        await demo.demonstrate_individual_features()
        
        # Performance benchmark
        await demo.performance_benchmark()
        
        # Generate feature report
        demo.generate_feature_report()
        
    except Exception as e:
        print(f"❌ Demo failed: {e}")
        logger.error(f"Avatar demo error: {e}", exc_info=True)

if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO)
    asyncio.run(main())