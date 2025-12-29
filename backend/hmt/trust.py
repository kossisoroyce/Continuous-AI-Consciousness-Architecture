"""
Trust Calibration System

Tracks alignment between AI confidence and actual outcomes to enable
calibrated trust between human operators and AI systems.
"""

from dataclasses import dataclass, field
from typing import Dict, List, Optional, Tuple
from datetime import datetime
from enum import Enum
import uuid
import json


class ConfidenceBasis(Enum):
    """Factors that contribute to AI confidence."""
    HIGH_EVIDENCE = "high_evidence"
    CONSISTENT_HISTORY = "consistent_history"
    CLEAR_PATTERN = "clear_pattern"
    DOMAIN_EXPERTISE = "domain_expertise"
    RECENT_SIMILAR_SUCCESS = "recent_similar_success"


class UncertaintySource(Enum):
    """Sources of uncertainty in recommendations."""
    LIMITED_DATA = "limited_data"
    CONFLICTING_EVIDENCE = "conflicting_evidence"
    NOVEL_SITUATION = "novel_situation"
    AMBIGUOUS_CONTEXT = "ambiguous_context"
    TIME_PRESSURE = "time_pressure"
    MISSING_INFORMATION = "missing_information"


@dataclass
class ConfidenceSignal:
    """AI's self-assessed confidence in a recommendation."""
    recommendation_id: str
    confidence_score: float  # 0.0 - 1.0
    confidence_basis: List[str] = field(default_factory=list)
    uncertainty_sources: List[str] = field(default_factory=list)
    timestamp: datetime = field(default_factory=datetime.now)
    
    def to_dict(self) -> Dict:
        return {
            'recommendation_id': self.recommendation_id,
            'confidence_score': self.confidence_score,
            'confidence_basis': self.confidence_basis,
            'uncertainty_sources': self.uncertainty_sources,
            'timestamp': self.timestamp.isoformat()
        }
    
    @classmethod
    def from_dict(cls, data: Dict) -> 'ConfidenceSignal':
        return cls(
            recommendation_id=data['recommendation_id'],
            confidence_score=data['confidence_score'],
            confidence_basis=data.get('confidence_basis', []),
            uncertainty_sources=data.get('uncertainty_sources', []),
            timestamp=datetime.fromisoformat(data['timestamp']) if 'timestamp' in data else datetime.now()
        )


@dataclass
class RecommendationRecord:
    """Record of a single recommendation and its outcome."""
    id: str
    operator_id: str
    context: str
    recommendation: str
    confidence: ConfidenceSignal
    outcome: Optional[bool] = None  # True = correct, False = incorrect, None = pending
    operator_accepted: Optional[bool] = None
    feedback_notes: Optional[str] = None
    created_at: datetime = field(default_factory=datetime.now)
    resolved_at: Optional[datetime] = None
    
    def to_dict(self) -> Dict:
        return {
            'id': self.id,
            'operator_id': self.operator_id,
            'context': self.context,
            'recommendation': self.recommendation,
            'confidence': self.confidence.to_dict(),
            'outcome': self.outcome,
            'operator_accepted': self.operator_accepted,
            'feedback_notes': self.feedback_notes,
            'created_at': self.created_at.isoformat(),
            'resolved_at': self.resolved_at.isoformat() if self.resolved_at else None
        }
    
    @classmethod
    def from_dict(cls, data: Dict) -> 'RecommendationRecord':
        return cls(
            id=data['id'],
            operator_id=data['operator_id'],
            context=data['context'],
            recommendation=data['recommendation'],
            confidence=ConfidenceSignal.from_dict(data['confidence']),
            outcome=data.get('outcome'),
            operator_accepted=data.get('operator_accepted'),
            feedback_notes=data.get('feedback_notes'),
            created_at=datetime.fromisoformat(data['created_at']) if 'created_at' in data else datetime.now(),
            resolved_at=datetime.fromisoformat(data['resolved_at']) if data.get('resolved_at') else None
        )


