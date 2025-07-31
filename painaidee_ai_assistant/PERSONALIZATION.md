# Enhanced AI Assistant Personalization System

## ภาพรวม (Overview)

ระบบ AI Assistant ที่สามารถเรียนรู้ความชอบของผู้ใช้แบบ Personalization พร้อมระบบจดจำข้อมูลส่วนบุคคลและให้คำแนะนำการท่องเที่ยวแบบเฉพาะบุคคล

The enhanced AI Assistant now includes comprehensive personalization features that can learn user preferences and provide personalized travel recommendations.

## 🎯 ฟีเจอร์หลัก (Key Features)

### 1. การจดจำข้อมูลผู้ใช้ (User Profile Management)
- **ชื่อและข้อมูลส่วนตัว**: จดจำชื่อ, ชื่อเล่น, อายุ, ที่อยู่
- **ความชอบสถานที่**: จดจำสถานที่ที่ผู้ใช้สนใจ
- **ฤดูกาลโปรด**: จดจำฤดูกาลที่ผู้ใช้ชอบเดินทาง (ร้อน, ฝน, หนาว)
- **งบประมาณ**: จดจำช่วงงบประมาณ (ประหยัด, ปานกลาง, หรูหรา)
- **รูปแบบการเดินทาง**: จดจำสไตล์การท่องเที่ยวที่ชอบ

### 2. ระบบหน่วยความจำการสนทนา (Enhanced Chat Memory)
- **การจัดเก็บบทสนทนา**: เก็บประวัติการสนทนาแบบถาวร
- **การค้นหาความจำ**: ค้นหาบทสนทนาที่เกี่ยวข้องจากอดีต
- **บริบทการสนทนา**: จดจำบริบทและหัวข้อที่กำลังพูดถึง
- **คะแนนความสำคัญ**: จัดอันดับความสำคัญของความจำแต่ละรายการ

### 3. คำแนะนำแบบเฉพาะบุคคล (Personalized Recommendations)
- **การแนะนำตามความชอบ**: แนะนำสถานที่ตามประวัติความสนใจ
- **การแนะนำตามบริบท**: คำนึงถึงสภาพอากาศ, เวลา, ฤดูกาล
- **การให้คะแนนความเหมาะสม**: คำนวณคะแนนความเหมาะสมสำหรับแต่ละคำแนะนำ
- **เหตุผลของการแนะนำ**: อธิบายเหตุผลที่แนะนำสถานที่นั้น

### 4. การเรียนรู้จาก Feedback
- **บันทึกความคิดเห็น**: เก็บ feedback จากผู้ใช้
- **ปรับปรุงการแนะนำ**: ใช้ feedback เพื่อปรับปรุงคำแนะนำในอนาคต
- **คะแนนความพึงพอใจ**: ติดตามระดับความพึงพอใจของผู้ใช้

## 🚀 การใช้งาน API (API Usage)

### สร้างโปรไฟล์ผู้ใช้ใหม่
```bash
curl -X POST "http://localhost:8000/personalization/users/user_001/profile" \
-H "Content-Type: application/json" \
-d '{
  "name": "นายสมชาย ใจดี",
  "nickname": "สมชาย", 
  "age_range": "26-35",
  "language_preference": "th",
  "location": "กรุงเทพมหานคร",
  "budget_range": "mid"
}'
```

### อัปเดตความชอบการเดินทาง
```bash
curl -X PUT "http://localhost:8000/personalization/users/user_001/profile/travel" \
-H "Content-Type: application/json" \
-d '{
  "favorite_places": ["วัดพระแก้ว", "ภูเก็ต", "เชียงใหม่"],
  "favorite_seasons": ["cool", "hot"],
  "place_types": ["temple", "beach", "mountain"],
  "travel_style": ["cultural", "relaxing"],
  "budget_range": "mid",
  "group_preference": "family"
}'
```

