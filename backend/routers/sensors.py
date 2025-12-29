"""
Sensor Fusion & Object Tracking API Router
Endpoints for multi-sensor fusion and persistent object tracking
"""
from fastapi import APIRouter, HTTPException
from pydantic import BaseModel
from typing import Optional, List, Dict, Any
from datetime import datetime

router = APIRouter()

# Import sensor systems
from sensors.fusion import sensor_fusion, SensorData, SensorType
from sensors.tracker import object_tracker

# ============== Sensor Registration ==============

class RegisterSensorRequest(BaseModel):
    sensor_id: str
    sensor_type: str

@router.post("/sensors/register")
async def register_sensor(request: RegisterSensorRequest):
    """Register a new sensor source"""
    try:
        sensor_type = SensorType(request.sensor_type)
    except ValueError:
        raise HTTPException(
            status_code=400, 
            detail=f"Invalid sensor type. Valid types: {[t.value for t in SensorType]}"
        )
    
    sensor_fusion.register_sensor(request.sensor_id, sensor_type)
    
    return {
        "sensor_id": request.sensor_id,
        "sensor_type": request.sensor_type,
        "status": "registered"
    }

@router.get("/sensors")
async def list_sensors():
    """List all registered sensors"""
    sensors = []
    for sensor_id, data in sensor_fusion.sensors.items():
        sensors.append({
            "sensor_id": sensor_id,
            "sensor_type": data.sensor_type.value if hasattr(data.sensor_type, 'value') else data.sensor_type,
            "last_update": data.timestamp.isoformat(),
            "confidence": data.confidence
        })
    
    return {"sensors": sensors}

# ============== Sensor Data Input ==============

class SensorDataRequest(BaseModel):
    sensor_id: str
    sensor_type: str
    detections: List[Dict[str, Any]] = []
    position: Optional[Dict[str, float]] = None
    velocity: Optional[Dict[str, float]] = None
    raw_data: Dict[str, Any] = {}
    confidence: float = 1.0

@router.post("/sensors/data")
async def submit_sensor_data(request: SensorDataRequest):
    """Submit sensor data for fusion"""
    try:
        sensor_type = SensorType(request.sensor_type)
    except ValueError:
        sensor_type = SensorType.CAMERA_RGB  # Default
    
    data = SensorData(
        sensor_id=request.sensor_id,
        sensor_type=sensor_type,
        detections=request.detections,
        position=request.position,
        velocity=request.velocity,
        raw_data=request.raw_data,
        confidence=request.confidence
    )
    
    # Process through fusion
    output = sensor_fusion.update(data)
    
    return {
        "timestamp": output.timestamp.isoformat(),
        "detection_count": len(output.detections),
        "active_sensors": output.active_sensors,
        "threat_level": output.threat_level,
        "detections": [
            {
                "track_id": d.track_id,
                "class": d.class_name,
                "confidence": round(d.class_confidence, 3),
                "fusion_confidence": round(d.fusion_confidence, 3),
                "bbox": d.bbox,
                "position": d.position,
                "sensor_sources": d.sensor_sources
            }
            for d in output.detections
        ]
    }

# ============== Fused Output ==============

@router.get("/sensors/fused")
async def get_fused_state():
    """Get current fused sensor state"""
    tracks = sensor_fusion.get_tracks()
    
    return {
        "timestamp": datetime.utcnow().isoformat(),
        "track_count": len(tracks),
        "active_sensors": list(sensor_fusion.sensors.keys()),
        "tracks": [
            {
                "track_id": t.track_id,
                "class": t.class_name,
                "confidence": round(t.class_confidence, 3),
                "fusion_confidence": round(t.fusion_confidence, 3),
                "bbox": t.bbox,
                "position": t.position,
                "velocity": t.velocity,
                "sensor_sources": t.sensor_sources,
                "first_seen": t.first_seen.isoformat(),
                "last_seen": t.last_seen.isoformat(),
                "age_frames": t.age_frames
            }
            for t in tracks
        ]
    }

@router.get("/sensors/fused/track/{track_id}")
async def get_fused_track(track_id: str):
    """Get specific fused track"""
    track = sensor_fusion.get_track(track_id)
    
    if not track:
        raise HTTPException(status_code=404, detail="Track not found")
    
    return {
        "track_id": track.track_id,
        "class": track.class_name,
        "confidence": round(track.class_confidence, 3),
        "fusion_confidence": round(track.fusion_confidence, 3),
        "bbox": track.bbox,
        "position": track.position,
        "velocity": track.velocity,
        "sensor_sources": track.sensor_sources,
        "first_seen": track.first_seen.isoformat(),
        "last_seen": track.last_seen.isoformat()
    }

# ============== Object Tracking ==============

class TrackingUpdateRequest(BaseModel):
    detections: List[Dict[str, Any]]

@router.post("/tracking/update")
async def update_tracking(request: TrackingUpdateRequest):
    """Update object tracker with new detections"""
    tracks = object_tracker.update(request.detections)
    
    return {
        "timestamp": datetime.utcnow().isoformat(),
        "confirmed_tracks": len(tracks),
        "total_tracks": len(object_tracker.get_all_tracks()),
        "tracks": [
            {
                "track_id": t.track_id,
                "class": t.class_name,
                "confidence": round(t.confidence, 3),
                "bbox": t.bbox,
                "velocity": t.velocity,
                "hits": t.hits,
                "age": t.age,
                "is_confirmed": t.is_confirmed
            }
            for t in tracks
        ]
    }

@router.get("/tracking/tracks")
async def get_all_tracks():
    """Get all current tracks"""
    confirmed = object_tracker.get_confirmed_tracks()
    all_tracks = object_tracker.get_all_tracks()
    
    return {
        "confirmed_count": len(confirmed),
        "total_count": len(all_tracks),
        "confirmed_tracks": [
            {
                "track_id": t.track_id,
                "class": t.class_name,
                "confidence": round(t.confidence, 3),
                "bbox": t.bbox,
                "velocity": t.velocity,
                "hits": t.hits,
                "misses": t.misses,
                "age": t.age,
                "first_seen": t.first_seen.isoformat(),
                "last_seen": t.last_seen.isoformat()
            }
            for t in confirmed
        ]
    }

@router.get("/tracking/track/{track_id}")
async def get_track(track_id: str):
    """Get specific track details"""
    track = object_tracker.get_track(track_id)
    
    if not track:
        raise HTTPException(status_code=404, detail="Track not found")
    
    return {
        "track_id": track.track_id,
        "class": track.class_name,
        "confidence": round(track.confidence, 3),
        "bbox": track.bbox,
        "predicted_bbox": track.predicted_bbox,
        "velocity": track.velocity,
        "acceleration": track.acceleration,
        "hits": track.hits,
        "misses": track.misses,
        "age": track.age,
        "is_confirmed": track.is_confirmed,
        "is_lost": track.is_lost,
        "first_seen": track.first_seen.isoformat(),
        "last_seen": track.last_seen.isoformat()
    }

@router.post("/tracking/reset")
async def reset_tracking():
    """Reset all tracking state"""
    object_tracker.reset()
    
    return {"message": "Tracking reset", "tracks": 0}

@router.get("/sensors/types")
async def list_sensor_types():
    """List all available sensor types"""
    return {
        "sensor_types": [
            {"value": t.value, "name": t.name}
            for t in SensorType
        ]
    }