@dataclass
class TrustCalibrationState:
    """Tracks alignment between AI confidence and actual outcomes for an operator."""
    operator_id: str
    
    # Calibration counters
    total_recommendations: int = 0
    high_confidence_correct: int = 0
    high_confidence_incorrect: int = 0
    low_confidence_correct: int = 0
    low_confidence_incorrect: int = 0
    medium_confidence_correct: int = 0
    medium_confidence_incorrect: int = 0
    
    # Acceptance tracking
    recommendations_accepted: int = 0
    recommendations_rejected: int = 0
    
    # Recent history for windowed metrics
    recent_outcomes: List[Tuple[float, bool]] = field(default_factory=list)
    
    @property
    def calibration_score(self) -> float:
        """
        How well does confidence predict correctness?
        1.0 = perfectly calibrated, 0.0 = inverse calibration
        """
        if self.total_recommendations < 5:
            return 0.5  # Insufficient data
        
        # High confidence should be mostly correct
        high_total = self.high_confidence_correct + self.high_confidence_incorrect
        high_accuracy = self.high_confidence_correct / max(1, high_total)
        
        # Low confidence should be less accurate (uncertainty is appropriate)
        low_total = self.low_confidence_correct + self.low_confidence_incorrect
        low_accuracy = self.low_confidence_correct / max(1, low_total) if low_total > 0 else 0.5
        
        # Good calibration: high confidence = high accuracy, low confidence = lower accuracy
        # The gap between high and low accuracy indicates calibration quality
        if high_total > 0 and low_total > 0:
            calibration = (high_accuracy - low_accuracy + 1) / 2
        else:
            calibration = high_accuracy if high_total > 0 else 0.5
        
        return max(0.0, min(1.0, calibration))
    
    @property
    def overall_accuracy(self) -> float:
        """Overall recommendation accuracy."""
        total_resolved = (
            self.high_confidence_correct + self.high_confidence_incorrect +
            self.medium_confidence_correct + self.medium_confidence_incorrect +
            self.low_confidence_correct + self.low_confidence_incorrect
        )
        total_correct = (
            self.high_confidence_correct + 
            self.medium_confidence_correct + 
            self.low_confidence_correct
        )
        return total_correct / max(1, total_resolved)
    
    @property
    def overtrust_risk(self) -> float:
        """Risk that operator trusts AI too much (high confidence failures)."""
        high_total = self.high_confidence_correct + self.high_confidence_incorrect
        if high_total == 0:
            return 0.0
        return self.high_confidence_incorrect / high_total
    
    @property
    def undertrust_risk(self) -> float:
        """Risk that operator doesn't trust AI enough (rejecting good recommendations)."""
        if self.total_recommendations == 0:
            return 0.0
        # Proxy: high rejection rate despite good calibration
        rejection_rate = self.recommendations_rejected / max(1, self.recommendations_accepted + self.recommendations_rejected)
        return rejection_rate * self.calibration_score
    
    @property
    def acceptance_rate(self) -> float:
        """Rate at which operator accepts recommendations."""
        total = self.recommendations_accepted + self.recommendations_rejected
        return self.recommendations_accepted / max(1, total)
    
    def to_dict(self) -> Dict:
        return {
            'operator_id': self.operator_id,
            'total_recommendations': self.total_recommendations,
            'high_confidence_correct': self.high_confidence_correct,
            'high_confidence_incorrect': self.high_confidence_incorrect,
            'low_confidence_correct': self.low_confidence_correct,
            'low_confidence_incorrect': self.low_confidence_incorrect,
            'medium_confidence_correct': self.medium_confidence_correct,
            'medium_confidence_incorrect': self.medium_confidence_incorrect,
            'recommendations_accepted': self.recommendations_accepted,
            'recommendations_rejected': self.recommendations_rejected,
            'calibration_score': self.calibration_score,
            'overall_accuracy': self.overall_accuracy,
            'overtrust_risk': self.overtrust_risk,
            'undertrust_risk': self.undertrust_risk,
            'acceptance_rate': self.acceptance_rate
        }
    
    @classmethod
    def from_dict(cls, data: Dict) -> 'TrustCalibrationState':
        state = cls(operator_id=data['operator_id'])
        state.total_recommendations = data.get('total_recommendations', 0)
        state.high_confidence_correct = data.get('high_confidence_correct', 0)
        state.high_confidence_incorrect = data.get('high_confidence_incorrect', 0)
        state.low_confidence_correct = data.get('low_confidence_correct', 0)
        state.low_confidence_incorrect = data.get('low_confidence_incorrect', 0)
        state.medium_confidence_correct = data.get('medium_confidence_correct', 0)
        state.medium_confidence_incorrect = data.get('medium_confidence_incorrect', 0)
        state.recommendations_accepted = data.get('recommendations_accepted', 0)
        state.recommendations_rejected = data.get('recommendations_rejected', 0)
        return state


