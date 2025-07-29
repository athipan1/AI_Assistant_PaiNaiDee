"""
Gesture Training System
Allows users to record and train custom gestures with machine learning
"""

import numpy as np
import json
import pickle
import logging
from typing import Dict, List, Optional, Tuple, Any
from dataclasses import dataclass, asdict
from pathlib import Path
import time
import hashlib
from sklearn.ensemble import RandomForestClassifier
from sklearn.model_selection import train_test_split
from sklearn.metrics import accuracy_score, classification_report
import joblib

logger = logging.getLogger(__name__)

@dataclass
class GestureSample:
    """Single gesture sample for training"""
    landmarks: List[List[float]]  # 21 landmarks, each with [x, y, z]
    gesture_label: str
    user_id: str
    timestamp: float
    confidence: float = 1.0
    metadata: Dict[str, Any] = None

@dataclass
class GestureDataset:
    """Dataset for gesture training"""
    samples: List[GestureSample]
    gesture_labels: List[str]
    created_timestamp: float
    last_updated: float
    total_samples: int
    samples_per_gesture: Dict[str, int]

@dataclass 
class TrainingResult:
    """Result of gesture training"""
    model_id: str
    accuracy: float
    training_samples: int
    gesture_labels: List[str]
    training_time_seconds: float
    model_path: str
    confusion_matrix: Optional[List[List[int]]] = None
    classification_report: Optional[str] = None

