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
    from api.location_routes import create_location_routes
    from api.emotion_routes import router as emotion_router
    from api.gesture_routes import create_gesture_api_routes
    from api.action_plan_routes import router as action_plan_router
    from api.tts_routes import create_tts_routes
    from api.rag_routes import create_rag_routes
    from api.plugin_routes import create_plugin_routes
    from api.multiuser_routes import create_multiuser_routes
    from api.group_trip_routes import create_group_trip_routes
    from api.public_api_routes import router as public_api_router
    from api.partner_dashboard_routes import router as partner_dashboard_router
    from api.auth_middleware import APIKeyAuthMiddleware
    from api.enhanced_avatar_routes import create_enhanced_avatar_routes
    from api.world_3d_routes import create_3d_world_routes
    HAS_AI_ROUTES = True
    HAS_TOURISM_ROUTES = True
    HAS_LOCATION_ROUTES = True
    HAS_EMOTION_ROUTES = True
    HAS_GESTURE_ROUTES = True
    HAS_ACTION_PLAN_ROUTES = True
    HAS_TTS_ROUTES = True
    HAS_RAG_ROUTES = True
    HAS_PLUGIN_ROUTES = True
    HAS_MULTIUSER_ROUTES = True
    HAS_GROUP_TRIP_ROUTES = True
    HAS_PUBLIC_API_ROUTES = True
    HAS_ENHANCED_AVATAR_ROUTES = True
    HAS_3D_WORLD_ROUTES = True
except ImportError as e:
    print(f"Warning: Could not import AI routes: {e}")
    print("Running in minimal mode - only 3D model features available")
    HAS_AI_ROUTES = False
    HAS_LOCATION_ROUTES = False
    HAS_TOURISM_ROUTES = False
    HAS_EMOTION_ROUTES = False
    HAS_GESTURE_ROUTES = False
    HAS_ACTION_PLAN_ROUTES = False
    HAS_TTS_ROUTES = False
    HAS_RAG_ROUTES = False
    HAS_PLUGIN_ROUTES = False
    HAS_MULTIUSER_ROUTES = False
    HAS_GROUP_TRIP_ROUTES = False
    HAS_PUBLIC_API_ROUTES = False
    HAS_RAG_ROUTES = False
    HAS_PLUGIN_ROUTES = False
    HAS_GROUP_TRIP_ROUTES = False
    HAS_ENHANCED_AVATAR_ROUTES = False
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
    try:
        from api.action_plan_routes import router as action_plan_router
        HAS_ACTION_PLAN_ROUTES = True
    except ImportError as action_e:
        HAS_ACTION_PLAN_ROUTES = False
        print(f"Warning: Action plan routes not available: {action_e}")
        action_plan_router = None
    try:
        from api.tts_routes import create_tts_routes
        HAS_TTS_ROUTES = True
    except ImportError as tts_e:
        HAS_TTS_ROUTES = False
        print(f"Warning: TTS routes not available: {tts_e}")
    try:
        from api.plugin_routes import create_plugin_routes
        HAS_PLUGIN_ROUTES = True
    except ImportError as plugin_e:
        HAS_PLUGIN_ROUTES = False
        print(f"Warning: Plugin routes not available: {plugin_e}")
    performance_router = None

# Load environment variables
load_dotenv()

# Create FastAPI app
app = FastAPI(
    title="PaiNaiDee AI Assistant",
    description="AI-powered tourism assistant for Thailand with 3D model visualization and plugin system",
    version="1.0.0"
)

# Startup event to initialize plugins and Socket.IO
@app.on_event("startup")
async def startup_event():
    """Initialize plugins and Socket.IO on startup"""
    if HAS_PLUGIN_ROUTES:
        try:
            from api.plugin_routes import initialize_default_plugins
            await initialize_default_plugins()
            print("✅ Plugin system initialized successfully")
        except Exception as e:
            print(f"⚠️ Plugin system initialization failed: {e}")
    else:
        print("⚠️ Plugin system not available")
    
    # Initialize Socket.IO for 3D World
    try:
        from api.socketio_3d_world import init_socketio_with_fastapi
        socket_manager = init_socketio_with_fastapi(app)
        print("✅ Socket.IO for 3D World initialized successfully")
    except Exception as e:
        print(f"⚠️ Socket.IO initialization failed: {e}")

# Configure CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Configure this for production
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Add API key authentication middleware for public API routes
if HAS_PUBLIC_API_ROUTES:
    app.add_middleware(APIKeyAuthMiddleware)

# Include API routes
if HAS_AI_ROUTES:
    app.include_router(ai_router, prefix="/ai", tags=["AI Assistant"])

# Add emotion analysis routes
if HAS_EMOTION_ROUTES:
    app.include_router(emotion_router, prefix="/emotion", tags=["Emotion Analysis"])

