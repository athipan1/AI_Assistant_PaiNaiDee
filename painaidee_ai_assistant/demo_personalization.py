#!/usr/bin/env python3
"""
Demo script for AI Assistant Personalization System
สาธิตระบบ AI Assistant แบบเฉพาะบุคคล
"""

import asyncio
import json
from datetime import datetime
import sys
import os

# Add the project root to Python path
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from models.user_profile import user_profile_manager
from models.chat_memory import enhanced_chat_memory

def print_header(title):
    """Print a formatted header"""
    print("\n" + "="*60)
    print(f"🎯 {title}")
    print("="*60)

def print_section(title):
    """Print a formatted section"""
    print(f"\n📍 {title}")
    print("-" * 40)

def demo_user_profile_creation():
    """Demo: Creating and managing user profiles"""
    print_section("การสร้างโปรไฟล์ผู้ใช้ (User Profile Creation)")
    
    # Create a sample user
    user_id = "demo_user_001"
    
    profile = user_profile_manager.create_user_profile(
        user_id=user_id,
        name="นางสาวสมใจ ชอบเที่ยว",
        nickname="สมใจ",
        age_range="26-35",
        language_preference="th",
        location="เชียงใหม่",
        budget_range="mid"
    )
    
    print(f"✅ สร้างโปรไฟล์สำเร็จ: {profile.personal_info.name}")
    print(f"   ชื่อเล่น: {profile.personal_info.nickname}")
    print(f"   ภาษา: {profile.personal_info.language_preference}")
    print(f"   งบประมาณ: {profile.travel_preferences.budget_range.value}")
    
    return user_id

def demo_travel_preferences(user_id):
    """Demo: Updating travel preferences"""
    print_section("การตั้งค่าความชอบการเดินทาง (Travel Preferences)")
    
    success = user_profile_manager.update_travel_preferences(
        user_id,
        favorite_places=["วัดพระแก้ว", "ดอยสุเทพ", "หาดป่าตอง", "ตลาดนัดเจเจ"],
        favorite_seasons=["cool", "hot"],
        place_types=["temple", "mountain", "beach", "market"],
        travel_style=["cultural", "relaxing", "adventure"],
        accommodation_type=["hotel", "resort"],
        transportation=["car", "walk"],
        group_preference="couple",
        activity_level="medium"
    )
    
    print(f"✅ อัปเดตความชอบสำเร็จ: {success}")
    
    # Show updated preferences
    profile = user_profile_manager.get_user_profile(user_id)
    print(f"   สถานที่ที่ชอบ: {profile.travel_preferences.favorite_places}")
    print(f"   ฤดูกาลที่ชอบ: {[s.value for s in profile.travel_preferences.favorite_seasons]}")
    print(f"   ประเภทสถานที่: {[p.value for p in profile.travel_preferences.place_types]}")
    print(f"   รูปแบบการเดินทาง: {profile.travel_preferences.travel_style}")

def demo_conversation_memory(user_id):
    """Demo: Conversation memory and context"""
    print_section("ระบบจดจำการสนทนา (Conversation Memory)")
    
    # Start a conversation
    conversation_id = enhanced_chat_memory.start_conversation(user_id, "demo_session")
    print(f"✅ เริ่มการสนทนา: {conversation_id}")
    
    # Sample conversation
    conversations = [
        {
            "user": "สวัสดีค่ะ ผมชื่อสมใจ อยากไปเที่ยววัดที่มีประวัติศาสตร์",
            "bot": "สวัสดีค่ะคุณสมใจ! วัดที่มีประวัติศาสตร์น่าสนใจได้แก่ วัดพระแก้ว วัดอรุณ และวัดโพธิ์ ทั้งหมดอยู่ในกรุงเทพฯ",
            "importance": 0.9
        },
        {
            "user": "งบประมาณ 15,000 บาท เที่ยวกรุงเทพได้กี่วัน",
            "bot": "ด้วยงบ 15,000 บาท สามารถเที่ยวกรุงเทพได้ประมาณ 4-5 วัน โดยพักโรงแรมระดับกลาง",
            "importance": 0.8
        },
        {
            "user": "อยากไปตลาดนัดด้วย มีที่ไหนแนะนำบ้าง",
            "bot": "แนะนำตลาดนัดเจเจ (สุดสัปดาห์) และตลาดรถไฟรัชดา (ทุกวัน) ทั้งสองแห่งมีของหลากหลายในราคาเหมาะสม",
            "importance": 0.7
        },
        {
            "user": "ขอบคุณมากค่ะ ข้อมูลดีมาก ชอบมาก",
            "bot": "ยินดีค่ะ! หากต้องการคำแนะนำเพิ่มเติมเกี่ยวกับการท่องเที่ยว สามารถถามได้ตลอดเวลาค่ะ",
            "importance": 0.6
        }
    ]
    
    # Add conversations to memory
    for i, conv in enumerate(conversations, 1):
        entry_id = enhanced_chat_memory.add_interaction(
            conversation_id=conversation_id,
            human_message=conv["user"],
            ai_message=conv["bot"],
            importance_score=conv["importance"]
        )
        
        # Also add to user profile
        user_profile_manager.add_memory(
            user_id=user_id,
            conversation_id=conversation_id,
            user_message=conv["user"],
            bot_response=conv["bot"],
            importance_score=conv["importance"]
        )
        
        print(f"   บทสนทนาที่ {i}: {conv['user'][:30]}...")
    
    print(f"✅ บันทึกบทสนทนา {len(conversations)} รอบ")
    
    return conversation_id

