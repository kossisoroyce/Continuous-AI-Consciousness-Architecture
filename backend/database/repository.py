"""
Brain repository - CRUD operations with reliability features.
"""

from datetime import datetime, timedelta
from typing import Optional, List, Dict, Any
from sqlalchemy.orm import Session
from sqlalchemy import desc

from .models import Brain, BrainSnapshot, BrainEvent, SessionLog


class BrainRepository:
    """Repository for brain operations with automatic snapshots and event logging."""
    
    def __init__(self, db: Session):
        self.db = db
        self.snapshot_interval = timedelta(hours=1)
        self.max_snapshots_per_brain = 24  # Keep last 24 snapshots
    
    # ========== BRAIN CRUD ==========
    
    def create(self, brain_id: str, name: str = None) -> Brain:
        """Create a new brain."""
        brain = Brain(
            id=brain_id,
            name=name or f"Brain-{brain_id[:8]}",
            nurture_state={},
            experience_state={},
            hmt_state={}
        )
        self.db.add(brain)
        self.db.commit()
        self.db.refresh(brain)
        
        self._log_event(brain_id, "created", "Brain initialized")
        return brain
    
    def get(self, brain_id: str) -> Optional[Brain]:
        """Get brain by ID."""
        return self.db.query(Brain).filter(Brain.id == brain_id).first()
    
    def get_all(self, status: str = None) -> List[Brain]:
        """Get all brains, optionally filtered by status."""
        query = self.db.query(Brain)
        if status:
            query = query.filter(Brain.status == status)
        return query.order_by(desc(Brain.updated_at)).all()
    
    def update_state(
        self, 
        brain_id: str, 
        nurture_state: Dict = None,
        experience_state: Dict = None,
        hmt_state: Dict = None,
        create_snapshot: bool = False
    ) -> Optional[Brain]:
        """Update brain state with optional snapshot."""
        brain = self.get(brain_id)
        if not brain:
            return None
        
        # Create snapshot if needed
        if create_snapshot or self._should_auto_snapshot(brain):
            self._create_snapshot(brain, "auto", "Periodic auto-snapshot")
        
        # Update states
        if nurture_state is not None:
            old_stability = brain.stability
            old_plasticity = brain.plasticity
            
            brain.nurture_state = nurture_state
            brain.stability = nurture_state.get("stability", brain.stability)
            brain.plasticity = nurture_state.get("plasticity", brain.plasticity)
            brain.phase = nurture_state.get("phase", brain.phase)
            
            # Log significant changes
            if abs(brain.stability - old_stability) > 0.1:
                self._log_event(
                    brain_id, "stability_shift", 
                    f"Stability: {old_stability:.2f} → {brain.stability:.2f}",
                    stability_delta=brain.stability - old_stability
                )
        
        if experience_state is not None:
            brain.experience_state = experience_state
            brain.interaction_count = experience_state.get("interaction_count", brain.interaction_count)
        
        if hmt_state is not None:
            brain.hmt_state = hmt_state
            if "trust" in hmt_state:
                brain.trust_calibration = hmt_state["trust"].get("calibration_score", brain.trust_calibration)
                brain.overtrust_risk = hmt_state["trust"].get("overtrust_risk", brain.overtrust_risk)
                brain.undertrust_risk = hmt_state["trust"].get("undertrust_risk", brain.undertrust_risk)
        
        brain.updated_at = datetime.utcnow()
        self.db.commit()
        self.db.refresh(brain)
        return brain
    
    def delete(self, brain_id: str) -> bool:
        """Delete brain (cascades to snapshots and events)."""
        brain = self.get(brain_id)
        if not brain:
            return False
        
        self.db.delete(brain)
        self.db.commit()
        return True
    
    def archive(self, brain_id: str) -> Optional[Brain]:
        """Archive brain instead of deleting."""
        brain = self.get(brain_id)
        if not brain:
            return None
        
        self._create_snapshot(brain, "pre_archive", "Snapshot before archiving")
        brain.status = "archived"
        self.db.commit()
        self._log_event(brain_id, "archived", "Brain archived")
        return brain
    
    # ========== SNAPSHOTS ==========
    
    def create_snapshot(self, brain_id: str, description: str = None) -> Optional[BrainSnapshot]:
        """Create a manual snapshot."""
        brain = self.get(brain_id)
        if not brain:
            return None
        return self._create_snapshot(brain, "manual", description)
    
    def get_snapshots(self, brain_id: str, limit: int = 10) -> List[BrainSnapshot]:
        """Get recent snapshots for a brain."""
        return (
            self.db.query(BrainSnapshot)
            .filter(BrainSnapshot.brain_id == brain_id)
            .order_by(desc(BrainSnapshot.created_at))
            .limit(limit)
            .all()
        )
    
    def restore_snapshot(self, snapshot_id: int) -> Optional[Brain]:
        """Restore brain to a previous snapshot."""
        snapshot = self.db.query(BrainSnapshot).filter(BrainSnapshot.id == snapshot_id).first()
        if not snapshot:
            return None
        
        brain = self.get(snapshot.brain_id)
        if not brain:
            return None
        
        # Create pre-restore snapshot
        self._create_snapshot(brain, "pre_restore", f"Before restoring to snapshot {snapshot_id}")
        
        # Restore state
        brain.nurture_state = snapshot.nurture_state
        brain.experience_state = snapshot.experience_state
        brain.hmt_state = snapshot.hmt_state
        brain.stability = snapshot.stability
        brain.plasticity = snapshot.plasticity
        brain.phase = snapshot.phase
        brain.updated_at = datetime.utcnow()
        
        self.db.commit()
        self._log_event(brain.id, "restored", f"Restored to snapshot from {snapshot.created_at}", severity="warning")
        return brain
    
    def _create_snapshot(self, brain: Brain, snapshot_type: str, description: str = None) -> BrainSnapshot:
        """Internal snapshot creation."""
        snapshot = BrainSnapshot(
            brain_id=brain.id,
            snapshot_type=snapshot_type,
            description=description,
            nurture_state=brain.nurture_state or {},
            experience_state=brain.experience_state or {},
            hmt_state=brain.hmt_state,
            stability=brain.stability,
            plasticity=brain.plasticity,
            phase=brain.phase
        )
        self.db.add(snapshot)
        self.db.commit()
        
        # Cleanup old snapshots
        self._cleanup_old_snapshots(brain.id)
        
        return snapshot
    
    def _should_auto_snapshot(self, brain: Brain) -> bool:
        """Check if auto-snapshot is needed."""
        last_snapshot = (
            self.db.query(BrainSnapshot)
            .filter(BrainSnapshot.brain_id == brain.id)
            .order_by(desc(BrainSnapshot.created_at))
            .first()
        )
        if not last_snapshot:
            return True
        return datetime.utcnow() - last_snapshot.created_at > self.snapshot_interval
    
    def _cleanup_old_snapshots(self, brain_id: str):
        """Remove old auto-snapshots beyond limit."""
        snapshots = (
            self.db.query(BrainSnapshot)
            .filter(BrainSnapshot.brain_id == brain_id, BrainSnapshot.snapshot_type == "auto")
            .order_by(desc(BrainSnapshot.created_at))
            .offset(self.max_snapshots_per_brain)
            .all()
        )
        for s in snapshots:
            self.db.delete(s)
        self.db.commit()
    
    # ========== EVENTS ==========
    
    def get_events(self, brain_id: str, limit: int = 50, event_type: str = None) -> List[BrainEvent]:
        """Get recent events for a brain."""
        query = self.db.query(BrainEvent).filter(BrainEvent.brain_id == brain_id)
        if event_type:
            query = query.filter(BrainEvent.event_type == event_type)
        return query.order_by(desc(BrainEvent.timestamp)).limit(limit).all()
    
    def _log_event(
        self, 
        brain_id: str, 
        event_type: str, 
        description: str = None,
        severity: str = "info",
        data: Dict = None,
        stability_delta: float = None,
        plasticity_delta: float = None
    ):
        """Internal event logging."""
        event = BrainEvent(
            brain_id=brain_id,
            event_type=event_type,
            severity=severity,
            description=description,
            data=data,
            stability_delta=stability_delta,
            plasticity_delta=plasticity_delta
        )
        self.db.add(event)
        self.db.commit()
    
    # ========== SESSIONS ==========
    
    def start_session(self, session_id: str, brain_id: str, operator_id: str = "default") -> SessionLog:
        """Start a new session."""
        session = SessionLog(
            id=session_id,
            brain_id=brain_id,
            operator_id=operator_id
        )
        self.db.add(session)
        self.db.commit()
        self._log_event(brain_id, "session_start", f"Session started: {session_id}")
        return session
    
    def end_session(self, session_id: str, stats: Dict = None) -> Optional[SessionLog]:
        """End a session with stats."""
        session = self.db.query(SessionLog).filter(SessionLog.id == session_id).first()
        if not session:
            return None
        
        session.ended_at = datetime.utcnow()
        if stats:
            session.message_count = stats.get("message_count", session.message_count)
            session.thought_count = stats.get("thought_count", session.thought_count)
            session.avg_workload = stats.get("avg_workload")
            session.trust_delta = stats.get("trust_delta")
            session.misalignment_count = stats.get("misalignment_count", 0)
        
        self.db.commit()
        self._log_event(session.brain_id, "session_end", f"Session ended: {session_id}")
        return session
    
    def get_sessions(self, brain_id: str, limit: int = 20) -> List[SessionLog]:
        """Get recent sessions for a brain."""
        return (
            self.db.query(SessionLog)
            .filter(SessionLog.brain_id == brain_id)
            .order_by(desc(SessionLog.started_at))
            .limit(limit)
            .all()
        )
