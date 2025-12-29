"""
Explanation Generation System

Converts internal AI reasoning into operator-appropriate explanations
with multiple levels of detail.
"""

from dataclasses import dataclass, field
from typing import Dict, List, Optional, Any
from datetime import datetime
from enum import Enum


class ExplanationLevel(Enum):
    """Detail levels for explanations."""
    BRIEF = "brief"          # One sentence summary
    STANDARD = "standard"    # Key factors + confidence
    DETAILED = "detailed"    # Full reasoning chain
    TECHNICAL = "technical"  # Include uncertainty quantification


@dataclass
class Explanation:
    """Structured explanation of AI reasoning."""
    level: ExplanationLevel
    summary: str
    key_factors: List[str] = field(default_factory=list)
    confidence_statement: str = ""
    caveats: List[str] = field(default_factory=list)
    reasoning_chain: Optional[List[str]] = None
    evidence_used: Optional[List[str]] = None
    alternatives_considered: Optional[List[str]] = None
    uncertainty_details: Optional[Dict[str, float]] = None
    timestamp: datetime = field(default_factory=datetime.now)
    
    def to_dict(self) -> Dict:
        return {
            'level': self.level.value,
            'summary': self.summary,
            'key_factors': self.key_factors,
            'confidence_statement': self.confidence_statement,
            'caveats': self.caveats,
            'reasoning_chain': self.reasoning_chain,
            'evidence_used': self.evidence_used,
            'alternatives_considered': self.alternatives_considered,
            'uncertainty_details': self.uncertainty_details,
            'timestamp': self.timestamp.isoformat()
        }
    
    def to_operator_string(self) -> str:
        """Format explanation as operator-readable text."""
        if self.level == ExplanationLevel.BRIEF:
            return self.summary
        
        parts = [self.summary]
        
        if self.key_factors:
            parts.append("\nKey factors:")
            for factor in self.key_factors:
                parts.append(f"  • {factor}")
        
        if self.confidence_statement:
            parts.append(f"\n{self.confidence_statement}")
        
        if self.caveats:
            parts.append("\nCaveats:")
            for caveat in self.caveats:
                parts.append(f"  ⚠ {caveat}")
        
        if self.level in [ExplanationLevel.DETAILED, ExplanationLevel.TECHNICAL]:
            if self.reasoning_chain:
                parts.append("\nReasoning:")
                for i, step in enumerate(self.reasoning_chain, 1):
                    parts.append(f"  {i}. {step}")
            
            if self.alternatives_considered:
                parts.append("\nAlternatives considered:")
                for alt in self.alternatives_considered:
                    parts.append(f"  - {alt}")
        
        if self.level == ExplanationLevel.TECHNICAL and self.uncertainty_details:
            parts.append("\nUncertainty breakdown:")
            for source, value in self.uncertainty_details.items():
                parts.append(f"  {source}: {value:.1%}")
        
        return "\n".join(parts)


