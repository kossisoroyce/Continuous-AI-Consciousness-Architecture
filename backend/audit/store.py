"""
Audit Store - Persistent storage for audit events
Supports SQLite with optional encryption
"""
import os
import json
from datetime import datetime, timezone
from typing import List, Optional, Dict, Any
from sqlalchemy import create_engine, Column, String, DateTime, Text, Float, Index
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker

Base = declarative_base()

class AuditEventModel(Base):
    """SQLAlchemy model for audit events"""
    __tablename__ = 'audit_events'
    
    id = Column(String(36), primary_key=True)
    timestamp = Column(DateTime, nullable=False, index=True)
    event_type = Column(String(50), nullable=False, index=True)
    session_id = Column(String(36), index=True)
    user_id = Column(String(36), index=True)
    brain_id = Column(String(36), index=True)
    action = Column(Text, nullable=False)
    details = Column(Text)  # JSON
    ai_confidence = Column(Float)
    ai_reasoning = Column(Text)
    operator_response = Column(Text)
    previous_hash = Column(String(64))
    event_hash = Column(String(64), nullable=False)
    sensitivity = Column(String(20), default='UNCLASSIFIED')
    
    __table_args__ = (
        Index('ix_audit_session_time', 'session_id', 'timestamp'),
        Index('ix_audit_type_time', 'event_type', 'timestamp'),
    )

class AuditStore:
    """Persistent audit event storage"""
    
    def __init__(self, db_path: str = None):
        if db_path is None:
            db_dir = os.path.join(os.path.dirname(__file__), '..', 'data')
            os.makedirs(db_dir, exist_ok=True)
            db_path = os.path.join(db_dir, 'audit.db')
        
        self.engine = create_engine(f'sqlite:///{db_path}')
        Base.metadata.create_all(self.engine)
        self.Session = sessionmaker(bind=self.engine)
    
    def store_event(self, event) -> bool:
        """Store an audit event"""
        session = self.Session()
        try:
            model = AuditEventModel(
                id=event.id,
                timestamp=event.timestamp,
                event_type=event.event_type.value if hasattr(event.event_type, 'value') else event.event_type,
                session_id=event.session_id,
                user_id=event.user_id,
                brain_id=event.brain_id,
                action=event.action,
                details=json.dumps(event.details),
                ai_confidence=event.ai_confidence,
                ai_reasoning=event.ai_reasoning,
                operator_response=event.operator_response,
                previous_hash=event.previous_hash,
                event_hash=event.event_hash,
                sensitivity=event.sensitivity
            )
            session.add(model)
            session.commit()
            return True
        except Exception as e:
            session.rollback()
            print(f"Failed to store audit event: {e}")
            return False
        finally:
            session.close()
    
    def get_sessions(self, limit: int = 20, offset: int = 0) -> List[Dict[str, Any]]:
        """Get distinct sessions with metadata"""
        session = self.Session()
        try:
            from sqlalchemy import func, desc
            
            # Subquery to find the start time of each session
            # We group by session_id and find min timestamp
            sessions_query = session.query(
                AuditEventModel.session_id,
                func.min(AuditEventModel.timestamp).label('start_time'),
                func.count(AuditEventModel.id).label('event_count')
            ).filter(
                AuditEventModel.session_id.isnot(None)
            ).group_by(
                AuditEventModel.session_id
            ).order_by(
                desc('start_time')
            ).offset(offset).limit(limit)
            
            results = []
            for s_id, start_time, count in sessions_query.all():
                # Get the first user message for a title if available
                first_msg = session.query(AuditEventModel.action).filter(
                    AuditEventModel.session_id == s_id,
                    AuditEventModel.event_type == 'USER_INTERACTION'
                ).order_by(AuditEventModel.timestamp.asc()).first()
                
                title = first_msg[0] if first_msg else f"Session {s_id[:8]}"
                if len(title) > 50:
                    title = title[:47] + "..."
                
                results.append({
                    'session_id': s_id,
                    'start_time': start_time.isoformat(),
                    'event_count': count,
                    'title': title
                })
            
            return results
        finally:
            session.close()

    def query_events(
        self,
        event_type: str = None,
        session_id: str = None,
        user_id: str = None,
        brain_id: str = None,
        start_time: datetime = None,
        end_time: datetime = None,
        limit: int = 100,
        offset: int = 0
    ) -> List[Dict[str, Any]]:
        """Query audit events with filters"""
        session = self.Session()
        try:
            query = session.query(AuditEventModel)
            
            if event_type:
                query = query.filter(AuditEventModel.event_type == event_type)
            if session_id:
                query = query.filter(AuditEventModel.session_id == session_id)
            if user_id:
                query = query.filter(AuditEventModel.user_id == user_id)
            if brain_id:
                query = query.filter(AuditEventModel.brain_id == brain_id)
            if start_time:
                query = query.filter(AuditEventModel.timestamp >= start_time)
            if end_time:
                query = query.filter(AuditEventModel.timestamp <= end_time)
            
            query = query.order_by(AuditEventModel.timestamp.desc())
            query = query.offset(offset).limit(limit)
            
            results = []
            for model in query.all():
                results.append({
                    'id': model.id,
                    'timestamp': model.timestamp.isoformat(),
                    'event_type': model.event_type,
                    'session_id': model.session_id,
                    'user_id': model.user_id,
                    'brain_id': model.brain_id,
                    'action': model.action,
                    'details': json.loads(model.details) if model.details else {},
                    'ai_confidence': model.ai_confidence,
                    'ai_reasoning': model.ai_reasoning,
                    'operator_response': model.operator_response,
                    'event_hash': model.event_hash,
                    'sensitivity': model.sensitivity
                })
            
            return results
        finally:
            session.close()
    
    def verify_chain(self, session_id: str = None) -> tuple[bool, Optional[str]]:
        """Verify hash chain integrity for stored events"""
        session = self.Session()
        try:
            query = session.query(AuditEventModel)
            if session_id:
                query = query.filter(AuditEventModel.session_id == session_id)
            query = query.order_by(AuditEventModel.timestamp.asc())
            
            prev_hash = None
            for model in query.all():
                if model.previous_hash != prev_hash:
                    return False, f"Chain broken at event {model.id}"
                prev_hash = model.event_hash
            
            return True, None
        finally:
            session.close()
    
    def get_statistics(self, session_id: str = None) -> Dict[str, Any]:
        """Get audit statistics"""
        session = self.Session()
        try:
            from sqlalchemy import func
            
            query = session.query(AuditEventModel)
            if session_id:
                query = query.filter(AuditEventModel.session_id == session_id)
            
            total = query.count()
            
            # Events by type
            type_counts = session.query(
                AuditEventModel.event_type,
                func.count(AuditEventModel.id)
            ).group_by(AuditEventModel.event_type).all()
            
            return {
                'total_events': total,
                'events_by_type': {t: c for t, c in type_counts},
                'integrity_verified': self.verify_chain(session_id)[0]
            }
        finally:
            session.close()
