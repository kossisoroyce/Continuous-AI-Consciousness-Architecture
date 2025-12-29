"""
Mission Replay & Analysis System
Records and replays mission data with AI decision explanations
"""
from typing import Dict, List, Optional, Any
from pydantic import BaseModel, Field
from datetime import datetime, timezone, timedelta
from enum import Enum
import uuid
import json
import os

class EventType(str, Enum):
    """Mission event types"""
    MISSION_START = "mission_start"
    MISSION_END = "mission_end"
    CHECKPOINT = "checkpoint"
    
    DETECTION = "detection"
    TRACK_NEW = "track_new"
    TRACK_UPDATE = "track_update"
    TRACK_LOST = "track_lost"
    
    AI_RECOMMENDATION = "ai_recommendation"
    AI_DECISION = "ai_decision"
    AI_ALERT = "ai_alert"
    
    OPERATOR_ACTION = "operator_action"
    OPERATOR_OVERRIDE = "operator_override"
    OPERATOR_COMMAND = "operator_command"
    
    TRUST_UPDATE = "trust_update"
    COGNITIVE_LOAD = "cognitive_load"
    
    SENSOR_DATA = "sensor_data"
    SYSTEM_EVENT = "system_event"

class MissionEvent(BaseModel):
    """Single event in mission timeline"""
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    timestamp: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
    event_type: EventType
    
    # Event data
    data: Dict[str, Any] = Field(default_factory=dict)
    
    # Context
    operator_id: Optional[str] = None
    brain_id: Optional[str] = None
    
    # For AI events
    ai_confidence: Optional[float] = None
    ai_reasoning: Optional[str] = None
    
    # Replay metadata
    frame_number: int = 0
    relative_time_ms: int = 0

class MissionRecording(BaseModel):
    """Complete mission recording"""
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    name: str
    description: str = ""
    
    # Timing
    start_time: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
    end_time: Optional[datetime] = None
    duration_seconds: float = 0
    
    # Events
    events: List[MissionEvent] = Field(default_factory=list)
    
    # Participants
    operators: List[str] = Field(default_factory=list)
    brain_ids: List[str] = Field(default_factory=list)
    
    # Statistics
    total_detections: int = 0
    ai_recommendations: int = 0
    operator_overrides: int = 0
    average_trust_score: float = 0.5
    average_cognitive_load: float = 0.5
    
    # Analysis
    key_moments: List[Dict[str, Any]] = Field(default_factory=list)
    lessons_learned: List[str] = Field(default_factory=list)

