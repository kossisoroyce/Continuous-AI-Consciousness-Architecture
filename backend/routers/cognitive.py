"""
Cognitive Systems API Router
Endpoints for adaptive communication, cognitive load, and mission replay
"""
from fastapi import APIRouter, HTTPException, Depends
from pydantic import BaseModel
from typing import Optional, List, Dict, Any
from datetime import datetime

router = APIRouter()

# Import cognitive systems
from cognitive.adaptive_comm import adaptive_communicator, CommunicationStyle
from cognitive.cognitive_load import cognitive_load_predictor, CognitiveState
from cognitive.mission_replay import mission_recorder, MissionReplay, EventType

# ============== Adaptive Communication ==============

class AnalyzeMessageRequest(BaseModel):
    operator_id: str
    message: str

class AdaptResponseRequest(BaseModel):
    operator_id: str
    response: str
    override_style: Optional[str] = None

@router.post("/cognitive/analyze-message")
async def analyze_operator_message(request: AnalyzeMessageRequest):
    """Analyze operator message to learn communication style"""
    profile = adaptive_communicator.analyze_message(
        request.operator_id,
        request.message
    )
    return {
        "operator_id": profile.operator_id,
        "expertise_level": profile.expertise_level.value,
        "preferred_style": profile.preferred_style.value,
        "reading_grade_level": round(profile.reading_grade_level, 1),
        "technical_term_ratio": round(profile.technical_term_ratio, 3),
        "messages_analyzed": profile.messages_analyzed,
        "domain_familiarity": profile.domain_familiarity
    }

@router.post("/cognitive/adapt-response")
async def adapt_ai_response(request: AdaptResponseRequest):
    """Adapt AI response to match operator's communication style"""
    override = None
    if request.override_style:
        try:
            override = CommunicationStyle(request.override_style)
        except ValueError:
            pass
    
    adapted = adaptive_communicator.adapt_response(
        request.response,
        request.operator_id,
        override
    )
    
    profile = adaptive_communicator.get_profile(request.operator_id)
    
    return {
        "original": request.response,
        "adapted": adapted,
        "style_used": profile.preferred_style.value,
        "operator_expertise": profile.expertise_level.value
    }

@router.get("/cognitive/operator-profile/{operator_id}")
async def get_operator_profile(operator_id: str):
    """Get operator's communication profile"""
    profile = adaptive_communicator.get_profile(operator_id)
    return {
        "operator_id": profile.operator_id,
        "expertise_level": profile.expertise_level.value,
        "preferred_style": profile.preferred_style.value,
        "reading_grade_level": round(profile.reading_grade_level, 1),
        "vocabulary_richness": round(profile.vocabulary_richness, 3),
        "technical_term_ratio": round(profile.technical_term_ratio, 3),
        "domain_familiarity": profile.domain_familiarity,
        "messages_analyzed": profile.messages_analyzed,
        "prefers_detail": profile.prefers_detail,
        "prefers_examples": profile.prefers_examples
    }

@router.get("/cognitive/style-prompt/{operator_id}")
async def get_style_prompt(operator_id: str):
    """Get LLM system prompt modifier for operator's style"""
    prompt = adaptive_communicator.get_style_prompt(operator_id)
    profile = adaptive_communicator.get_profile(operator_id)
    
    return {
        "operator_id": operator_id,
        "style": profile.preferred_style.value,
        "system_prompt_modifier": prompt
    }

# ============== Cognitive Load ==============

class CognitiveLoadUpdateRequest(BaseModel):
    operator_id: str
    metrics: Dict[str, float]

@router.post("/cognitive/load/update")
async def update_cognitive_load(request: CognitiveLoadUpdateRequest):
    """Update cognitive load prediction with new metrics"""
    state = cognitive_load_predictor.update(
        request.operator_id,
        request.metrics
    )
    
    return {
        "operator_id": state.operator_id,
        "overall_load": round(state.overall_load, 3),
        "state": state.state.value,
        "visual_load": round(state.visual_load, 3),
        "cognitive_load": round(state.cognitive_load, 3),
        "predicted_load_5min": round(state.predicted_load_5min, 3),
        "predicted_state_5min": state.predicted_state_5min.value,
        "overload_risk": round(state.overload_risk, 3),
        "recommendations": state.recommendations,
        "factors": [
            {
                "name": f.name,
                "value": round(f.current_value, 3),
                "weight": f.weight,
                "trend": f.trend
            }
            for f in state.factors
        ]
    }

@router.get("/cognitive/load/{operator_id}")
async def get_cognitive_load(operator_id: str):
    """Get current cognitive load state for operator"""
    state = cognitive_load_predictor.get_current_state(operator_id)
    
    if not state:
        return {
            "operator_id": operator_id,
            "state": "unknown",
            "message": "No cognitive load data available"
        }
    
    return {
        "operator_id": state.operator_id,
        "overall_load": round(state.overall_load, 3),
        "state": state.state.value,
        "overload_risk": round(state.overload_risk, 3),
        "recommendations": state.recommendations
    }

@router.get("/cognitive/load/{operator_id}/history")
async def get_cognitive_load_history(operator_id: str, minutes: int = 30):
    """Get cognitive load history for operator"""
    history = cognitive_load_predictor.get_history(operator_id, minutes)
    
    return {
        "operator_id": operator_id,
        "period_minutes": minutes,
        "data_points": len(history),
        "history": [
            {
                "timestamp": s.timestamp.isoformat(),
                "load": round(s.overall_load, 3),
                "state": s.state.value
            }
            for s in history
        ]
    }

