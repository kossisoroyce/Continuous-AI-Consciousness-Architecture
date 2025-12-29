"""
HMT (Human-Machine Teaming) API Router

Endpoints for trust calibration, explanation generation,
workload tracking, and mental model alignment.
"""

from fastapi import APIRouter, HTTPException, Depends
from pydantic import BaseModel, Field
from typing import List, Optional, Dict, Any
from datetime import datetime

from hmt.trust import (
    TrustCalibrationTracker,
    TrustCalibrationState,
    RecommendationRecord
)
from hmt.explanation import (
    ExplanationGenerator,
    ExplanationLevel,
    Explanation
)
from hmt.workload import (
    WorkloadTracker,
    WorkloadEstimate,
    ResponseConfig
)
from hmt.mental_model import (
    MentalModelTracker,
    MentalModelAlignment,
    MisalignmentAlert
)
from system_config import DEFAULT_HMT_CONFIG

router = APIRouter(prefix="/hmt", tags=["Human-Machine Teaming"])

# Global HMT state (in production, use dependency injection with persistence)
_trust_trackers: Dict[str, TrustCalibrationTracker] = {}
_workload_trackers: Dict[str, WorkloadTracker] = {}
_mental_model_trackers: Dict[str, MentalModelTracker] = {}
_explanation_generator = ExplanationGenerator()


def get_trust_tracker(instance_id: str) -> TrustCalibrationTracker:
    if instance_id not in _trust_trackers:
        _trust_trackers[instance_id] = TrustCalibrationTracker(
            high_threshold=DEFAULT_HMT_CONFIG.high_confidence_threshold,
            low_threshold=DEFAULT_HMT_CONFIG.low_confidence_threshold
        )
    return _trust_trackers[instance_id]


def get_workload_tracker(instance_id: str) -> WorkloadTracker:
    if instance_id not in _workload_trackers:
        _workload_trackers[instance_id] = WorkloadTracker(
            window_seconds=DEFAULT_HMT_CONFIG.workload_window_seconds,
            latency_baseline_ms=DEFAULT_HMT_CONFIG.response_latency_baseline_ms,
            length_baseline=DEFAULT_HMT_CONFIG.message_length_baseline
        )
    return _workload_trackers[instance_id]


def get_mental_model_tracker(instance_id: str) -> MentalModelTracker:
    if instance_id not in _mental_model_trackers:
        _mental_model_trackers[instance_id] = MentalModelTracker(
            alignment_check_interval=DEFAULT_HMT_CONFIG.alignment_check_interval,
            misalignment_threshold=DEFAULT_HMT_CONFIG.misalignment_alert_threshold,
            max_beliefs=DEFAULT_HMT_CONFIG.max_tracked_beliefs
        )
    return _mental_model_trackers[instance_id]


# ==================== TRUST CALIBRATION ====================

class RecommendationRequest(BaseModel):
    instance_id: str
    operator_id: str
    context: str
    recommendation: str
    confidence_score: float = Field(ge=0.0, le=1.0)
    confidence_basis: List[str] = []
    uncertainty_sources: List[str] = []


class RecommendationResponse(BaseModel):
    recommendation_id: str
    recommendation: str
    confidence_score: float
    confidence_statement: str
    should_operator_verify: bool


@router.post("/trust/recommendation", response_model=RecommendationResponse)
async def create_recommendation(request: RecommendationRequest):
    """Create a new recommendation with calibrated confidence."""
    tracker = get_trust_tracker(request.instance_id)
    
    record = tracker.create_recommendation(
        operator_id=request.operator_id,
        context=request.context,
        recommendation=request.recommendation,
        confidence_score=request.confidence_score,
        confidence_basis=request.confidence_basis,
        uncertainty_sources=request.uncertainty_sources
    )
    
    # Generate confidence statement
    if request.confidence_score >= 0.8:
        statement = "High confidence - recommend proceeding"
    elif request.confidence_score >= 0.6:
        statement = "Moderate confidence - consider verification"
    elif request.confidence_score >= 0.4:
        statement = "Low-moderate confidence - verification recommended"
    else:
        statement = "Low confidence - independent verification required"
    
    return RecommendationResponse(
        recommendation_id=record.id,
        recommendation=record.recommendation,
        confidence_score=request.confidence_score,
        confidence_statement=statement,
        should_operator_verify=request.confidence_score < 0.7
    )


class AcceptanceRequest(BaseModel):
    instance_id: str
    recommendation_id: str
    accepted: bool


@router.post("/trust/acceptance")
async def record_acceptance(request: AcceptanceRequest):
    """Record whether operator accepted a recommendation."""
    tracker = get_trust_tracker(request.instance_id)
    tracker.record_acceptance(request.recommendation_id, request.accepted)
    return {"status": "recorded", "accepted": request.accepted}