### เริ่มการสนทนาใหม่
```bash
curl -X POST "http://localhost:8000/personalization/users/user_001/conversations/start" \
-H "Content-Type: application/json" \
-d '{
  "session_id": "session_001"
}'
```

### เพิ่มความจำการสนทนา
```bash
curl -X POST "http://localhost:8000/personalization/users/user_001/memory" \
-H "Content-Type: application/json" \
-d '{
  "conversation_id": "user_001_session_001_1234567890",
  "user_message": "อยากไปเที่ยววัดที่สวยๆ",
  "bot_response": "แนะนำวัดพระแก้วและวัดอรุณราชวราราม เหมาะสำหรับการท่องเที่ยวเชิงวัฒนธรรม",
  "importance_score": 0.8,
  "context": {
    "topic": "temple_tourism",
    "season": "cool"
  }
}'
```

### ขอคำแนะนำแบบเฉพาะบุคคล
```bash
curl -X POST "http://localhost:8000/personalization/users/user_001/recommendations" \
-H "Content-Type: application/json" \
-d '{
  "query": "อยากไปเที่ยวที่มีวิวสวย",
  "context": {
    "season": "cool",
    "weather": "sunny"
  },
  "limit": 5
}'
```

### แชทกับ AI แบบส่วนตัว
```bash
curl -X POST "http://localhost:8000/ai/personalized/chat?user_id=user_001" \
-H "Content-Type: application/json" \
-d '{
  "message": "แนะนำที่เที่ยวสำหรับครอบครัวหน่อย",
  "session_id": "chat_session_001"
}'
```

## 📊 โครงสร้างข้อมูล (Data Structure)

### UserProfile
```python
{
  "user_id": "user_001",
  "personal_info": {
    "name": "นายสมชาย ใจดี",
    "nickname": "สมชาย",
    "age_range": "26-35",
    "language_preference": "th",
    "location": "กรุงเทพมหานคร"
  },
  "travel_preferences": {
    "favorite_places": ["วัดพระแก้ว", "ภูเก็ต"],
    "favorite_seasons": ["cool", "hot"],
    "budget_range": "mid",
    "travel_style": ["cultural", "relaxing"],
    "group_preference": "family"
  },
  "interaction_history": {
    "total_conversations": 15,
    "total_recommendations_accepted": 8,
    "satisfaction_rate": 0.85,
    "personalization_score": 0.75
  }
}
```

### Personalized Recommendation
```python
{
  "place_name": "วัดพระแก้ว",
  "place_name_en": "Temple of the Emerald Buddha",
  "type": "temple",
  "province": "กรุงเทพมหานคร",
  "score": 0.85,
  "reasons": [
    "ตรงกับประเภทสถานที่ที่ชอบ (temple)",
    "เหมาะสมกับงบประมาณmid",
    "ตรงกับสถานที่ที่เคยสนใจ"
  ],
  "personalization_level": "high"
}
```

## 🔧 การติดตั้งและตั้งค่า (Installation & Setup)

### ข้อกำหนดเพิ่มเติม
```bash
# ติดตั้ง dependencies เพิ่มเติม (ถ้าต้องการ)
pip install sqlalchemy psycopg2-binary redis pinecone-client alembic
```

### ตัวแปรสิ่งแวดล้อม
```bash
# .env file
DATABASE_URL=sqlite:///./cache/user_profiles/personalization.db
REDIS_URL=redis://localhost:6379/0
PINECONE_API_KEY=your_pinecone_api_key
PINECONE_ENVIRONMENT=your_pinecone_environment
```

## 🧪 การทดสอบ (Testing)

### รันการทดสอบ
```bash
cd painaidee_ai_assistant
python -m pytest tests/test_personalization.py -v
```

