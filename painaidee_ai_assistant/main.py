"""
PaiNaiDee AI Assistant Backend
FastAPI-based AI assistant for Thai tourism app
"""

import os
from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from dotenv import load_dotenv
import uvicorn

# Import API routes
from api.ai_routes import router as ai_router

# Load environment variables
load_dotenv()

# Create FastAPI app
app = FastAPI(
    title="PaiNaiDee AI Assistant",
    description="AI-powered tourism assistant for Thailand",
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
app.include_router(ai_router, prefix="/ai", tags=["AI Assistant"])

@app.get("/")
async def root():
    """Health check endpoint"""
    return {
        "message": "PaiNaiDee AI Assistant is running!",
        "status": "healthy",
        "version": "1.0.0"
    }

@app.get("/health")
async def health_check():
    """Detailed health check"""
    return {
        "status": "healthy",
        "ai_models_loaded": True,  # This would check actual model status
        "version": "1.0.0"
    }

if __name__ == "__main__":
    # Get configuration from environment
    host = os.getenv("HOST", "0.0.0.0")
    port = int(os.getenv("PORT", 8000))
    
    uvicorn.run(
        "main:app",
        host=host,
        port=port,
        reload=True,  # Set to False in production
        workers=1     # Increase for production
    )