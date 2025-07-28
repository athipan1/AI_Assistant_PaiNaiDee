"""
API routes for Model Versioning and Delta Updates
Provides RESTful endpoints for managing model versions and efficient updates
"""

from fastapi import APIRouter, HTTPException, UploadFile, File, Form
from typing import List, Optional, Dict, Any
from pydantic import BaseModel
import os
import tempfile
import json

from ..models.versioning import versioning_manager, ModelVersion


# Pydantic models for request/response
class VersionCreateRequest(BaseModel):
    version: Optional[str] = None
    description: str = ""
    changes: List[str] = []
    increment_type: str = "patch"  # major, minor, patch


class VersionResponse(BaseModel):
    version: str
    model_name: str
    file_size: int
    created_at: str
    description: str
    changes: List[str]
    delta_size: Optional[int] = None
    has_delta: bool = False


class UpdateSizeResponse(BaseModel):
    update_method: str
    size: int
    compression_ratio: float
    bandwidth_saved: int


def create_versioning_routes(app):
    """Add versioning routes to FastAPI app"""
    
    @app.post("/api/versions/create/{model_name}")
    async def create_model_version(
        model_name: str,
        request: VersionCreateRequest,
        model_file: UploadFile = File(...)
    ):
        """Create a new version of a model"""
        try:
            # Save uploaded file temporarily
            with tempfile.NamedTemporaryFile(delete=False, suffix=f"_{model_name}") as temp_file:
                content = await model_file.read()
                temp_file.write(content)
                temp_path = temp_file.name
            
            try:
                # Create version
                version = versioning_manager.create_version(
                    model_path=temp_path,
                    version=request.version,
                    description=request.description,
                    changes=request.changes,
                    increment_type=request.increment_type
                )
                
                return {
                    "message": f"Version {version.version} created successfully",
                    "version": VersionResponse(
                        version=version.version,
                        model_name=version.model_name,
                        file_size=version.file_size,
                        created_at=version.created_at,
                        description=version.description,
                        changes=version.changes,
                        delta_size=version.delta_size,
                        has_delta=version.delta_from_previous is not None
                    ),
                    "status": "success"
                }
                
            finally:
                # Clean up temp file
                os.unlink(temp_path)
                
        except Exception as e:
            raise HTTPException(status_code=400, detail=str(e))
    
    @app.get("/api/versions/{model_name}")
    async def list_model_versions(model_name: str):
        """List all versions of a model"""
        try:
            versions = versioning_manager.get_versions(model_name)
            
            if not versions:
                return {
                    "versions": [],
                    "count": 0,
                    "status": "success"
                }
            
            version_responses = [
                VersionResponse(
                    version=v.version,
                    model_name=v.model_name,
                    file_size=v.file_size,
                    created_at=v.created_at,
                    description=v.description,
                    changes=v.changes,
                    delta_size=v.delta_size,
                    has_delta=v.delta_from_previous is not None
                )
                for v in versions
            ]
            
            return {
                "versions": version_responses,
                "count": len(version_responses),
                "status": "success"
            }
            
        except Exception as e:
            raise HTTPException(status_code=500, detail=str(e))
    
    @app.get("/api/versions/{model_name}/{version}")
    async def get_model_version(model_name: str, version: str):
        """Get specific version details"""
        try:
            model_version = versioning_manager.get_version(model_name, version)
            
            if not model_version:
                raise HTTPException(status_code=404, detail="Version not found")
            
            return {
                "version": VersionResponse(
                    version=model_version.version,
                    model_name=model_version.model_name,
                    file_size=model_version.file_size,
                    created_at=model_version.created_at,
                    description=model_version.description,
                    changes=model_version.changes,
                    delta_size=model_version.delta_size,
                    has_delta=model_version.delta_from_previous is not None
                ),
                "status": "success"
            }
            
        except HTTPException:
            raise
        except Exception as e:
            raise HTTPException(status_code=500, detail=str(e))
    
    @app.get("/api/versions/{model_name}/latest")
    async def get_latest_version(model_name: str):
        """Get the latest version of a model"""
        try:
            latest = versioning_manager.get_latest_version(model_name)
            
            if not latest:
                raise HTTPException(status_code=404, detail="Model not found")
            
            return {
                "version": VersionResponse(
                    version=latest.version,
                    model_name=latest.model_name,
                    file_size=latest.file_size,
                    created_at=latest.created_at,
                    description=latest.description,
                    changes=latest.changes,
                    delta_size=latest.delta_size,
                    has_delta=latest.delta_from_previous is not None
                ),
                "status": "success"
            }
            
        except HTTPException:
            raise
        except Exception as e:
            raise HTTPException(status_code=500, detail=str(e))
    
    @app.get("/api/versions/{model_name}/history")
    async def get_version_history(model_name: str):
        """Get comprehensive version history"""
        try:
            history = versioning_manager.get_version_history(model_name)
            
            if "error" in history:
                raise HTTPException(status_code=404, detail=history["error"])
            
            return {
                "history": history,
                "status": "success"
            }
            
        except HTTPException:
            raise
        except Exception as e:
            raise HTTPException(status_code=500, detail=str(e))
    
    @app.get("/api/versions/{model_name}/update-size/{from_version}/{to_version}")
    async def calculate_update_size(model_name: str, from_version: str, to_version: str):
        """Calculate the bandwidth needed for updating between versions"""
        try:
            size_info = versioning_manager.calculate_update_size(model_name, from_version, to_version)
            
            if "error" in size_info:
                raise HTTPException(status_code=404, detail=size_info["error"])
            
            return {
                "update_info": UpdateSizeResponse(
                    update_method=size_info["update_method"],
                    size=size_info["size"],
                    compression_ratio=size_info["compression_ratio"],
                    bandwidth_saved=size_info["bandwidth_saved"]
                ),
                "status": "success"
            }
            
        except HTTPException:
            raise
        except Exception as e:
            raise HTTPException(status_code=500, detail=str(e))
    
    @app.post("/api/versions/{model_name}/apply-delta")
    async def apply_delta_update(
        model_name: str,
        from_version: str = Form(...),
        to_version: str = Form(...),
        base_file: UploadFile = File(...)
    ):
        """Apply a delta update to upgrade a model file"""
        try:
            # Get version info
            to_ver = versioning_manager.get_version(model_name, to_version)
            if not to_ver or not to_ver.delta_from_previous:
                raise HTTPException(status_code=404, detail="Delta update not available")
            
            # Save base file temporarily
            with tempfile.NamedTemporaryFile(delete=False) as temp_base:
                content = await base_file.read()
                temp_base.write(content)
                temp_base_path = temp_base.name
            
            try:
                # Apply delta
                with tempfile.NamedTemporaryFile(delete=False) as temp_output:
                    temp_output_path = temp_output.name
                
                success = versioning_manager.apply_delta(
                    base_file=temp_base_path,
                    delta_file=to_ver.delta_from_previous,
                    output_file=temp_output_path
                )
                
                if not success:
                    raise HTTPException(status_code=400, detail="Failed to apply delta update")
                
                # Read updated file
                with open(temp_output_path, 'rb') as f:
                    updated_content = f.read()
                
                return {
                    "message": f"Delta update applied successfully",
                    "from_version": from_version,
                    "to_version": to_version,
                    "output_size": len(updated_content),
                    "status": "success"
                }
                
            finally:
                # Clean up temp files
                os.unlink(temp_base_path)
                if os.path.exists(temp_output_path):
                    os.unlink(temp_output_path)
                
        except HTTPException:
            raise
        except Exception as e:
            raise HTTPException(status_code=500, detail=str(e))
    
    @app.delete("/api/versions/{model_name}/cleanup")
    async def cleanup_old_versions(model_name: str, keep_latest: int = 5):
        """Clean up old versions to save storage space"""
        try:
            result = versioning_manager.cleanup_old_versions(model_name, keep_latest)
            
            return {
                "cleanup_result": result,
                "status": "success"
            }
            
        except Exception as e:
            raise HTTPException(status_code=500, detail=str(e))
    
    @app.get("/api/versions/summary")
    async def get_versioning_summary():
        """Get overall versioning system summary"""
        try:
            summary = {
                "total_models": 0,
                "total_versions": 0,
                "total_storage_size": 0,
                "total_delta_size": 0,
                "compression_efficiency": 0,
                "models": []
            }
            
            # Iterate through all models in metadata
            for model_name in versioning_manager.metadata:
                history = versioning_manager.get_version_history(model_name)
                if "error" not in history:
                    summary["total_models"] += 1
                    summary["total_versions"] += history["total_versions"]
                    summary["total_storage_size"] += history["total_storage_size"]
                    summary["total_delta_size"] += history["total_delta_size"]
                    
                    summary["models"].append({
                        "model_name": model_name,
                        "versions": history["total_versions"],
                        "latest_version": history["latest_version"],
                        "storage_size": history["total_storage_size"]
                    })
            
            # Calculate overall compression efficiency
            if summary["total_storage_size"] > 0:
                summary["compression_efficiency"] = (
                    summary["total_storage_size"] - summary["total_delta_size"]
                ) / summary["total_storage_size"]
            
            return {
                "summary": summary,
                "status": "success"
            }
            
        except Exception as e:
            raise HTTPException(status_code=500, detail=str(e))


# Create router instance
versioning_router = APIRouter()

def setup_versioning_routes():
    """Setup all versioning routes"""
    
    # Define routes on the router
    # (Routes are defined in the create_versioning_routes function above
    # but for FastAPI router pattern, we'll recreate them here)
    
    @versioning_router.post("/versions/create/{model_name}")
    async def create_model_version_route(
        model_name: str,
        request: VersionCreateRequest,
        model_file: UploadFile = File(...)
    ):
        # Implementation moved to create_versioning_routes for now
        pass
    
    return versioning_router