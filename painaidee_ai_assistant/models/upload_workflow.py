"""
Upload & Approval Workflow System
Provides comprehensive file upload, validation, and content moderation workflow
"""

import os
import json
import uuid
import mimetypes
from typing import Dict, List, Optional, Any, Union
from dataclasses import dataclass, asdict
from datetime import datetime, timedelta
from pathlib import Path
import hashlib
import tempfile
import asyncio
from enum import Enum


class UploadStatus(Enum):
    UPLOADING = "uploading"
    VALIDATING = "validating"
    PENDING_REVIEW = "pending_review"
    APPROVED = "approved"
    REJECTED = "rejected"
    PROCESSING = "processing"
    PUBLISHED = "published"
    ERROR = "error"


class ValidationResult(Enum):
    PASS = "pass"
    WARNING = "warning"
    FAIL = "fail"


@dataclass
class UploadedFile:
    """Represents an uploaded file in the system"""
    file_id: str
    original_filename: str
    file_path: str
    file_size: int
    file_hash: str
    content_type: str
    uploader_id: str
    upload_timestamp: str
    status: UploadStatus
    validation_results: List[Dict[str, Any]]
    metadata: Dict[str, Any]
    tags: List[str]
    categories: List[str]
    description: str
    license: str
    is_public: bool


@dataclass
class ValidationRule:
    """Represents a validation rule for uploaded content"""
    rule_id: str
    name: str
    description: str
    rule_type: str  # file_size, format, content, metadata
    parameters: Dict[str, Any]
    severity: str  # error, warning, info
    is_enabled: bool


@dataclass
class ModerationReview:
    """Represents a moderation review"""
    review_id: str
    file_id: str
    reviewer_id: str
    review_timestamp: str
    decision: str  # approve, reject, request_changes
    comments: str
    quality_score: Optional[float]
    content_flags: List[str]


