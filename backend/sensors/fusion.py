"""
Multi-Sensor Fusion System
Kalman filter-based sensor fusion for HMT platform
"""
from typing import Dict, List, Optional, Any
from pydantic import BaseModel, Field
from datetime import datetime, timezone
from enum import Enum
import uuid
import math

class SensorType(str, Enum):
    """Supported sensor types"""
    CAMERA_RGB = "camera_rgb"
    CAMERA_IR = "camera_ir"
    RADAR = "radar"
    LIDAR = "lidar"
    GPS = "gps"
    IMU = "imu"
    ACOUSTIC = "acoustic"
    RF_DETECTOR = "rf_detector"
    DRONE_TELEMETRY = "drone_telemetry"

class SensorData(BaseModel):
    """Raw sensor data input"""
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    sensor_id: str
    sensor_type: SensorType
    timestamp: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
    
    # Position data (if applicable)
    position: Optional[Dict[str, float]] = None  # x, y, z
    velocity: Optional[Dict[str, float]] = None  # vx, vy, vz
    
    # Detection data (if applicable)
    detections: List[Dict[str, Any]] = Field(default_factory=list)
    
    # Sensor-specific data
    raw_data: Dict[str, Any] = Field(default_factory=dict)
    
    # Confidence/quality metrics
    confidence: float = 1.0
    noise_estimate: float = 0.0
    
    class Config:
        use_enum_values = True

class FusedDetection(BaseModel):
    """Fused detection from multiple sensors"""
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    track_id: Optional[str] = None  # Persistent tracking ID
    
    # Fused position
    position: Dict[str, float]  # x, y, z (optional)
    velocity: Optional[Dict[str, float]] = None
    
    # Classification
    class_name: str
    class_confidence: float
    
    # Bounding box (in image coordinates)
    bbox: Optional[List[float]] = None  # [x, y, w, h]
    
    # Contributing sensors
    sensor_sources: List[str] = Field(default_factory=list)
    
    # Fusion confidence (higher = more sensors agree)
    fusion_confidence: float = 0.0
    
    # State
    first_seen: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
    last_seen: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
    age_frames: int = 0

class FusedOutput(BaseModel):
    """Complete fused sensor output"""
    timestamp: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
    detections: List[FusedDetection] = Field(default_factory=list)
    
    # Platform state
    platform_position: Optional[Dict[str, float]] = None
    platform_orientation: Optional[Dict[str, float]] = None
    
    # Environment
    visibility_estimate: float = 1.0  # 0-1
    threat_level: str = "LOW"  # LOW, MEDIUM, HIGH, CRITICAL
    
    # Sensor health
    active_sensors: List[str] = Field(default_factory=list)
    degraded_sensors: List[str] = Field(default_factory=list)

class KalmanFilter:
    """Simple Kalman filter for position/velocity estimation"""
    
    def __init__(self, state_dim: int = 4):
        """
        Initialize Kalman filter
        State: [x, y, vx, vy]
        """
        self.state_dim = state_dim
        self.state = [0.0] * state_dim
        self.covariance = [[1.0 if i == j else 0.0 for j in range(state_dim)] for i in range(state_dim)]
        
        # Process noise
        self.Q = [[0.1 if i == j else 0.0 for j in range(state_dim)] for i in range(state_dim)]
        
        # Measurement noise
        self.R = [[1.0 if i == j else 0.0 for j in range(2)] for i in range(2)]
    
    def predict(self, dt: float = 0.033):
        """Predict next state"""
        # State transition: x' = x + vx*dt, y' = y + vy*dt
        if self.state_dim >= 4:
            self.state[0] += self.state[2] * dt
            self.state[1] += self.state[3] * dt
    
    def update(self, measurement: List[float]):
        """Update state with measurement [x, y]"""
        # Simplified update - just blend with measurement
        alpha = 0.7  # Measurement weight
        self.state[0] = alpha * measurement[0] + (1 - alpha) * self.state[0]
        self.state[1] = alpha * measurement[1] + (1 - alpha) * self.state[1]
        
        # Estimate velocity from position change
        if len(measurement) >= 2:
            # Simple velocity estimation
            pass
    
    def get_state(self) -> Dict[str, float]:
        """Get current state estimate"""
        return {
            'x': self.state[0],
            'y': self.state[1],
            'vx': self.state[2] if self.state_dim >= 3 else 0,
            'vy': self.state[3] if self.state_dim >= 4 else 0
        }

