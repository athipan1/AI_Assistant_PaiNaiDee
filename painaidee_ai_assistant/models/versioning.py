"""
Model Versioning System for 3D Assets
Provides semantic versioning, delta updates, and efficient bandwidth management
"""

import os
import json
import hashlib
import shutil
from typing import Dict, List, Optional, Tuple, Any
from pathlib import Path
from datetime import datetime
import zipfile
import tempfile
from dataclasses import dataclass, asdict


@dataclass
class ModelVersion:
    """Represents a specific version of a 3D model"""
    version: str  # Semantic version (e.g., "1.2.3")
    model_name: str
    file_path: str
    file_hash: str
    file_size: int
    created_at: str
    description: str
    changes: List[str]
    delta_from_previous: Optional[str] = None  # Path to delta file
    delta_size: Optional[int] = None


@dataclass
class DeltaUpdate:
    """Represents a delta update between two model versions"""
    from_version: str
    to_version: str
    delta_file: str
    delta_size: int
    compression_ratio: float
    created_at: str


class ModelVersioningManager:
    """Manages model versions and delta updates for efficient bandwidth usage"""
    
    def __init__(self, models_base_dir: str = "../assets/models", versions_dir: str = "versions"):
        self.models_base_dir = Path(models_base_dir)
        self.versions_dir = self.models_base_dir / versions_dir
        self.metadata_file = self.versions_dir / "versions_metadata.json"
        self.deltas_dir = self.versions_dir / "deltas"
        
        # Create directories if they don't exist
        self.versions_dir.mkdir(parents=True, exist_ok=True)
        self.deltas_dir.mkdir(parents=True, exist_ok=True)
        
        # Load existing metadata
        self.metadata = self._load_metadata()
    
    def _load_metadata(self) -> Dict[str, List[Dict]]:
        """Load version metadata from JSON file"""
        if self.metadata_file.exists():
            try:
                with open(self.metadata_file, 'r') as f:
                    return json.load(f)
            except Exception as e:
                print(f"Error loading metadata: {e}")
        return {}
    
    def _save_metadata(self):
        """Save version metadata to JSON file"""
        try:
            with open(self.metadata_file, 'w') as f:
                json.dump(self.metadata, f, indent=2)
        except Exception as e:
            print(f"Error saving metadata: {e}")
    
    def _calculate_file_hash(self, file_path: str) -> str:
        """Calculate SHA-256 hash of a file"""
        sha256_hash = hashlib.sha256()
        with open(file_path, "rb") as f:
            for chunk in iter(lambda: f.read(4096), b""):
                sha256_hash.update(chunk)
        return sha256_hash.hexdigest()
    
    def _parse_version(self, version: str) -> Tuple[int, int, int]:
        """Parse semantic version string into major, minor, patch tuple"""
        try:
            parts = version.split('.')
            return (int(parts[0]), int(parts[1]), int(parts[2]))
        except (ValueError, IndexError):
            raise ValueError(f"Invalid version format: {version}. Use semantic versioning (e.g., '1.0.0')")
    
    def _increment_version(self, current_version: str, increment_type: str = "patch") -> str:
        """Increment version number based on type"""
        major, minor, patch = self._parse_version(current_version)
        
        if increment_type == "major":
            return f"{major + 1}.0.0"
        elif increment_type == "minor":
            return f"{major}.{minor + 1}.0"
        else:  # patch
            return f"{major}.{minor}.{patch + 1}"
    
    def create_version(self, model_path: str, version: str = None, 
                      description: str = "", changes: List[str] = None,
                      increment_type: str = "patch") -> ModelVersion:
        """Create a new version of a model"""
        
        if not os.path.exists(model_path):
            raise FileNotFoundError(f"Model file not found: {model_path}")
        
        model_name = os.path.basename(model_path)
        file_hash = self._calculate_file_hash(model_path)
        file_size = os.path.getsize(model_path)
        
        # Auto-increment version if not provided
        if version is None:
            if model_name in self.metadata and self.metadata[model_name]:
                latest_version = self.metadata[model_name][-1]["version"]
                version = self._increment_version(latest_version, increment_type)
            else:
                version = "1.0.0"
        
        # Check if this exact version already exists
        if model_name in self.metadata:
            for existing in self.metadata[model_name]:
                if existing["version"] == version:
                    if existing["file_hash"] == file_hash:
                        print(f"Version {version} already exists with same content")
                        return ModelVersion(**existing)
                    else:
                        raise ValueError(f"Version {version} already exists with different content")
        
        # Create versioned copy
        version_dir = self.versions_dir / model_name / version
        version_dir.mkdir(parents=True, exist_ok=True)
        
        version_file_path = version_dir / model_name
        shutil.copy2(model_path, version_file_path)
        
        # Create delta from previous version if exists
        delta_from_previous = None
        delta_size = None
        
        if model_name in self.metadata and self.metadata[model_name]:
            previous_version = self.metadata[model_name][-1]
            try:
                delta_info = self._create_delta(
                    previous_version["file_path"],
                    str(version_file_path),
                    previous_version["version"],
                    version
                )
                delta_from_previous = delta_info.delta_file
                delta_size = delta_info.delta_size
            except Exception as e:
                print(f"Failed to create delta: {e}")
        
        # Create version object
        model_version = ModelVersion(
            version=version,
            model_name=model_name,
            file_path=str(version_file_path),
            file_hash=file_hash,
            file_size=file_size,
            created_at=datetime.now().isoformat(),
            description=description,
            changes=changes or [],
            delta_from_previous=delta_from_previous,
            delta_size=delta_size
        )
        
        # Update metadata
        if model_name not in self.metadata:
            self.metadata[model_name] = []
        
        self.metadata[model_name].append(asdict(model_version))
        self._save_metadata()
        
        return model_version
    
    def _create_delta(self, old_file: str, new_file: str, 
                     from_version: str, to_version: str) -> DeltaUpdate:
        """Create delta update between two file versions using binary diff"""
        
        delta_filename = f"{os.path.basename(old_file)}_{from_version}_to_{to_version}.delta"
        delta_path = self.deltas_dir / delta_filename
        
        # Simple delta: create a compressed diff package
        with tempfile.TemporaryDirectory() as temp_dir:
            # Create metadata for delta
            delta_info = {
                "from_version": from_version,
                "to_version": to_version,
                "from_hash": self._calculate_file_hash(old_file),
                "to_hash": self._calculate_file_hash(new_file),
                "created_at": datetime.now().isoformat()
            }
            
            # Copy new file to temp directory
            temp_new_file = os.path.join(temp_dir, "new_version")
            shutil.copy2(new_file, temp_new_file)
            
            # Create metadata file
            metadata_file = os.path.join(temp_dir, "delta_metadata.json")
            with open(metadata_file, 'w') as f:
                json.dump(delta_info, f, indent=2)
            
            # Create compressed delta package
            with zipfile.ZipFile(delta_path, 'w', zipfile.ZIP_DEFLATED) as zipf:
                zipf.write(temp_new_file, "new_version")
                zipf.write(metadata_file, "delta_metadata.json")
        
        original_size = os.path.getsize(new_file)
        delta_size = os.path.getsize(delta_path)
        compression_ratio = delta_size / original_size if original_size > 0 else 1.0
        
        return DeltaUpdate(
            from_version=from_version,
            to_version=to_version,
            delta_file=str(delta_path),
            delta_size=delta_size,
            compression_ratio=compression_ratio,
            created_at=datetime.now().isoformat()
        )
    
    def apply_delta(self, base_file: str, delta_file: str, output_file: str) -> bool:
        """Apply delta update to reconstruct new version"""
        try:
            with tempfile.TemporaryDirectory() as temp_dir:
                # Extract delta package
                with zipfile.ZipFile(delta_file, 'r') as zipf:
                    zipf.extractall(temp_dir)
                
                # Load metadata
                metadata_file = os.path.join(temp_dir, "delta_metadata.json")
                with open(metadata_file, 'r') as f:
                    delta_info = json.load(f)
                
                # Verify base file hash
                base_hash = self._calculate_file_hash(base_file)
                if base_hash != delta_info["from_hash"]:
                    raise ValueError("Base file hash mismatch")
                
                # Copy new version
                new_version_file = os.path.join(temp_dir, "new_version")
                shutil.copy2(new_version_file, output_file)
                
                # Verify output hash
                output_hash = self._calculate_file_hash(output_file)
                if output_hash != delta_info["to_hash"]:
                    raise ValueError("Output file hash mismatch")
                
                return True
                
        except Exception as e:
            print(f"Failed to apply delta: {e}")
            return False
    
    def get_versions(self, model_name: str) -> List[ModelVersion]:
        """Get all versions of a model"""
        if model_name not in self.metadata:
            return []
        
        return [ModelVersion(**version_data) for version_data in self.metadata[model_name]]
    
    def get_latest_version(self, model_name: str) -> Optional[ModelVersion]:
        """Get the latest version of a model"""
        versions = self.get_versions(model_name)
        if not versions:
            return None
        
        # Sort by version and return latest
        sorted_versions = sorted(versions, key=lambda v: self._parse_version(v.version))
        return sorted_versions[-1]
    
    def get_version(self, model_name: str, version: str) -> Optional[ModelVersion]:
        """Get a specific version of a model"""
        versions = self.get_versions(model_name)
        for v in versions:
            if v.version == version:
                return v
        return None
    
    def calculate_update_size(self, model_name: str, from_version: str, to_version: str) -> Dict[str, Any]:
        """Calculate the size needed for updating from one version to another"""
        from_ver = self.get_version(model_name, from_version)
        to_ver = self.get_version(model_name, to_version)
        
        if not from_ver or not to_ver:
            return {"error": "Version not found"}
        
        # Check if direct delta exists
        if to_ver.delta_from_previous and from_version == self._get_previous_version(model_name, to_version):
            return {
                "update_method": "direct_delta",
                "size": to_ver.delta_size,
                "compression_ratio": to_ver.delta_size / to_ver.file_size,
                "bandwidth_saved": to_ver.file_size - to_ver.delta_size
            }
        
        # Otherwise, full download needed
        return {
            "update_method": "full_download",
            "size": to_ver.file_size,
            "compression_ratio": 1.0,
            "bandwidth_saved": 0
        }
    
    def _get_previous_version(self, model_name: str, version: str) -> Optional[str]:
        """Get the version immediately before the specified version"""
        versions = self.get_versions(model_name)
        sorted_versions = sorted(versions, key=lambda v: self._parse_version(v.version))
        
        for i, v in enumerate(sorted_versions):
            if v.version == version and i > 0:
                return sorted_versions[i - 1].version
        return None
    
    def get_version_history(self, model_name: str) -> Dict[str, Any]:
        """Get comprehensive version history for a model"""
        versions = self.get_versions(model_name)
        if not versions:
            return {"error": "Model not found"}
        
        sorted_versions = sorted(versions, key=lambda v: self._parse_version(v.version))
        
        total_size = sum(v.file_size for v in versions)
        total_delta_size = sum(v.delta_size or 0 for v in versions)
        
        return {
            "model_name": model_name,
            "total_versions": len(versions),
            "latest_version": sorted_versions[-1].version,
            "total_storage_size": total_size,
            "total_delta_size": total_delta_size,
            "compression_efficiency": (total_size - total_delta_size) / total_size if total_size > 0 else 0,
            "versions": [
                {
                    "version": v.version,
                    "size": v.file_size,
                    "delta_size": v.delta_size,
                    "created_at": v.created_at,
                    "description": v.description,
                    "changes": v.changes
                }
                for v in sorted_versions
            ]
        }
    
    def cleanup_old_versions(self, model_name: str, keep_latest: int = 5) -> Dict[str, Any]:
        """Clean up old versions, keeping only the latest N versions"""
        versions = self.get_versions(model_name)
        if len(versions) <= keep_latest:
            return {"message": "No cleanup needed", "removed": 0}
        
        sorted_versions = sorted(versions, key=lambda v: self._parse_version(v.version))
        to_remove = sorted_versions[:-keep_latest]
        
        removed_count = 0
        freed_space = 0
        
        for version in to_remove:
            try:
                # Remove version file
                if os.path.exists(version.file_path):
                    freed_space += os.path.getsize(version.file_path)
                    os.remove(version.file_path)
                
                # Remove delta file if exists
                if version.delta_from_previous and os.path.exists(version.delta_from_previous):
                    freed_space += os.path.getsize(version.delta_from_previous)
                    os.remove(version.delta_from_previous)
                
                removed_count += 1
                
            except Exception as e:
                print(f"Error removing version {version.version}: {e}")
        
        # Update metadata
        self.metadata[model_name] = [asdict(v) for v in sorted_versions[-keep_latest:]]
        self._save_metadata()
        
        return {
            "message": f"Cleaned up {removed_count} old versions",
            "removed": removed_count,
            "freed_space": freed_space
        }


# Initialize global versioning manager
versioning_manager = ModelVersioningManager()