class MissionRecorder:
    """Records mission events for later replay"""
    
    def __init__(self):
        self.active_recordings: Dict[str, MissionRecording] = {}
        self.completed_recordings: Dict[str, MissionRecording] = {}
        self.frame_counters: Dict[str, int] = {}
        
        # Storage path
        self.storage_path = os.path.join(
            os.path.dirname(__file__), '..', 'data', 'missions'
        )
        os.makedirs(self.storage_path, exist_ok=True)
    
    def start_recording(
        self, 
        name: str, 
        description: str = "",
        operator_id: str = None,
        brain_id: str = None
    ) -> str:
        """Start a new mission recording"""
        recording = MissionRecording(
            name=name,
            description=description,
            operators=[operator_id] if operator_id else [],
            brain_ids=[brain_id] if brain_id else []
        )
        
        self.active_recordings[recording.id] = recording
        self.frame_counters[recording.id] = 0
        
        # Record start event
        self.record_event(
            recording.id,
            EventType.MISSION_START,
            {"name": name, "description": description},
            operator_id=operator_id,
            brain_id=brain_id
        )
        
        return recording.id
    
    def stop_recording(self, recording_id: str) -> Optional[MissionRecording]:
        """Stop and finalize a recording"""
        if recording_id not in self.active_recordings:
            return None
        
        recording = self.active_recordings[recording_id]
        recording.end_time = datetime.now(timezone.utc)
        recording.duration_seconds = (
            recording.end_time - recording.start_time
        ).total_seconds()
        
        # Record end event
        self.record_event(
            recording_id,
            EventType.MISSION_END,
            {"duration_seconds": recording.duration_seconds}
        )
        
        # Calculate statistics
        self._calculate_statistics(recording)
        
        # Identify key moments
        recording.key_moments = self._identify_key_moments(recording)
        
        # Move to completed
        del self.active_recordings[recording_id]
        self.completed_recordings[recording_id] = recording
        
        # Save to disk
        self._save_recording(recording)
        
        return recording
    
    def record_event(
        self,
        recording_id: str,
        event_type: EventType,
        data: Dict[str, Any],
        operator_id: str = None,
        brain_id: str = None,
        ai_confidence: float = None,
        ai_reasoning: str = None
    ) -> Optional[MissionEvent]:
        """Record an event to the mission timeline"""
        if recording_id not in self.active_recordings:
            return None
        
        recording = self.active_recordings[recording_id]
        frame = self.frame_counters[recording_id]
        self.frame_counters[recording_id] += 1
        
        # Calculate relative time
        relative_time = int(
            (datetime.now(timezone.utc) - recording.start_time).total_seconds() * 1000
        )
        
        event = MissionEvent(
            event_type=event_type,
            data=data,
            operator_id=operator_id,
            brain_id=brain_id,
            ai_confidence=ai_confidence,
            ai_reasoning=ai_reasoning,
            frame_number=frame,
            relative_time_ms=relative_time
        )
        
        recording.events.append(event)
        
        # Update participant lists
        if operator_id and operator_id not in recording.operators:
            recording.operators.append(operator_id)
        if brain_id and brain_id not in recording.brain_ids:
            recording.brain_ids.append(brain_id)
        
        return event
    
    def record_ai_decision(
        self,
        recording_id: str,
        decision: str,
        confidence: float,
        reasoning: str,
        context: Dict[str, Any] = None,
        brain_id: str = None
    ) -> Optional[MissionEvent]:
        """Convenience method for recording AI decisions with XAI"""
        return self.record_event(
            recording_id,
            EventType.AI_DECISION,
            {
                "decision": decision,
                "context": context or {},
                "explainability": {
                    "confidence": confidence,
                    "reasoning": reasoning,
                    "factors": self._extract_decision_factors(reasoning)
                }
            },
            brain_id=brain_id,
            ai_confidence=confidence,
            ai_reasoning=reasoning
        )
    
    def record_detection(
        self,
        recording_id: str,
        detections: List[Dict[str, Any]],
        brain_id: str = None
    ) -> Optional[MissionEvent]:
        """Record object detections"""
        return self.record_event(
            recording_id,
            EventType.DETECTION,
            {
                "count": len(detections),
                "detections": detections
            },
            brain_id=brain_id
        )
    
    def _calculate_statistics(self, recording: MissionRecording):
        """Calculate summary statistics for recording"""
        detection_count = 0
        ai_rec_count = 0
        override_count = 0
        trust_scores = []
        cognitive_loads = []
        
        for event in recording.events:
            if event.event_type == EventType.DETECTION:
                detection_count += event.data.get("count", 0)
            elif event.event_type == EventType.AI_RECOMMENDATION:
                ai_rec_count += 1
            elif event.event_type == EventType.OPERATOR_OVERRIDE:
                override_count += 1
            elif event.event_type == EventType.TRUST_UPDATE:
                trust_scores.append(event.data.get("trust_score", 0.5))
            elif event.event_type == EventType.COGNITIVE_LOAD:
                cognitive_loads.append(event.data.get("load", 0.5))
        
        recording.total_detections = detection_count
        recording.ai_recommendations = ai_rec_count
        recording.operator_overrides = override_count
        recording.average_trust_score = sum(trust_scores) / len(trust_scores) if trust_scores else 0.5
        recording.average_cognitive_load = sum(cognitive_loads) / len(cognitive_loads) if cognitive_loads else 0.5
    
    def _identify_key_moments(self, recording: MissionRecording) -> List[Dict[str, Any]]:
        """Identify key moments in the mission for review"""
        key_moments = []
        
        for i, event in enumerate(recording.events):
            is_key = False
            reason = ""
            
            # AI decisions with low confidence
            if event.event_type == EventType.AI_DECISION:
                if event.ai_confidence and event.ai_confidence < 0.6:
                    is_key = True
                    reason = f"Low confidence AI decision ({event.ai_confidence:.0%})"
            
            # Operator overrides
            elif event.event_type == EventType.OPERATOR_OVERRIDE:
                is_key = True
                reason = "Operator overrode AI recommendation"
            
            # High cognitive load
            elif event.event_type == EventType.COGNITIVE_LOAD:
                if event.data.get("load", 0) > 0.8:
                    is_key = True
                    reason = f"High cognitive load ({event.data.get('load', 0):.0%})"
            
            # Critical alerts
            elif event.event_type == EventType.AI_ALERT:
                if event.data.get("severity") == "critical":
                    is_key = True
                    reason = "Critical AI alert"
            
            if is_key:
                key_moments.append({
                    "event_id": event.id,
                    "timestamp": event.timestamp.isoformat(),
                    "relative_time_ms": event.relative_time_ms,
                    "type": event.event_type.value,
                    "reason": reason,
                    "data": event.data
                })
        
        return key_moments
    
    def _extract_decision_factors(self, reasoning: str) -> List[str]:
        """Extract key factors from AI reasoning text"""
        # Simple extraction - look for common patterns
        factors = []
        
        keywords = [
            "because", "due to", "based on", "considering",
            "given that", "since", "as a result of"
        ]
        
        for keyword in keywords:
            if keyword in reasoning.lower():
                # Extract the clause following the keyword
                idx = reasoning.lower().find(keyword)
                clause = reasoning[idx:idx+100].split('.')[0]
                factors.append(clause.strip())
        
        return factors[:5]  # Limit to 5 factors
    
    def _save_recording(self, recording: MissionRecording):
        """Save recording to disk"""
        filename = f"{recording.id}.json"
        filepath = os.path.join(self.storage_path, filename)
        
        with open(filepath, 'w') as f:
            f.write(recording.model_dump_json(indent=2))
    
    def load_recording(self, recording_id: str) -> Optional[MissionRecording]:
        """Load recording from disk"""
        # Check memory first
        if recording_id in self.completed_recordings:
            return self.completed_recordings[recording_id]
        
        # Try loading from disk
        filename = f"{recording_id}.json"
        filepath = os.path.join(self.storage_path, filename)
        
        if os.path.exists(filepath):
            with open(filepath, 'r') as f:
                data = json.load(f)
                recording = MissionRecording(**data)
                self.completed_recordings[recording_id] = recording
                return recording
        
        return None
    
    def list_recordings(self) -> List[Dict[str, Any]]:
        """List all available recordings"""
        recordings = []
        
        # From memory
        for rec in self.completed_recordings.values():
            recordings.append({
                "id": rec.id,
                "name": rec.name,
                "start_time": rec.start_time.isoformat(),
                "duration_seconds": rec.duration_seconds,
                "event_count": len(rec.events)
            })
        
        # From disk
        for filename in os.listdir(self.storage_path):
            if filename.endswith('.json'):
                rec_id = filename[:-5]
                if rec_id not in self.completed_recordings:
                    filepath = os.path.join(self.storage_path, filename)
                    with open(filepath, 'r') as f:
                        data = json.load(f)
                        recordings.append({
                            "id": data.get("id"),
                            "name": data.get("name"),
                            "start_time": data.get("start_time"),
                            "duration_seconds": data.get("duration_seconds", 0),
                            "event_count": len(data.get("events", []))
                        })
        
        return recordings