class ContentValidator:
    """Validates uploaded content against defined rules"""
    
    def __init__(self):
        self.validation_rules = self._load_validation_rules()
    
    def _load_validation_rules(self) -> List[ValidationRule]:
        """Load validation rules configuration"""
        return [
            ValidationRule(
                rule_id="file_size_limit",
                name="File Size Limit",
                description="Check if file size is within acceptable limits",
                rule_type="file_size",
                parameters={"max_size_mb": 100, "min_size_kb": 1},
                severity="error",
                is_enabled=True
            ),
            ValidationRule(
                rule_id="supported_formats",
                name="Supported File Formats",
                description="Check if file format is supported",
                rule_type="format",
                parameters={"allowed_formats": [".fbx", ".obj", ".gltf", ".glb", ".dae", ".3ds", ".blend"]},
                severity="error",
                is_enabled=True
            ),
            ValidationRule(
                rule_id="file_integrity",
                name="File Integrity Check",
                description="Verify file is not corrupted",
                rule_type="content",
                parameters={"check_headers": True, "verify_structure": True},
                severity="error",
                is_enabled=True
            ),
            ValidationRule(
                rule_id="metadata_completeness",
                name="Metadata Completeness",
                description="Check if required metadata is provided",
                rule_type="metadata",
                parameters={"required_fields": ["title", "description", "license"]},
                severity="warning",
                is_enabled=True
            ),
            ValidationRule(
                rule_id="content_safety",
                name="Content Safety Check",
                description="Check for inappropriate content",
                rule_type="content",
                parameters={"scan_for_malware": True, "content_policy": "family_safe"},
                severity="error",
                is_enabled=True
            ),
            ValidationRule(
                rule_id="quality_metrics",
                name="Quality Assessment",
                description="Assess model quality metrics",
                rule_type="content",
                parameters={"check_geometry": True, "assess_complexity": True},
                severity="info",
                is_enabled=True
            )
        ]
    
    async def validate_file(self, file_path: str, metadata: Dict[str, Any]) -> List[Dict[str, Any]]:
        """Validate uploaded file against all rules"""
        validation_results = []
        
        for rule in self.validation_rules:
            if not rule.is_enabled:
                continue
            
            try:
                result = await self._apply_validation_rule(rule, file_path, metadata)
                validation_results.append(result)
            except Exception as e:
                validation_results.append({
                    "rule_id": rule.rule_id,
                    "rule_name": rule.name,
                    "result": ValidationResult.FAIL.value,
                    "message": f"Validation error: {str(e)}",
                    "severity": "error"
                })
        
        return validation_results
    
    async def _apply_validation_rule(self, rule: ValidationRule, file_path: str, metadata: Dict[str, Any]) -> Dict[str, Any]:
        """Apply a specific validation rule"""
        result = {
            "rule_id": rule.rule_id,
            "rule_name": rule.name,
            "result": ValidationResult.PASS.value,
            "message": "",
            "severity": rule.severity,
            "details": {}
        }
        
        if rule.rule_type == "file_size":
            file_size = os.path.getsize(file_path)
            max_size = rule.parameters.get("max_size_mb", 100) * 1024 * 1024
            min_size = rule.parameters.get("min_size_kb", 1) * 1024
            
            if file_size > max_size:
                result["result"] = ValidationResult.FAIL.value
                result["message"] = f"File too large: {file_size / (1024*1024):.1f}MB (max: {max_size / (1024*1024)}MB)"
            elif file_size < min_size:
                result["result"] = ValidationResult.FAIL.value
                result["message"] = f"File too small: {file_size / 1024:.1f}KB (min: {min_size / 1024}KB)"
            else:
                result["message"] = f"File size OK: {file_size / (1024*1024):.1f}MB"
            
            result["details"]["file_size_bytes"] = file_size
        
        elif rule.rule_type == "format":
            file_ext = Path(file_path).suffix.lower()
            allowed_formats = rule.parameters.get("allowed_formats", [])
            
            if file_ext not in allowed_formats:
                result["result"] = ValidationResult.FAIL.value
                result["message"] = f"Unsupported format: {file_ext} (allowed: {', '.join(allowed_formats)})"
            else:
                result["message"] = f"Format supported: {file_ext}"
            
            result["details"]["file_extension"] = file_ext
        
        elif rule.rule_type == "metadata":
            required_fields = rule.parameters.get("required_fields", [])
            missing_fields = []
            
            for field in required_fields:
                if field not in metadata or not metadata[field]:
                    missing_fields.append(field)
            
            if missing_fields:
                result["result"] = ValidationResult.WARNING.value
                result["message"] = f"Missing required metadata: {', '.join(missing_fields)}"
            else:
                result["message"] = "All required metadata provided"
            
            result["details"]["missing_fields"] = missing_fields
        
        elif rule.rule_type == "content":
            # Content validation (simplified)
            try:
                # Basic file header check
                with open(file_path, 'rb') as f:
                    header = f.read(100)
                
                if len(header) == 0:
                    result["result"] = ValidationResult.FAIL.value
                    result["message"] = "File appears to be empty or corrupted"
                elif b'\x00' * 50 in header:  # Too many null bytes might indicate corruption
                    result["result"] = ValidationResult.WARNING.value
                    result["message"] = "File may be corrupted (excessive null bytes in header)"
                else:
                    result["message"] = "File content appears valid"
                
                result["details"]["header_size"] = len(header)
                
            except Exception as e:
                result["result"] = ValidationResult.FAIL.value
                result["message"] = f"Content validation failed: {str(e)}"
        
        return result