class GestureTrainingSystem:
    """System for training custom gesture recognition models"""
    
    def __init__(self, training_data_dir: str = "cache/gesture_training"):
        self.training_data_dir = Path(training_data_dir)
        self.training_data_dir.mkdir(parents=True, exist_ok=True)
        
        self.models_dir = self.training_data_dir / "models"
        self.models_dir.mkdir(exist_ok=True)
        
        self.datasets_dir = self.training_data_dir / "datasets"
        self.datasets_dir.mkdir(exist_ok=True)
        
        # Current dataset
        self.current_dataset: Optional[GestureDataset] = None
        self.load_current_dataset()
        
        # Trained models cache
        self.trained_models = {}
        self.load_trained_models()
        
        logger.info(f"Gesture training system initialized at {self.training_data_dir}")
    
    def create_new_dataset(self, dataset_name: str = None) -> str:
        """Create a new gesture dataset"""
        if dataset_name is None:
            dataset_name = f"dataset_{int(time.time())}"
        
        self.current_dataset = GestureDataset(
            samples=[],
            gesture_labels=[],
            created_timestamp=time.time(),
            last_updated=time.time(),
            total_samples=0,
            samples_per_gesture={}
        )
        
        self.save_current_dataset(dataset_name)
        logger.info(f"Created new gesture dataset: {dataset_name}")
        return dataset_name
    
    def add_gesture_sample(self, landmarks: List[List[float]], gesture_label: str, 
                          user_id: str = "default", confidence: float = 1.0,
                          metadata: Dict[str, Any] = None) -> bool:
        """Add a gesture sample to the current dataset"""
        try:
            if self.current_dataset is None:
                self.create_new_dataset()
            
            # Validate landmarks format (should be 21 landmarks with [x, y, z])
            if not self._validate_landmarks(landmarks):
                logger.error("Invalid landmarks format")
                return False
            
            sample = GestureSample(
                landmarks=landmarks,
                gesture_label=gesture_label,
                user_id=user_id,
                timestamp=time.time(),
                confidence=confidence,
                metadata=metadata or {}
            )
            
            self.current_dataset.samples.append(sample)
            
            # Update dataset statistics
            if gesture_label not in self.current_dataset.gesture_labels:
                self.current_dataset.gesture_labels.append(gesture_label)
                self.current_dataset.samples_per_gesture[gesture_label] = 0
            
            self.current_dataset.samples_per_gesture[gesture_label] += 1
            self.current_dataset.total_samples += 1
            self.current_dataset.last_updated = time.time()
            
            logger.info(f"Added gesture sample: {gesture_label} (total: {self.current_dataset.total_samples})")
            return True
            
        except Exception as e:
            logger.error(f"Error adding gesture sample: {e}")
            return False
    
    def _validate_landmarks(self, landmarks: List[List[float]]) -> bool:
        """Validate landmarks format"""
        if not isinstance(landmarks, list) or len(landmarks) != 21:
            return False
        
        for landmark in landmarks:
            if not isinstance(landmark, list) or len(landmark) != 3:
                return False
            if not all(isinstance(coord, (int, float)) for coord in landmark):
                return False
        
        return True
    
    def extract_features(self, landmarks: List[List[float]]) -> np.ndarray:
        """Extract features from hand landmarks for ML training"""
        landmarks_array = np.array(landmarks)
        
        # Normalize landmarks (center at wrist)
        wrist = landmarks_array[0]
        normalized_landmarks = landmarks_array - wrist
        
        features = []
        
        # 1. Raw normalized coordinates (21 landmarks * 3 coords = 63 features)
        features.extend(normalized_landmarks.flatten())
        
        # 2. Distances between key landmarks
        finger_tips = [4, 8, 12, 16, 20]  # Thumb, Index, Middle, Ring, Pinky tips
        finger_bases = [2, 5, 9, 13, 17]  # Finger base joints
        
        # Distances from wrist to fingertips
        for tip_idx in finger_tips:
            distance = np.linalg.norm(landmarks_array[tip_idx] - wrist)
            features.append(distance)
        
        # Distances between fingertips
        for i, tip1 in enumerate(finger_tips):
            for tip2 in finger_tips[i+1:]:
                distance = np.linalg.norm(landmarks_array[tip1] - landmarks_array[tip2])
                features.append(distance)
        
        # 3. Angles between fingers
        for i in range(len(finger_tips) - 1):
            v1 = landmarks_array[finger_tips[i]] - wrist
            v2 = landmarks_array[finger_tips[i+1]] - wrist
            
            # Calculate angle
            cos_angle = np.dot(v1, v2) / (np.linalg.norm(v1) * np.linalg.norm(v2) + 1e-8)
            angle = np.arccos(np.clip(cos_angle, -1.0, 1.0))
            features.append(angle)
        
        # 4. Hand orientation features
        # Palm normal vector (using three palm points)
        palm_points = np.array([landmarks_array[0], landmarks_array[5], landmarks_array[17]])
        v1 = palm_points[1] - palm_points[0]
        v2 = palm_points[2] - palm_points[0]
        palm_normal = np.cross(v1, v2)
        palm_normal = palm_normal / (np.linalg.norm(palm_normal) + 1e-8)
        features.extend(palm_normal)
        
        # 5. Finger extension features
        for base_idx, tip_idx in zip(finger_bases, finger_tips):
            extension = np.linalg.norm(landmarks_array[tip_idx] - landmarks_array[base_idx])
            features.append(extension)
        
        # 6. Hand spread (variance of fingertip positions)
        fingertip_positions = landmarks_array[finger_tips]
        spread = np.var(fingertip_positions, axis=0).sum()
        features.append(spread)
        
        return np.array(features)
    
    def train_model(self, model_name: str = None, test_size: float = 0.2, 
                   min_samples_per_gesture: int = 5) -> Optional[TrainingResult]:
        """Train a gesture recognition model from the current dataset"""
        try:
            if self.current_dataset is None or self.current_dataset.total_samples == 0:
                logger.error("No dataset available for training")
                return None
            
            # Check minimum samples per gesture
            insufficient_gestures = [
                gesture for gesture, count in self.current_dataset.samples_per_gesture.items()
                if count < min_samples_per_gesture
            ]
            
            if insufficient_gestures:
                logger.error(f"Insufficient samples for gestures: {insufficient_gestures}. Need at least {min_samples_per_gesture} samples each.")
                return None
            
            start_time = time.time()
            
            # Prepare training data
            X = []  # Features
            y = []  # Labels
            
            for sample in self.current_dataset.samples:
                features = self.extract_features(sample.landmarks)
                X.append(features)
                y.append(sample.gesture_label)
            
            X = np.array(X)
            y = np.array(y)
            
            # Split data
            X_train, X_test, y_train, y_test = train_test_split(
                X, y, test_size=test_size, random_state=42, stratify=y
            )
            
            # Train Random Forest model
            model = RandomForestClassifier(
                n_estimators=100,
                max_depth=10,
                random_state=42,
                n_jobs=-1
            )
            
            model.fit(X_train, y_train)
            
            # Evaluate model
            y_pred = model.predict(X_test)
            accuracy = accuracy_score(y_test, y_pred)
            
            # Generate model ID
            if model_name is None:
                model_name = f"gesture_model_{int(time.time())}"
            
            model_id = hashlib.md5(f"{model_name}_{time.time()}".encode()).hexdigest()[:8]
            
            # Save model
            model_path = self.models_dir / f"{model_id}.joblib"
            joblib.dump({
                'model': model,
                'gesture_labels': self.current_dataset.gesture_labels,
                'feature_names': self._get_feature_names(),
                'training_metadata': {
                    'model_name': model_name,
                    'model_id': model_id,
                    'training_samples': len(X_train),
                    'test_samples': len(X_test),
                    'gesture_labels': self.current_dataset.gesture_labels,
                    'samples_per_gesture': self.current_dataset.samples_per_gesture
                }
            }, model_path)
            
            training_time = time.time() - start_time
            
            # Create training result
            result = TrainingResult(
                model_id=model_id,
                accuracy=accuracy,
                training_samples=len(X_train),
                gesture_labels=self.current_dataset.gesture_labels,
                training_time_seconds=training_time,
                model_path=str(model_path),
                classification_report=classification_report(y_test, y_pred)
            )
            
            # Cache the trained model
            self.trained_models[model_id] = {
                'model': model,
                'metadata': result,
                'gesture_labels': self.current_dataset.gesture_labels
            }
            
            logger.info(f"Trained gesture model {model_id} with accuracy {accuracy:.3f}")
            return result
            
        except Exception as e:
            logger.error(f"Error training model: {e}")
            return None
    
    def _get_feature_names(self) -> List[str]:
        """Get feature names for the model"""
        feature_names = []
        
        # Raw coordinates
        landmark_names = [
            'WRIST', 'THUMB_CMC', 'THUMB_MCP', 'THUMB_IP', 'THUMB_TIP',
            'INDEX_MCP', 'INDEX_PIP', 'INDEX_DIP', 'INDEX_TIP',
            'MIDDLE_MCP', 'MIDDLE_PIP', 'MIDDLE_DIP', 'MIDDLE_TIP',
            'RING_MCP', 'RING_PIP', 'RING_DIP', 'RING_TIP',
            'PINKY_MCP', 'PINKY_PIP', 'PINKY_DIP', 'PINKY_TIP'
        ]
        
        for name in landmark_names:
            for coord in ['x', 'y', 'z']:
                feature_names.append(f'{name}_{coord}')
        
        # Distance features
        finger_names = ['THUMB', 'INDEX', 'MIDDLE', 'RING', 'PINKY']
        for finger in finger_names:
            feature_names.append(f'WRIST_TO_{finger}_TIP_DIST')
        
        # Inter-finger distances
        for i, finger1 in enumerate(finger_names):
            for finger2 in finger_names[i+1:]:
                feature_names.append(f'{finger1}_TO_{finger2}_DIST')
        
        # Angle features
        for i in range(len(finger_names) - 1):
            feature_names.append(f'{finger_names[i]}_TO_{finger_names[i+1]}_ANGLE')
        
        # Palm normal
        for coord in ['x', 'y', 'z']:
            feature_names.append(f'PALM_NORMAL_{coord}')
        
        # Extension features
        for finger in finger_names:
            feature_names.append(f'{finger}_EXTENSION')
        
        # Hand spread
        feature_names.append('HAND_SPREAD')
        
        return feature_names
    
    def predict_gesture(self, landmarks: List[List[float]], model_id: str = None) -> Optional[Dict[str, Any]]:
        """Predict gesture using a trained model"""
        try:
            if model_id is None:
                # Use the most recent model
                if not self.trained_models:
                    logger.error("No trained models available")
                    return None
                model_id = max(self.trained_models.keys())
            
            if model_id not in self.trained_models:
                # Try to load model from disk
                if not self.load_model(model_id):
                    logger.error(f"Model {model_id} not found")
                    return None
            
            model_data = self.trained_models[model_id]
            model = model_data['model']
            gesture_labels = model_data['gesture_labels']
            
            # Extract features
            features = self.extract_features(landmarks)
            features = features.reshape(1, -1)
            
            # Predict
            prediction = model.predict(features)[0]
            probabilities = model.predict_proba(features)[0]
            
            # Get confidence scores for all gestures
            gesture_confidences = {}
            for i, label in enumerate(gesture_labels):
                gesture_confidences[label] = float(probabilities[i])
            
            max_confidence = max(probabilities)
            
            return {
                'predicted_gesture': prediction,
                'confidence': float(max_confidence),
                'all_confidences': gesture_confidences,
                'model_id': model_id,
                'timestamp': time.time()
            }
            
        except Exception as e:
            logger.error(f"Error predicting gesture: {e}")
            return None
    
    def load_model(self, model_id: str) -> bool:
        """Load a trained model from disk"""
        try:
            model_path = self.models_dir / f"{model_id}.joblib"
            if not model_path.exists():
                return False
            
            model_data = joblib.load(model_path)
            
            self.trained_models[model_id] = {
                'model': model_data['model'],
                'gesture_labels': model_data['gesture_labels'],
                'metadata': model_data.get('training_metadata', {})
            }
            
            logger.info(f"Loaded model {model_id}")
            return True
            
        except Exception as e:
            logger.error(f"Error loading model {model_id}: {e}")
            return False
    
    def load_trained_models(self):
        """Load all trained models from disk"""
        try:
            for model_file in self.models_dir.glob("*.joblib"):
                model_id = model_file.stem
                self.load_model(model_id)
        except Exception as e:
            logger.error(f"Error loading trained models: {e}")
    
    def get_model_info(self, model_id: str) -> Optional[Dict[str, Any]]:
        """Get information about a trained model"""
        if model_id not in self.trained_models:
            if not self.load_model(model_id):
                return None
        
        model_data = self.trained_models[model_id]
        return {
            'model_id': model_id,
            'gesture_labels': model_data['gesture_labels'],
            'metadata': model_data.get('metadata', {}),
            'available': True
        }
    
    def list_trained_models(self) -> List[Dict[str, Any]]:
        """List all trained models"""
        models = []
        for model_id, model_data in self.trained_models.items():
            models.append({
                'model_id': model_id,
                'gesture_labels': model_data['gesture_labels'],
                'num_gestures': len(model_data['gesture_labels']),
                'metadata': model_data.get('metadata', {})
            })
        return models
    
    def save_current_dataset(self, dataset_name: str = "current"):
        """Save the current dataset to disk"""
        if self.current_dataset is None:
            return
        
        dataset_path = self.datasets_dir / f"{dataset_name}.json"
        
        # Convert dataset to JSON-serializable format
        dataset_dict = asdict(self.current_dataset)
        
        with open(dataset_path, 'w') as f:
            json.dump(dataset_dict, f, indent=2)
        
        logger.info(f"Saved dataset to {dataset_path}")
    
    def load_current_dataset(self, dataset_name: str = "current"):
        """Load a dataset from disk"""
        try:
            dataset_path = self.datasets_dir / f"{dataset_name}.json"
            if not dataset_path.exists():
                return False
            
            with open(dataset_path, 'r') as f:
                dataset_dict = json.load(f)
            
            # Convert back to dataclass
            samples = []
            for sample_dict in dataset_dict['samples']:
                sample = GestureSample(**sample_dict)
                samples.append(sample)
            
            dataset_dict['samples'] = samples
            self.current_dataset = GestureDataset(**dataset_dict)
            
            logger.info(f"Loaded dataset from {dataset_path}")
            return True
            
        except Exception as e:
            logger.error(f"Error loading dataset: {e}")
            return False
    
    def get_dataset_info(self) -> Optional[Dict[str, Any]]:
        """Get information about the current dataset"""
        if self.current_dataset is None:
            return None
        
        return {
            'total_samples': self.current_dataset.total_samples,
            'gesture_labels': self.current_dataset.gesture_labels,
            'samples_per_gesture': self.current_dataset.samples_per_gesture,
            'created_timestamp': self.current_dataset.created_timestamp,
            'last_updated': self.current_dataset.last_updated
        }
    
    def clear_dataset(self):
        """Clear the current dataset"""
        self.current_dataset = None
        logger.info("Cleared current dataset")
    
    def export_dataset(self, output_path: str) -> bool:
        """Export dataset to a file"""
        try:
            if self.current_dataset is None:
                return False
            
            with open(output_path, 'w') as f:
                json.dump(asdict(self.current_dataset), f, indent=2)
            
            logger.info(f"Exported dataset to {output_path}")
            return True
            
        except Exception as e:
            logger.error(f"Error exporting dataset: {e}")
            return False

# Global training system instance
gesture_training_system = GestureTrainingSystem()