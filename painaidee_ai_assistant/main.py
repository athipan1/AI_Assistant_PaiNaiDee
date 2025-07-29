"""
PaiNaiDee AI Assistant Backend
FastAPI-based AI assistant for Thai tourism app with 3D model integration
"""

import os
from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse
from dotenv import load_dotenv
import uvicorn

# Import API routes
try:
    from api.ai_routes import router as ai_router
    from api.model_routes import create_model_routes, model_selector
    from api.performance_routes import router as performance_router
    from api.versioning_routes import create_versioning_routes
    from api.cdn_routes import create_cdn_routes
    from api.lod_routes import create_lod_routes
    from api.external_routes import create_external_api_routes
    from api.admin_routes import create_admin_routes
    from api.upload_routes import create_upload_routes
    from api.tourism_routes import create_tourism_routes
    from api.emotion_routes import router as emotion_router
    from api.gesture_routes import create_gesture_api_routes
    HAS_AI_ROUTES = True
    HAS_TOURISM_ROUTES = True
    HAS_EMOTION_ROUTES = True
    HAS_GESTURE_ROUTES = True
except ImportError as e:
    print(f"Warning: Could not import AI routes: {e}")
    print("Running in minimal mode - only 3D model features available")
    HAS_AI_ROUTES = False
    from api.model_routes import create_model_routes, model_selector
    from api.versioning_routes import create_versioning_routes
    from api.cdn_routes import create_cdn_routes
    from api.lod_routes import create_lod_routes
    from api.external_routes import create_external_api_routes
    from api.admin_routes import create_admin_routes
    from api.upload_routes import create_upload_routes
    try:
        from api.tourism_routes import create_tourism_routes
        HAS_TOURISM_ROUTES = True
    except ImportError as tourism_e:
        HAS_TOURISM_ROUTES = False
        print(f"Warning: Tourism enhancement routes not available: {tourism_e}")
    try:
        from api.emotion_routes import router as emotion_router
        HAS_EMOTION_ROUTES = True
    except ImportError as emotion_e:
        HAS_EMOTION_ROUTES = False
        print(f"Warning: Emotion analysis routes not available: {emotion_e}")
        emotion_router = None
    try:
        from api.gesture_routes import create_gesture_api_routes
        HAS_GESTURE_ROUTES = True
    except ImportError as gesture_e:
        HAS_GESTURE_ROUTES = False
        print(f"Warning: Gesture recognition routes not available: {gesture_e}")
    performance_router = None

# Load environment variables
load_dotenv()

# Create FastAPI app
app = FastAPI(
    title="PaiNaiDee AI Assistant",
    description="AI-powered tourism assistant for Thailand with 3D model visualization",
    version="1.0.0"
)

# Configure CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Configure this for production
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Include API routes
if HAS_AI_ROUTES:
    app.include_router(ai_router, prefix="/ai", tags=["AI Assistant"])

# Add emotion analysis routes
if HAS_EMOTION_ROUTES:
    app.include_router(emotion_router, prefix="/emotion", tags=["Emotion Analysis"])

# Add model routes
create_model_routes(app)

# Add versioning routes
create_versioning_routes(app)

# Add CDN routes
create_cdn_routes(app)

# Add LOD prediction routes
create_lod_routes(app)

# Add external API routes
create_external_api_routes(app)

# Add admin dashboard routes
create_admin_routes(app)

# Add upload workflow routes
create_upload_routes(app)

# Add tourism enhancement routes
if HAS_TOURISM_ROUTES:
    create_tourism_routes(app)

# Add gesture recognition routes
if HAS_GESTURE_ROUTES:
    create_gesture_api_routes(app)

# Add performance optimization routes
if performance_router:
    app.include_router(performance_router, prefix="/api", tags=["Performance"])

# Mount static files for 3D viewer
app.mount("/static", StaticFiles(directory="static"), name="static")

