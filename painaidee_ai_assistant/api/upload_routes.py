"""
API routes for Upload & Approval Workflow
Provides RESTful endpoints for file upload, validation, and content moderation
"""

from fastapi import APIRouter, HTTPException, UploadFile, File, Form, Depends
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from typing import List, Optional, Dict, Any
from pydantic import BaseModel
import os

from models.upload_workflow import upload_workflow, UploadStatus


# Simple authentication (in production, use proper JWT/OAuth)
security = HTTPBearer()

def verify_user_token(credentials: HTTPAuthorizationCredentials = Depends(security)):
    """Verify user authentication token"""
    # In production, verify JWT token and extract user info
    return {"user_id": "demo_user", "role": "user"}

def verify_moderator_token(credentials: HTTPAuthorizationCredentials = Depends(security)):
    """Verify moderator authentication token"""
    # In production, verify JWT token and check moderator permissions
    return {"user_id": "demo_moderator", "role": "moderator"}


# Pydantic models for request/response
class UploadInitiateRequest(BaseModel):
    filename: str
    file_size: int
    description: str = ""
    tags: List[str] = []
    categories: List[str] = []
    license: str = "unknown"
    is_public: bool = False
    auto_approve: bool = False


class ModerationDecisionRequest(BaseModel):
    file_id: str
    decision: str  # approve, reject, request_changes
    comments: str = ""
    quality_score: Optional[float] = None


class UploadMetadata(BaseModel):
    title: str
    description: str = ""
    tags: List[str] = []
    categories: List[str] = []
    license: str = "unknown"
    is_public: bool = False
    auto_approve: bool = False


