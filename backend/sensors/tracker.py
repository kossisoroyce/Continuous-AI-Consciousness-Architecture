"""
Real-Time Object Tracker
Persistent object tracking with unique IDs across frames
"""
from typing import Dict, List, Optional, Tuple
from pydantic import BaseModel, Field
from datetime import datetime, timezone
import uuid
import math

class TrackedObject(BaseModel):
    """Tracked object with persistent ID"""
    track_id: str
    class_name: str
    confidence: float
    bbox: List[float]  # [x, y, w, h]
    
    # Tracking state
    velocity: Tuple[float, float] = (0.0, 0.0)
    acceleration: Tuple[float, float] = (0.0, 0.0)
    
    # History
    hits: int = 1
    misses: int = 0
    age: int = 0
    
    # Timestamps
    first_seen: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
    last_seen: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
    
    # State
    is_confirmed: bool = False
    is_lost: bool = False
    
    # Predicted position for next frame
    predicted_bbox: Optional[List[float]] = None
    
    def predict(self, dt: float = 0.033):
        """Predict next position based on velocity"""
        if self.bbox:
            cx = self.bbox[0] + self.bbox[2] / 2
            cy = self.bbox[1] + self.bbox[3] / 2
            
            # Apply velocity
            new_cx = cx + self.velocity[0] * dt
            new_cy = cy + self.velocity[1] * dt
            
            self.predicted_bbox = [
                new_cx - self.bbox[2] / 2,
                new_cy - self.bbox[3] / 2,
                self.bbox[2],
                self.bbox[3]
            ]
    
    def update(self, detection: Dict):
        """Update track with new detection"""
        new_bbox = detection.get('bbox', self.bbox)
        
        # Calculate velocity from position change
        if self.bbox and new_bbox:
            old_cx = self.bbox[0] + self.bbox[2] / 2
            old_cy = self.bbox[1] + self.bbox[3] / 2
            new_cx = new_bbox[0] + new_bbox[2] / 2
            new_cy = new_bbox[1] + new_bbox[3] / 2
            
            # Smooth velocity update
            alpha = 0.3
            self.velocity = (
                alpha * (new_cx - old_cx) * 30 + (1 - alpha) * self.velocity[0],
                alpha * (new_cy - old_cy) * 30 + (1 - alpha) * self.velocity[1]
            )
        
        self.bbox = new_bbox
        self.confidence = detection.get('confidence', self.confidence)
        self.class_name = detection.get('class', self.class_name)
        self.hits += 1
        self.misses = 0
        self.age += 1
        self.last_seen = datetime.now(timezone.utc)
        
        # Confirm track after enough hits
        if self.hits >= 3:
            self.is_confirmed = True
    
    def mark_missed(self):
        """Mark track as missed this frame"""
        self.misses += 1
        self.age += 1
        
        # Use prediction as current position
        if self.predicted_bbox:
            self.bbox = self.predicted_bbox
        
        # Mark as lost if too many misses
        if self.misses > 10:
            self.is_lost = True