class ExplanationGenerator:
    """Generates explanations from AI internal state and reasoning."""
    
    def __init__(self, config: Optional[Dict] = None):
        self.config = config or {
            'brief_max_length': 100,
            'standard_max_length': 300,
            'detailed_max_length': 800
        }
    
    def generate(
        self,
        recommendation: str,
        confidence_score: float,
        internal_thoughts: List[str] = None,
        relevant_facts: List[str] = None,
        open_questions: List[str] = None,
        context: str = "",
        level: ExplanationLevel = ExplanationLevel.STANDARD
    ) -> Explanation:
        """Generate an explanation at the specified detail level."""
        
        internal_thoughts = internal_thoughts or []
        relevant_facts = relevant_facts or []
        open_questions = open_questions or []
        
        # Extract key factors from internal thoughts and facts
        key_factors = self._extract_key_factors(
            recommendation, internal_thoughts, relevant_facts
        )
        
        # Generate confidence statement
        confidence_statement = self._generate_confidence_statement(
            confidence_score, relevant_facts, open_questions
        )
        
        # Identify caveats/uncertainties
        caveats = self._identify_caveats(
            confidence_score, open_questions, internal_thoughts
        )
        
        # Generate summary
        summary = self._generate_summary(
            recommendation, key_factors, confidence_score, level
        )
        
        explanation = Explanation(
            level=level,
            summary=summary,
            key_factors=key_factors[:5],  # Limit to top 5
            confidence_statement=confidence_statement,
            caveats=caveats[:3]  # Limit to top 3
        )
        
        # Add detailed content for higher levels
        if level in [ExplanationLevel.DETAILED, ExplanationLevel.TECHNICAL]:
            explanation.reasoning_chain = self._build_reasoning_chain(
                internal_thoughts, relevant_facts, recommendation
            )
            explanation.evidence_used = relevant_facts[:5]
            explanation.alternatives_considered = self._extract_alternatives(
                internal_thoughts
            )
        
        if level == ExplanationLevel.TECHNICAL:
            explanation.uncertainty_details = self._compute_uncertainty_breakdown(
                confidence_score, open_questions, relevant_facts
            )
        
        return explanation
    
    def _extract_key_factors(
        self,
        recommendation: str,
        thoughts: List[str],
        facts: List[str]
    ) -> List[str]:
        """Extract main factors supporting the recommendation."""
        factors = []
        
        # Use facts as primary factors
        for fact in facts[:3]:
            if isinstance(fact, dict):
                factors.append(fact.get('content', str(fact)))
            else:
                factors.append(str(fact))
        
        # Extract supporting points from thoughts
        supporting_keywords = ['because', 'since', 'due to', 'based on', 'indicates']
        for thought in thoughts:
            thought_lower = thought.lower() if isinstance(thought, str) else ""
            for keyword in supporting_keywords:
                if keyword in thought_lower:
                    factors.append(thought[:100])  # Truncate long thoughts
                    break
        
        return factors[:5]
    
    def _generate_confidence_statement(
        self,
        confidence: float,
        facts: List[str],
        questions: List[str]
    ) -> str:
        """Generate natural language confidence statement."""
        if confidence >= 0.8:
            base = "I'm highly confident in this recommendation"
            if facts:
                return f"{base} based on {len(facts)} supporting facts."
            return f"{base}."
        elif confidence >= 0.6:
            base = "I'm fairly confident"
            if questions:
                return f"{base}, though {len(questions)} open questions remain."
            return f"{base} in this recommendation."
        elif confidence >= 0.4:
            return "I have moderate confidence. Consider this as one option among several."
        else:
            return "I have low confidence in this. Proceed with caution and verify independently."
    
    def _identify_caveats(
        self,
        confidence: float,
        questions: List[str],
        thoughts: List[str]
    ) -> List[str]:
        """Identify important caveats and limitations."""
        caveats = []
        
        # Add open questions as caveats
        for q in questions[:2]:
            if isinstance(q, dict):
                caveats.append(f"Unresolved: {q.get('question', str(q))}")
            else:
                caveats.append(f"Unresolved: {q}")
        
        # Low confidence is itself a caveat
        if confidence < 0.5:
            caveats.append("Limited evidence available for this recommendation")
        
        # Look for uncertainty language in thoughts
        uncertainty_markers = ['unclear', 'uncertain', 'might', 'possibly', 'however']
        for thought in thoughts:
            thought_str = str(thought).lower()
            for marker in uncertainty_markers:
                if marker in thought_str:
                    caveats.append(f"Uncertainty noted: {thought[:80]}")
                    break
        
        return caveats[:5]
    
    def _generate_summary(
        self,
        recommendation: str,
        factors: List[str],
        confidence: float,
        level: ExplanationLevel
    ) -> str:
        """Generate appropriate summary for the level."""
        if level == ExplanationLevel.BRIEF:
            if factors:
                return f"{recommendation} (based on: {factors[0][:50]})"
            return recommendation
        
        confidence_word = (
            "highly confident" if confidence >= 0.8 else
            "confident" if confidence >= 0.6 else
            "moderately confident" if confidence >= 0.4 else
            "uncertain"
        )
        
        return f"Recommendation: {recommendation}. I am {confidence_word} in this assessment."
    
    def _build_reasoning_chain(
        self,
        thoughts: List[str],
        facts: List[str],
        recommendation: str
    ) -> List[str]:
        """Build logical reasoning chain from thoughts and facts."""
        chain = []
        
        # Start with facts as premises
        for fact in facts[:3]:
            content = fact.get('content', str(fact)) if isinstance(fact, dict) else str(fact)
            chain.append(f"Observed: {content}")
        
        # Add relevant thoughts as reasoning steps
        for thought in thoughts[:3]:
            chain.append(f"Considered: {thought[:100]}")
        
        # Conclude with recommendation
        chain.append(f"Therefore: {recommendation}")
        
        return chain
    
    def _extract_alternatives(self, thoughts: List[str]) -> List[str]:
        """Extract alternative options that were considered."""
        alternatives = []
        alt_markers = ['alternatively', 'another option', 'could also', 'or we could']
        
        for thought in thoughts:
            thought_str = str(thought).lower()
            for marker in alt_markers:
                if marker in thought_str:
                    alternatives.append(thought[:100])
                    break
        
        return alternatives[:3]
    
    def _compute_uncertainty_breakdown(
        self,
        confidence: float,
        questions: List[str],
        facts: List[str]
    ) -> Dict[str, float]:
        """Compute detailed uncertainty breakdown for technical level."""
        total_uncertainty = 1.0 - confidence
        
        breakdown = {}
        
        # Distribute uncertainty across sources
        if questions:
            breakdown['open_questions'] = min(0.3, len(questions) * 0.1)
        
        if len(facts) < 3:
            breakdown['limited_evidence'] = 0.2
        
        remaining = total_uncertainty - sum(breakdown.values())
        if remaining > 0:
            breakdown['model_uncertainty'] = remaining
        
        return breakdown
    
    def generate_for_workload(
        self,
        recommendation: str,
        confidence_score: float,
        workload_level: float,
        **kwargs
    ) -> Explanation:
        """Generate explanation appropriate for current operator workload."""
        if workload_level > 0.7:
            level = ExplanationLevel.BRIEF
        elif workload_level > 0.4:
            level = ExplanationLevel.STANDARD
        else:
            level = ExplanationLevel.DETAILED
        
        return self.generate(
            recommendation=recommendation,
            confidence_score=confidence_score,
            level=level,
            **kwargs
        )