def create_upload_routes(app):
    """Add upload and workflow routes to FastAPI app"""
    
    @app.post("/api/upload/initiate")
    async def initiate_upload(
        request: UploadInitiateRequest,
        user_info: dict = Depends(verify_user_token)
    ):
        """Initiate file upload process"""
        try:
            metadata = {
                "title": request.filename,
                "description": request.description,
                "tags": request.tags,
                "categories": request.categories,
                "license": request.license,
                "is_public": request.is_public,
                "auto_approve": request.auto_approve
            }
            
            result = await upload_workflow.initiate_upload(
                uploader_id=user_info["user_id"],
                filename=request.filename,
                file_size=request.file_size,
                metadata=metadata
            )
            
            return result
            
        except Exception as e:
            raise HTTPException(status_code=500, detail=str(e))
    
    @app.post("/api/upload/{file_id}")
    async def upload_file(
        file_id: str,
        file: UploadFile = File(...),
        metadata: str = Form("{}"),
        user_info: dict = Depends(verify_user_token)
    ):
        """Upload file content"""
        try:
            import json
            
            # Parse metadata
            try:
                metadata_dict = json.loads(metadata)
            except json.JSONDecodeError:
                metadata_dict = {}
            
            # Read file content
            file_content = await file.read()
            
            # Process uploaded file
            result = await upload_workflow.process_uploaded_file(
                file_id=file_id,
                file_content=file_content,
                metadata=metadata_dict
            )
            
            return result
            
        except Exception as e:
            raise HTTPException(status_code=500, detail=str(e))
    
    @app.get("/api/upload/{file_id}/progress")
    async def get_upload_progress(
        file_id: str,
        user_info: dict = Depends(verify_user_token)
    ):
        """Get upload progress for a file"""
        try:
            progress = upload_workflow.get_upload_progress(file_id)
            
            return {
                "progress": progress,
                "status": "success"
            }
            
        except Exception as e:
            raise HTTPException(status_code=500, detail=str(e))
    
    @app.get("/api/uploads/my")
    async def get_my_uploads(
        status: Optional[str] = None,
        user_info: dict = Depends(verify_user_token)
    ):
        """Get current user's uploads"""
        try:
            uploads = upload_workflow.get_user_uploads(
                uploader_id=user_info["user_id"],
                status=status
            )
            
            return {
                "uploads": uploads,
                "count": len(uploads),
                "status": "success"
            }
            
        except Exception as e:
            raise HTTPException(status_code=500, detail=str(e))
    
    @app.get("/api/uploads/{file_id}")
    async def get_upload_details(
        file_id: str,
        user_info: dict = Depends(verify_user_token)
    ):
        """Get detailed information about an upload"""
        try:
            if file_id not in upload_workflow.uploaded_files:
                raise HTTPException(status_code=404, detail="Upload not found")
            
            uploaded_file = upload_workflow.uploaded_files[file_id]
            
            # Check permissions (user can see their own uploads, moderators can see all)
            if (uploaded_file.uploader_id != user_info["user_id"] and 
                user_info.get("role") not in ["moderator", "admin"]):
                raise HTTPException(status_code=403, detail="Access denied")
            
            # Get reviews for this file
            file_reviews = [
                {
                    "review_id": review.review_id,
                    "reviewer_id": review.reviewer_id,
                    "review_timestamp": review.review_timestamp,
                    "decision": review.decision,
                    "comments": review.comments,
                    "quality_score": review.quality_score
                }
                for review in upload_workflow.moderation_reviews.values()
                if review.file_id == file_id
            ]
            
            upload_details = {
                "file_id": file_id,
                "original_filename": uploaded_file.original_filename,
                "file_size": uploaded_file.file_size,
                "content_type": uploaded_file.content_type,
                "uploader_id": uploaded_file.uploader_id,
                "upload_timestamp": uploaded_file.upload_timestamp,
                "status": uploaded_file.status.value,
                "description": uploaded_file.description,
                "tags": uploaded_file.tags,
                "categories": uploaded_file.categories,
                "license": uploaded_file.license,
                "is_public": uploaded_file.is_public,
                "validation_results": uploaded_file.validation_results,
                "reviews": file_reviews
            }
            
            return {
                "upload_details": upload_details,
                "status": "success"
            }
            
        except HTTPException:
            raise
        except Exception as e:
            raise HTTPException(status_code=500, detail=str(e))
    
    @app.get("/api/moderation/queue")
    async def get_moderation_queue(
        status: Optional[str] = None,
        moderator_info: dict = Depends(verify_moderator_token)
    ):
        """Get files pending moderation (moderator only)"""
        try:
            queue = upload_workflow.get_moderation_queue(status)
            
            return {
                "moderation_queue": queue,
                "count": len(queue),
                "status": "success"
            }
            
        except Exception as e:
            raise HTTPException(status_code=500, detail=str(e))
    
    @app.post("/api/moderation/review")
    async def submit_moderation_review(
        request: ModerationDecisionRequest,
        moderator_info: dict = Depends(verify_moderator_token)
    ):
        """Submit moderation review (moderator only)"""
        try:
            result = await upload_workflow.submit_moderation_review(
                file_id=request.file_id,
                reviewer_id=moderator_info["user_id"],
                decision=request.decision,
                comments=request.comments,
                quality_score=request.quality_score
            )
            
            return result
            
        except Exception as e:
            raise HTTPException(status_code=500, detail=str(e))
    
    @app.get("/api/uploads/statistics")
    async def get_upload_statistics(
        moderator_info: dict = Depends(verify_moderator_token)
    ):
        """Get upload and workflow statistics (moderator only)"""
        try:
            stats = upload_workflow.get_workflow_statistics()
            
            return {
                "workflow_statistics": stats,
                "status": "success"
            }
            
        except Exception as e:
            raise HTTPException(status_code=500, detail=str(e))
    
    @app.get("/api/uploads/all")
    async def get_all_uploads(
        status: Optional[str] = None,
        uploader_id: Optional[str] = None,
        limit: int = 50,
        offset: int = 0,
        moderator_info: dict = Depends(verify_moderator_token)
    ):
        """Get all uploads with filtering (moderator only)"""
        try:
            all_uploads = []
            
            for file_id, uploaded_file in upload_workflow.uploaded_files.items():
                # Apply filters
                if status and uploaded_file.status.value != status:
                    continue
                if uploader_id and uploaded_file.uploader_id != uploader_id:
                    continue
                
                upload_info = {
                    "file_id": file_id,
                    "original_filename": uploaded_file.original_filename,
                    "uploader_id": uploaded_file.uploader_id,
                    "upload_timestamp": uploaded_file.upload_timestamp,
                    "status": uploaded_file.status.value,
                    "file_size": uploaded_file.file_size,
                    "description": uploaded_file.description,
                    "tags": uploaded_file.tags,
                    "categories": uploaded_file.categories,
                    "review_count": len([r for r in upload_workflow.moderation_reviews.values() if r.file_id == file_id])
                }
                all_uploads.append(upload_info)
            
            # Sort by upload timestamp (newest first)
            all_uploads.sort(key=lambda x: x["upload_timestamp"], reverse=True)
            
            # Apply pagination
            paginated_uploads = all_uploads[offset:offset + limit]
            
            return {
                "uploads": paginated_uploads,
                "total_count": len(all_uploads),
                "returned_count": len(paginated_uploads),
                "offset": offset,
                "limit": limit,
                "status": "success"
            }
            
        except Exception as e:
            raise HTTPException(status_code=500, detail=str(e))
    
    @app.post("/api/uploads/{file_id}/reprocess")
    async def reprocess_upload(
        file_id: str,
        moderator_info: dict = Depends(verify_moderator_token)
    ):
        """Reprocess an upload through validation (moderator only)"""
        try:
            if file_id not in upload_workflow.uploaded_files:
                raise HTTPException(status_code=404, detail="Upload not found")
            
            uploaded_file = upload_workflow.uploaded_files[file_id]
            
            # Re-run validation
            validation_results = await upload_workflow.validator.validate_file(
                uploaded_file.file_path,
                uploaded_file.metadata
            )
            
            # Update validation results
            uploaded_file.validation_results = validation_results
            
            # Update status based on new validation
            has_errors = any(r["result"] == "fail" for r in validation_results)
            if has_errors:
                uploaded_file.status = UploadStatus.ERROR
            else:
                uploaded_file.status = UploadStatus.PENDING_REVIEW
            
            upload_workflow._save_workflow_data()
            
            return {
                "message": "Upload reprocessed successfully",
                "new_status": uploaded_file.status.value,
                "validation_results": validation_results,
                "status": "success"
            }
            
        except HTTPException:
            raise
        except Exception as e:
            raise HTTPException(status_code=500, detail=str(e))
    
    @app.delete("/api/uploads/{file_id}")
    async def delete_upload(
        file_id: str,
        user_info: dict = Depends(verify_user_token)
    ):
        """Delete an upload"""
        try:
            if file_id not in upload_workflow.uploaded_files:
                raise HTTPException(status_code=404, detail="Upload not found")
            
            uploaded_file = upload_workflow.uploaded_files[file_id]
            
            # Check permissions (user can delete their own uploads, moderators can delete any)
            if (uploaded_file.uploader_id != user_info["user_id"] and 
                user_info.get("role") not in ["moderator", "admin"]):
                raise HTTPException(status_code=403, detail="Access denied")
            
            # Delete physical file
            try:
                if os.path.exists(uploaded_file.file_path):
                    os.remove(uploaded_file.file_path)
            except Exception as e:
                print(f"Error deleting file: {e}")
            
            # Remove from tracking
            del upload_workflow.uploaded_files[file_id]
            
            # Remove associated reviews
            reviews_to_remove = [
                review_id for review_id, review in upload_workflow.moderation_reviews.items()
                if review.file_id == file_id
            ]
            for review_id in reviews_to_remove:
                del upload_workflow.moderation_reviews[review_id]
            
            upload_workflow._save_workflow_data()
            
            return {
                "message": "Upload deleted successfully",
                "status": "success"
            }
            
        except HTTPException:
            raise
        except Exception as e:
            raise HTTPException(status_code=500, detail=str(e))
    
    @app.get("/api/validation/rules")
    async def get_validation_rules():
        """Get current validation rules"""
        try:
            rules = [
                {
                    "rule_id": rule.rule_id,
                    "name": rule.name,
                    "description": rule.description,
                    "rule_type": rule.rule_type,
                    "parameters": rule.parameters,
                    "severity": rule.severity,
                    "is_enabled": rule.is_enabled
                }
                for rule in upload_workflow.validator.validation_rules
            ]
            
            return {
                "validation_rules": rules,
                "count": len(rules),
                "status": "success"
            }
            
        except Exception as e:
            raise HTTPException(status_code=500, detail=str(e))
    
    @app.get("/api/workflow/status")
    async def get_workflow_status():
        """Get overall workflow system status"""
        try:
            stats = upload_workflow.get_workflow_statistics()
            
            workflow_status = {
                "system_health": "healthy",
                "total_uploads": stats["total_uploads"],
                "pending_moderation": stats["status_distribution"].get("pending_review", 0),
                "active_upload_sessions": len(upload_workflow.upload_progress),
                "validation_rules_active": len([r for r in upload_workflow.validator.validation_rules if r.is_enabled]),
                "storage_usage": {
                    "total_files": stats["total_uploads"],
                    "total_size_mb": stats["content_metrics"]["total_file_size"] / (1024 * 1024),
                    "avg_file_size_mb": stats["content_metrics"]["avg_file_size"] / (1024 * 1024)
                },
                "moderation_performance": {
                    "approval_rate": stats["moderation_stats"]["approval_rate"],
                    "pending_reviews": stats["status_distribution"].get("pending_review", 0),
                    "completed_reviews": stats["moderation_stats"]["total_reviews"]
                }
            }
            
            return {
                "workflow_status": workflow_status,
                "status": "success"
            }
            
        except Exception as e:
            raise HTTPException(status_code=500, detail=str(e))