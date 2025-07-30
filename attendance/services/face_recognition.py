"""
Enhanced Face Recognition Service for Time Attendance System
Integrates with Advanced Enrollment and CCTV systems for robust recognition
"""

import face_recognition
import cv2
import numpy as np
import base64
import io
from PIL import Image
from typing import Dict, List, Tuple, Optional, Any
import logging
import time
from pathlib import Path

logger = logging.getLogger(__name__)

class EnhancedFaceRecognitionService:
    """Enhanced face recognition service with multi-angle support"""
    
    def __init__(self, advanced_enrollment_service=None):
        self.enabled = self._check_dependencies()
        self.confidence_threshold = 0.6  # Similarity threshold for face matching
        self.quality_threshold = 0.5     # Minimum quality score for face images
        self.enrollment_service = advanced_enrollment_service
        
        # Enhanced recognition settings
        self.multi_angle_enabled = True
        self.lighting_compensation = True
        self.distance_normalization = True
        
        # Recognition cache
        self.recognition_cache = {}
        self.cache_timeout = 10  # seconds
        
        logger.info(f"Enhanced Face Recognition Service initialized - Enabled: {self.enabled}")
    
    def init_app(self, app):
        """Initialize the face recognition service with Flask app"""
        app.config.setdefault('FACE_RECOGNITION_ENABLED', self.enabled)
        app.config.setdefault('FACE_CONFIDENCE_THRESHOLD', self.confidence_threshold)
        app.config.setdefault('FACE_QUALITY_THRESHOLD', self.quality_threshold)
        app.config.setdefault('MULTI_ANGLE_RECOGNITION', self.multi_angle_enabled)
        
        # Update settings from app config
        if app.config.get('FACE_CONFIDENCE_THRESHOLD'):
            self.confidence_threshold = app.config['FACE_CONFIDENCE_THRESHOLD']
        if app.config.get('FACE_QUALITY_THRESHOLD'):
            self.quality_threshold = app.config['FACE_QUALITY_THRESHOLD']
        if app.config.get('MULTI_ANGLE_RECOGNITION'):
            self.multi_angle_enabled = app.config['MULTI_ANGLE_RECOGNITION']
            
        logger.info(f"Enhanced Face Recognition Service initialized with Flask app - Enabled: {self.enabled}")
    
    def _check_dependencies(self) -> bool:
        """Check if required dependencies are available"""
        try:
            import face_recognition
            import cv2
            return True
        except ImportError as e:
            logger.warning(f"Face recognition dependencies not available: {e}")
            return False
    
    def validate_face_quality(self, image_data: str) -> Dict[str, Any]:
        """
        Validate the quality of a face image
        
        Args:
            image_data: Base64 encoded image data
            
        Returns:
            Dictionary with quality assessment
        """
        if not self.enabled or not image_data:
            return {
                'valid': False,
                'quality_score': 0.0,
                'message': 'Face recognition not available or no image data',
                'recommendations': ['Ensure face recognition dependencies are installed']
            }
        
        try:
            # Decode base64 image
            if 'data:image' in image_data:
                image_data = image_data.split(',')[1]
            
            image_bytes = base64.b64decode(image_data)
            image = Image.open(io.BytesIO(image_bytes))
            
            # Convert to RGB if needed
            if image.mode != 'RGB':
                image = image.convert('RGB')
            
            # Convert PIL image to numpy array for face_recognition
            image_array = np.array(image)
            
            # Find face locations
            face_locations = face_recognition.face_locations(image_array)
            
            quality_result = {
                'valid': False,
                'quality_score': 0.0,
                'message': '',
                'recommendations': [],
                'face_count': len(face_locations),
                'image_size': f"{image.width}x{image.height}"
            }
            
            # Check if any faces found
            if len(face_locations) == 0:
                quality_result.update({
                    'message': 'No face detected in image',
                    'recommendations': [
                        'Ensure face is clearly visible',
                        'Check lighting conditions',
                        'Position face in center of frame'
                    ]
                })
                return quality_result
            
            # Check for multiple faces
            if len(face_locations) > 1:
                quality_result.update({
                    'message': 'Multiple faces detected',
                    'recommendations': [
                        'Ensure only one person in frame',
                        'Remove other people from background'
                    ]
                })
                return quality_result
            
            # Analyze the single face found
            face_location = face_locations[0]
            top, right, bottom, left = face_location
            
            # Calculate face size relative to image
            face_width = right - left
            face_height = bottom - top
            face_area = face_width * face_height
            image_area = image.width * image.height
            face_ratio = face_area / image_area
            
            # Quality scoring based on multiple factors
            quality_score = 50.0  # Base score
            
            # Face size scoring (20 points)
            if face_ratio > 0.1:  # Face takes up at least 10% of image
                if face_ratio < 0.5:  # Not too large (less than 50%)
                    quality_score += 20
                else:
                    quality_score += 10  # Partial points for very large faces
            else:
                quality_result['recommendations'].append('Move closer to camera for larger face')
            
            # Image resolution scoring (15 points)
            if image.width >= 480 and image.height >= 480:
                quality_score += 15
            elif image.width >= 320 and image.height >= 320:
                quality_score += 10
            else:
                quality_result['recommendations'].append('Use higher resolution camera')
            
            # Brightness analysis (15 points)
            gray_image = cv2.cvtColor(image_array, cv2.COLOR_RGB2GRAY)
            face_region = gray_image[top:bottom, left:right]
            avg_brightness = np.mean(face_region)
            
            if 80 <= avg_brightness <= 180:  # Good brightness range
                quality_score += 15
            elif 60 <= avg_brightness <= 200:  # Acceptable range
                quality_score += 10
            else:
                if avg_brightness < 60:
                    quality_result['recommendations'].append('Improve lighting - image too dark')
                else:
                    quality_result['recommendations'].append('Reduce lighting - image too bright')
            
            # Face encoding quality check (bonus points)
            try:
                face_encodings = face_recognition.face_encodings(image_array, face_locations)
                if len(face_encodings) > 0:
                    quality_score += 10  # Bonus for successful encoding
                    
                    # Check encoding quality (variation in values indicates good features)
                    encoding = face_encodings[0]
                    encoding_variance = np.var(encoding)
                    if encoding_variance > 0.01:  # Good feature variation
                        quality_score += 5
                
            except Exception as e:
                logger.warning(f"Face encoding failed during quality check: {e}")
                quality_result['recommendations'].append('Face features unclear - improve image quality')
            
            # Final quality assessment
            quality_result.update({
                'quality_score': min(100.0, quality_score),
                'valid': quality_score >= (self.quality_threshold * 100),
                'face_size_ratio': face_ratio,
                'brightness': avg_brightness
            })
            
            if quality_result['valid']:
                quality_result['message'] = 'Good quality face image'
            else:
                quality_result['message'] = f'Quality score {quality_score:.1f}/100 - Below threshold'
                if not quality_result['recommendations']:
                    quality_result['recommendations'].append('Improve overall image quality')
            
            return quality_result
            
        except Exception as e:
            logger.error(f"Face quality validation error: {e}")
            return {
                'valid': False,
                'quality_score': 0.0,
                'message': f'Image processing error: {str(e)}',
                'recommendations': ['Please try with a different image']
            }
    
    def encode_face_from_image_data(self, image_data: str) -> List[List[float]]:
        """
        Extract face encodings from base64 image data
        
        Args:
            image_data: Base64 encoded image
            
        Returns:
            List of face encodings (128-dimensional vectors)
        """
        if not self.enabled:
            logger.warning("Face recognition not enabled")
            return []
        
        try:
            # Decode base64 image
            if 'data:image' in image_data:
                image_data = image_data.split(',')[1]
            
            image_bytes = base64.b64decode(image_data)
            image = Image.open(io.BytesIO(image_bytes))
            
            # Convert to RGB
            if image.mode != 'RGB':
                image = image.convert('RGB')
            
            # Convert to numpy array
            image_array = np.array(image)
            
            # Find face locations and encodings
            face_locations = face_recognition.face_locations(image_array)
            face_encodings = face_recognition.face_encodings(image_array, face_locations)
            
            # Convert numpy arrays to lists for JSON serialization
            encodings_list = [encoding.tolist() for encoding in face_encodings]
            
            logger.info(f"Extracted {len(encodings_list)} face encodings from image")
            return encodings_list
            
        except Exception as e:
            logger.error(f"Face encoding error: {e}")
            return []
    
    def recognize_face(self, image_data: str, known_encodings: Dict[str, List[List[float]]]) -> Tuple[Optional[str], float]:
        """
        Recognize a face from image data against known encodings
        
        Args:
            image_data: Base64 encoded image
            known_encodings: Dictionary mapping employee_id to list of face encodings
            
        Returns:
            Tuple of (employee_id, confidence) or (None, 0.0) if no match
        """
        if not self.enabled:
            logger.warning("Face recognition not enabled")
            return None, 0.0
        
        if not known_encodings:
            logger.warning("No known face encodings provided")
            return None, 0.0
        
        try:
            # Extract face encodings from input image
            input_encodings = self.encode_face_from_image_data(image_data)
            
            if not input_encodings:
                logger.warning("No face found in input image")
                return None, 0.0
            
            # Use the first face found in the image
            input_encoding = np.array(input_encodings[0])
            
            best_match_id = None
            best_confidence = 0.0
            
            # Compare against all known faces
            for employee_id, employee_encodings in known_encodings.items():
                for known_encoding_list in employee_encodings:
                    known_encoding = np.array(known_encoding_list)
                    
                    # Calculate face distance (lower is better)
                    face_distance = face_recognition.face_distance([known_encoding], input_encoding)[0]
                    
                    # Convert distance to confidence (0-1, higher is better)
                    confidence = 1.0 - face_distance
                    
                    # Track best match
                    if confidence > best_confidence and confidence >= self.confidence_threshold:
                        best_confidence = confidence
                        best_match_id = employee_id
            
            if best_match_id:
                logger.info(f"Face recognized: {best_match_id} (confidence: {best_confidence:.3f})")
            else:
                logger.info(f"No face match found (best confidence: {best_confidence:.3f})")
            
            return best_match_id, best_confidence
            
        except Exception as e:
            logger.error(f"Face recognition error: {e}")
            return None, 0.0
    
    def compare_faces(self, encoding1: List[float], encoding2: List[float]) -> float:
        """
        Compare two face encodings and return similarity score
        
        Args:
            encoding1: First face encoding
            encoding2: Second face encoding
            
        Returns:
            Similarity score (0-1, higher is more similar)
        """
        if not self.enabled:
            return 0.0
        
        try:
            enc1 = np.array(encoding1)
            enc2 = np.array(encoding2)
            
            distance = face_recognition.face_distance([enc1], enc2)[0]
            similarity = 1.0 - distance
            
            return max(0.0, similarity)
            
        except Exception as e:
            logger.error(f"Face comparison error: {e}")
            return 0.0
    
    def extract_face_encoding(self, image_path: str) -> Optional[List[float]]:
        """
        Extract face encoding from image file
        
        Args:
            image_path: Path to image file
            
        Returns:
            Face encoding as list or None if no face found
        """
        if not self.enabled:
            return None
        
        try:
            # Load image
            image = face_recognition.load_image_file(image_path)
            
            # Get face encodings
            encodings = face_recognition.face_encodings(image)
            
            if encodings:
                return encodings[0].tolist()
            
            return None
            
        except Exception as e:
            logger.error(f"Face encoding from file error: {e}")
            return None
    
    def validate_image_quality(self, image_data: Any) -> bool:
        """
        Simple boolean validation for image quality (for backward compatibility)
        
        Args:
            image_data: Image data to validate
            
        Returns:
            True if valid, False otherwise
        """
        if image_data is None:
            return False
        
        if isinstance(image_data, str):
            quality_result = self.validate_face_quality(image_data)
            return quality_result.get('valid', False)
        
        return False
    
    def get_status(self) -> Dict[str, Any]:
        """Get service status information"""
        return {
            'enabled': self.enabled,
            'confidence_threshold': self.confidence_threshold,
            'quality_threshold': self.quality_threshold,
            'dependencies': {
                'face_recognition': self._check_library('face_recognition'),
                'cv2': self._check_library('cv2'),
                'PIL': self._check_library('PIL')
            }
        }
    
    def _check_library(self, library_name: str) -> bool:
        """Check if a library is available"""
        try:
            __import__(library_name)
            return True
        except ImportError:
            return False
    
    def enhanced_recognize_faces(self, frame: np.ndarray, camera_id: str = None) -> List[Dict]:
        """Enhanced face recognition using multi-angle embeddings"""
        if not self.enabled or not self.enrollment_service:
            return []
        
        # Use the advanced enrollment service for recognition
        recognition_result = self.enrollment_service.recognize_employee(frame, camera_id or 'unknown')
        
        if recognition_result:
            return [{
                'employee_id': recognition_result['employee_id'],
                'employee_name': recognition_result['employee_name'],
                'confidence': recognition_result['confidence'],
                'face_location': recognition_result['face_location'],
                'detection_method': 'multi_angle_enhanced'
            }]
        
        return []
    
    def recognize_faces_in_image(self, image_data: str, known_employees: List[Dict] = None) -> List[Dict]:
        """Enhanced face recognition in base64 image with multi-angle support"""
        if not self.enabled:
            return []
        
        try:
            # Process image
            frame = self._process_image_data(image_data)
            if frame is None:
                return []
            
            # Use enhanced recognition if available
            if self.enrollment_service and self.multi_angle_enabled:
                return self.enhanced_recognize_faces(frame)
            
            # Fallback to standard recognition
            if known_employees:
                return self._standard_recognize_faces(frame, known_employees)
            
            return []
            
        except Exception as e:
            logger.error(f"Error in enhanced face recognition: {e}")
            return []
    
    def _standard_recognize_faces(self, frame: np.ndarray, known_employees: List[Dict]) -> List[Dict]:
        """Standard face recognition (fallback method)"""
        face_locations = face_recognition.face_locations(frame)
        if not face_locations:
            return []
        
        face_encodings = face_recognition.face_encodings(frame, face_locations)
        if not face_encodings:
            return []
        
        results = []
        
        for face_encoding, face_location in zip(face_encodings, face_locations):
            best_match = None
            best_distance = float('inf')
            
            for employee in known_employees:
                if not employee.get('face_encodings'):
                    continue
                
                # Compare with all encodings for this employee
                for encoding in employee['face_encodings']:
                    distance = face_recognition.face_distance([encoding], face_encoding)[0]
                    
                    if distance < best_distance and distance < (1 - self.confidence_threshold):
                        best_distance = distance
                        best_match = employee
            
            if best_match:
                confidence = 1 - best_distance
                results.append({
                    'employee_id': best_match['employee_id'],
                    'employee_name': best_match.get('name', 'Unknown'),
                    'confidence': confidence,
                    'face_location': face_location,
                    'detection_method': 'standard'
                })
        
        return results
    
    def _process_image_data(self, image_data: str) -> Optional[np.ndarray]:
        """Process base64 image data"""
        try:
            # Remove data URL prefix if present
            if image_data.startswith('data:image'):
                image_data = image_data.split(',')[1]
            
            # Decode base64
            image_bytes = base64.b64decode(image_data)
            
            # Convert to PIL Image
            pil_image = Image.open(io.BytesIO(image_bytes))
            
            # Convert to numpy array (BGR for OpenCV)
            frame = cv2.cvtColor(np.array(pil_image), cv2.COLOR_RGB2BGR)
            
            return frame
            
        except Exception as e:
            logger.error(f"Error processing image data: {e}")
            return None
    
    def set_enrollment_service(self, enrollment_service):
        """Set the advanced enrollment service for enhanced recognition"""
        self.enrollment_service = enrollment_service
        logger.info("Advanced enrollment service connected to face recognition")
    
    def get_recognition_stats(self) -> Dict:
        """Get recognition performance statistics"""
        cache_size = len(self.recognition_cache)
        
        return {
            'enabled': self.enabled,
            'multi_angle_enabled': self.multi_angle_enabled,
            'confidence_threshold': self.confidence_threshold,
            'quality_threshold': self.quality_threshold,
            'cache_size': cache_size,
            'has_enrollment_service': self.enrollment_service is not None
        }
    
    def clear_recognition_cache(self):
        """Clear the recognition cache"""
        self.recognition_cache.clear()
        logger.info("Recognition cache cleared")
    
    def recognize_face_with_advanced_enrollment(self, face_encoding: np.ndarray, 
                                              advanced_enrollment_service=None) -> Dict:
        """Enhanced face recognition using advanced multi-embedding profiles
        
        Args:
            face_encoding: Face encoding to match
            advanced_enrollment_service: Reference to advanced enrollment service
            
        Returns:
            Dict with recognition results including confidence scores
        """
        if not self.enabled:
            return {
                'success': False,
                'employee_id': None,
                'confidence': 0.0,
                'method': 'disabled',
                'message': 'Face recognition not enabled'
            }
        
        if advanced_enrollment_service is None:
            # Fall back to standard recognition
            return self.recognize_face(face_encoding)
        
        best_match = {
            'employee_id': None,
            'confidence': 0.0,
            'match_type': 'none',
            'embedding_used': 'none'
        }
        
        # Check against all enrolled employee profiles
        for employee_id, profile in advanced_enrollment_service.employee_profiles.items():
            if not profile.enrollment_complete:
                continue
            
            # Test against primary embeddings first (highest quality)
            if profile.primary_embeddings:
                distances = face_recognition.face_distance(profile.primary_embeddings, face_encoding)
                min_distance = np.min(distances)
                confidence = 1 - min_distance  # Convert distance to confidence
                
                if confidence > best_match['confidence'] and confidence > self.recognition_threshold:
                    best_match.update({
                        'employee_id': employee_id,
                        'confidence': confidence,
                        'match_type': 'primary',
                        'embedding_used': f"primary_{np.argmin(distances)}"
                    })
            
            # If no strong primary match, try variation embeddings
            if best_match['confidence'] < 0.8 and profile.variation_embeddings:
                
                # Try excellent quality embeddings
                excellent_embeddings = profile.variation_embeddings.get('quality_tiers', {}).get('excellent', [])
                if excellent_embeddings:
                    distances = face_recognition.face_distance(excellent_embeddings, face_encoding)
                    min_distance = np.min(distances)
                    confidence = 1 - min_distance
                    
                    if confidence > best_match['confidence'] and confidence > self.recognition_threshold:
                        best_match.update({
                            'employee_id': employee_id,
                            'confidence': confidence,
                            'match_type': 'excellent_quality',
                            'embedding_used': f"excellent_{np.argmin(distances)}"
                        })
                
                # Try angle-specific embeddings for better pose matching
                angle_embeddings = profile.variation_embeddings.get('angles', {})
                for angle, embeddings in angle_embeddings.items():
                    if embeddings:
                        distances = face_recognition.face_distance(embeddings, face_encoding)
                        min_distance = np.min(distances)
                        confidence = 1 - min_distance
                        
                        if confidence > best_match['confidence'] and confidence > self.recognition_threshold:
                            best_match.update({
                                'employee_id': employee_id,
                                'confidence': confidence,
                                'match_type': f'angle_specific',
                                'embedding_used': f"{angle}_{np.argmin(distances)}"
                            })
                
                # Try lighting-specific embeddings
                lighting_embeddings = profile.variation_embeddings.get('lighting', {})
                for lighting, embeddings in lighting_embeddings.items():
                    if embeddings:
                        distances = face_recognition.face_distance(embeddings, face_encoding)
                        min_distance = np.min(distances)
                        confidence = 1 - min_distance
                        
                        if confidence > best_match['confidence'] and confidence > self.recognition_threshold:
                            best_match.update({
                                'employee_id': employee_id,
                                'confidence': confidence,
                                'match_type': f'lighting_specific',
                                'embedding_used': f"{lighting}_{np.argmin(distances)}"
                            })
        
        # Prepare result
        if best_match['employee_id']:
            # Get employee details
            try:
                from ..models.employee import Employee
                employees = self.db_service.find_all(Employee)
                employee = next((e for e in employees if e.employee_id == best_match['employee_id']), None)
                
                result = {
                    'success': True,
                    'employee_id': best_match['employee_id'],
                    'employee_name': f"{employee.first_name} {employee.last_name}" if employee else "Unknown",
                    'confidence': best_match['confidence'],
                    'method': 'advanced_multi_embedding',
                    'match_details': {
                        'match_type': best_match['match_type'],
                        'embedding_used': best_match['embedding_used'],
                        'total_embeddings_checked': len(profile.captures) if 'profile' in locals() else 0
                    },
                    'message': f"Recognized with {best_match['confidence']:.1%} confidence using {best_match['match_type']} embeddings"
                }
                
                logger.info(f"Advanced recognition: {result['employee_name']} "
                           f"({best_match['confidence']:.1%} via {best_match['match_type']})")
                
                return result
                
            except Exception as e:
                logger.error(f"Error getting employee details: {e}")
                return {
                    'success': True,
                    'employee_id': best_match['employee_id'],
                    'employee_name': "Unknown",
                    'confidence': best_match['confidence'],
                    'method': 'advanced_multi_embedding',
                    'message': f"Recognized but error getting details: {str(e)}"
                }
        else:
            return {
                'success': False,
                'employee_id': None,
                'confidence': 0.0,
                'method': 'advanced_multi_embedding',
                'message': 'No matching employee found in advanced enrollment database'
            }

# Global instance for the application
face_service = EnhancedFaceRecognitionService()

# Export main functions for backward compatibility
validate_face_quality = face_service.validate_face_quality
encode_face_from_image_data = face_service.encode_face_from_image_data
recognize_face = face_service.recognize_face
compare_faces = face_service.compare_faces
extract_face_encoding = face_service.extract_face_encoding