class MissionReplay:
    """Replays recorded missions with analysis"""
    
    def __init__(self, recording: MissionRecording):
        self.recording = recording
        self.current_index = 0
        self.playback_speed = 1.0
        self.is_playing = False
    
    def get_event_at_time(self, relative_time_ms: int) -> List[MissionEvent]:
        """Get all events at or before a specific time"""
        return [
            e for e in self.recording.events
            if e.relative_time_ms <= relative_time_ms
        ]
    
    def get_events_in_range(
        self, 
        start_ms: int, 
        end_ms: int
    ) -> List[MissionEvent]:
        """Get events within a time range"""
        return [
            e for e in self.recording.events
            if start_ms <= e.relative_time_ms <= end_ms
        ]
    
    def get_ai_decisions(self) -> List[MissionEvent]:
        """Get all AI decision events"""
        return [
            e for e in self.recording.events
            if e.event_type in [EventType.AI_DECISION, EventType.AI_RECOMMENDATION]
        ]
    
    def get_operator_actions(self) -> List[MissionEvent]:
        """Get all operator action events"""
        return [
            e for e in self.recording.events
            if e.event_type in [
                EventType.OPERATOR_ACTION,
                EventType.OPERATOR_OVERRIDE,
                EventType.OPERATOR_COMMAND
            ]
        ]
    
    def analyze_decision(self, event_id: str) -> Dict[str, Any]:
        """Deep analysis of a specific AI decision"""
        event = next(
            (e for e in self.recording.events if e.id == event_id),
            None
        )
        
        if not event:
            return {"error": "Event not found"}
        
        # Find surrounding context
        event_idx = self.recording.events.index(event)
        context_before = self.recording.events[max(0, event_idx-5):event_idx]
        context_after = self.recording.events[event_idx+1:event_idx+6]
        
        # Find if there was an override
        was_overridden = any(
            e.event_type == EventType.OPERATOR_OVERRIDE and
            e.relative_time_ms > event.relative_time_ms and
            e.relative_time_ms < event.relative_time_ms + 30000
            for e in context_after
        )
        
        return {
            "event": event.model_dump(),
            "context_before": [e.model_dump() for e in context_before],
            "context_after": [e.model_dump() for e in context_after],
            "was_overridden": was_overridden,
            "confidence": event.ai_confidence,
            "reasoning": event.ai_reasoning,
            "factors": event.data.get("explainability", {}).get("factors", [])
        }
    
    def generate_after_action_report(self) -> Dict[str, Any]:
        """Generate comprehensive after-action report"""
        return {
            "mission_id": self.recording.id,
            "mission_name": self.recording.name,
            "duration": self.recording.duration_seconds,
            "summary": {
                "total_events": len(self.recording.events),
                "detections": self.recording.total_detections,
                "ai_recommendations": self.recording.ai_recommendations,
                "operator_overrides": self.recording.operator_overrides,
                "override_rate": (
                    self.recording.operator_overrides / max(1, self.recording.ai_recommendations)
                )
            },
            "performance": {
                "average_trust": self.recording.average_trust_score,
                "average_cognitive_load": self.recording.average_cognitive_load,
                "trust_trend": self._calculate_trend("trust"),
                "cognitive_load_trend": self._calculate_trend("cognitive_load")
            },
            "key_moments": self.recording.key_moments,
            "lessons_learned": self.recording.lessons_learned,
            "recommendations": self._generate_recommendations()
        }
    
    def _calculate_trend(self, metric_type: str) -> str:
        """Calculate trend for a metric over the mission"""
        if metric_type == "trust":
            events = [
                e for e in self.recording.events
                if e.event_type == EventType.TRUST_UPDATE
            ]
            values = [e.data.get("trust_score", 0.5) for e in events]
        else:
            events = [
                e for e in self.recording.events
                if e.event_type == EventType.COGNITIVE_LOAD
            ]
            values = [e.data.get("load", 0.5) for e in events]
        
        if len(values) < 2:
            return "insufficient_data"
        
        first_half = sum(values[:len(values)//2]) / (len(values)//2)
        second_half = sum(values[len(values)//2:]) / (len(values) - len(values)//2)
        
        if second_half > first_half + 0.1:
            return "increasing"
        elif second_half < first_half - 0.1:
            return "decreasing"
        return "stable"
    
    def _generate_recommendations(self) -> List[str]:
        """Generate recommendations based on mission analysis"""
        recommendations = []
        
        # High override rate
        if self.recording.ai_recommendations > 0:
            override_rate = self.recording.operator_overrides / self.recording.ai_recommendations
            if override_rate > 0.3:
                recommendations.append(
                    f"High override rate ({override_rate:.0%}) - review AI calibration settings"
                )
        
        # High cognitive load
        if self.recording.average_cognitive_load > 0.7:
            recommendations.append(
                "Average cognitive load was high - consider task automation or workload distribution"
            )
        
        # Low trust
        if self.recording.average_trust_score < 0.4:
            recommendations.append(
                "Trust scores were low - review AI explanation quality and accuracy"
            )
        
        # Key moment patterns
        override_moments = [
            km for km in self.recording.key_moments
            if "override" in km.get("reason", "").lower()
        ]
        if len(override_moments) > 3:
            recommendations.append(
                f"{len(override_moments)} override events - analyze common patterns"
            )
        
        return recommendations

# Global recorder instance
mission_recorder = MissionRecorder()
