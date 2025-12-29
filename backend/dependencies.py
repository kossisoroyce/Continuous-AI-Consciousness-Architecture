from typing import Dict
from nurture import NurtureEngine
from system_config import NurtureConfig, DEFAULT_NURTURE_CONFIG as DEFAULT_CONFIG
from nurture.store import NurtureStore
from nurture.significance import get_dynamic_threshold
from experience import ExperientialEngine
from schemas import StateResponse, ExperientialStateResponse

# Initialize components
store = NurtureStore(storage_dir="./nurture_data")
engine = NurtureEngine(config=DEFAULT_CONFIG)

# Experiential Layer state (session-based)
experiential_sessions: Dict[str, ExperientialEngine] = {}

def get_store():
    return store

def get_engine():
    return engine

def get_experiential_sessions():
    return experiential_sessions

def state_to_response(state) -> StateResponse:
    """Convert NurtureState to StateResponse."""
    return StateResponse(
        instance_id=state.instance_id,
        phase=state.phase,
        stability=round(state.stability, 4),
        plasticity=round(state.plasticity, 4),
        interaction_count=state.interaction_count,
        significant_count=state.significant_count,
        stance={k: round(v, 4) for k, v in state.stance_json.items()},
        environment=state.env_json,
        current_threshold=round(
            get_dynamic_threshold(state.plasticity, DEFAULT_CONFIG), 4
        ),
        created_at=state.created_at.isoformat(),
        last_updated=state.last_updated.isoformat()
    )

def experiential_to_response(exp_engine: ExperientialEngine) -> ExperientialStateResponse:
    """Convert ExperientialEngine state to response model."""
    summary = exp_engine.get_state_summary()
    return ExperientialStateResponse(
        session_id=summary.get('session_id', ''),
        interaction_count=summary.get('interaction_count', 0),
        topic_summary=summary.get('topic_summary', ''),
        emotion_summary=summary.get('emotion_summary', ''),
        user_summary=summary.get('user_summary', ''),
        facts_count=summary.get('facts_count', 0),
        open_questions=summary.get('open_questions', 0),
        active_commitments=summary.get('active_commitments', 0),
        session_familiarity=summary.get('session_familiarity', 0.0),
        total_sessions=summary.get('total_sessions', 0),
        context_string=exp_engine.get_context_for_prompt(),
        internal_thoughts=[{
            'timestamp': t['timestamp'].isoformat() if hasattr(t['timestamp'], 'isoformat') else str(t['timestamp']),
            'type': t['prompt'].type if hasattr(t['prompt'], 'type') else str(t['prompt'].get('type', '')),
            'prompt': t['prompt'].content if hasattr(t['prompt'], 'content') else str(t['prompt'].get('content', '')),
            'thought': t['thought']
        } for t in exp_engine.stim_state.internal_thoughts]
    )
