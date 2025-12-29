"""
Immutable Audit Logger
Provides tamper-evident logging for all system events
"""
import hashlib
import json
import uuid
from datetime import datetime, timezone
from enum import Enum
from typing import Optional, Dict, Any, List
from pydantic import BaseModel, Field
import os

class AuditEventType(str, Enum):
    # Authentication & Access
    AUTH_LOGIN = "auth.login"
    AUTH_LOGOUT = "auth.logout"
    AUTH_FAILED = "auth.failed"
    ACCESS_GRANTED = "access.granted"
    ACCESS_DENIED = "access.denied"
    
    # AI Decision Events
    AI_RECOMMENDATION = "ai.recommendation"
    AI_DECISION = "ai.decision"
    AI_OVERRIDE = "ai.override"
    AI_ERROR = "ai.error"
    AI_CONFIDENCE_CHANGE = "ai.confidence_change"
    
    # Operator Actions
    OPERATOR_ACCEPT = "operator.accept"
    OPERATOR_REJECT = "operator.reject"
    OPERATOR_MODIFY = "operator.modify"
    OPERATOR_COMMAND = "operator.command"
    
    # Trust & Calibration
    TRUST_UPDATE = "trust.update"
    TRUST_ALERT = "trust.alert"
    CALIBRATION_CHANGE = "calibration.change"
    
    # Mission Events
    MISSION_START = "mission.start"
    MISSION_END = "mission.end"
    MISSION_CHECKPOINT = "mission.checkpoint"
    
    # Detection Events
    DETECTION_NEW = "detection.new"
    DETECTION_TRACK = "detection.track"
    DETECTION_LOST = "detection.lost"
    DETECTION_CLASSIFY = "detection.classify"
    
    # System Events
    SYSTEM_START = "system.start"
    SYSTEM_STOP = "system.stop"
    SYSTEM_ERROR = "system.error"
    CONFIG_CHANGE = "config.change"
    
    # Data Events
    DATA_EXPORT = "data.export"
    DATA_ACCESS = "data.access"
    DATA_MODIFY = "data.modify"

class AuditEvent(BaseModel):
    """Immutable audit event with cryptographic integrity"""
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    timestamp: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
    event_type: AuditEventType
    session_id: Optional[str] = None
    user_id: Optional[str] = None
    brain_id: Optional[str] = None
    
    # Event details
    action: str
    details: Dict[str, Any] = Field(default_factory=dict)
    
    # AI-specific fields
    ai_confidence: Optional[float] = None
    ai_reasoning: Optional[str] = None
    operator_response: Optional[str] = None
    
    # Integrity
    previous_hash: Optional[str] = None
    event_hash: Optional[str] = None
    
    # Classification
    sensitivity: str = "UNCLASSIFIED"  # UNCLASSIFIED, CUI, SECRET, TOP SECRET
    
    def compute_hash(self) -> str:
        """Compute SHA-256 hash of event for integrity verification"""
        data = {
            "id": self.id,
            "timestamp": self.timestamp.isoformat(),
            "event_type": self.event_type.value,
            "session_id": self.session_id,
            "user_id": self.user_id,
            "brain_id": self.brain_id,
            "action": self.action,
            "details": self.details,
            "ai_confidence": self.ai_confidence,
            "ai_reasoning": self.ai_reasoning,
            "previous_hash": self.previous_hash
        }
        json_str = json.dumps(data, sort_keys=True, default=str)
        return hashlib.sha256(json_str.encode()).hexdigest()
    
    def to_immutable(self, previous_hash: Optional[str] = None) -> 'AuditEvent':
        """Create immutable version with hash chain"""
        self.previous_hash = previous_hash
        self.event_hash = self.compute_hash()
        return self

