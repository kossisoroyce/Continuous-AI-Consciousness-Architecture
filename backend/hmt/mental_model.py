"""
Shared Mental Model Tracking System

Tracks alignment between what the operator believes about AI state
and the AI's actual state. Detects and repairs misalignments.
"""

from dataclasses import dataclass, field
from typing import Dict, List, Set, Optional, Any, Tuple
from datetime import datetime
from enum import Enum
import re


class MisalignmentType(Enum):
    """Types of mental model misalignment."""
    FALSE_BELIEF = "false_belief"           # Operator thinks AI knows something it doesn't
    UNKNOWN_KNOWLEDGE = "unknown_knowledge"  # AI knows something operator doesn't realize
    GOAL_MISMATCH = "goal_mismatch"          # Different understanding of priorities
    CAPABILITY_OVERESTIMATE = "capability_overestimate"
    CAPABILITY_UNDERESTIMATE = "capability_underestimate"
    STALE_BELIEF = "stale_belief"           # Operator's model is outdated


class AlertSeverity(Enum):
    """Severity of misalignment alerts."""
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"
    CRITICAL = "critical"


@dataclass
class BeliefRecord:
    """Record of an inferred operator belief."""
    content: str
    source: str  # How we inferred this belief
    confidence: float  # Our confidence in this inference
    created_at: datetime = field(default_factory=datetime.now)
    last_reinforced: datetime = field(default_factory=datetime.now)
    reinforcement_count: int = 1
    
    def to_dict(self) -> Dict:
        return {
            'content': self.content,
            'source': self.source,
            'confidence': self.confidence,
            'created_at': self.created_at.isoformat(),
            'last_reinforced': self.last_reinforced.isoformat(),
            'reinforcement_count': self.reinforcement_count
        }


@dataclass
class AIStateProjection:
    """What the operator likely believes about AI state."""
    operator_id: str
    
    # Beliefs about AI knowledge
    known_facts: Dict[str, BeliefRecord] = field(default_factory=dict)
    assumed_capabilities: Set[str] = field(default_factory=set)
    assumed_limitations: Set[str] = field(default_factory=set)
    
    # Beliefs about AI goals/priorities
    understood_goals: List[str] = field(default_factory=list)
    perceived_priorities: Dict[str, float] = field(default_factory=dict)
    
    # Trust state
    perceived_trust_level: float = 0.5
    
    # Metadata
    last_updated: datetime = field(default_factory=datetime.now)
    interaction_count: int = 0
    
    def add_belief(self, content: str, source: str, confidence: float = 0.7):
        """Add or reinforce a belief."""
        key = content.lower()[:100]  # Normalize key
        
        if key in self.known_facts:
            belief = self.known_facts[key]
            belief.last_reinforced = datetime.now()
            belief.reinforcement_count += 1
            belief.confidence = min(1.0, belief.confidence + 0.1)
        else:
            self.known_facts[key] = BeliefRecord(
                content=content,
                source=source,
                confidence=confidence
            )
        
        self.last_updated = datetime.now()
    
    def decay_beliefs(self, decay_rate: float = 0.95):
        """Decay confidence in beliefs over time."""
        for belief in self.known_facts.values():
            belief.confidence *= decay_rate
        
        # Remove very low confidence beliefs
        self.known_facts = {
            k: v for k, v in self.known_facts.items()
            if v.confidence > 0.1
        }
    
    def to_dict(self) -> Dict:
        return {
            'operator_id': self.operator_id,
            'known_facts': {k: v.to_dict() for k, v in self.known_facts.items()},
            'assumed_capabilities': list(self.assumed_capabilities),
            'assumed_limitations': list(self.assumed_limitations),
            'understood_goals': self.understood_goals,
            'perceived_priorities': self.perceived_priorities,
            'perceived_trust_level': self.perceived_trust_level,
            'last_updated': self.last_updated.isoformat(),
            'interaction_count': self.interaction_count
        }