class UploadWorkflowManager:
    """Manages the complete upload and approval workflow"""
    
    def __init__(self, upload_dir: str = "uploads", workflow_data_dir: str = "workflow_data"):
        self.upload_dir = Path(upload_dir)
        self.workflow_data_dir = Path(workflow_data_dir)
        
        # Create directories
        self.upload_dir.mkdir(exist_ok=True)
        self.workflow_data_dir.mkdir(exist_ok=True)
        
        # Initialize components
        self.validator = ContentValidator()
        
        # Storage for workflow data
        self.uploaded_files: Dict[str, UploadedFile] = {}
        self.moderation_reviews: Dict[str, ModerationReview] = {}
        self.upload_progress: Dict[str, Dict[str, Any]] = {}
        
        # Load existing data
        self._load_workflow_data()
    
    def _load_workflow_data(self):
        """Load existing workflow data"""
        try:
            # Load uploaded files
            files_file = self.workflow_data_dir / "uploaded_files.json"
            if files_file.exists():
                with open(files_file, 'r') as f:
                    data = json.load(f)
                    self.uploaded_files = {k: UploadedFile(**{**v, 'status': UploadStatus(v['status'])}) for k, v in data.items()}
            
            # Load moderation reviews
            reviews_file = self.workflow_data_dir / "moderation_reviews.json"
            if reviews_file.exists():
                with open(reviews_file, 'r') as f:
                    data = json.load(f)
                    self.moderation_reviews = {k: ModerationReview(**v) for k, v in data.items()}
        
        except Exception as e:
            print(f"Error loading workflow data: {e}")
    
    def _save_workflow_data(self):
        """Save workflow data to disk"""
        try:
            # Save uploaded files
            with open(self.workflow_data_dir / "uploaded_files.json", 'w') as f:
                data = {k: {**asdict(v), 'status': v.status.value} for k, v in self.uploaded_files.items()}
                json.dump(data, f, indent=2)
            
            # Save moderation reviews
            with open(self.workflow_data_dir / "moderation_reviews.json", 'w') as f:
                data = {k: asdict(v) for k, v in self.moderation_reviews.items()}
                json.dump(data, f, indent=2)
        
        except Exception as e:
            print(f"Error saving workflow data: {e}")
    
    def _calculate_file_hash(self, file_path: str) -> str:
        """Calculate SHA-256 hash of file"""
        sha256_hash = hashlib.sha256()
        with open(file_path, "rb") as f:
            for chunk in iter(lambda: f.read(4096), b""):
                sha256_hash.update(chunk)
        return sha256_hash.hexdigest()
    
    async def initiate_upload(self, uploader_id: str, filename: str, file_size: int, 
                            metadata: Dict[str, Any]) -> Dict[str, Any]:
        """Initiate upload process and return upload session"""
        file_id = str(uuid.uuid4())
        
        # Create upload session
        upload_session = {
            "file_id": file_id,
            "uploader_id": uploader_id,
            "filename": filename,
            "file_size": file_size,
            "metadata": metadata,
            "status": "initiated",
            "upload_url": f"/upload/{file_id}",
            "created_at": datetime.now().isoformat(),
            "expires_at": (datetime.now() + timedelta(hours=2)).isoformat()
        }
        
        self.upload_progress[file_id] = upload_session
        
        return {
            "upload_session": upload_session,
            "status": "success"
        }
    
    async def process_uploaded_file(self, file_id: str, file_content: bytes, 
                                  metadata: Dict[str, Any]) -> Dict[str, Any]:
        """Process uploaded file through validation workflow"""
        if file_id not in self.upload_progress:
            return {"error": "Invalid upload session", "status": "error"}
        
        try:
            # Update progress
            self.upload_progress[file_id]["status"] = "processing"
            
            # Save file temporarily
            upload_session = self.upload_progress[file_id]
            filename = upload_session["filename"]
            file_path = self.upload_dir / f"{file_id}_{filename}"
            
            with open(file_path, 'wb') as f:
                f.write(file_content)
            
            # Calculate file hash
            file_hash = self._calculate_file_hash(str(file_path))
            
            # Check for duplicates
            for existing_file in self.uploaded_files.values():
                if existing_file.file_hash == file_hash:
                    return {
                        "error": "Duplicate file detected",
                        "existing_file_id": existing_file.file_id,
                        "status": "duplicate"
                    }
            
            # Create uploaded file record
            uploaded_file = UploadedFile(
                file_id=file_id,
                original_filename=filename,
                file_path=str(file_path),
                file_size=len(file_content),
                file_hash=file_hash,
                content_type=mimetypes.guess_type(filename)[0] or "application/octet-stream",
                uploader_id=upload_session["uploader_id"],
                upload_timestamp=datetime.now().isoformat(),
                status=UploadStatus.VALIDATING,
                validation_results=[],
                metadata=metadata,
                tags=metadata.get("tags", []),
                categories=metadata.get("categories", []),
                description=metadata.get("description", ""),
                license=metadata.get("license", "unknown"),
                is_public=metadata.get("is_public", False)
            )
            
            # Run validation
            validation_results = await self.validator.validate_file(str(file_path), metadata)
            uploaded_file.validation_results = validation_results
            
            # Determine next status based on validation
            has_errors = any(r["result"] == ValidationResult.FAIL.value for r in validation_results)
            has_warnings = any(r["result"] == ValidationResult.WARNING.value for r in validation_results)
            
            if has_errors:
                uploaded_file.status = UploadStatus.ERROR
            elif has_warnings or not metadata.get("auto_approve", False):
                uploaded_file.status = UploadStatus.PENDING_REVIEW
            else:
                uploaded_file.status = UploadStatus.APPROVED
            
            # Save uploaded file
            self.uploaded_files[file_id] = uploaded_file
            self._save_workflow_data()
            
            # Clean up upload progress
            del self.upload_progress[file_id]
            
            return {
                "file_id": file_id,
                "status": uploaded_file.status.value,
                "validation_results": validation_results,
                "requires_review": uploaded_file.status == UploadStatus.PENDING_REVIEW,
                "message": "File uploaded and processed successfully"
            }
            
        except Exception as e:
            # Update progress with error
            if file_id in self.upload_progress:
                self.upload_progress[file_id]["status"] = "error"
                self.upload_progress[file_id]["error"] = str(e)
            
            return {
                "error": f"Upload processing failed: {str(e)}",
                "status": "error"
            }
    
    def get_upload_progress(self, file_id: str) -> Dict[str, Any]:
        """Get upload progress for a file"""
        if file_id in self.upload_progress:
            return self.upload_progress[file_id]
        elif file_id in self.uploaded_files:
            uploaded_file = self.uploaded_files[file_id]
            return {
                "file_id": file_id,
                "status": uploaded_file.status.value,
                "completed": True,
                "validation_complete": True
            }
        else:
            return {"error": "Upload not found", "status": "not_found"}
    
    def get_moderation_queue(self, status: Optional[str] = None) -> List[Dict[str, Any]]:
        """Get files pending moderation"""
        files_for_review = []
        
        for file_id, uploaded_file in self.uploaded_files.items():
            if status and uploaded_file.status.value != status:
                continue
            
            if uploaded_file.status in [UploadStatus.PENDING_REVIEW, UploadStatus.REJECTED]:
                file_info = {
                    "file_id": file_id,
                    "filename": uploaded_file.original_filename,
                    "uploader_id": uploaded_file.uploader_id,
                    "upload_timestamp": uploaded_file.upload_timestamp,
                    "status": uploaded_file.status.value,
                    "file_size": uploaded_file.file_size,
                    "content_type": uploaded_file.content_type,
                    "description": uploaded_file.description,
                    "tags": uploaded_file.tags,
                    "categories": uploaded_file.categories,
                    "license": uploaded_file.license,
                    "validation_summary": self._summarize_validation_results(uploaded_file.validation_results),
                    "existing_reviews": len([r for r in self.moderation_reviews.values() if r.file_id == file_id])
                }
                files_for_review.append(file_info)
        
        # Sort by upload timestamp (oldest first)
        files_for_review.sort(key=lambda x: x["upload_timestamp"])
        
        return files_for_review
    
    def _summarize_validation_results(self, validation_results: List[Dict[str, Any]]) -> Dict[str, Any]:
        """Summarize validation results"""
        summary = {
            "total_rules": len(validation_results),
            "passed": 0,
            "warnings": 0,
            "errors": 0,
            "critical_issues": []
        }
        
        for result in validation_results:
            if result["result"] == ValidationResult.PASS.value:
                summary["passed"] += 1
            elif result["result"] == ValidationResult.WARNING.value:
                summary["warnings"] += 1
            elif result["result"] == ValidationResult.FAIL.value:
                summary["errors"] += 1
                if result["severity"] == "error":
                    summary["critical_issues"].append(result["message"])
        
        return summary
    
    async def submit_moderation_review(self, file_id: str, reviewer_id: str, 
                                     decision: str, comments: str, 
                                     quality_score: Optional[float] = None) -> Dict[str, Any]:
        """Submit moderation review for a file"""
        if file_id not in self.uploaded_files:
            return {"error": "File not found", "status": "error"}
        
        uploaded_file = self.uploaded_files[file_id]
        
        # Create review record
        review = ModerationReview(
            review_id=str(uuid.uuid4()),
            file_id=file_id,
            reviewer_id=reviewer_id,
            review_timestamp=datetime.now().isoformat(),
            decision=decision,
            comments=comments,
            quality_score=quality_score,
            content_flags=[]  # Would be extracted from comments or separate input
        )
        
        self.moderation_reviews[review.review_id] = review
        
        # Update file status based on decision
        if decision == "approve":
            uploaded_file.status = UploadStatus.APPROVED
        elif decision == "reject":
            uploaded_file.status = UploadStatus.REJECTED
        elif decision == "request_changes":
            uploaded_file.status = UploadStatus.PENDING_REVIEW
            # Could trigger notification to uploader
        
        self._save_workflow_data()
        
        return {
            "review_id": review.review_id,
            "file_status": uploaded_file.status.value,
            "message": f"Review submitted: {decision}",
            "status": "success"
        }
    
    def get_user_uploads(self, uploader_id: str, status: Optional[str] = None) -> List[Dict[str, Any]]:
        """Get uploads for a specific user"""
        user_uploads = []
        
        for file_id, uploaded_file in self.uploaded_files.items():
            if uploaded_file.uploader_id != uploader_id:
                continue
            
            if status and uploaded_file.status.value != status:
                continue
            
            # Get latest review if any
            latest_review = None
            file_reviews = [r for r in self.moderation_reviews.values() if r.file_id == file_id]
            if file_reviews:
                latest_review = max(file_reviews, key=lambda x: x.review_timestamp)
            
            upload_info = {
                "file_id": file_id,
                "filename": uploaded_file.original_filename,
                "upload_timestamp": uploaded_file.upload_timestamp,
                "status": uploaded_file.status.value,
                "file_size": uploaded_file.file_size,
                "description": uploaded_file.description,
                "tags": uploaded_file.tags,
                "validation_summary": self._summarize_validation_results(uploaded_file.validation_results),
                "latest_review": {
                    "decision": latest_review.decision,
                    "comments": latest_review.comments,
                    "quality_score": latest_review.quality_score,
                    "review_timestamp": latest_review.review_timestamp
                } if latest_review else None
            }
            user_uploads.append(upload_info)
        
        return user_uploads
    
    def get_workflow_statistics(self) -> Dict[str, Any]:
        """Get workflow statistics"""
        stats = {
            "total_uploads": len(self.uploaded_files),
            "status_distribution": {},
            "validation_stats": {
                "total_validations": 0,
                "avg_issues_per_file": 0,
                "common_issues": {}
            },
            "moderation_stats": {
                "total_reviews": len(self.moderation_reviews),
                "avg_review_time_hours": 0,
                "approval_rate": 0
            },
            "content_metrics": {
                "total_file_size": 0,
                "avg_file_size": 0,
                "format_distribution": {},
                "license_distribution": {}
            }
        }
        
        # Status distribution
        for uploaded_file in self.uploaded_files.values():
            status = uploaded_file.status.value
            stats["status_distribution"][status] = stats["status_distribution"].get(status, 0) + 1
        
        # Validation stats
        total_issues = 0
        issue_types = {}
        
        for uploaded_file in self.uploaded_files.values():
            stats["validation_stats"]["total_validations"] += len(uploaded_file.validation_results)
            
            for result in uploaded_file.validation_results:
                if result["result"] != ValidationResult.PASS.value:
                    total_issues += 1
                    rule_name = result["rule_name"]
                    issue_types[rule_name] = issue_types.get(rule_name, 0) + 1
        
        if self.uploaded_files:
            stats["validation_stats"]["avg_issues_per_file"] = total_issues / len(self.uploaded_files)
        stats["validation_stats"]["common_issues"] = dict(sorted(issue_types.items(), key=lambda x: x[1], reverse=True)[:5])
        
        # Moderation stats
        approved_count = sum(1 for f in self.uploaded_files.values() if f.status == UploadStatus.APPROVED)
        total_reviewed = sum(1 for f in self.uploaded_files.values() if f.status in [UploadStatus.APPROVED, UploadStatus.REJECTED])
        
        if total_reviewed > 0:
            stats["moderation_stats"]["approval_rate"] = approved_count / total_reviewed
        
        # Content metrics
        total_size = sum(f.file_size for f in self.uploaded_files.values())
        stats["content_metrics"]["total_file_size"] = total_size
        
        if self.uploaded_files:
            stats["content_metrics"]["avg_file_size"] = total_size / len(self.uploaded_files)
        
        # Format and license distribution
        for uploaded_file in self.uploaded_files.values():
            ext = Path(uploaded_file.original_filename).suffix.lower()
            stats["content_metrics"]["format_distribution"][ext] = stats["content_metrics"]["format_distribution"].get(ext, 0) + 1
            
            license_type = uploaded_file.license
            stats["content_metrics"]["license_distribution"][license_type] = stats["content_metrics"]["license_distribution"].get(license_type, 0) + 1
        
        return stats


# Initialize global upload workflow manager
upload_workflow = UploadWorkflowManager()