### ตัวอย่างการทดสอบแบบเร็ว
```python
from models.user_profile import user_profile_manager

# สร้างผู้ใช้ทดสอบ
profile = user_profile_manager.create_user_profile(
    user_id='test_user',
    name='Test User',
    budget_range='mid'
)

# อัปเดตความชอบ
user_profile_manager.update_travel_preferences(
    'test_user',
    favorite_places=['วัดพระแก้ว'],
    favorite_seasons=['cool']
)

# ขอคำแนะนำ
recommendations = user_profile_manager.get_personalized_recommendations(
    'test_user',
    query='วัดที่สวย'
)

print(f"Got {len(recommendations)} recommendations")
```

## 📈 คุณสมบัติการเรียนรู้ (Learning Capabilities)

### 1. การเรียนรู้จากการโต้ตอบ
- ระบบจะเรียนรู้จากทุกการสนทนา
- ปรับคะแนนความสำคัญตามการใช้งาน
- จดจำสถานที่ที่ผู้ใช้สนใจจากบทสนทนา

### 2. การปรับปรุงตามเวลา
- ความจำเก่าจะลดความสำคัญลง
- ความชอบใหม่จะได้รับน้ำหนักมากขึ้น
- ระบบจะปรับตัวตามพฤติกรรมที่เปลี่ยนไป

### 3. การกรองตามบริบท
- คำนึงถึงฤดูกาลปัจจุบัน
- พิจารณาสภาพอากาศ
- ปรับคำแนะนำตามเวลาในวัน

## 🔒 ความปลอดภัยและความเป็นส่วนตัว (Privacy & Security)

### การป้องกันข้อมูล
- ข้อมูลผู้ใช้เข้ารหัสในฐานข้อมูล
- ไม่แชร์ข้อมูลส่วนบุคคลระหว่างผู้ใช้
- มีระบบทำลายข้อมูลเมื่อผู้ใช้ขอลบ

### การควบคุมข้อมูล
- ผู้ใช้สามารถขอดูข้อมูลทั้งหมดได้
- สามารถแก้ไขหรือลบข้อมูลได้
- มีการ export ข้อมูลในรูปแบบ JSON

## 🚀 การพัฒนาต่อ (Future Enhancements)

### ระยะใกล้
- [ ] เพิ่มการรองรับ PostgreSQL
- [ ] เพิ่มการรองรับ Redis
- [ ] เพิ่ม Pinecone Vector Database
- [ ] เพิ่มการรองรับ LangChain Memory

### ระยะกลาง
- [ ] ระบบแนะนำแบบ Collaborative Filtering
- [ ] การเรียนรู้แบบ Deep Learning
- [ ] ระบบจัดกลุ่มผู้ใช้
- [ ] API สำหรับ Mobile App

### ระยะไกล
- [ ] ระบบ AI แบบ Multi-modal
- [ ] การรองรับภาษาต่างประเทศ
- [ ] ระบบคาดการณ์ทำเนียบเดินทาง
- [ ] การเชื่อมต่อกับระบบจองที่พัก

## 📞 การสนับสนุน (Support)

หากพบปัญหาหรือต้องการความช่วยเหลือ:
1. ตรวจสอบ logs ในไฟล์ `logs/personalization.log`
2. รันการทดสอบด้วย `pytest tests/test_personalization.py`
3. ตรวจสอบการตั้งค่าในไฟล์ `.env`

## 🎉 สรุป

ระบบ AI Assistant Personalization ให้ความสามารถในการ:
- จดจำข้อมูลส่วนตัวและความชอบของผู้ใช้
- ให้คำแนะนำการท่องเที่ยวแบบเฉพาะบุคคล
- เรียนรู้และปรับปรุงจากการโต้ตอบ
- จัดเก็บและค้นหาความจำการสนทนา
- รองรับการใช้งานแบบ Multi-session

ระบบนี้ทำให้ AI Assistant สามารถให้บริการที่ดีขึ้นและตรงกับความต้องการของผู้ใช้แต่ละคนมากยิ่งขึ้น