# Serve 3D models
@app.get("/models/{model_name}")
async def serve_model(model_name: str):
    """Serve 3D model files"""
    try:
        model_info = model_selector.get_model_info(model_name)
        return FileResponse(model_info["path"])
    except FileNotFoundError:
        raise HTTPException(status_code=404, detail="Model not found")
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/admin")
async def admin_dashboard():
    """Serve the admin dashboard interface"""
    admin_dashboard_path = "static/admin_dashboard.html"
    
    if os.path.exists(admin_dashboard_path):
        return FileResponse(admin_dashboard_path)
    else:
        return {
            "message": "Admin Dashboard",
            "status": "available",
            "endpoints": {
                "overview": "/admin/dashboard/overview",
                "analytics": "/admin/analytics/detailed",
                "moderation": "/admin/content/moderation",
                "system_health": "/admin/system/health"
            }
        }

@app.get("/gesture")
async def gesture_viewer():
    """Serve the enhanced 3D gesture recognition viewer"""
    gesture_viewer_path = "static/gesture_viewer.html"
    
    if os.path.exists(gesture_viewer_path):
        return FileResponse(gesture_viewer_path)
    else:
        return {
            "message": "Enhanced 3D Gesture Recognition Viewer",
            "status": "available",
            "endpoints": {
                "gesture_recognize": "/gesture/recognize",
                "gesture_config": "/gesture/config",
                "custom_gestures": "/gesture/custom/list",
                "performance_stats": "/gesture/performance"
            }
        }

@app.get("/")
async def root():
    """Serve the 3D model viewer interface"""
    # Check if demo version exists, fallback to index
    demo_path = "static/demo.html"
    index_path = "static/index.html"
    
    if os.path.exists(demo_path):
        return FileResponse(demo_path)
    elif os.path.exists(index_path):
        return FileResponse(index_path)
    else:
        return {
            "message": "PaiNaiDee AI Assistant with 3D Models is running!",
            "status": "healthy",
            "version": "1.0.0",
            "features": ["3D Model Viewer", "AI Model Selection", "Interactive Controls", "Emotion Analysis", "3D Gesture Recognition"],
            "endpoints": {
                "models": "/ai/models",
                "select_model": "/ai/select_model",
                "analyze_emotion": "/emotion/analyze_emotion",
                "recommend_gesture": "/emotion/recommend_gesture",
                "gesture_recognition": "/gesture/recognize",
                "gesture_viewer": "/gesture",
                "viewer": "/static/demo.html"
            }
        }

@app.get("/health")
async def health_check():
    """Detailed health check"""
    try:
        available_models = model_selector.list_available_models()
        return {
            "status": "healthy",
            "ai_routes_loaded": HAS_AI_ROUTES,
            "models_available": len(available_models),
            "model_directory": str(model_selector.models_dir),
            "version": "1.0.0",
            "features": {
                "3d_viewer": True,
                "ai_selection": True,
                "model_serving": True,
                "interactive_controls": True,
                "emotion_analysis": HAS_EMOTION_ROUTES,
                "3d_gesture_recognition": HAS_GESTURE_ROUTES,
                "hand_tracking": HAS_GESTURE_ROUTES,
                "webxr_support": HAS_GESTURE_ROUTES,
                "custom_gesture_training": HAS_GESTURE_ROUTES,
                "tourist_interest_graph": HAS_TOURISM_ROUTES,
                "contextual_recommendations": HAS_TOURISM_ROUTES
            }
        }
    except Exception as e:
        return {
            "status": "error",
            "error": str(e),
            "version": "1.0.0"
        }

if __name__ == "__main__":
    # Get configuration from environment
    host = os.getenv("HOST", "0.0.0.0")
    port = int(os.getenv("PORT", 8000))
    
    print("🚀 Starting PaiNaiDee AI Assistant with Enhanced 3D Gesture Recognition...")
    print(f"📡 Server: http://{host}:{port}")
    print(f"🎲 3D Viewer: http://{host}:{port}/static/demo.html")
    print(f"🤏 Gesture Recognition: http://{host}:{port}/gesture")
    print(f"📚 API Docs: http://{host}:{port}/docs")
    print("=" * 60)
    
    uvicorn.run(
        "main:app",
        host=host,
        port=port,
        reload=True,  # Set to False in production
        workers=1     # Increase for production
    )