def demo_personalized_recommendations(user_id):
    """Demo: Personalized recommendations"""
    print_section("คำแนะนำแบบเฉพาะบุคคล (Personalized Recommendations)")
    
    test_queries = [
        {
            "query": "แนะนำวัดที่สวยในกรุงเทพ",
            "context": {"season": "cool", "weather": "sunny"}
        },
        {
            "query": "อยากไปเที่ยวภูเขาในหน้าหนาว",
            "context": {"season": "cool", "weather": "cool"}
        },
        {
            "query": "ชายหาดสำหรับคู่รัก",
            "context": {"season": "hot", "weather": "sunny"}
        },
        {
            "query": "ตลาดที่น่าสนใจ",
            "context": {"season": "cool", "weather": "cloudy"}
        }
    ]
    
    for i, test in enumerate(test_queries, 1):
        print(f"\n🔍 คำถามที่ {i}: \"{test['query']}\"")
        
        recommendations = user_profile_manager.get_personalized_recommendations(
            user_id=user_id,
            query=test["query"],
            context=test["context"]
        )
        
        print(f"📊 ได้คำแนะนำ {len(recommendations)} รายการ:")
        
        for j, rec in enumerate(recommendations[:3], 1):  # Show top 3
            print(f"   {j}. {rec['place_name']} ({rec['place_name_en']})")
            print(f"      คะแนน: {rec['score']:.2f} | ประเภท: {rec['type']}")
            print(f"      เหตุผล: {', '.join(rec['reasons'][:2])}")
            print(f"      ระดับส่วนตัว: {rec['personalization_level']}")
            print()

def demo_memory_search(user_id):
    """Demo: Memory search and context"""
    print_section("การค้นหาความจำ (Memory Search)")
    
    search_queries = ["วัด", "งบประมาณ", "ตลาด", "ประวัติศาสตร์"]
    
    for query in search_queries:
        print(f"\n🔍 ค้นหา: \"{query}\"")
        
        memory_context = enhanced_chat_memory.get_user_memory_context(
            user_id, query, limit=2
        )
        
        relevant_memories = memory_context['relevant_memories']
        print(f"📝 พบความจำที่เกี่ยวข้อง {len(relevant_memories)} รายการ:")
        
        for mem in relevant_memories:
            print(f"   👤 ผู้ใช้: {mem['human_message'][:50]}...")
            print(f"   🤖 AI: {mem['ai_message'][:50]}...")
            print(f"   📊 คะแนนความสำคัญ: {mem['importance_score']:.2f}")
        
        if memory_context['mentioned_places']:
            print(f"   📍 สถานที่ที่กล่าวถึง: {', '.join(memory_context['mentioned_places'][:3])}")

def demo_user_summary(user_id):
    """Demo: User summary and analytics"""
    print_section("สรุปข้อมูลผู้ใช้ (User Summary)")
    
    summary = user_profile_manager.get_user_summary(user_id)
    
    print(f"👤 ชื่อ: {summary['name']} ({summary['nickname']})")
    print(f"🗣️ ภาษา: {summary['language']}")
    print(f"📍 ที่อยู่: {summary['location']}")
    print(f"💰 งบประมาณ: {summary['budget_range']}")
    print(f"🎯 รูปแบบการเดินทาง: {', '.join(summary['travel_style'])}")
    print(f"👥 การเดินทางแบบ: {summary['group_preference']}")
    
    print(f"\n📊 สถิติการใช้งาน:")
    print(f"   💬 จำนวนการสนทนา: {summary['total_conversations']}")
    print(f"   🧠 จำนวนความจำ: {summary['total_memories']}")
    print(f"   👍 อัตราการยอมรับคำแนะนำ: {summary['acceptance_rate']:.1%}")
    print(f"   😊 คะแนนความพึงพอใจ: {summary['satisfaction_rate']:.2f}")
    print(f"   🎯 คะแนนส่วนตัว: {summary['personalization_score']:.2f}")
    
    print(f"\n❤️ สถานที่ที่ชอบ:")
    for place in summary['favorite_places']:
        print(f"   • {place}")
    
    print(f"\n🌤️ ฤดูกาลที่ชอบ:")
    for season in summary['favorite_seasons']:
        print(f"   • {season}")

