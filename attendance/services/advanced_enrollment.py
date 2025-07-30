"""
Advanced Multi-Angle Employee Enrollment Service
Creates comprehensive face embeddings for bulletproof recognition across 4 cameras
"""

import cv2
import numpy as np
import face_recognition
import threading
import time
from typing import Dict, List, Tuple, Optional
from dataclasses import dataclass, field
from pathlib import Path
import json
import logging
from collections import defaultdict

@dataclass
class EnrollmentCapture:
    timestamp: float
    angle: str  # 'front', 'left_30', 'right_45', etc.
    lighting: str  # 'normal', 'bright', 'dim', 'backlit'
    distance: str  # 'close', 'medium', 'far'
    expression: str  # 'neutral', 'smile', 'talking', 'masked'
    face_bbox: Tuple[int, int, int, int]
    face_encoding: np.ndarray
    quality_score: float
    image_path: str
    camera_id: str

@dataclass
class EmployeeEmbeddingProfile:
    employee_id: str
    name: str
    captures: List[EnrollmentCapture] = field(default_factory=list)
    primary_embeddings: List[np.ndarray] = field(default_factory=list)
    variation_embeddings: Dict[str, List[np.ndarray]] = field(default_factory=dict)
    quality_threshold: float = 0.8
    min_captures_required: int = 25
    enrollment_complete: bool = False
    last_updated: float = 0

