"""
Hugging Face Spaces deployment entry point for PaiNaiDee AI Assistant
"""
import os
import sys
import gradio as gr
import requests
import json
import threading
import time
import uvicorn
from typing import Dict, Any

# Add the painaidee_ai_assistant directory to the Python path
sys.path.append(os.path.join(os.path.dirname(__file__), 'painaidee_ai_assistant'))

# Global variable to store server status
server_running = False
server_url = "http://localhost:8000"

def start_fastapi_server():
    """Start the FastAPI server in a separate thread"""
    global server_running
    try:
        from painaidee_ai_assistant.main import app
        uvicorn.run(app, host="127.0.0.1", port=8000, log_level="warning")
    except Exception as e:
        print(f"Error starting FastAPI server: {e}")
        # Create a minimal server for demo purposes
        from fastapi import FastAPI
        demo_app = FastAPI(title="PaiNaiDee AI Assistant - Demo")
        
        @demo_app.get("/")
        def demo_root():
            return {"message": "🇹🇭 PaiNaiDee AI Assistant Demo", "status": "running"}
        
        @demo_app.post("/ai/select_model")
        def demo_model_selection(request: dict):
            return {
                "selected_model": "Walking.fbx",
                "confidence": 0.85,
                "description": "Demo response - Walking animation",
                "status": "success"
            }
        
        uvicorn.run(demo_app, host="127.0.0.1", port=8000, log_level="warning")

def check_server_health():
    """Check if the FastAPI server is running"""
    try:
        response = requests.get(f"{server_url}/", timeout=5)
        return response.status_code == 200
    except:
        return False

def test_ai_selection(question: str) -> str:
    """Test AI model selection"""
    try:
        if not check_server_health():
            return "❌ Server not ready. Please wait a moment and try again."
        
        response = requests.post(
            f"{server_url}/ai/select_model",
            json={"question": question},
            timeout=10
        )
        
        if response.status_code == 200:
            result = response.json()
            return f"""✅ **AI Response:**
            
**Selected Model:** {result.get('selected_model', 'N/A')}
**Confidence:** {result.get('confidence', 0):.2f}
**Description:** {result.get('description', 'N/A')}
**Status:** {result.get('status', 'N/A')}
"""
        else:
            return f"❌ Error: HTTP {response.status_code}"
            
    except Exception as e:
        return f"❌ Error: {str(e)}"

def test_emotion_analysis(text: str) -> str:
    """Test emotion analysis"""
    try:
        if not check_server_health():
            return "❌ Server not ready. Please wait a moment and try again."
        
        response = requests.post(
            f"{server_url}/emotion/analyze_emotion",
            json={"text": text},
            timeout=10
        )
        
        if response.status_code == 200:
            result = response.json()
            return f"""✅ **Emotion Analysis:**
            
**Primary Emotion:** {result.get('primary_emotion', 'N/A')}
**Confidence:** {result.get('confidence', 0):.2f}
**Suggested Gesture:** {result.get('suggested_gesture', 'N/A')}
"""
        else:
            return f"❌ Error: HTTP {response.status_code}"
            
    except Exception as e:
        return f"❌ Error: {str(e)}"

def get_server_status() -> str:
    """Get server status"""
    if check_server_health():
        return "🟢 **Server Status:** Online and Ready"
    else:
        return "🔴 **Server Status:** Starting... (please wait 30-60 seconds)"

# Start FastAPI server in background
print("🚀 Starting PaiNaiDee AI Assistant server...")
server_thread = threading.Thread(target=start_fastapi_server, daemon=True)
server_thread.start()

