"""
Cognitive Load Prediction System
Predicts operator cognitive state to prevent overwhelm
"""
from typing import Dict, List, Optional, Tuple
from pydantic import BaseModel, Field
from datetime import datetime, timezone, timedelta
from enum import Enum
import math

class CognitiveState(str, Enum):
    """Operator cognitive state levels"""
    OPTIMAL = "optimal"          # Engaged, responsive
    ELEVATED = "elevated"        # High but manageable
    HIGH = "high"                # Approaching overload
    OVERLOAD = "overload"        # Cognitive overload
    UNDERLOAD = "underload"      # Disengaged, bored

class WorkloadFactor(BaseModel):
    """Individual workload contributing factor"""
    name: str
    current_value: float  # 0-1
    weight: float  # Importance weight
    trend: str = "stable"  # increasing, decreasing, stable

class CognitiveLoadState(BaseModel):
    """Complete cognitive load state"""
    operator_id: str
    timestamp: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
    
    # Overall metrics
    overall_load: float = 0.5  # 0-1
    state: CognitiveState = CognitiveState.OPTIMAL
    
    # Component loads
    visual_load: float = 0.0
    auditory_load: float = 0.0
    cognitive_load: float = 0.0
    motor_load: float = 0.0
    
    # Contributing factors
    factors: List[WorkloadFactor] = Field(default_factory=list)
    
    # Predictions
    predicted_load_5min: float = 0.5
    predicted_state_5min: CognitiveState = CognitiveState.OPTIMAL
    overload_risk: float = 0.0  # 0-1 probability
    
    # Recommendations
    recommendations: List[str] = Field(default_factory=list)

