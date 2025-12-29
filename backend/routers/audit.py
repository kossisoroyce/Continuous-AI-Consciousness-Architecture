"""
Audit API Router
Endpoints for audit logging, querying, and integrity verification
"""
from fastapi import APIRouter, HTTPException, Query
from pydantic import BaseModel
from typing import Optional, List, Dict, Any
from datetime import datetime, timezone

router = APIRouter()

# Import audit systems
from audit.logger import audit_logger, AuditEventType
from audit.store import AuditStore

# Initialize store
audit_store = AuditStore()

# ============== Audit Logging ==============

class LogEventRequest(BaseModel):
    event_type: str
    action: str
    details: Dict[str, Any] = {}
    session_id: Optional[str] = None
    user_id: Optional[str] = None
    brain_id: Optional[str] = None
    ai_confidence: Optional[float] = None
    ai_reasoning: Optional[str] = None
    sensitivity: str = "UNCLASSIFIED"

class LogAIDecisionRequest(BaseModel):
    action: str
    recommendation: str
    confidence: float
    reasoning: str
    session_id: Optional[str] = None
    brain_id: Optional[str] = None
    details: Dict[str, Any] = {}

class LogOperatorActionRequest(BaseModel):
    action: str
    response: str
    related_ai_event_id: Optional[str] = None
    session_id: Optional[str] = None
    user_id: Optional[str] = None
    details: Dict[str, Any] = {}

@router.post("/audit/log")
async def log_event(request: LogEventRequest):
    """Log a general audit event"""
    try:
        event_type = AuditEventType(request.event_type)
    except ValueError:
        raise HTTPException(
            status_code=400, 
            detail=f"Invalid event type: {request.event_type}. Valid types: {[e.value for e in AuditEventType]}"
        )
    
    event = audit_logger.log(
        event_type=event_type,
        action=request.action,
        details=request.details,
        session_id=request.session_id,
        user_id=request.user_id,
        brain_id=request.brain_id,
        ai_confidence=request.ai_confidence,
        ai_reasoning=request.ai_reasoning,
        sensitivity=request.sensitivity
    )
    
    # Also store in database
    audit_store.store_event(event)
    
    return {
        "event_id": event.id,
        "timestamp": event.timestamp.isoformat(),
        "event_hash": event.event_hash
    }

@router.post("/audit/log/ai-decision")
async def log_ai_decision(request: LogAIDecisionRequest):
    """Log an AI decision with explainability data"""
    event = audit_logger.log_ai_decision(
        action=request.action,
        recommendation=request.recommendation,
        confidence=request.confidence,
        reasoning=request.reasoning,
        session_id=request.session_id,
        brain_id=request.brain_id,
        details=request.details
    )
    
    audit_store.store_event(event)
    
    return {
        "event_id": event.id,
        "timestamp": event.timestamp.isoformat(),
        "confidence": request.confidence
    }

@router.post("/audit/log/operator-action")
async def log_operator_action(request: LogOperatorActionRequest):
    """Log an operator action"""
    event = audit_logger.log_operator_action(
        action=request.action,
        response=request.response,
        related_ai_event_id=request.related_ai_event_id,
        session_id=request.session_id,
        user_id=request.user_id,
        details=request.details
    )
    
    audit_store.store_event(event)
    
    return {
        "event_id": event.id,
        "timestamp": event.timestamp.isoformat(),
        "event_type": event.event_type.value
    }

# ============== Audit Query ==============

@router.get("/audit/events")
async def query_events(
    event_type: Optional[str] = None,
    session_id: Optional[str] = None,
    user_id: Optional[str] = None,
    brain_id: Optional[str] = None,
    start_time: Optional[str] = None,
    end_time: Optional[str] = None,
    limit: int = Query(default=100, le=1000),
    offset: int = 0
):
    """Query audit events with filters"""
    start_dt = None
    end_dt = None
    
    if start_time:
        try:
            start_dt = datetime.fromisoformat(start_time.replace('Z', '+00:00'))
        except ValueError:
            raise HTTPException(status_code=400, detail="Invalid start_time format")
    
    if end_time:
        try:
            end_dt = datetime.fromisoformat(end_time.replace('Z', '+00:00'))
        except ValueError:
            raise HTTPException(status_code=400, detail="Invalid end_time format")
    
    events = audit_store.query_events(
        event_type=event_type,
        session_id=session_id,
        user_id=user_id,
        brain_id=brain_id,
        start_time=start_dt,
        end_time=end_dt,
        limit=limit,
        offset=offset
    )
    
    return {
        "count": len(events),
        "offset": offset,
        "limit": limit,
        "events": events
    }

@router.get("/audit/events/{event_id}")
async def get_event(event_id: str):
    """Get a specific audit event"""
    events = audit_store.query_events(limit=1000)
    event = next((e for e in events if e.get("id") == event_id), None)
    
    if not event:
        raise HTTPException(status_code=404, detail="Event not found")
    
    return event

@router.get("/audit/session/{session_id}")
async def get_session_events(session_id: str, limit: int = Query(default=500, le=2000)):
    """Get all events for a session"""
    events = audit_store.query_events(session_id=session_id, limit=limit)
    
    return {
        "session_id": session_id,
        "event_count": len(events),
        "events": events
    }

@router.get("/audit/sessions")
async def list_sessions(limit: int = Query(default=20, le=100), offset: int = 0):
    """List historical sessions from audit log"""
    sessions = audit_store.get_sessions(limit=limit, offset=offset)
    
    return {
        "count": len(sessions),
        "offset": offset,
        "limit": limit,
        "sessions": sessions
    }

# ============== Integrity Verification ==============

@router.get("/audit/verify")
async def verify_integrity(session_id: Optional[str] = None):
    """Verify audit log integrity"""
    # Verify in-memory chain
    memory_valid, memory_error = audit_logger.verify_integrity()
    
    # Verify stored chain
    store_valid, store_error = audit_store.verify_chain(session_id)
    
    return {
        "memory_chain_valid": memory_valid,
        "memory_chain_error": memory_error,
        "store_chain_valid": store_valid,
        "store_chain_error": store_error,
        "overall_valid": memory_valid and store_valid
    }

@router.get("/audit/statistics")
async def get_statistics(session_id: Optional[str] = None):
    """Get audit statistics"""
    stats = audit_store.get_statistics(session_id)
    
    return {
        "session_id": session_id,
        **stats
    }

# ============== Export ==============

@router.get("/audit/export")
async def export_audit_log(
    session_id: Optional[str] = None,
    include_hashes: bool = True,
    format: str = "json"
):
    """Export audit log for review"""
    events = audit_logger.export_for_review(
        session_id=session_id,
        include_hashes=include_hashes
    )
    
    return {
        "session_id": session_id,
        "export_time": datetime.now(timezone.utc).isoformat(),
        "event_count": len(events),
        "format": format,
        "events": events
    }

@router.get("/audit/event-types")
async def list_event_types():
    """List all available audit event types"""
    return {
        "event_types": [
            {"value": e.value, "name": e.name}
            for e in AuditEventType
        ]
    }
