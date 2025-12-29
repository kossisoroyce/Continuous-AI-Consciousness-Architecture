"""
Workload-Aware Interaction System

Detects operator cognitive load and adapts AI interaction style accordingly.
"""

from dataclasses import dataclass, field
from typing import Dict, List, Optional, Tuple
from datetime import datetime, timedelta
from enum import Enum
import statistics


class InteractionMode(Enum):
    """AI interaction modes based on operator workload."""
    PROACTIVE = "proactive"    # AI can initiate, provide details
    RESPONSIVE = "responsive"  # AI responds when asked, moderate detail
    MINIMAL = "minimal"        # Brief responses only, no unsolicited info


@dataclass
class WorkloadSignals:
    """Raw signals used to estimate workload."""
    response_latency_ms: float = 0.0
    message_length: int = 0
    typo_count: int = 0
    correction_count: int = 0
    timestamp: datetime = field(default_factory=datetime.now)
    
    def to_dict(self) -> Dict:
        return {
            'response_latency_ms': self.response_latency_ms,
            'message_length': self.message_length,
            'typo_count': self.typo_count,
            'correction_count': self.correction_count,
            'timestamp': self.timestamp.isoformat()
        }


@dataclass
class WorkloadEstimate:
    """Estimated operator cognitive workload."""
    level: float  # 0.0 (idle) to 1.0 (overloaded)
    
    # Component scores
    latency_score: float = 0.0
    brevity_score: float = 0.0
    error_score: float = 0.0
    fatigue_score: float = 0.0
    
    # Derived
    confidence: float = 0.5  # Confidence in estimate
    timestamp: datetime = field(default_factory=datetime.now)
    
    @property
    def interaction_mode(self) -> InteractionMode:
        """Recommended interaction mode based on workload."""
        if self.level < 0.3:
            return InteractionMode.PROACTIVE
        elif self.level < 0.7:
            return InteractionMode.RESPONSIVE
        else:
            return InteractionMode.MINIMAL
    
    @property
    def recommended_response_length(self) -> str:
        """Recommended response length category."""
        if self.level < 0.3:
            return "detailed"
        elif self.level < 0.5:
            return "standard"
        elif self.level < 0.7:
            return "brief"
        else:
            return "minimal"
    
    @property
    def should_include_proactive_info(self) -> bool:
        """Whether to include unsolicited helpful information."""
        return self.level < 0.4
    
    @property
    def should_ask_clarifying_questions(self) -> bool:
        """Whether it's appropriate to ask clarifying questions."""
        return self.level < 0.6
    
    def to_dict(self) -> Dict:
        return {
            'level': self.level,
            'latency_score': self.latency_score,
            'brevity_score': self.brevity_score,
            'error_score': self.error_score,
            'fatigue_score': self.fatigue_score,
            'confidence': self.confidence,
            'interaction_mode': self.interaction_mode.value,
            'recommended_response_length': self.recommended_response_length,
            'timestamp': self.timestamp.isoformat()
        }


@dataclass
class ResponseConfig:
    """Configuration for AI response based on workload."""
    max_length: int
    include_explanation: bool
    include_proactive_info: bool
    ask_clarifying_questions: bool
    verbosity: str  # "minimal", "brief", "standard", "detailed"
    
    @classmethod
    def from_workload(cls, workload: WorkloadEstimate) -> 'ResponseConfig':
        """Create response config from workload estimate."""
        if workload.level < 0.3:
            return cls(
                max_length=800,
                include_explanation=True,
                include_proactive_info=True,
                ask_clarifying_questions=True,
                verbosity="detailed"
            )
        elif workload.level < 0.5:
            return cls(
                max_length=400,
                include_explanation=True,
                include_proactive_info=True,
                ask_clarifying_questions=True,
                verbosity="standard"
            )
        elif workload.level < 0.7:
            return cls(
                max_length=200,
                include_explanation=False,
                include_proactive_info=False,
                ask_clarifying_questions=False,
                verbosity="brief"
            )
        else:
            return cls(
                max_length=100,
                include_explanation=False,
                include_proactive_info=False,
                ask_clarifying_questions=False,
                verbosity="minimal"
            )