@router.get("/cognitive/load/{operator_id}/should-intervene")
async def should_intervene(operator_id: str):
    """Check if AI should intervene to reduce operator load"""
    should, reason = cognitive_load_predictor.should_intervene(operator_id)
    
    return {
        "operator_id": operator_id,
        "should_intervene": should,
        "reason": reason
    }

# ============== Mission Recording & Replay ==============

class StartRecordingRequest(BaseModel):
    name: str
    description: str = ""
    operator_id: Optional[str] = None
    brain_id: Optional[str] = None

class RecordEventRequest(BaseModel):
    recording_id: str
    event_type: str
    data: Dict[str, Any]
    operator_id: Optional[str] = None
    brain_id: Optional[str] = None
    ai_confidence: Optional[float] = None
    ai_reasoning: Optional[str] = None

@router.post("/mission/start-recording")
async def start_mission_recording(request: StartRecordingRequest):
    """Start recording a new mission"""
    recording_id = mission_recorder.start_recording(
        request.name,
        request.description,
        request.operator_id,
        request.brain_id
    )
    
    return {
        "recording_id": recording_id,
        "name": request.name,
        "status": "recording"
    }

@router.post("/mission/stop-recording/{recording_id}")
async def stop_mission_recording(recording_id: str):
    """Stop and finalize a mission recording"""
    recording = mission_recorder.stop_recording(recording_id)
    
    if not recording:
        raise HTTPException(status_code=404, detail="Recording not found")
    
    return {
        "recording_id": recording.id,
        "name": recording.name,
        "duration_seconds": recording.duration_seconds,
        "total_events": len(recording.events),
        "key_moments_count": len(recording.key_moments),
        "status": "completed"
    }

@router.post("/mission/record-event")
async def record_mission_event(request: RecordEventRequest):
    """Record an event to an active mission recording"""
    try:
        event_type = EventType(request.event_type)
    except ValueError:
        raise HTTPException(status_code=400, detail=f"Invalid event type: {request.event_type}")
    
    event = mission_recorder.record_event(
        request.recording_id,
        event_type,
        request.data,
        request.operator_id,
        request.brain_id,
        request.ai_confidence,
        request.ai_reasoning
    )
    
    if not event:
        raise HTTPException(status_code=404, detail="Recording not found or not active")
    
    return {
        "event_id": event.id,
        "frame_number": event.frame_number,
        "relative_time_ms": event.relative_time_ms
    }

@router.get("/mission/recordings")
async def list_mission_recordings():
    """List all available mission recordings"""
    recordings = mission_recorder.list_recordings()
    return {"recordings": recordings}

@router.get("/mission/recording/{recording_id}")
async def get_mission_recording(recording_id: str):
    """Get a specific mission recording"""
    recording = mission_recorder.load_recording(recording_id)
    
    if not recording:
        raise HTTPException(status_code=404, detail="Recording not found")
    
    return {
        "id": recording.id,
        "name": recording.name,
        "description": recording.description,
        "start_time": recording.start_time.isoformat(),
        "end_time": recording.end_time.isoformat() if recording.end_time else None,
        "duration_seconds": recording.duration_seconds,
        "operators": recording.operators,
        "brain_ids": recording.brain_ids,
        "total_events": len(recording.events),
        "statistics": {
            "total_detections": recording.total_detections,
            "ai_recommendations": recording.ai_recommendations,
            "operator_overrides": recording.operator_overrides,
            "average_trust": recording.average_trust_score,
            "average_cognitive_load": recording.average_cognitive_load
        },
        "key_moments": recording.key_moments
    }

@router.get("/mission/recording/{recording_id}/report")
async def get_after_action_report(recording_id: str):
    """Generate after-action report for a mission"""
    recording = mission_recorder.load_recording(recording_id)
    
    if not recording:
        raise HTTPException(status_code=404, detail="Recording not found")
    
    replay = MissionReplay(recording)
    return replay.generate_after_action_report()

@router.get("/mission/recording/{recording_id}/events")
async def get_mission_events(
    recording_id: str,
    start_ms: int = 0,
    end_ms: int = None,
    event_type: str = None
):
    """Get events from a mission recording"""
    recording = mission_recorder.load_recording(recording_id)
    
    if not recording:
        raise HTTPException(status_code=404, detail="Recording not found")
    
    replay = MissionReplay(recording)
    
    if end_ms:
        events = replay.get_events_in_range(start_ms, end_ms)
    else:
        events = replay.get_event_at_time(start_ms if start_ms else 999999999)
    
    if event_type:
        events = [e for e in events if e.event_type.value == event_type]
    
    return {
        "recording_id": recording_id,
        "event_count": len(events),
        "events": [
            {
                "id": e.id,
                "timestamp": e.timestamp.isoformat(),
                "relative_time_ms": e.relative_time_ms,
                "type": e.event_type.value,
                "data": e.data,
                "ai_confidence": e.ai_confidence,
                "ai_reasoning": e.ai_reasoning
            }
            for e in events[:100]  # Limit response size
        ]
    }

@router.get("/mission/recording/{recording_id}/analyze-decision/{event_id}")
async def analyze_ai_decision(recording_id: str, event_id: str):
    """Deep analysis of a specific AI decision"""
    recording = mission_recorder.load_recording(recording_id)
    
    if not recording:
        raise HTTPException(status_code=404, detail="Recording not found")
    
    replay = MissionReplay(recording)
    return replay.analyze_decision(event_id)