# Create Gradio interface
with gr.Blocks(
    title="PaiNaiDee AI Assistant | ผู้ช่วย AI ไปไหนดี",
    theme=gr.themes.Soft(),
    css="""
    .gradio-container {
        max-width: 1200px !important;
    }
    .thai-text {
        font-family: 'Noto Sans Thai', sans-serif;
    }
    """
) as iface:
    
    gr.Markdown("""
    # 🇹🇭 PaiNaiDee AI Assistant | ผู้ช่วย AI ไปไหนดี
    
    ## Intelligent Thai Tourism Assistant with 3D Visualization
    ### ระบบผู้ช่วยท่องเที่ยวอัจฉริยะพร้อม 3D Visualization
    
    **Features | ฟีเจอร์หลัก:**
    - 🤖 AI-powered 3D model selection | การเลือกโมเดล 3D อัตโนมัติ
    - 🎭 Advanced emotion analysis | ระบบวิเคราะห์อารมณ์ขั้นสูง
    - 🌍 Tourism intelligence | ระบบแนะนำท่องเที่ยวอัจฉริยะ
    - 🎮 Interactive 3D viewer | ระบบแสดงผล 3D แบบโต้ตอบ
    """)
    
    with gr.Row():
        status_display = gr.Markdown(get_server_status())
        refresh_btn = gr.Button("🔄 Refresh Status", size="sm")
    
    with gr.Tabs():
        
        with gr.Tab("🤖 AI Model Selection"):
            gr.Markdown("### Ask questions to select appropriate 3D models")
            gr.Markdown("### ถามคำถามเพื่อเลือกโมเดล 3D ที่เหมาะสม")
            
            with gr.Row():
                with gr.Column():
                    model_question = gr.Textbox(
                        label="Your Question | คำถามของคุณ",
                        placeholder="e.g., 'Show me a walking person' or 'หาคนที่กำลังเดิน'",
                        lines=2
                    )
                    model_submit = gr.Button("🎯 Select Model", variant="primary")
                
                with gr.Column():
                    model_result = gr.Markdown(label="AI Response | การตอบสนองของ AI")
            
            gr.Examples(
                examples=[
                    "Show me a walking person",
                    "Display a character in idle pose",
                    "I want to see running animation",
                    "หาคนที่กำลังเดิน",
                    "แสดงตัวละครที่ยืนนิ่ง"
                ],
                inputs=model_question
            )
        
        with gr.Tab("🎭 Emotion Analysis"):
            gr.Markdown("### Analyze emotions from text and get gesture recommendations")
            gr.Markdown("### วิเคราะห์อารมณ์จากข้อความและแนะนำท่าทาง")
            
            with gr.Row():
                with gr.Column():
                    emotion_text = gr.Textbox(
                        label="Your Text | ข้อความของคุณ",
                        placeholder="e.g., 'I'm excited about my trip!' or 'ฉันตื่นเต้นกับการเดินทาง!'",
                        lines=3
                    )
                    emotion_submit = gr.Button("🎭 Analyze Emotion", variant="primary")
                
                with gr.Column():
                    emotion_result = gr.Markdown(label="Emotion Analysis | การวิเคราะห์อารมณ์")
            
            gr.Examples(
                examples=[
                    "I'm so excited about my vacation!",
                    "I'm worried about traveling alone",
                    "This place looks amazing!",
                    "ฉันตื่นเต้นมากกับการเดินทาง!",
                    "ฉันกังวลเรื่องการเดินทางคนเดียว",
                    "สถานที่นี้ดูน่าทึ่งมาก!"
                ],
                inputs=emotion_text
            )
        
        with gr.Tab("📚 API Documentation"):
            gr.Markdown(f"""
            ### 🔗 API Endpoints
            
            Access the full API documentation at: **{server_url}/docs**
            
            **Key Endpoints:**
            - `POST /ai/select_model` - AI model selection
            - `POST /emotion/analyze_emotion` - Emotion analysis
            - `POST /tourism/recommendations/contextual` - Tourism recommendations
            - `GET /performance/system_health` - System health check
            
            ### 🌐 Direct Access
            - **Main API:** {server_url}
            - **Interactive Docs:** {server_url}/docs
            - **Health Check:** {server_url}/performance/system_health
            - **3D Demo:** {server_url}/static/demo.html (if available)
            """)
        
        with gr.Tab("ℹ️ About | เกี่ยวกับ"):
            gr.Markdown("""
            ### 🎯 About PaiNaiDee AI Assistant
            
            **PaiNaiDee** (ไปไหนดี - "Where should I go?") is an intelligent Thai tourism assistant that combines:
            
            - **Advanced AI Models:** BERT-based emotion analysis and natural language processing
            - **3D Visualization:** Interactive 3D models with emotion-responsive animations
            - **Tourism Intelligence:** Context-aware recommendations based on weather, time, and preferences
            - **Cultural Context:** Understanding of Thai tourism patterns and cultural nuances
            - **Multimodal Interface:** Voice, text, and visual interactions
            
            ### 🛠️ Technology Stack
            - **Backend:** FastAPI with Python
            - **AI/ML:** Transformers, PyTorch, scikit-learn
            - **3D Graphics:** Three.js, WebGL
            - **Computer Vision:** OpenCV, MediaPipe
            - **Deployment:** Docker, Hugging Face Spaces
            
            ### 📞 Support
            - **GitHub:** [AI_Assistant_PaiNaiDee](https://github.com/athipan1/AI_Assistant_PaiNaiDee)
            - **Issues:** Report bugs and request features
            - **Documentation:** Comprehensive API docs and tutorials
            
            ---
            **Made with ❤️ for Thai tourism and AI innovation**
            **สร้างด้วยความรักเพื่อการท่องเที่ยวไทยและนวัตกรรม AI**
            """)
    
    # Event handlers
    model_submit.click(
        fn=test_ai_selection,
        inputs=[model_question],
        outputs=[model_result]
    )
    
    emotion_submit.click(
        fn=test_emotion_analysis,
        inputs=[emotion_text],
        outputs=[emotion_result]
    )
    
    refresh_btn.click(
        fn=get_server_status,
        outputs=[status_display]
    )

if __name__ == "__main__":
    # Give server time to start
    time.sleep(5)
    iface.launch(
        server_name="0.0.0.0",
        server_port=7860,
        share=False,
        show_api=False
    )