class TrustCalibrationTracker:
    """Manages trust calibration across multiple operators."""
    
    def __init__(self, high_threshold: float = 0.7, low_threshold: float = 0.3):
        self.high_threshold = high_threshold
        self.low_threshold = low_threshold
        self.operator_states: Dict[str, TrustCalibrationState] = {}
        self.recommendations: Dict[str, RecommendationRecord] = {}
    
    def get_operator_state(self, operator_id: str) -> TrustCalibrationState:
        """Get or create trust state for an operator."""
        if operator_id not in self.operator_states:
            self.operator_states[operator_id] = TrustCalibrationState(operator_id=operator_id)
        return self.operator_states[operator_id]
    
    def create_recommendation(
        self,
        operator_id: str,
        context: str,
        recommendation: str,
        confidence_score: float,
        confidence_basis: List[str] = None,
        uncertainty_sources: List[str] = None
    ) -> RecommendationRecord:
        """Create a new recommendation with confidence signal."""
        rec_id = str(uuid.uuid4())[:8]
        
        confidence = ConfidenceSignal(
            recommendation_id=rec_id,
            confidence_score=confidence_score,
            confidence_basis=confidence_basis or [],
            uncertainty_sources=uncertainty_sources or []
        )
        
        record = RecommendationRecord(
            id=rec_id,
            operator_id=operator_id,
            context=context,
            recommendation=recommendation,
            confidence=confidence
        )
        
        self.recommendations[rec_id] = record
        state = self.get_operator_state(operator_id)
        state.total_recommendations += 1
        
        return record
    
    def record_acceptance(self, recommendation_id: str, accepted: bool):
        """Record whether operator accepted the recommendation."""
        if recommendation_id not in self.recommendations:
            return
        
        record = self.recommendations[recommendation_id]
        record.operator_accepted = accepted
        
        state = self.get_operator_state(record.operator_id)
        if accepted:
            state.recommendations_accepted += 1
        else:
            state.recommendations_rejected += 1
    
    def record_outcome(
        self,
        recommendation_id: str,
        was_correct: bool,
        feedback_notes: Optional[str] = None
    ) -> Optional[TrustCalibrationState]:
        """Record the actual outcome of a recommendation."""
        if recommendation_id not in self.recommendations:
            return None
        
        record = self.recommendations[recommendation_id]
        record.outcome = was_correct
        record.feedback_notes = feedback_notes
        record.resolved_at = datetime.now()
        
        state = self.get_operator_state(record.operator_id)
        confidence = record.confidence.confidence_score
        
        # Categorize by confidence level
        if confidence >= self.high_threshold:
            if was_correct:
                state.high_confidence_correct += 1
            else:
                state.high_confidence_incorrect += 1
        elif confidence <= self.low_threshold:
            if was_correct:
                state.low_confidence_correct += 1
            else:
                state.low_confidence_incorrect += 1
        else:
            if was_correct:
                state.medium_confidence_correct += 1
            else:
                state.medium_confidence_incorrect += 1
        
        # Track in recent outcomes
        state.recent_outcomes.append((confidence, was_correct))
        if len(state.recent_outcomes) > 50:
            state.recent_outcomes = state.recent_outcomes[-50:]
        
        return state
    
    def get_recommendation(self, recommendation_id: str) -> Optional[RecommendationRecord]:
        """Get a recommendation by ID."""
        return self.recommendations.get(recommendation_id)
    
    def get_pending_recommendations(self, operator_id: str) -> List[RecommendationRecord]:
        """Get all pending (unresolved) recommendations for an operator."""
        return [
            rec for rec in self.recommendations.values()
            if rec.operator_id == operator_id and rec.outcome is None
        ]
    
    def compute_recommended_confidence_adjustment(self, operator_id: str) -> float:
        """
        Suggest how AI should adjust confidence based on calibration history.
        Positive = AI should be more confident, Negative = less confident.
        """
        state = self.get_operator_state(operator_id)
        
        if state.total_recommendations < 10:
            return 0.0  # Not enough data
        
        # If overtrust risk is high, AI should be less confident
        if state.overtrust_risk > 0.3:
            return -0.1 * state.overtrust_risk
        
        # If undertrust is high and accuracy is good, AI could be more confident
        if state.undertrust_risk > 0.2 and state.overall_accuracy > 0.7:
            return 0.05
        
        return 0.0
    
    def to_dict(self) -> Dict:
        return {
            'high_threshold': self.high_threshold,
            'low_threshold': self.low_threshold,
            'operator_states': {k: v.to_dict() for k, v in self.operator_states.items()},
            'recommendations': {k: v.to_dict() for k, v in self.recommendations.items()}
        }
    
    @classmethod
    def from_dict(cls, data: Dict) -> 'TrustCalibrationTracker':
        tracker = cls(
            high_threshold=data.get('high_threshold', 0.7),
            low_threshold=data.get('low_threshold', 0.3)
        )
        tracker.operator_states = {
            k: TrustCalibrationState.from_dict(v) 
            for k, v in data.get('operator_states', {}).items()
        }
        tracker.recommendations = {
            k: RecommendationRecord.from_dict(v)
            for k, v in data.get('recommendations', {}).items()
        }
        return tracker