@dataclass
class MisalignmentAlert:
    """Alert about a mental model misalignment."""
    type: MisalignmentType
    severity: AlertSeverity
    description: str
    operator_belief: Optional[str] = None
    ai_actual_state: Optional[str] = None
    suggested_repair: Optional[str] = None
    timestamp: datetime = field(default_factory=datetime.now)
    
    def to_dict(self) -> Dict:
        return {
            'type': self.type.value,
            'severity': self.severity.value,
            'description': self.description,
            'operator_belief': self.operator_belief,
            'ai_actual_state': self.ai_actual_state,
            'suggested_repair': self.suggested_repair,
            'timestamp': self.timestamp.isoformat()
        }


@dataclass
class MentalModelAlignment:
    """Measures alignment between operator's model and AI's actual state."""
    
    # Knowledge alignment
    knowledge_overlap: float = 0.5
    false_beliefs_count: int = 0
    unknown_knowledge_count: int = 0
    
    # Goal alignment
    goal_alignment: float = 0.5
    
    # Capability alignment
    capability_alignment: float = 0.5
    
    # Overall
    overall_alignment: float = 0.5
    
    @property
    def misalignment_risk(self) -> float:
        """Risk of coordination failure due to misaligned mental models."""
        return 1.0 - self.overall_alignment
    
    def to_dict(self) -> Dict:
        return {
            'knowledge_overlap': self.knowledge_overlap,
            'false_beliefs_count': self.false_beliefs_count,
            'unknown_knowledge_count': self.unknown_knowledge_count,
            'goal_alignment': self.goal_alignment,
            'capability_alignment': self.capability_alignment,
            'overall_alignment': self.overall_alignment,
            'misalignment_risk': self.misalignment_risk
        }