class WorkloadTracker:
    """Tracks operator workload signals over time."""
    
    def __init__(
        self,
        window_seconds: float = 300.0,
        latency_baseline_ms: float = 3000.0,
        length_baseline: int = 50
    ):
        self.window_seconds = window_seconds
        self.latency_baseline_ms = latency_baseline_ms
        self.length_baseline = length_baseline
        
        # Signal history
        self.signals: List[WorkloadSignals] = []
        self.session_start: datetime = datetime.now()
        self.last_ai_message_time: Optional[datetime] = None
        
        # Adaptive baselines
        self.observed_latencies: List[float] = []
        self.observed_lengths: List[int] = []
    
    def record_ai_message(self, timestamp: Optional[datetime] = None):
        """Record when AI sends a message (for latency calculation)."""
        self.last_ai_message_time = timestamp or datetime.now()
    
    def record_operator_message(
        self,
        message: str,
        timestamp: Optional[datetime] = None
    ) -> WorkloadSignals:
        """Record operator message and extract workload signals."""
        timestamp = timestamp or datetime.now()
        
        # Calculate response latency
        latency_ms = 0.0
        if self.last_ai_message_time:
            latency = (timestamp - self.last_ai_message_time).total_seconds() * 1000
            latency_ms = max(0, latency)
        
        # Count potential typos (very simple heuristic)
        typo_indicators = self._count_typo_indicators(message)
        
        # Create signal record
        signals = WorkloadSignals(
            response_latency_ms=latency_ms,
            message_length=len(message),
            typo_count=typo_indicators,
            correction_count=message.lower().count('*'),  # Markdown corrections
            timestamp=timestamp
        )
        
        self.signals.append(signals)
        self.observed_latencies.append(latency_ms)
        self.observed_lengths.append(len(message))
        
        # Trim old signals
        self._trim_old_signals()
        
        return signals
    
    def _count_typo_indicators(self, message: str) -> int:
        """Count potential typo indicators (simple heuristic)."""
        count = 0
        words = message.split()
        
        for word in words:
            # Very short words with unusual characters
            if len(word) <= 2 and not word.isalpha():
                count += 1
            # Repeated characters (e.g., "helllo")
            for i in range(len(word) - 2):
                if word[i] == word[i+1] == word[i+2]:
                    count += 1
        
        return count
    
    def _trim_old_signals(self):
        """Remove signals outside the tracking window."""
        cutoff = datetime.now() - timedelta(seconds=self.window_seconds)
        self.signals = [s for s in self.signals if s.timestamp > cutoff]
        
        # Keep baselines bounded
        if len(self.observed_latencies) > 100:
            self.observed_latencies = self.observed_latencies[-100:]
        if len(self.observed_lengths) > 100:
            self.observed_lengths = self.observed_lengths[-100:]
    
    def estimate_workload(self) -> WorkloadEstimate:
        """Estimate current operator workload from recent signals."""
        if len(self.signals) < 2:
            return WorkloadEstimate(
                level=0.5,
                confidence=0.2
            )
        
        recent = self.signals[-10:]  # Last 10 messages
        
        # Calculate component scores
        latency_score = self._compute_latency_score(recent)
        brevity_score = self._compute_brevity_score(recent)
        error_score = self._compute_error_score(recent)
        fatigue_score = self._compute_fatigue_score()
        
        # Weighted combination
        level = (
            latency_score * 0.3 +
            brevity_score * 0.3 +
            error_score * 0.2 +
            fatigue_score * 0.2
        )
        
        # Confidence based on data quantity
        confidence = min(1.0, len(self.signals) / 10)
        
        return WorkloadEstimate(
            level=max(0.0, min(1.0, level)),
            latency_score=latency_score,
            brevity_score=brevity_score,
            error_score=error_score,
            fatigue_score=fatigue_score,
            confidence=confidence
        )
    
    def _compute_latency_score(self, signals: List[WorkloadSignals]) -> float:
        """Higher latency = higher workload (slower responses)."""
        if not signals:
            return 0.5
        
        latencies = [s.response_latency_ms for s in signals if s.response_latency_ms > 0]
        if not latencies:
            return 0.5
        
        avg_latency = statistics.mean(latencies)
        
        # Adaptive baseline
        baseline = self.latency_baseline_ms
        if len(self.observed_latencies) > 10:
            baseline = statistics.median(self.observed_latencies)
        
        # Score: >2x baseline = high workload
        ratio = avg_latency / max(1, baseline)
        return min(1.0, ratio / 2.0)
    
    def _compute_brevity_score(self, signals: List[WorkloadSignals]) -> float:
        """Shorter messages = higher workload."""
        if not signals:
            return 0.5
        
        lengths = [s.message_length for s in signals]
        avg_length = statistics.mean(lengths)
        
        # Adaptive baseline
        baseline = self.length_baseline
        if len(self.observed_lengths) > 10:
            baseline = statistics.median(self.observed_lengths)
        
        # Score: shorter than baseline = higher workload
        ratio = avg_length / max(1, baseline)
        # Invert: shorter = higher score
        return max(0.0, min(1.0, 1.0 - (ratio / 2.0)))
    
    def _compute_error_score(self, signals: List[WorkloadSignals]) -> float:
        """More typos/corrections = higher workload."""
        if not signals:
            return 0.0
        
        total_errors = sum(s.typo_count + s.correction_count for s in signals)
        avg_errors = total_errors / len(signals)
        
        # Score: >1 error per message = high workload indicator
        return min(1.0, avg_errors / 2.0)
    
    def _compute_fatigue_score(self) -> float:
        """Longer session = higher fatigue."""
        session_duration = (datetime.now() - self.session_start).total_seconds()
        
        # Assume fatigue increases over time
        # Full fatigue score at 4 hours
        four_hours = 4 * 60 * 60
        return min(1.0, session_duration / four_hours)
    
    def get_response_config(self) -> ResponseConfig:
        """Get recommended response configuration."""
        workload = self.estimate_workload()
        return ResponseConfig.from_workload(workload)
    
    def reset_session(self):
        """Reset for new session."""
        self.signals = []
        self.session_start = datetime.now()
        self.last_ai_message_time = None
    
    def to_dict(self) -> Dict:
        return {
            'window_seconds': self.window_seconds,
            'latency_baseline_ms': self.latency_baseline_ms,
            'length_baseline': self.length_baseline,
            'signals': [s.to_dict() for s in self.signals[-20:]],  # Last 20
            'session_start': self.session_start.isoformat(),
            'current_estimate': self.estimate_workload().to_dict()
        }
