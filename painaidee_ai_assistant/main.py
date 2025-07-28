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
    HAS_AI_ROUTES = True
except ImportError as e:
    print(f"Warning: Could not import AI routes: {e}")
    print("Running in minimal mode - only 3D model features available")
    HAS_AI_ROUTES = False
    from api.model_routes import create_model_routes, model_selector

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

# Add model routes
create_model_routes(app)

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
            "features": ["3D Model Viewer", "AI Model Selection", "Interactive Controls"],
            "endpoints": {
                "models": "/ai/models",
                "select_model": "/ai/select_model",
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
                "interactive_controls": True
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
    
    print("🚀 Starting PaiNaiDee AI Assistant with 3D Models...")
    print(f"📡 Server: http://{host}:{port}")
    print(f"🎲 3D Viewer: http://{host}:{port}/static/demo.html")
    print(f"📚 API Docs: http://{host}:{port}/docs")
    print("=" * 60)
    
    uvicorn.run(
        "main:app",
        host=host,
        port=port,
        reload=True,  # Set to False in production
        workers=1     # Increase for production
    )