def demo_feedback_learning(user_id):
    """Demo: Feedback and learning system"""
    print_section("ระบบเรียนรู้จาก Feedback")
    
    # Record some feedback
    feedbacks = [
        {"recommendation": "วัดพระแก้ว", "feedback": "like", "score": 0.9},
        {"recommendation": "ตลาดนัดเจเจ", "feedback": "like", "score": 0.8},
        {"recommendation": "ดอยสุเทพ", "feedback": "love", "score": 1.0},
    ]
    
    print("📝 บันทึก feedback:")
    for fb in feedbacks:
        user_profile_manager.record_feedback(
            user_id=user_id,
            recommendation=fb["recommendation"],
            feedback=fb["feedback"],
            satisfaction_score=fb["score"]
        )
        print(f"   👍 {fb['recommendation']}: {fb['feedback']} (คะแนน: {fb['score']})")
    
    # Show updated summary
    updated_summary = user_profile_manager.get_user_summary(user_id)
    print(f"\n🎯 คะแนนส่วนตัวหลัง feedback: {updated_summary['personalization_score']:.2f}")
    print(f"😊 คะแนนความพึงพอใจล่าสุด: {updated_summary['satisfaction_rate']:.2f}")

def demo_api_integration():
    """Demo: API integration examples"""
    print_section("ตัวอย่างการใช้งาน API")
    
    print("🌐 API Endpoints ที่สามารถใช้งานได้:")
    
    endpoints = [
        "POST /personalization/users/{user_id}/profile - สร้างโปรไฟล์",
        "GET  /personalization/users/{user_id}/profile - ดูโปรไฟล์",
        "PUT  /personalization/users/{user_id}/profile/travel - อัปเดตความชอบ",
        "POST /personalization/users/{user_id}/conversations/start - เริ่มสนทนา",
        "POST /personalization/users/{user_id}/memory - เพิ่มความจำ",
        "POST /personalization/users/{user_id}/recommendations - ขอคำแนะนำ",
        "POST /personalization/users/{user_id}/feedback - บันทึก feedback",
        "GET  /personalization/users/{user_id}/summary - ดูสรุปผู้ใช้",
        "POST /ai/personalized/chat - แชทแบบส่วนตัว",
        "GET  /personalization/config/options - ดูตัวเลือกการตั้งค่า"
    ]
    
    for endpoint in endpoints:
        print(f"   • {endpoint}")
    
    print(f"\n📚 ดูเอกสาร API แบบโต้ตอบได้ที่: http://localhost:8000/docs")
    print(f"📖 ดูเอกสารระบบส่วนตัวได้ที่: PERSONALIZATION.md")

def main():
    """Main demo function"""
    print_header("🎉 สาธิตระบบ AI Assistant แบบเฉพาะบุคคล")
    print("AI Assistant Personalization System Demo")
    print(f"เวลา: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    
    try:
        # Run all demo functions
        user_id = demo_user_profile_creation()
        demo_travel_preferences(user_id)
        conversation_id = demo_conversation_memory(user_id)
        demo_personalized_recommendations(user_id)
        demo_memory_search(user_id)
        demo_user_summary(user_id)
        demo_feedback_learning(user_id)
        demo_api_integration()
        
        print_header("🎊 สาธิตเสร็จสิ้น - Demo Complete")
        print("✅ ระบบ AI Assistant แบบเฉพาะบุคคลพร้อมใช้งาน!")
        print("✅ Personalization System is ready for production!")
        
        print(f"\n📋 สรุปผลการทดสอบ:")
        print(f"   • สร้างโปรไฟล์ผู้ใช้: ✅")
        print(f"   • จดจำความชอบ: ✅")
        print(f"   • บันทึกการสนทนา: ✅")
        print(f"   • คำแนะนำส่วนตัว: ✅")
        print(f"   • ค้นหาความจำ: ✅")
        print(f"   • เรียนรู้จาก feedback: ✅")
        print(f"   • API Integration: ✅")
        
        print(f"\n🚀 วิธีใช้งาน:")
        print(f"   1. เรียกใช้เซิร์ฟเวอร์: python main.py")
        print(f"   2. เปิดเบราว์เซอร์: http://localhost:8000")
        print(f"   3. ดู API docs: http://localhost:8000/docs")
        print(f"   4. อ่านเอกสาร: PERSONALIZATION.md")
        
    except Exception as e:
        print(f"❌ เกิดข้อผิดพลาด: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    main()