# Add action plan routes
if HAS_ACTION_PLAN_ROUTES:
    app.include_router(action_plan_router, prefix="/action", tags=["Action Plans"])

# Add location-based tourism routes
if HAS_LOCATION_ROUTES:
    location_router = create_location_routes()
    app.include_router(location_router, tags=["Location Services"])

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

# Add TTS routes
if HAS_TTS_ROUTES:
    create_tts_routes(app)

# Add RAG routes
if HAS_RAG_ROUTES:
    rag_router = create_rag_routes()
    app.include_router(rag_router, tags=["RAG"])

# Add Plugin routes
if HAS_PLUGIN_ROUTES:
    plugin_router = create_plugin_routes()
    app.include_router(plugin_router, tags=["Plugin System"])
    
    # Add admin plugin routes
    try:
        from api.admin_plugin_routes import create_admin_plugin_routes
        admin_plugin_router = create_admin_plugin_routes()
        app.include_router(admin_plugin_router, tags=["Plugin Admin"])
    except ImportError as e:
        print(f"Warning: Admin plugin routes not available: {e}")

# Add performance optimization routes
if performance_router:
    app.include_router(performance_router, prefix="/api", tags=["Performance"])

# Add multi-user collaboration routes
if HAS_MULTIUSER_ROUTES:
    create_multiuser_routes(app)

# Add group trip planning routes
if HAS_GROUP_TRIP_ROUTES:
    try:
        group_trip_router = create_group_trip_routes()
        app.include_router(group_trip_router, tags=["Group Trip Planning"])
    except Exception as e:
        print(f"Warning: Group trip routes not available: {e}")

# Add Public API routes
if HAS_PUBLIC_API_ROUTES:
    app.include_router(public_api_router, tags=["Public API"])
    app.include_router(partner_dashboard_router, tags=["Partner Dashboard"])

# Add enhanced avatar routes
try:
    from api.enhanced_avatar_routes import create_enhanced_avatar_routes
    enhanced_avatar_router = create_enhanced_avatar_routes()
    app.include_router(enhanced_avatar_router, tags=["Enhanced Avatar"])
    print("INFO: Enhanced Avatar API routes added")
except Exception as avatar_e:
    print(f"Warning: Enhanced Avatar routes failed to load: {avatar_e}")

# Add 3D World routes
try:
    from api.world_3d_routes import create_3d_world_routes
    world_3d_router = create_3d_world_routes()
    app.include_router(world_3d_router, tags=["3D World"])
    print("INFO: 3D World API routes added")
except Exception as world_e:
    print(f"Warning: 3D World routes failed to load: {world_e}")

# Add WebXR routes
try:
    from api.webxr_routes import create_webxr_routes
    webxr_router = create_webxr_routes()
    app.include_router(webxr_router, tags=["WebXR/AR"])
    print("INFO: WebXR/AR API routes added")
except Exception as webxr_e:
    print(f"Warning: WebXR routes failed to load: {webxr_e}")

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

@app.get("/3d_world")
async def world_3d_viewer():
    """Serve the 3D World viewer interface"""
    world_3d_path = "static/3d_world_demo.html"
    
    if os.path.exists(world_3d_path):
        return FileResponse(world_3d_path)
    else:
        return {
            "message": "3D World Viewer",
            "status": "available",
            "endpoints": {
                "locations": "/3d_world/locations",
                "ai_navigate": "/3d_world/ai/navigate",
                "ai_action": "/3d_world/ai/action",
                "ai_status": "/3d_world/ai/status",
                "active_users": "/3d_world/users/active",
                "websocket": "/3d_world/ws/{user_id}"
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
            "features": ["3D Model Viewer", "AI Model Selection", "Interactive Controls", "Emotion Analysis", "3D Gesture Recognition", "Plugin System", "External API Integration"],
            "endpoints": {
                "models": "/ai/models",
                "select_model": "/ai/select_model",
                "analyze_emotion": "/emotion/analyze_emotion",
                "recommend_gesture": "/emotion/recommend_gesture",
                "gesture_recognition": "/gesture/recognize",
                "gesture_viewer": "/gesture",
                "action_plans": "/action/generate_plan",
                "execute_plan": "/action/execute_plan",
                "quick_action": "/action/quick_action",
                "plugin_query": "/plugin/query",
                "latest_attractions": "/plugin/get_latest_attractions",
                "event_news": "/plugin/get_event_news", 
                "temple_info": "/plugin/get_temple_info",
                "plugin_admin": "/plugin/admin/stats",
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
                "contextual_recommendations": HAS_TOURISM_ROUTES,
                "multimodal_action_plans": HAS_ACTION_PLAN_ROUTES,
                "intent_to_action_mapping": HAS_ACTION_PLAN_ROUTES,
                "plugin_system": HAS_PLUGIN_ROUTES,
                "external_api_integration": HAS_PLUGIN_ROUTES
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