class AdvancedEnrollmentService:
    """Advanced enrollment service for comprehensive face recognition"""
    
    def __init__(self, data_dir: str = "enrollment_data"):
        self.data_dir = Path(data_dir)
        self.data_dir.mkdir(exist_ok=True)
        
        # Enrollment parameters
        self.required_angles = [
            'front', 'left_30', 'left_45', 'left_60',
            'right_30', 'right_45', 'right_60',
            'up_15', 'down_15'
        ]
        self.required_lighting = ['normal', 'bright', 'dim']
        self.required_distances = ['close', 'medium', 'far']
        self.required_expressions = ['neutral', 'smile', 'talking']
        
        # Quality thresholds
        self.min_face_size = (80, 80)
        self.max_face_size = (500, 500)
        self.quality_threshold = 0.7
        self.similarity_threshold = 0.4  # For grouping similar embeddings
        
        # Storage
        self.employee_profiles = {}
        self.enrollment_sessions = {}
        
        # Cameras for enrollment
        self.enrollment_cameras = {}
        self.active_enrollments = set()
        
        logging.basicConfig(level=logging.INFO)
        self.logger = logging.getLogger(__name__)
    
    def start_employee_enrollment(self, employee_id: str, employee_name: str) -> str:
        """Start comprehensive enrollment session for an employee"""
        session_id = f"enroll_{employee_id}_{int(time.time())}"
        
        # Create employee profile
        profile = EmployeeEmbeddingProfile(
            employee_id=employee_id,
            name=employee_name
        )
        
        self.employee_profiles[employee_id] = profile
        self.enrollment_sessions[session_id] = {
            'employee_id': employee_id,
            'start_time': time.time(),
            'captures_needed': self._calculate_captures_needed(),
            'captures_completed': 0,
            'current_phase': 'angle_capture',
            'instructions': self._get_enrollment_instructions('angle_capture')
        }
        
        self.active_enrollments.add(employee_id)
        
        self.logger.info(f"Started enrollment for {employee_name} (ID: {employee_id})")
        return session_id
    
    def _calculate_captures_needed(self) -> Dict[str, int]:
        """Calculate number of captures needed for each category"""
        return {
            'angles': len(self.required_angles) * 2,  # 2 captures per angle
            'lighting': len(self.required_lighting) * 3,  # 3 captures per lighting
            'distances': len(self.required_distances) * 3,  # 3 captures per distance
            'expressions': len(self.required_expressions) * 2,  # 2 captures per expression
            'total': 54  # Total comprehensive captures
        }
    
    def process_enrollment_frame(self, camera_id: str, frame: np.ndarray, session_id: str) -> Dict:
        """Process frame during enrollment session"""
        if session_id not in self.enrollment_sessions:
            return {'error': 'Invalid session ID'}
        
        session = self.enrollment_sessions[session_id]
        employee_id = session['employee_id']
        profile = self.employee_profiles[employee_id]
        
        # Detect and process faces
        face_locations = face_recognition.face_locations(frame, model="cnn")  # Use CNN for better quality
        face_encodings = face_recognition.face_encodings(frame, face_locations)
        
        results = {
            'session_id': session_id,
            'faces_detected': len(face_locations),
            'captures_added': 0,
            'current_phase': session['current_phase'],
            'progress': 0,
            'instructions': session['instructions']
        }
        
        if len(face_locations) == 1 and len(face_encodings) == 1:
            # Single face detected - good for enrollment
            face_location = face_locations[0]
            face_encoding = face_encodings[0]
            
            # Analyze capture quality and characteristics
            capture_analysis = self._analyze_capture(frame, face_location, face_encoding, camera_id)
            
            if capture_analysis['quality_score'] >= self.quality_threshold:
                # Create enrollment capture
                capture = EnrollmentCapture(
                    timestamp=time.time(),
                    angle=capture_analysis['angle'],
                    lighting=capture_analysis['lighting'],
                    distance=capture_analysis['distance'],
                    expression=capture_analysis['expression'],
                    face_bbox=face_location,
                    face_encoding=face_encoding,
                    quality_score=capture_analysis['quality_score'],
                    image_path=self._save_enrollment_image(frame, face_location, employee_id),
                    camera_id=camera_id
                )
                
                # Add to profile if it adds value
                if self._should_add_capture(profile, capture):
                    profile.captures.append(capture)
                    session['captures_completed'] += 1
                    results['captures_added'] = 1
                    
                    self.logger.info(f"Added capture for {employee_id}: {capture.angle}, {capture.lighting}, {capture.distance}")
        
        # Update session progress
        results['progress'] = self._calculate_enrollment_progress(session, profile)
        
        # Check if enrollment is complete
        if results['progress'] >= 100:
            self._finalize_enrollment(employee_id)
            results['enrollment_complete'] = True
        
        return results
    
    def _analyze_capture(self, frame: np.ndarray, face_location: Tuple, face_encoding: np.ndarray, camera_id: str) -> Dict:
        """Analyze capture characteristics for enrollment categorization"""
        top, right, bottom, left = face_location
        face_width = right - left
        face_height = bottom - top
        
        # Face size analysis (distance estimation)
        face_area = face_width * face_height
        if face_area > 15000:
            distance = 'close'
        elif face_area > 8000:
            distance = 'medium'
        else:
            distance = 'far'
        
        # Angle analysis based on face landmarks
        face_landmarks = face_recognition.face_landmarks(frame, [face_location])
        angle = self._estimate_face_angle(face_landmarks[0] if face_landmarks else None)
        
        # Lighting analysis
        face_region = frame[top:bottom, left:right]
        lighting = self._analyze_lighting(face_region)
        
        # Expression analysis (simplified)
        expression = self._analyze_expression(face_landmarks[0] if face_landmarks else None)
        
        # Quality score calculation
        quality_score = self._calculate_quality_score(frame, face_location, face_encoding)
        
        return {
            'angle': angle,
            'lighting': lighting,
            'distance': distance,
            'expression': expression,
            'quality_score': quality_score,
            'face_size': (face_width, face_height)
        }
    
    def _estimate_face_angle(self, landmarks: Optional[Dict]) -> str:
        """Estimate face angle from landmarks"""
        if not landmarks:
            return 'unknown'
        
        # Use nose and eye positions to estimate angle
        left_eye = np.array(landmarks['left_eye']).mean(axis=0)
        right_eye = np.array(landmarks['right_eye']).mean(axis=0)
        nose_tip = landmarks['nose_tip'][2]  # Bottom of nose
        
        # Calculate eye line angle
        eye_angle = np.arctan2(right_eye[1] - left_eye[1], right_eye[0] - left_eye[0]) * 180 / np.pi
        
        # Calculate nose offset
        eye_center = (left_eye + right_eye) / 2
        nose_offset_x = nose_tip[0] - eye_center[0]
        
        # Determine angle category
        if abs(nose_offset_x) < 10 and abs(eye_angle) < 5:
            return 'front'
        elif nose_offset_x > 20:
            if nose_offset_x > 40:
                return 'right_60'
            elif nose_offset_x > 25:
                return 'right_45'
            else:
                return 'right_30'
        elif nose_offset_x < -20:
            if nose_offset_x < -40:
                return 'left_60'
            elif nose_offset_x < -25:
                return 'left_45'
            else:
                return 'left_30'
        elif eye_angle > 5:
            return 'up_15'
        elif eye_angle < -5:
            return 'down_15'
        else:
            return 'front'
    
    def _analyze_lighting(self, face_region: np.ndarray) -> str:
        """Analyze lighting conditions of face region"""
        if len(face_region.shape) == 3:
            gray_face = cv2.cvtColor(face_region, cv2.COLOR_BGR2GRAY)
        else:
            gray_face = face_region
        
        mean_brightness = np.mean(gray_face)
        std_brightness = np.std(gray_face)
        
        # Categorize lighting
        if mean_brightness > 180:
            return 'bright'
        elif mean_brightness < 80:
            return 'dim'
        elif std_brightness < 30:  # Low contrast might indicate backlit
            return 'backlit'
        else:
            return 'normal'
    
    def _analyze_expression(self, landmarks: Optional[Dict]) -> str:
        """Analyze facial expression from landmarks"""
        if not landmarks:
            return 'neutral'
        
        # Simplified expression detection
        mouth_points = landmarks['bottom_lip'] + landmarks['top_lip']
        mouth_width = max(mouth_points, key=lambda x: x[0])[0] - min(mouth_points, key=lambda x: x[0])[0]
        mouth_height = max(mouth_points, key=lambda x: x[1])[1] - min(mouth_points, key=lambda x: x[1])[1]
        
        mouth_ratio = mouth_height / mouth_width if mouth_width > 0 else 0
        
        if mouth_ratio > 0.3:
            return 'talking'
        elif mouth_width > 50:  # Approximate smile detection
            return 'smile'
        else:
            return 'neutral'
    
    def _calculate_quality_score(self, frame: np.ndarray, face_location: Tuple, face_encoding: np.ndarray) -> float:
        """Calculate quality score for the capture"""
        top, right, bottom, left = face_location
        face_region = frame[top:bottom, left:right]
        
        # Face size score
        face_area = (right - left) * (bottom - top)
        size_score = min(face_area / 10000, 1.0)  # Normalize to 1.0
        
        # Sharpness score using Laplacian variance
        if len(face_region.shape) == 3:
            gray_face = cv2.cvtColor(face_region, cv2.COLOR_BGR2GRAY)
        else:
            gray_face = face_region
        
        laplacian_var = cv2.Laplacian(gray_face, cv2.CV_64F).var()
        sharpness_score = min(laplacian_var / 1000, 1.0)  # Normalize
        
        # Brightness consistency score
        brightness_score = 1.0 - min(abs(np.mean(gray_face) - 128) / 128, 1.0)
        
        # Combined quality score
        quality_score = (size_score * 0.4 + sharpness_score * 0.4 + brightness_score * 0.2)
        
        return quality_score
    
    def _should_add_capture(self, profile: EmployeeEmbeddingProfile, new_capture: EnrollmentCapture) -> bool:
        """Determine if new capture adds value to the profile"""
        # Check if we already have enough captures of this type
        similar_captures = [
            c for c in profile.captures
            if (c.angle == new_capture.angle and 
                c.lighting == new_capture.lighting and 
                c.distance == new_capture.distance)
        ]
        
        if len(similar_captures) >= 3:  # Max 3 captures per category combination
            return False
        
        # Check if encoding is too similar to existing ones
        for existing_capture in profile.captures[-10:]:  # Check last 10 captures
            similarity = np.dot(existing_capture.face_encoding, new_capture.face_encoding)
            if similarity > 0.95:  # Too similar
                return False
        
        return True
    
    def _save_enrollment_image(self, frame: np.ndarray, face_location: Tuple, employee_id: str) -> str:
        """Save enrollment image for records"""
        employee_dir = self.data_dir / employee_id / "enrollment_images"
        employee_dir.mkdir(parents=True, exist_ok=True)
        
        timestamp = int(time.time())
        image_path = employee_dir / f"capture_{timestamp}.jpg"
        
        # Extract and save face region
        top, right, bottom, left = face_location
        # Add padding
        padding = 50
        top = max(0, top - padding)
        left = max(0, left - padding)
        bottom = min(frame.shape[0], bottom + padding)
        right = min(frame.shape[1], right + padding)
        
        face_image = frame[top:bottom, left:right]
        cv2.imwrite(str(image_path), face_image)
        
        return str(image_path)
    
    def _calculate_enrollment_progress(self, session: Dict, profile: EmployeeEmbeddingProfile) -> float:
        """Calculate enrollment completion percentage"""
        captures = profile.captures
        if not captures:
            return 0
        
        # Count captures by category
        angle_coverage = len(set(c.angle for c in captures)) / len(self.required_angles)
        lighting_coverage = len(set(c.lighting for c in captures)) / len(self.required_lighting)
        distance_coverage = len(set(c.distance for c in captures)) / len(self.required_distances)
        expression_coverage = len(set(c.expression for c in captures)) / len(self.required_expressions)
        
        # Minimum captures requirement
        min_captures_met = len(captures) >= profile.min_captures_required
        
        # Overall progress
        category_progress = (angle_coverage + lighting_coverage + distance_coverage + expression_coverage) / 4
        
        if min_captures_met and category_progress > 0.8:
            return 100
        else:
            return min(category_progress * 80 + (len(captures) / profile.min_captures_required) * 20, 99)
    
    def _finalize_enrollment(self, employee_id: str):
        """Finalize enrollment and create optimized embeddings"""
        profile = self.employee_profiles[employee_id]
        
        # Create primary embeddings (best quality captures)
        sorted_captures = sorted(profile.captures, key=lambda x: x.quality_score, reverse=True)
        profile.primary_embeddings = [c.face_encoding for c in sorted_captures[:10]]  # Top 10
        
        # Create variation embeddings grouped by characteristics
        for angle in self.required_angles:
            angle_captures = [c for c in profile.captures if c.angle == angle]
            if angle_captures:
                profile.variation_embeddings[f'angle_{angle}'] = [c.face_encoding for c in angle_captures]
        
        for lighting in self.required_lighting:
            lighting_captures = [c for c in profile.captures if c.lighting == lighting]
            if lighting_captures:
                profile.variation_embeddings[f'lighting_{lighting}'] = [c.face_encoding for c in lighting_captures]
        
        for distance in self.required_distances:
            distance_captures = [c for c in profile.captures if c.distance == distance]
            if distance_captures:
                profile.variation_embeddings[f'distance_{distance}'] = [c.face_encoding for c in distance_captures]
        
        # Mark enrollment as complete
        profile.enrollment_complete = True
        profile.last_updated = time.time()
        
        # Save to disk
        self._save_employee_profile(profile)
        
        # Remove from active enrollments
        self.active_enrollments.discard(employee_id)
        
        self.logger.info(f"Enrollment completed for {profile.name} with {len(profile.captures)} captures")
    
    def _save_employee_profile(self, profile: EmployeeEmbeddingProfile):
        """Save employee profile to disk"""
        employee_dir = self.data_dir / profile.employee_id
        employee_dir.mkdir(exist_ok=True)
        
        # Convert numpy arrays to lists for JSON serialization
        profile_data = {
            'employee_id': profile.employee_id,
            'name': profile.name,
            'enrollment_complete': profile.enrollment_complete,
            'last_updated': profile.last_updated,
            'captures_count': len(profile.captures),
            'primary_embeddings': [embedding.tolist() for embedding in profile.primary_embeddings],
            'variation_embeddings': {
                key: [embedding.tolist() for embedding in embeddings]
                for key, embeddings in profile.variation_embeddings.items()
            },
            'capture_metadata': [
                {
                    'timestamp': c.timestamp,
                    'angle': c.angle,
                    'lighting': c.lighting,
                    'distance': c.distance,
                    'expression': c.expression,
                    'quality_score': c.quality_score,
                    'camera_id': c.camera_id
                }
                for c in profile.captures
            ]
        }
        
        profile_file = employee_dir / 'enrollment_profile.json'
        with open(profile_file, 'w') as f:
            json.dump(profile_data, f, indent=2)
        
        # Save embeddings separately in numpy format for faster loading
        embeddings_file = employee_dir / 'embeddings.npz'
        np.savez_compressed(
            embeddings_file,
            primary_embeddings=np.array(profile.primary_embeddings),
            **{key: np.array(embeddings) for key, embeddings in profile.variation_embeddings.items()}
        )
    
    def load_employee_profile(self, employee_id: str) -> Optional[EmployeeEmbeddingProfile]:
        """Load employee profile from disk"""
        employee_dir = self.data_dir / employee_id
        profile_file = employee_dir / 'enrollment_profile.json'
        embeddings_file = employee_dir / 'embeddings.npz'
        
        if not profile_file.exists() or not embeddings_file.exists():
            return None
        
        try:
            # Load profile metadata
            with open(profile_file, 'r') as f:
                profile_data = json.load(f)
            
            # Load embeddings
            embeddings_data = np.load(embeddings_file)
            
            # Reconstruct profile
            profile = EmployeeEmbeddingProfile(
                employee_id=profile_data['employee_id'],
                name=profile_data['name'],
                enrollment_complete=profile_data['enrollment_complete'],
                last_updated=profile_data['last_updated']
            )
            
            profile.primary_embeddings = [embeddings_data['primary_embeddings'][i] 
                                        for i in range(len(embeddings_data['primary_embeddings']))]
            
            # Load variation embeddings
            for key in embeddings_data.files:
                if key != 'primary_embeddings':
                    profile.variation_embeddings[key] = [embeddings_data[key][i] 
                                                       for i in range(len(embeddings_data[key]))]
            
            self.employee_profiles[employee_id] = profile
            return profile
            
        except Exception as e:
            self.logger.error(f"Error loading profile for {employee_id}: {e}")
            return None
    
    def _get_enrollment_instructions(self, phase: str) -> str:
        """Get instructions for current enrollment phase"""
        instructions = {
            'angle_capture': "Please look directly at the camera, then slowly turn your head left and right. Hold each position for 2 seconds.",
            'lighting_check': "Please step into different lighting conditions - normal, bright, and dim areas.",
            'distance_variation': "Please move closer and farther from the camera to capture different distances.",
            'expression_variation': "Please show different expressions - neutral, smile, and speak a few words.",
            'quality_check': "Capturing high-quality images. Please remain still and look at the camera.",
            'completion': "Enrollment complete! Your profile has been created successfully."
        }
        return instructions.get(phase, "Please follow the on-screen instructions.")
    
    def recognize_employee(self, frame: np.ndarray, camera_id: str) -> Optional[Dict]:
        """Recognize employee using advanced multi-angle embeddings"""
        # Detect faces in frame
        face_locations = face_recognition.face_locations(frame)
        if not face_locations:
            return None
        
        face_encodings = face_recognition.face_encodings(frame, face_locations)
        if not face_encodings:
            return None
        
        # For each detected face
        for face_encoding, face_location in zip(face_encodings, face_locations):
            # Analyze current capture characteristics
            capture_analysis = self._analyze_capture(frame, face_location, face_encoding, camera_id)
            
            best_match = None
            best_confidence = 0
            
            # Compare against all enrolled employees
            for employee_id, profile in self.employee_profiles.items():
                if not profile.enrollment_complete:
                    continue
                
                # Calculate confidence using different embedding sets
                confidences = []
                
                # Primary embeddings confidence
                if profile.primary_embeddings:
                    similarities = face_recognition.face_distance(profile.primary_embeddings, face_encoding)
                    primary_confidence = 1 - np.min(similarities)  # Best match
                    confidences.append(primary_confidence * 0.5)  # 50% weight
                
                # Variation embeddings confidence based on detected characteristics
                variation_key = f"angle_{capture_analysis['angle']}"
                if variation_key in profile.variation_embeddings:
                    similarities = face_recognition.face_distance(profile.variation_embeddings[variation_key], face_encoding)
                    angle_confidence = 1 - np.min(similarities)
                    confidences.append(angle_confidence * 0.2)  # 20% weight
                
                lighting_key = f"lighting_{capture_analysis['lighting']}"
                if lighting_key in profile.variation_embeddings:
                    similarities = face_recognition.face_distance(profile.variation_embeddings[lighting_key], face_encoding)
                    lighting_confidence = 1 - np.min(similarities)
                    confidences.append(lighting_confidence * 0.2)  # 20% weight
                
                distance_key = f"distance_{capture_analysis['distance']}"
                if distance_key in profile.variation_embeddings:
                    similarities = face_recognition.face_distance(profile.variation_embeddings[distance_key], face_encoding)
                    distance_confidence = 1 - np.min(similarities)
                    confidences.append(distance_confidence * 0.1)  # 10% weight
                
                # Overall confidence
                overall_confidence = sum(confidences) if confidences else 0
                
                # Update best match
                if overall_confidence > best_confidence and overall_confidence > 0.6:  # Confidence threshold
                    best_confidence = overall_confidence
                    best_match = {
                        'employee_id': employee_id,
                        'employee_name': profile.name,
                        'confidence': overall_confidence,
                        'face_location': face_location,
                        'detection_characteristics': capture_analysis
                    }
            
            return best_match
        
        return None
    
    def add_employee_photos_batch(self, employee_id: str, employee_name: str, 
                                 photo_paths: List[str]) -> Dict:
        """Add multiple photos for an employee to create comprehensive embeddings
        
        Args:
            employee_id: Unique employee identifier
            employee_name: Employee's full name
            photo_paths: List of paths to photo files
            
        Returns:
            Dict with processing results and statistics
        """
        if employee_id not in self.employee_profiles:
            # Create new profile if doesn't exist
            profile = EmployeeEmbeddingProfile(
                employee_id=employee_id,
                name=employee_name
            )
            self.employee_profiles[employee_id] = profile
        else:
            profile = self.employee_profiles[employee_id]
        
        results = {
            'employee_id': employee_id,
            'total_photos': len(photo_paths),
            'processed_photos': 0,
            'faces_detected': 0,
            'embeddings_created': 0,
            'high_quality_captures': 0,
            'skipped_photos': 0,
            'errors': [],
            'quality_breakdown': {
                'excellent': 0,  # >0.9
                'good': 0,       # 0.8-0.9
                'fair': 0,       # 0.7-0.8
                'poor': 0        # <0.7
            },
            'angle_coverage': defaultdict(int),
            'lighting_coverage': defaultdict(int),
            'distance_coverage': defaultdict(int)
        }
        
        for i, photo_path in enumerate(photo_paths):
            try:
                # Load image
                image = cv2.imread(photo_path)
                if image is None:
                    results['errors'].append(f"Could not load image: {photo_path}")
                    results['skipped_photos'] += 1
                    continue
                
                # Convert BGR to RGB for face_recognition
                rgb_image = cv2.cvtColor(image, cv2.COLOR_BGR2RGB)
                
                # Detect faces
                face_locations = face_recognition.face_locations(rgb_image, model="cnn")
                face_encodings = face_recognition.face_encodings(rgb_image, face_locations)
                
                results['processed_photos'] += 1
                
                if len(face_locations) == 0:
                    results['errors'].append(f"No face detected in: {photo_path}")
                    continue
                elif len(face_locations) > 1:
                    results['errors'].append(f"Multiple faces detected in: {photo_path} - using best quality")
                
                # Process each detected face (or just the best one if multiple)
                for j, (face_location, face_encoding) in enumerate(zip(face_locations, face_encodings)):
                    if j > 0 and len(face_locations) > 1:
                        break  # Only process the first/best face if multiple detected
                    
                    results['faces_detected'] += 1
                    
                    # Analyze capture quality and characteristics
                    capture_analysis = self._analyze_capture(
                        rgb_image, face_location, face_encoding, f"upload_batch_{i}"
                    )
                    
                    quality_score = capture_analysis['quality_score']
                    
                    # Categorize quality
                    if quality_score >= 0.9:
                        results['quality_breakdown']['excellent'] += 1
                    elif quality_score >= 0.8:
                        results['quality_breakdown']['good'] += 1
                    elif quality_score >= 0.7:
                        results['quality_breakdown']['fair'] += 1
                    else:
                        results['quality_breakdown']['poor'] += 1
                    
                    # Track coverage
                    results['angle_coverage'][capture_analysis['angle']] += 1
                    results['lighting_coverage'][capture_analysis['lighting']] += 1
                    results['distance_coverage'][capture_analysis['distance']] += 1
                    
                    # Only add if quality meets threshold
                    if quality_score >= self.quality_threshold:
                        # Create enrollment capture
                        capture = EnrollmentCapture(
                            timestamp=time.time(),
                            angle=capture_analysis['angle'],
                            lighting=capture_analysis['lighting'],
                            distance=capture_analysis['distance'],
                            expression=capture_analysis['expression'],
                            face_bbox=face_location,
                            face_encoding=face_encoding,
                            quality_score=quality_score,
                            image_path=photo_path,
                            camera_id=f"upload_batch_{i}"
                        )
                        
                        # Add to profile
                        profile.captures.append(capture)
                        results['embeddings_created'] += 1
                        
                        if quality_score >= 0.8:
                            results['high_quality_captures'] += 1
                    
            except Exception as e:
                results['errors'].append(f"Error processing {photo_path}: {str(e)}")
                self.logger.error(f"Error processing {photo_path}: {e}")
        
        # Process embeddings to create final profile
        if results['embeddings_created'] > 0:
            self._process_embeddings_for_profile(profile)
            
            # Check if enrollment is sufficient
            if len(profile.captures) >= profile.min_captures_required:
                profile.enrollment_complete = True
                profile.last_updated = time.time()
                
                # Save profile
                self.save_employee_profile(employee_id)
                
                self.logger.info(f"Batch enrollment completed for {employee_name}: "
                               f"{results['embeddings_created']} embeddings created from "
                               f"{results['processed_photos']} photos")
            else:
                self.logger.warning(f"Insufficient quality captures for {employee_name}: "
                                  f"{len(profile.captures)}/{profile.min_captures_required} required")
        
        return results
    
    def upload_employee_photos_folder(self, employee_id: str, employee_name: str, 
                                    folder_path: str) -> Dict:
        """Upload all photos from a folder for an employee
        
        Args:
            employee_id: Unique employee identifier  
            employee_name: Employee's full name
            folder_path: Path to folder containing employee photos
            
        Returns:
            Dict with processing results
        """
        folder = Path(folder_path)
        if not folder.exists():
            return {'error': f"Folder not found: {folder_path}"}
        
        # Find all image files
        image_extensions = {'.jpg', '.jpeg', '.png', '.bmp', '.tiff', '.webp'}
        photo_paths = []
        
        for ext in image_extensions:
            photo_paths.extend(folder.glob(f"*{ext}"))
            photo_paths.extend(folder.glob(f"*{ext.upper()}"))
        
        photo_paths = [str(p) for p in photo_paths]
        
        if not photo_paths:
            return {'error': f"No image files found in folder: {folder_path}"}
        
        self.logger.info(f"Found {len(photo_paths)} photos in {folder_path} for {employee_name}")
        
        return self.add_employee_photos_batch(employee_id, employee_name, photo_paths)
    
    def _process_embeddings_for_profile(self, profile: EmployeeEmbeddingProfile):
        """Process and organize embeddings for optimal recognition"""
        if not profile.captures:
            return
        
        # Group embeddings by characteristics for better matching
        angle_groups = defaultdict(list)
        lighting_groups = defaultdict(list)
        quality_groups = defaultdict(list)
        
        for capture in profile.captures:
            angle_groups[capture.angle].append(capture.face_encoding)
            lighting_groups[capture.lighting].append(capture.face_encoding)
            
            # Group by quality
            if capture.quality_score >= 0.9:
                quality_groups['excellent'].append(capture.face_encoding)
            elif capture.quality_score >= 0.8:
                quality_groups['good'].append(capture.face_encoding)
            else:
                quality_groups['fair'].append(capture.face_encoding)
        
        # Create primary embeddings (best quality ones)
        profile.primary_embeddings = quality_groups['excellent'] + quality_groups['good']
        
        # Store variation embeddings for different scenarios
        profile.variation_embeddings = {
            'angles': dict(angle_groups),
            'lighting': dict(lighting_groups),
            'quality_tiers': dict(quality_groups)
        }
        
        self.logger.info(f"Processed {len(profile.captures)} captures into "
                        f"{len(profile.primary_embeddings)} primary embeddings for {profile.name}")

# Global service instance
enrollment_service = None

def initialize_enrollment_service(data_dir: str = "enrollment_data"):
    """Initialize the global enrollment service instance"""
    global enrollment_service
    enrollment_service = AdvancedEnrollmentService(data_dir)
    return enrollment_service