class SensorFusion:
    """
    Multi-sensor fusion engine
    Combines detections from multiple sensors into unified tracks
    """
    
    def __init__(self):
        self.sensors: Dict[str, SensorData] = {}
        self.tracks: Dict[str, FusedDetection] = {}
        self.kalman_filters: Dict[str, KalmanFilter] = {}
        self.next_track_id = 1
        
        # Fusion parameters
        self.iou_threshold = 0.3  # For matching detections
        self.max_age = 30  # Frames before track is deleted
        self.min_hits = 3  # Minimum detections to confirm track
    
    def register_sensor(self, sensor_id: str, sensor_type: SensorType):
        """Register a new sensor source"""
        self.sensors[sensor_id] = SensorData(
            sensor_id=sensor_id,
            sensor_type=sensor_type
        )
    
    def update(self, sensor_data: SensorData) -> FusedOutput:
        """
        Process new sensor data and update fused state
        """
        # Update sensor registry
        self.sensors[sensor_data.sensor_id] = sensor_data
        
        # Process detections
        new_detections = sensor_data.detections
        
        # Match to existing tracks
        matched, unmatched_dets, unmatched_tracks = self._match_detections(
            new_detections, 
            sensor_data.sensor_id
        )
        
        # Update matched tracks
        for track_id, detection in matched:
            self._update_track(track_id, detection, sensor_data.sensor_id)
        
        # Create new tracks for unmatched detections
        for detection in unmatched_dets:
            self._create_track(detection, sensor_data.sensor_id)
        
        # Age unmatched tracks
        for track_id in unmatched_tracks:
            self.tracks[track_id].age_frames += 1
        
        # Remove old tracks
        self._cleanup_tracks()
        
        # Build output
        return self._build_output()
    
    def _match_detections(self, detections: List[Dict], sensor_id: str):
        """Match new detections to existing tracks using IoU"""
        matched = []
        unmatched_dets = list(detections)
        unmatched_tracks = list(self.tracks.keys())
        
        if not detections or not self.tracks:
            return matched, unmatched_dets, unmatched_tracks
        
        # Simple greedy matching by IoU
        for det in detections:
            det_bbox = det.get('bbox', [0, 0, 100, 100])
            best_iou = 0
            best_track = None
            
            for track_id in unmatched_tracks:
                track = self.tracks[track_id]
                if track.bbox:
                    iou = self._calculate_iou(det_bbox, track.bbox)
                    if iou > best_iou and iou > self.iou_threshold:
                        best_iou = iou
                        best_track = track_id
            
            if best_track:
                matched.append((best_track, det))
                unmatched_tracks.remove(best_track)
                unmatched_dets.remove(det)
        
        return matched, unmatched_dets, unmatched_tracks
    
    def _calculate_iou(self, box1: List[float], box2: List[float]) -> float:
        """Calculate Intersection over Union"""
        x1, y1, w1, h1 = box1
        x2, y2, w2, h2 = box2
        
        xi1 = max(x1, x2)
        yi1 = max(y1, y2)
        xi2 = min(x1 + w1, x2 + w2)
        yi2 = min(y1 + h1, y2 + h2)
        
        intersection = max(0, xi2 - xi1) * max(0, yi2 - yi1)
        union = w1 * h1 + w2 * h2 - intersection
        
        return intersection / union if union > 0 else 0
    
    def _create_track(self, detection: Dict, sensor_id: str):
        """Create new track from detection"""
        track_id = f"T{self.next_track_id:04d}"
        self.next_track_id += 1
        
        bbox = detection.get('bbox', [0, 0, 100, 100])
        
        self.tracks[track_id] = FusedDetection(
            track_id=track_id,
            position={'x': bbox[0] + bbox[2]/2, 'y': bbox[1] + bbox[3]/2, 'z': 0},
            class_name=detection.get('class', 'unknown'),
            class_confidence=detection.get('confidence', 0.5),
            bbox=bbox,
            sensor_sources=[sensor_id],
            fusion_confidence=detection.get('confidence', 0.5)
        )
        
        # Initialize Kalman filter for this track
        self.kalman_filters[track_id] = KalmanFilter()
        self.kalman_filters[track_id].state[0] = bbox[0] + bbox[2]/2
        self.kalman_filters[track_id].state[1] = bbox[1] + bbox[3]/2
    
    def _update_track(self, track_id: str, detection: Dict, sensor_id: str):
        """Update existing track with new detection"""
        track = self.tracks[track_id]
        bbox = detection.get('bbox', track.bbox)
        
        # Update Kalman filter
        if track_id in self.kalman_filters:
            kf = self.kalman_filters[track_id]
            kf.update([bbox[0] + bbox[2]/2, bbox[1] + bbox[3]/2])
            state = kf.get_state()
            track.position = {'x': state['x'], 'y': state['y'], 'z': 0}
            track.velocity = {'vx': state['vx'], 'vy': state['vy'], 'vz': 0}
        
        # Update track
        track.bbox = bbox
        track.class_confidence = max(track.class_confidence, detection.get('confidence', 0.5))
        track.last_seen = datetime.now(timezone.utc)
        track.age_frames = 0
        
        # Add sensor source if new
        if sensor_id not in track.sensor_sources:
            track.sensor_sources.append(sensor_id)
        
        # Update fusion confidence based on sensor agreement
        track.fusion_confidence = min(1.0, len(track.sensor_sources) * 0.3 + track.class_confidence * 0.4)
    
    def _cleanup_tracks(self):
        """Remove old/stale tracks"""
        to_remove = []
        for track_id, track in self.tracks.items():
            if track.age_frames > self.max_age:
                to_remove.append(track_id)
        
        for track_id in to_remove:
            del self.tracks[track_id]
            if track_id in self.kalman_filters:
                del self.kalman_filters[track_id]
    
    def _build_output(self) -> FusedOutput:
        """Build fused output from current state"""
        # Predict all Kalman filters
        for track_id, kf in self.kalman_filters.items():
            kf.predict()
        
        return FusedOutput(
            detections=list(self.tracks.values()),
            active_sensors=list(self.sensors.keys()),
            threat_level=self._assess_threat_level()
        )
    
    def _assess_threat_level(self) -> str:
        """Assess overall threat level from current tracks"""
        threat_classes = {'person': 0.2, 'vehicle': 0.3, 'aircraft': 0.5, 'weapon': 0.9}
        
        max_threat = 0.0
        for track in self.tracks.values():
            class_threat = threat_classes.get(track.class_name.lower(), 0.1)
            track_threat = class_threat * track.fusion_confidence
            max_threat = max(max_threat, track_threat)
        
        if max_threat > 0.7:
            return "CRITICAL"
        elif max_threat > 0.5:
            return "HIGH"
        elif max_threat > 0.3:
            return "MEDIUM"
        return "LOW"
    
    def get_tracks(self) -> List[FusedDetection]:
        """Get all current tracks"""
        return list(self.tracks.values())
    
    def get_track(self, track_id: str) -> Optional[FusedDetection]:
        """Get specific track by ID"""
        return self.tracks.get(track_id)

# Global fusion instance
sensor_fusion = SensorFusion()