class AuditLogger:
    """
    Thread-safe audit logger with hash chain for tamper detection
    """
    _instance = None
    _events: List[AuditEvent] = []
    _last_hash: Optional[str] = None
    _log_file: Optional[str] = None
    
    def __new__(cls):
        if cls._instance is None:
            cls._instance = super().__new__(cls)
            cls._instance._initialize()
        return cls._instance
    
    def _initialize(self):
        """Initialize the audit logger"""
        self._events = []
        self._last_hash = None
        
        # Create audit log directory
        log_dir = os.path.join(os.path.dirname(__file__), '..', 'data', 'audit')
        os.makedirs(log_dir, exist_ok=True)
        
        # Create new log file with timestamp
        timestamp = datetime.now(timezone.utc).strftime('%Y%m%d_%H%M%S')
        self._log_file = os.path.join(log_dir, f'audit_{timestamp}.jsonl')
        
        # Log system start
        self.log(
            event_type=AuditEventType.SYSTEM_START,
            action="Audit system initialized",
            details={"log_file": self._log_file}
        )
    
    def log(
        self,
        event_type: AuditEventType,
        action: str,
        details: Dict[str, Any] = None,
        session_id: str = None,
        user_id: str = None,
        brain_id: str = None,
        ai_confidence: float = None,
        ai_reasoning: str = None,
        operator_response: str = None,
        sensitivity: str = "UNCLASSIFIED"
    ) -> AuditEvent:
        """Log an audit event with hash chain integrity"""
        event = AuditEvent(
            event_type=event_type,
            action=action,
            details=details or {},
            session_id=session_id,
            user_id=user_id,
            brain_id=brain_id,
            ai_confidence=ai_confidence,
            ai_reasoning=ai_reasoning,
            operator_response=operator_response,
            sensitivity=sensitivity
        )
        
        # Add to hash chain
        event = event.to_immutable(self._last_hash)
        self._last_hash = event.event_hash
        self._events.append(event)
        
        # Write to file (append mode for durability)
        if self._log_file:
            try:
                with open(self._log_file, 'a') as f:
                    f.write(event.model_dump_json() + '\n')
            except Exception as e:
                print(f"Failed to write audit log: {e}")
        
        return event
    
    def log_ai_decision(
        self,
        action: str,
        recommendation: str,
        confidence: float,
        reasoning: str,
        session_id: str = None,
        brain_id: str = None,
        details: Dict[str, Any] = None
    ) -> AuditEvent:
        """Convenience method for logging AI decisions"""
        return self.log(
            event_type=AuditEventType.AI_RECOMMENDATION,
            action=action,
            details={
                "recommendation": recommendation,
                **(details or {})
            },
            session_id=session_id,
            brain_id=brain_id,
            ai_confidence=confidence,
            ai_reasoning=reasoning
        )
    
    def log_operator_action(
        self,
        action: str,
        response: str,
        related_ai_event_id: str = None,
        session_id: str = None,
        user_id: str = None,
        details: Dict[str, Any] = None
    ) -> AuditEvent:
        """Convenience method for logging operator actions"""
        event_type = AuditEventType.OPERATOR_ACCEPT
        if response.lower() in ['reject', 'rejected', 'no']:
            event_type = AuditEventType.OPERATOR_REJECT
        elif response.lower() in ['modify', 'modified', 'change']:
            event_type = AuditEventType.OPERATOR_MODIFY
        
        return self.log(
            event_type=event_type,
            action=action,
            details={
                "related_ai_event": related_ai_event_id,
                **(details or {})
            },
            session_id=session_id,
            user_id=user_id,
            operator_response=response
        )
    
    def log_detection(
        self,
        action: str,
        detection_data: Dict[str, Any],
        session_id: str = None,
        brain_id: str = None
    ) -> AuditEvent:
        """Log object detection events"""
        return self.log(
            event_type=AuditEventType.DETECTION_NEW,
            action=action,
            details=detection_data,
            session_id=session_id,
            brain_id=brain_id
        )
    
    def verify_integrity(self) -> tuple[bool, Optional[str]]:
        """Verify the integrity of the entire audit chain"""
        if not self._events:
            return True, None
        
        prev_hash = None
        for i, event in enumerate(self._events):
            # Verify hash chain
            if event.previous_hash != prev_hash:
                return False, f"Hash chain broken at event {i}: {event.id}"
            
            # Verify event hash
            computed = event.compute_hash()
            if event.event_hash != computed:
                return False, f"Event hash mismatch at {i}: {event.id}"
            
            prev_hash = event.event_hash
        
        return True, None
    
    def get_events(
        self,
        event_type: AuditEventType = None,
        session_id: str = None,
        start_time: datetime = None,
        end_time: datetime = None,
        limit: int = 100
    ) -> List[AuditEvent]:
        """Query audit events with filters"""
        results = []
        for event in reversed(self._events):
            if event_type and event.event_type != event_type:
                continue
            if session_id and event.session_id != session_id:
                continue
            if start_time and event.timestamp < start_time:
                continue
            if end_time and event.timestamp > end_time:
                continue
            
            results.append(event)
            if len(results) >= limit:
                break
        
        return results
    
    def export_for_review(
        self,
        session_id: str = None,
        include_hashes: bool = True
    ) -> List[Dict[str, Any]]:
        """Export events for mission review/analysis"""
        events = self.get_events(session_id=session_id, limit=10000)
        
        exported = []
        for event in events:
            data = event.model_dump()
            if not include_hashes:
                data.pop('previous_hash', None)
                data.pop('event_hash', None)
            exported.append(data)
        
        return exported

# Global singleton instance
audit_logger = AuditLogger()