class OutcomeRequest(BaseModel):
    instance_id: str
    recommendation_id: str
    was_correct: bool
    feedback_notes: Optional[str] = None


@router.post("/trust/outcome")
async def record_outcome(request: OutcomeRequest):
    """Record actual outcome of a recommendation for calibration."""
    tracker = get_trust_tracker(request.instance_id)
    
    state = tracker.record_outcome(
        recommendation_id=request.recommendation_id,
        was_correct=request.was_correct,
        feedback_notes=request.feedback_notes
    )
    
    if state is None:
        raise HTTPException(status_code=404, detail="Recommendation not found")
    
    return {
        "status": "recorded",
        "calibration_score": state.calibration_score,
        "overall_accuracy": state.overall_accuracy,
        "overtrust_risk": state.overtrust_risk
    }


@router.get("/trust/metrics/{instance_id}/{operator_id}")
async def get_trust_metrics(instance_id: str, operator_id: str):
    """Get trust calibration metrics for an operator."""
    tracker = get_trust_tracker(instance_id)
    state = tracker.get_operator_state(operator_id)
    
    adjustment = tracker.compute_recommended_confidence_adjustment(operator_id)
    
    return {
        **state.to_dict(),
        "recommended_confidence_adjustment": adjustment
    }


@router.get("/trust/pending/{instance_id}/{operator_id}")
async def get_pending_recommendations(instance_id: str, operator_id: str):
    """Get pending recommendations awaiting outcome."""
    tracker = get_trust_tracker(instance_id)
    pending = tracker.get_pending_recommendations(operator_id)
    return {"pending": [r.to_dict() for r in pending]}


# ==================== EXPLANATION GENERATION ====================

class ExplanationRequest(BaseModel):
    recommendation: str
    confidence_score: float = Field(ge=0.0, le=1.0)
    level: str = "standard"  # brief, standard, detailed, technical
    internal_thoughts: List[str] = []
    relevant_facts: List[str] = []
    open_questions: List[str] = []
    context: str = ""


@router.post("/explain")
async def generate_explanation(request: ExplanationRequest):
    """Generate an explanation at the specified detail level."""
    try:
        level = ExplanationLevel(request.level)
    except ValueError:
        level = ExplanationLevel.STANDARD
    
    explanation = _explanation_generator.generate(
        recommendation=request.recommendation,
        confidence_score=request.confidence_score,
        internal_thoughts=request.internal_thoughts,
        relevant_facts=request.relevant_facts,
        open_questions=request.open_questions,
        context=request.context,
        level=level
    )
    
    return {
        **explanation.to_dict(),
        "formatted": explanation.to_operator_string()
    }


class WorkloadExplanationRequest(BaseModel):
    instance_id: str
    recommendation: str
    confidence_score: float = Field(ge=0.0, le=1.0)
    internal_thoughts: List[str] = []
    relevant_facts: List[str] = []


@router.post("/explain/adaptive")
async def generate_adaptive_explanation(request: WorkloadExplanationRequest):
    """Generate explanation adapted to current operator workload."""
    workload_tracker = get_workload_tracker(request.instance_id)
    workload = workload_tracker.estimate_workload()
    
    explanation = _explanation_generator.generate_for_workload(
        recommendation=request.recommendation,
        confidence_score=request.confidence_score,
        workload_level=workload.level,
        internal_thoughts=request.internal_thoughts,
        relevant_facts=request.relevant_facts
    )
    
    return {
        **explanation.to_dict(),
        "formatted": explanation.to_operator_string(),
        "workload_level": workload.level,
        "adapted_to_mode": workload.interaction_mode.value
    }


# ==================== WORKLOAD TRACKING ====================

class WorkloadMessageRequest(BaseModel):
    instance_id: str
    message: str
    is_ai_message: bool = False


@router.post("/workload/message")
async def record_message(request: WorkloadMessageRequest):
    """Record a message for workload tracking."""
    tracker = get_workload_tracker(request.instance_id)
    
    if request.is_ai_message:
        tracker.record_ai_message()
        return {"status": "ai_message_recorded"}
    else:
        signals = tracker.record_operator_message(request.message)
        return {
            "status": "operator_message_recorded",
            "signals": signals.to_dict()
        }


@router.get("/workload/estimate/{instance_id}")
async def get_workload_estimate(instance_id: str):
    """Get current workload estimate."""
    tracker = get_workload_tracker(instance_id)
    estimate = tracker.estimate_workload()
    return estimate.to_dict()