class CognitiveLoadPredictor:
    """
    Predicts operator cognitive load based on multiple factors
    Uses multiple resource theory (Wickens)
    """
    
    def __init__(self):
        self.operator_states: Dict[str, List[CognitiveLoadState]] = {}
        self.baselines: Dict[str, Dict[str, float]] = {}
        
        # Workload factor definitions with weights
        self.factor_weights = {
            "active_detections": 0.15,
            "threat_level": 0.20,
            "decision_pending": 0.18,
            "time_pressure": 0.15,
            "task_complexity": 0.12,
            "information_rate": 0.10,
            "interruptions": 0.10
        }
    
    def update(
        self,
        operator_id: str,
        metrics: Dict[str, float]
    ) -> CognitiveLoadState:
        """
        Update cognitive load prediction with new metrics
        
        Args:
            operator_id: Operator identifier
            metrics: Dictionary of metric values (0-1 scale)
                - active_detections: Number of tracked objects / max capacity
                - threat_level: Current threat assessment (0=low, 1=critical)
                - decision_pending: Time since last required decision / timeout
                - time_pressure: Mission urgency level
                - task_complexity: Current task difficulty
                - information_rate: Data flow rate vs baseline
                - interruptions: Recent interruption count / threshold
        """
        # Initialize if needed
        if operator_id not in self.operator_states:
            self.operator_states[operator_id] = []
            self.baselines[operator_id] = {k: 0.3 for k in self.factor_weights}
        
        # Calculate component loads
        factors = []
        for factor_name, weight in self.factor_weights.items():
            value = metrics.get(factor_name, 0.3)
            baseline = self.baselines[operator_id].get(factor_name, 0.3)
            
            # Determine trend
            trend = "stable"
            if value > baseline + 0.1:
                trend = "increasing"
            elif value < baseline - 0.1:
                trend = "decreasing"
            
            factors.append(WorkloadFactor(
                name=factor_name,
                current_value=value,
                weight=weight,
                trend=trend
            ))
            
            # Update baseline with exponential moving average
            self.baselines[operator_id][factor_name] = 0.95 * baseline + 0.05 * value
        
        # Calculate overall cognitive load
        overall_load = sum(f.current_value * f.weight for f in factors)
        overall_load = max(0, min(1, overall_load))
        
        # Calculate component loads (simplified VACP model)
        visual_load = (
            metrics.get("active_detections", 0.3) * 0.4 +
            metrics.get("information_rate", 0.3) * 0.3 +
            metrics.get("task_complexity", 0.3) * 0.3
        )
        
        cognitive_load = (
            metrics.get("decision_pending", 0.3) * 0.4 +
            metrics.get("task_complexity", 0.3) * 0.3 +
            metrics.get("threat_level", 0.3) * 0.3
        )
        
        # Predict future load
        history = self.operator_states.get(operator_id, [])[-10:]
        predicted_load = self._predict_future_load(history, overall_load)
        
        # Assess overload risk
        overload_risk = self._calculate_overload_risk(overall_load, predicted_load, history)
        
        # Determine state
        state = self._determine_state(overall_load)
        predicted_state = self._determine_state(predicted_load)
        
        # Generate recommendations
        recommendations = self._generate_recommendations(
            state, factors, overload_risk
        )
        
        # Create state object
        load_state = CognitiveLoadState(
            operator_id=operator_id,
            overall_load=overall_load,
            state=state,
            visual_load=min(1, visual_load),
            cognitive_load=min(1, cognitive_load),
            factors=factors,
            predicted_load_5min=predicted_load,
            predicted_state_5min=predicted_state,
            overload_risk=overload_risk,
            recommendations=recommendations
        )
        
        # Store in history
        self.operator_states[operator_id].append(load_state)
        
        # Keep only last 100 states
        if len(self.operator_states[operator_id]) > 100:
            self.operator_states[operator_id] = self.operator_states[operator_id][-100:]
        
        return load_state
    
    def _predict_future_load(
        self, 
        history: List[CognitiveLoadState], 
        current: float
    ) -> float:
        """Predict load 5 minutes into future"""
        if len(history) < 3:
            return current
        
        # Simple linear regression on recent trend
        recent = [s.overall_load for s in history[-5:]] + [current]
        
        # Calculate trend
        n = len(recent)
        if n < 2:
            return current
        
        # Linear regression slope
        x_mean = (n - 1) / 2
        y_mean = sum(recent) / n
        
        numerator = sum((i - x_mean) * (recent[i] - y_mean) for i in range(n))
        denominator = sum((i - x_mean) ** 2 for i in range(n))
        
        if denominator == 0:
            return current
        
        slope = numerator / denominator
        
        # Project 5 minutes ahead (assuming ~2s between updates, ~150 steps)
        prediction = current + slope * 10  # Conservative projection
        
        return max(0, min(1, prediction))
    
    def _calculate_overload_risk(
        self,
        current: float,
        predicted: float,
        history: List[CognitiveLoadState]
    ) -> float:
        """Calculate probability of overload in near future"""
        # Base risk from current level
        risk = 0.0
        
        if current > 0.8:
            risk = 0.8
        elif current > 0.7:
            risk = 0.5
        elif current > 0.6:
            risk = 0.3
        else:
            risk = 0.1
        
        # Increase if trending up
        if predicted > current:
            risk += 0.2 * (predicted - current)
        
        # Check for sustained high load
        if len(history) >= 5:
            recent_high = sum(1 for s in history[-5:] if s.overall_load > 0.7)
            if recent_high >= 3:
                risk += 0.15
        
        return min(1, risk)
    
    def _determine_state(self, load: float) -> CognitiveState:
        """Determine cognitive state from load level"""
        if load < 0.2:
            return CognitiveState.UNDERLOAD
        elif load < 0.5:
            return CognitiveState.OPTIMAL
        elif load < 0.7:
            return CognitiveState.ELEVATED
        elif load < 0.85:
            return CognitiveState.HIGH
        else:
            return CognitiveState.OVERLOAD
    
    def _generate_recommendations(
        self,
        state: CognitiveState,
        factors: List[WorkloadFactor],
        overload_risk: float
    ) -> List[str]:
        """Generate actionable recommendations based on state"""
        recommendations = []
        
        if state == CognitiveState.OVERLOAD:
            recommendations.append("ALERT: Cognitive overload detected - reduce task complexity immediately")
            recommendations.append("Consider delegating secondary tasks to AI automation")
            recommendations.append("Take a brief pause if mission permits")
        
        elif state == CognitiveState.HIGH:
            recommendations.append("High cognitive load - prioritize critical tasks only")
            
            # Find highest contributing factors
            top_factors = sorted(factors, key=lambda f: f.current_value * f.weight, reverse=True)[:2]
            for f in top_factors:
                if f.name == "active_detections" and f.current_value > 0.7:
                    recommendations.append("Consider filtering to high-priority targets only")
                elif f.name == "decision_pending" and f.current_value > 0.7:
                    recommendations.append("Pending decision requiring attention")
                elif f.name == "information_rate" and f.current_value > 0.7:
                    recommendations.append("Information flow rate is high - consider summary mode")
        
        elif state == CognitiveState.ELEVATED:
            if overload_risk > 0.5:
                recommendations.append("Workload trending high - monitor closely")
        
        elif state == CognitiveState.UNDERLOAD:
            recommendations.append("Low engagement detected - consider expanding task scope")
            recommendations.append("Verify situational awareness is maintained")
        
        return recommendations
    
    def get_current_state(self, operator_id: str) -> Optional[CognitiveLoadState]:
        """Get most recent cognitive load state"""
        states = self.operator_states.get(operator_id, [])
        return states[-1] if states else None
    
    def get_history(
        self, 
        operator_id: str, 
        minutes: int = 30
    ) -> List[CognitiveLoadState]:
        """Get cognitive load history for operator"""
        cutoff = datetime.now(timezone.utc) - timedelta(minutes=minutes)
        states = self.operator_states.get(operator_id, [])
        return [s for s in states if s.timestamp >= cutoff]
    
    def should_intervene(self, operator_id: str) -> Tuple[bool, str]:
        """Determine if AI should intervene to reduce load"""
        state = self.get_current_state(operator_id)
        if not state:
            return False, ""
        
        if state.state == CognitiveState.OVERLOAD:
            return True, "Cognitive overload - automated intervention recommended"
        
        if state.overload_risk > 0.7 and state.state == CognitiveState.HIGH:
            return True, "High overload risk - preemptive intervention recommended"
        
        return False, ""

# Global instance
cognitive_load_predictor = CognitiveLoadPredictor()