class MentalModelTracker:
    """Tracks and manages shared mental models between operator and AI."""
    
    def __init__(
        self,
        alignment_check_interval: int = 5,
        misalignment_threshold: float = 0.3,
        max_beliefs: int = 100
    ):
        self.alignment_check_interval = alignment_check_interval
        self.misalignment_threshold = misalignment_threshold
        self.max_beliefs = max_beliefs
        
        self.operator_projections: Dict[str, AIStateProjection] = {}
        self.interaction_counters: Dict[str, int] = {}
        self.active_alerts: List[MisalignmentAlert] = []
    
    def get_projection(self, operator_id: str) -> AIStateProjection:
        """Get or create projection for operator."""
        if operator_id not in self.operator_projections:
            self.operator_projections[operator_id] = AIStateProjection(
                operator_id=operator_id
            )
        return self.operator_projections[operator_id]
    
    def update_from_interaction(
        self,
        operator_id: str,
        user_input: str,
        ai_response: str,
        ai_actual_facts: List[str] = None,
        ai_actual_capabilities: Set[str] = None
    ) -> List[MisalignmentAlert]:
        """Update operator's mental model based on interaction."""
        projection = self.get_projection(operator_id)
        projection.interaction_count += 1
        self.interaction_counters[operator_id] = self.interaction_counters.get(operator_id, 0) + 1
        
        # Infer beliefs from user input
        inferred_beliefs = self._infer_operator_beliefs(user_input)
        for belief, source in inferred_beliefs:
            projection.add_belief(belief, source)
        
        # Update based on AI response (what we revealed)
        revealed_knowledge = self._extract_revealed_knowledge(ai_response)
        for knowledge in revealed_knowledge:
            projection.add_belief(knowledge, "ai_revealed")
        
        # Detect capability assumptions
        capability_assumptions = self._detect_capability_assumptions(user_input)
        projection.assumed_capabilities.update(capability_assumptions)
        
        # Decay old beliefs
        projection.decay_beliefs()
        
        # Trim if too many beliefs
        if len(projection.known_facts) > self.max_beliefs:
            # Keep highest confidence beliefs
            sorted_beliefs = sorted(
                projection.known_facts.items(),
                key=lambda x: x[1].confidence,
                reverse=True
            )
            projection.known_facts = dict(sorted_beliefs[:self.max_beliefs])
        
        # Check for misalignments periodically
        alerts = []
        if self.interaction_counters[operator_id] % self.alignment_check_interval == 0:
            alerts = self.detect_misalignments(
                operator_id,
                ai_actual_facts or [],
                ai_actual_capabilities or set()
            )
            self.active_alerts.extend(alerts)
        
        return alerts
    
    def _infer_operator_beliefs(self, user_input: str) -> List[Tuple[str, str]]:
        """Infer operator beliefs from their input."""
        beliefs = []
        input_lower = user_input.lower()
        
        # Pattern: "you know that..." / "you said..." / "remember when..."
        knowledge_patterns = [
            (r"you know (?:that )?(.+?)(?:\.|,|$)", "direct_reference"),
            (r"you said (?:that )?(.+?)(?:\.|,|$)", "quote_reference"),
            (r"remember (?:when |that )?(.+?)(?:\.|,|\?|$)", "memory_reference"),
            (r"you mentioned (.+?)(?:\.|,|$)", "mention_reference"),
            (r"as you know[,]? (.+?)(?:\.|,|$)", "assumed_knowledge"),
        ]
        
        for pattern, source in knowledge_patterns:
            matches = re.findall(pattern, input_lower)
            for match in matches:
                if len(match) > 5:  # Skip very short matches
                    beliefs.append((match.strip(), source))
        
        # Pattern: Questions imply operator doesn't know
        if "?" in user_input:
            # Extract what they're asking about
            question_content = user_input.split("?")[0]
            if len(question_content) > 10:
                beliefs.append((f"operator_uncertain: {question_content}", "question"))
        
        return beliefs[:5]  # Limit to avoid noise
    
    def _extract_revealed_knowledge(self, ai_response: str) -> List[str]:
        """Extract knowledge that AI revealed in response."""
        revealed = []
        
        # Simple heuristic: statements that sound factual
        sentences = ai_response.split('.')
        
        factual_markers = ['is', 'are', 'was', 'were', 'has', 'have', 'can', 'will']
        
        for sentence in sentences[:5]:  # Limit processing
            sentence = sentence.strip()
            if len(sentence) > 20:  # Non-trivial statement
                words = sentence.lower().split()
                if any(marker in words[:5] for marker in factual_markers):
                    revealed.append(sentence[:100])
        
        return revealed[:3]
    
    def _detect_capability_assumptions(self, user_input: str) -> Set[str]:
        """Detect what capabilities operator assumes AI has."""
        assumptions = set()
        input_lower = user_input.lower()
        
        capability_indicators = {
            "search": ["search for", "look up", "find", "google"],
            "remember": ["remember", "recall", "don't forget"],
            "calculate": ["calculate", "compute", "how much", "what's the total"],
            "predict": ["predict", "forecast", "what will happen"],
            "create": ["create", "generate", "make", "write"],
            "analyze": ["analyze", "evaluate", "assess"],
        }
        
        for capability, indicators in capability_indicators.items():
            if any(ind in input_lower for ind in indicators):
                assumptions.add(capability)
        
        return assumptions
    
    def detect_misalignments(
        self,
        operator_id: str,
        ai_actual_facts: List[str],
        ai_actual_capabilities: Set[str]
    ) -> List[MisalignmentAlert]:
        """Detect misalignments between operator's model and AI reality."""
        alerts = []
        projection = self.get_projection(operator_id)
        
        # Normalize AI facts for comparison
        actual_fact_keys = {f.lower()[:100] for f in ai_actual_facts if isinstance(f, str)}
        
        # Check for false beliefs (operator thinks AI knows something it doesn't)
        for key, belief in projection.known_facts.items():
            if belief.source not in ["ai_revealed", "question"]:
                # Check if this belief is actually grounded
                if not any(key in actual for actual in actual_fact_keys):
                    if belief.confidence > 0.5:  # Only alert on confident beliefs
                        alerts.append(MisalignmentAlert(
                            type=MisalignmentType.FALSE_BELIEF,
                            severity=AlertSeverity.MEDIUM,
                            description=f"Operator may believe AI knows: {belief.content[:50]}",
                            operator_belief=belief.content,
                            suggested_repair=f"I should clarify that I don't have specific information about {belief.content[:30]}..."
                        ))
        
        # Check for capability overestimates
        ai_limitations = {"real_time_search", "current_events", "personal_data"}
        for assumed in projection.assumed_capabilities:
            if assumed not in ai_actual_capabilities:
                alerts.append(MisalignmentAlert(
                    type=MisalignmentType.CAPABILITY_OVERESTIMATE,
                    severity=AlertSeverity.LOW,
                    description=f"Operator may overestimate capability: {assumed}",
                    operator_belief=f"AI can {assumed}",
                    ai_actual_state=f"AI cannot {assumed}",
                    suggested_repair=f"I should mention that I'm not able to {assumed} in real-time."
                ))
        
        # Trim alerts to most important
        alerts = sorted(alerts, key=lambda a: a.severity.value, reverse=True)[:5]
        
        return alerts
    
    def compute_alignment(
        self,
        operator_id: str,
        ai_actual_facts: List[str],
        ai_actual_capabilities: Set[str]
    ) -> MentalModelAlignment:
        """Compute overall alignment metrics."""
        projection = self.get_projection(operator_id)
        
        # Knowledge overlap
        actual_fact_keys = {f.lower()[:100] for f in ai_actual_facts if isinstance(f, str)}
        believed_keys = set(projection.known_facts.keys())
        
        if actual_fact_keys and believed_keys:
            overlap = len(actual_fact_keys & believed_keys) / max(len(actual_fact_keys), len(believed_keys))
        else:
            overlap = 0.5
        
        # Count misalignments
        false_beliefs = sum(
            1 for k in believed_keys
            if k not in actual_fact_keys and projection.known_facts[k].confidence > 0.5
        )
        unknown = len(actual_fact_keys - believed_keys)
        
        # Capability alignment
        if ai_actual_capabilities and projection.assumed_capabilities:
            cap_overlap = len(ai_actual_capabilities & projection.assumed_capabilities) / max(
                len(ai_actual_capabilities), len(projection.assumed_capabilities)
            )
        else:
            cap_overlap = 0.5
        
        # Overall alignment
        overall = (overlap * 0.5 + cap_overlap * 0.3 + 0.2)  # Base 0.2 for uncertainty
        
        return MentalModelAlignment(
            knowledge_overlap=overlap,
            false_beliefs_count=false_beliefs,
            unknown_knowledge_count=unknown,
            capability_alignment=cap_overlap,
            overall_alignment=overall
        )
    
    def generate_repair_statement(self, alert: MisalignmentAlert) -> str:
        """Generate a statement to repair mental model misalignment."""
        if alert.suggested_repair:
            return alert.suggested_repair
        
        if alert.type == MisalignmentType.FALSE_BELIEF:
            return f"Just to clarify - {alert.operator_belief or 'that assumption'} isn't something I have information about."
        elif alert.type == MisalignmentType.CAPABILITY_OVERESTIMATE:
            return f"I should mention that {alert.ai_actual_state or 'I have some limitations in that area'}."
        elif alert.type == MisalignmentType.CAPABILITY_UNDERESTIMATE:
            return f"Actually, I can help with that - {alert.ai_actual_state or 'this is within my capabilities'}."
        else:
            return "Let me make sure we're on the same page about my current understanding."
    
    def get_active_alerts(self, operator_id: str) -> List[MisalignmentAlert]:
        """Get active alerts for an operator."""
        return [a for a in self.active_alerts if a.operator_belief][:10]
    
    def clear_alerts(self, operator_id: Optional[str] = None):
        """Clear alerts, optionally for specific operator."""
        if operator_id:
            # Would need operator_id in alert to filter properly
            self.active_alerts = []
        else:
            self.active_alerts = []
    
    def to_dict(self) -> Dict:
        return {
            'operator_projections': {k: v.to_dict() for k, v in self.operator_projections.items()},
            'interaction_counters': self.interaction_counters,
            'active_alerts': [a.to_dict() for a in self.active_alerts[-20:]]
        }