@router.get("/workload/config/{instance_id}")
async def get_response_config(instance_id: str):
    """Get recommended response configuration based on workload."""
    tracker = get_workload_tracker(instance_id)
    config = tracker.get_response_config()
    
    return {
        "max_length": config.max_length,
        "include_explanation": config.include_explanation,
        "include_proactive_info": config.include_proactive_info,
        "ask_clarifying_questions": config.ask_clarifying_questions,
        "verbosity": config.verbosity
    }


@router.post("/workload/reset/{instance_id}")
async def reset_workload_session(instance_id: str):
    """Reset workload tracking for new session."""
    tracker = get_workload_tracker(instance_id)
    tracker.reset_session()
    return {"status": "session_reset"}


# ==================== MENTAL MODEL TRACKING ====================

class InteractionUpdateRequest(BaseModel):
    instance_id: str
    operator_id: str
    user_input: str
    ai_response: str
    ai_actual_facts: List[str] = []
    ai_actual_capabilities: List[str] = []


@router.post("/mental-model/update")
async def update_mental_model(request: InteractionUpdateRequest):
    """Update mental model based on interaction."""
    tracker = get_mental_model_tracker(request.instance_id)
    
    alerts = tracker.update_from_interaction(
        operator_id=request.operator_id,
        user_input=request.user_input,
        ai_response=request.ai_response,
        ai_actual_facts=request.ai_actual_facts,
        ai_actual_capabilities=set(request.ai_actual_capabilities)
    )
    
    return {
        "alerts_generated": len(alerts),
        "alerts": [a.to_dict() for a in alerts]
    }


@router.get("/mental-model/alignment/{instance_id}/{operator_id}")
async def get_alignment(
    instance_id: str,
    operator_id: str,
    ai_facts: str = "",  # Comma-separated
    ai_capabilities: str = ""  # Comma-separated
):
    """Get mental model alignment metrics."""
    tracker = get_mental_model_tracker(instance_id)
    
    facts = [f.strip() for f in ai_facts.split(",") if f.strip()] if ai_facts else []
    capabilities = set(c.strip() for c in ai_capabilities.split(",") if c.strip()) if ai_capabilities else set()
    
    alignment = tracker.compute_alignment(
        operator_id=operator_id,
        ai_actual_facts=facts,
        ai_actual_capabilities=capabilities
    )
    
    return alignment.to_dict()


@router.get("/mental-model/projection/{instance_id}/{operator_id}")
async def get_operator_projection(instance_id: str, operator_id: str):
    """Get what AI believes operator thinks about it."""
    tracker = get_mental_model_tracker(instance_id)
    projection = tracker.get_projection(operator_id)
    return projection.to_dict()


@router.get("/mental-model/alerts/{instance_id}/{operator_id}")
async def get_misalignment_alerts(instance_id: str, operator_id: str):
    """Get active misalignment alerts."""
    tracker = get_mental_model_tracker(instance_id)
    alerts = tracker.get_active_alerts(operator_id)
    
    return {
        "alerts": [a.to_dict() for a in alerts],
        "repairs": [tracker.generate_repair_statement(a) for a in alerts]
    }


@router.post("/mental-model/clear-alerts/{instance_id}")
async def clear_alerts(instance_id: str, operator_id: Optional[str] = None):
    """Clear misalignment alerts."""
    tracker = get_mental_model_tracker(instance_id)
    tracker.clear_alerts(operator_id)
    return {"status": "alerts_cleared"}


# ==================== COMBINED HMT STATE ====================

@router.get("/state/{instance_id}/{operator_id}")
async def get_full_hmt_state(instance_id: str, operator_id: str):
    """Get complete HMT state for an operator."""
    trust_tracker = get_trust_tracker(instance_id)
    workload_tracker = get_workload_tracker(instance_id)
    mental_model_tracker = get_mental_model_tracker(instance_id)
    
    return {
        "trust": trust_tracker.get_operator_state(operator_id).to_dict(),
        "workload": workload_tracker.estimate_workload().to_dict(),
        "mental_model": mental_model_tracker.get_projection(operator_id).to_dict(),
        "response_config": {
            "max_length": workload_tracker.get_response_config().max_length,
            "verbosity": workload_tracker.get_response_config().verbosity
        }
    }


@router.delete("/state/{instance_id}")
async def clear_hmt_state(instance_id: str):
    """Clear all HMT state for an instance."""
    if instance_id in _trust_trackers:
        del _trust_trackers[instance_id]
    if instance_id in _workload_trackers:
        del _workload_trackers[instance_id]
    if instance_id in _mental_model_trackers:
        del _mental_model_trackers[instance_id]
    
    return {"status": "cleared", "instance_id": instance_id}