class ObjectTracker:
    """
    SORT-inspired object tracker
    Maintains persistent IDs for detected objects
    """
    
    def __init__(self):
        self.tracks: Dict[str, TrackedObject] = {}
        self.next_id = 1
        
        # Parameters
        self.iou_threshold = 0.25
        self.max_misses = 15
        self.min_hits_to_confirm = 3
    
    def update(self, detections: List[Dict]) -> List[TrackedObject]:
        """
        Update tracker with new detections
        Returns list of active tracks
        """
        # Predict all tracks
        for track in self.tracks.values():
            track.predict()
        
        # Match detections to tracks
        matched, unmatched_dets, unmatched_tracks = self._match(detections)
        
        # Update matched tracks
        for track_id, det in matched:
            self.tracks[track_id].update(det)
        
        # Create new tracks for unmatched detections
        for det in unmatched_dets:
            self._create_track(det)
        
        # Mark unmatched tracks as missed
        for track_id in unmatched_tracks:
            self.tracks[track_id].mark_missed()
        
        # Remove lost tracks
        self._cleanup()
        
        # Return confirmed tracks
        return [t for t in self.tracks.values() if t.is_confirmed and not t.is_lost]
    
    def _match(self, detections: List[Dict]) -> Tuple[List, List, List]:
        """Match detections to existing tracks using IoU"""
        matched = []
        unmatched_dets = list(range(len(detections)))
        unmatched_tracks = list(self.tracks.keys())
        
        if not detections or not self.tracks:
            return matched, [detections[i] for i in unmatched_dets], unmatched_tracks
        
        # Build cost matrix
        cost_matrix = []
        for track_id in self.tracks:
            track = self.tracks[track_id]
            track_bbox = track.predicted_bbox or track.bbox
            row = []
            for det in detections:
                det_bbox = det.get('bbox', [0, 0, 100, 100])
                iou = self._iou(track_bbox, det_bbox)
                row.append(1 - iou)  # Cost = 1 - IoU
            cost_matrix.append(row)
        
        # Greedy matching
        track_ids = list(self.tracks.keys())
        while cost_matrix and unmatched_dets and unmatched_tracks:
            # Find minimum cost
            min_cost = float('inf')
            min_i, min_j = -1, -1
            
            for i, track_id in enumerate(track_ids):
                if track_id not in unmatched_tracks:
                    continue
                for j in unmatched_dets:
                    if cost_matrix[i][j] < min_cost:
                        min_cost = cost_matrix[i][j]
                        min_i, min_j = i, j
            
            if min_cost > (1 - self.iou_threshold):
                break
            
            track_id = track_ids[min_i]
            matched.append((track_id, detections[min_j]))
            unmatched_tracks.remove(track_id)
            unmatched_dets.remove(min_j)
        
        return matched, [detections[i] for i in unmatched_dets], unmatched_tracks
    
    def _iou(self, box1: List[float], box2: List[float]) -> float:
        """Calculate IoU between two boxes [x, y, w, h]"""
        if not box1 or not box2:
            return 0
        
        x1, y1, w1, h1 = box1
        x2, y2, w2, h2 = box2
        
        xi1 = max(x1, x2)
        yi1 = max(y1, y2)
        xi2 = min(x1 + w1, x2 + w2)
        yi2 = min(y1 + h1, y2 + h2)
        
        intersection = max(0, xi2 - xi1) * max(0, yi2 - yi1)
        union = w1 * h1 + w2 * h2 - intersection
        
        return intersection / union if union > 0 else 0
    
    def _create_track(self, detection: Dict):
        """Create new track from detection"""
        track_id = f"OBJ-{self.next_id:05d}"
        self.next_id += 1
        
        self.tracks[track_id] = TrackedObject(
            track_id=track_id,
            class_name=detection.get('class', 'unknown'),
            confidence=detection.get('confidence', 0.5),
            bbox=detection.get('bbox', [0, 0, 100, 100])
        )
    
    def _cleanup(self):
        """Remove lost tracks"""
        to_remove = [tid for tid, t in self.tracks.items() if t.is_lost]
        for tid in to_remove:
            del self.tracks[tid]
    
    def get_track(self, track_id: str) -> Optional[TrackedObject]:
        """Get specific track"""
        return self.tracks.get(track_id)
    
    def get_all_tracks(self) -> List[TrackedObject]:
        """Get all tracks including unconfirmed"""
        return list(self.tracks.values())
    
    def get_confirmed_tracks(self) -> List[TrackedObject]:
        """Get only confirmed tracks"""
        return [t for t in self.tracks.values() if t.is_confirmed and not t.is_lost]
    
    def reset(self):
        """Reset tracker state"""
        self.tracks.clear()
        self.next_id = 1

# Global tracker instance
object_tracker = ObjectTracker()
