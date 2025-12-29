"""
SQLAlchemy models for brain persistence.
"""

from datetime import datetime
from typing import Optional
from sqlalchemy import Column, String, Float, Integer, DateTime, Text, ForeignKey, JSON, Boolean, Index
from sqlalchemy.orm import relationship, declarative_base

Base = declarative_base()


class Brain(Base):
    """
    Core brain entity - represents a persistent AI partner instance.
    Contains nurture state, experience state, and HMT metrics.
    """
    __tablename__ = "brains"
    
    id = Column(String(64), primary_key=True)
    name = Column(String(128), nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow, nullable=False)
    
    # Status
    status = Column(String(32), default="active")  # active, suspended, archived
    
    # Nurture Layer State (serialized JSON)
    nurture_state = Column(JSON, nullable=True)
    
    # Experience Layer State (serialized JSON) 
    experience_state = Column(JSON, nullable=True)
    
    # HMT State (serialized JSON)
    hmt_state = Column(JSON, nullable=True)
    
    # Core metrics (denormalized for quick access)
    stability = Column(Float, default=0.5)
    plasticity = Column(Float, default=0.5)
    phase = Column(String(32), default="formation")
    interaction_count = Column(Integer, default=0)
    
    # Trust metrics
    trust_calibration = Column(Float, default=0.5)
    overtrust_risk = Column(Float, default=0.0)
    undertrust_risk = Column(Float, default=0.0)
    
    # Relationships
    snapshots = relationship("BrainSnapshot", back_populates="brain", cascade="all, delete-orphan")
    events = relationship("BrainEvent", back_populates="brain", cascade="all, delete-orphan")
    sessions = relationship("SessionLog", back_populates="brain", cascade="all, delete-orphan")
    
    __table_args__ = (
        Index('idx_brain_status', 'status'),
        Index('idx_brain_updated', 'updated_at'),
    )


class BrainSnapshot(Base):
    """
    Point-in-time snapshot of brain state for recovery.
    Created periodically and before major operations.
    """
    __tablename__ = "brain_snapshots"
    
    id = Column(Integer, primary_key=True, autoincrement=True)
    brain_id = Column(String(64), ForeignKey("brains.id", ondelete="CASCADE"), nullable=False)
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    
    # Snapshot type
    snapshot_type = Column(String(32), default="auto")  # auto, manual, pre_operation
    description = Column(String(256), nullable=True)
    
    # Full state at snapshot time
    nurture_state = Column(JSON, nullable=False)
    experience_state = Column(JSON, nullable=False)
    hmt_state = Column(JSON, nullable=True)
    
    # Metrics at snapshot
    stability = Column(Float)
    plasticity = Column(Float)
    phase = Column(String(32))
    
    # Relationship
    brain = relationship("Brain", back_populates="snapshots")
    
    __table_args__ = (
        Index('idx_snapshot_brain', 'brain_id'),
        Index('idx_snapshot_created', 'created_at'),
    )


class BrainEvent(Base):
    """
    Audit log of significant brain events.
    """
    __tablename__ = "brain_events"
    
    id = Column(Integer, primary_key=True, autoincrement=True)
    brain_id = Column(String(64), ForeignKey("brains.id", ondelete="CASCADE"), nullable=False)
    timestamp = Column(DateTime, default=datetime.utcnow, nullable=False)
    
    # Event info
    event_type = Column(String(64), nullable=False)  # interaction, phase_change, backup, restore, etc
    severity = Column(String(16), default="info")  # info, warning, error, critical
    description = Column(Text, nullable=True)
    
    # Event data
    data = Column(JSON, nullable=True)
    
    # Metrics delta
    stability_delta = Column(Float, nullable=True)
    plasticity_delta = Column(Float, nullable=True)
    
    # Relationship
    brain = relationship("Brain", back_populates="events")
    
    __table_args__ = (
        Index('idx_event_brain', 'brain_id'),
        Index('idx_event_timestamp', 'timestamp'),
        Index('idx_event_type', 'event_type'),
    )


class SessionLog(Base):
    """
    Log of operator sessions with the brain.
    """
    __tablename__ = "session_logs"
    
    id = Column(String(64), primary_key=True)
    brain_id = Column(String(64), ForeignKey("brains.id", ondelete="CASCADE"), nullable=False)
    operator_id = Column(String(64), default="default")
    
    started_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    ended_at = Column(DateTime, nullable=True)
    
    # Session stats
    message_count = Column(Integer, default=0)
    thought_count = Column(Integer, default=0)
    
    # HMT metrics for session
    avg_workload = Column(Float, nullable=True)
    trust_delta = Column(Float, nullable=True)
    misalignment_count = Column(Integer, default=0)
    
    # Relationship
    brain = relationship("Brain", back_populates="sessions")
    
    __table_args__ = (
        Index('idx_session_brain', 'brain_id'),
        Index('idx_session_operator', 'operator_id'),
    )
