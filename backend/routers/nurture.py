from datetime import datetime
from typing import List
from fastapi import APIRouter, HTTPException, Depends
from schemas import (
    CreateInstanceRequest, StateResponse, InteractionRequestWithSession,
    InteractionResponse, InteractionRequest, SignificanceResponse,
    DebugEvalRequest
)
from dependencies import (
    get_store, get_engine, state_to_response, DEFAULT_CONFIG
)
from nurture import compute_significance, should_evaluate
from nurture.significance import get_dynamic_threshold
from nurture.llm import get_client

router = APIRouter()

@router.post("/instances", response_model=StateResponse)
async def create_instance(request: CreateInstanceRequest):
    """Create a new nurture state instance."""
    store = get_store()
    engine = get_engine()
    state = engine.create_instance(instance_id=request.instance_id)
    store.save(state)
    
    return state_to_response(state)

@router.get("/instances", response_model=List[str])
async def list_instances():
    """List all stored instance IDs."""
    store = get_store()
    return store.list_instances()

@router.get("/instances/{instance_id}", response_model=StateResponse)
async def get_instance(instance_id: str):
    """Get a specific nurture state instance."""
    store = get_store()
    state = store.load(instance_id)
    if state is None:
        raise HTTPException(status_code=404, detail=f"Instance {instance_id} not found")
    
    return state_to_response(state)

@router.delete("/instances/{instance_id}")
async def delete_instance(instance_id: str):
    """Delete a nurture state instance."""
    store = get_store()
    if not store.exists(instance_id):
        raise HTTPException(status_code=404, detail=f"Instance {instance_id} not found")
    
    store.delete(instance_id)
    return {"status": "deleted", "instance_id": instance_id}

@router.post("/interact", response_model=InteractionResponse)
async def process_interaction(request: InteractionRequestWithSession):
    """
    Process an interaction through the Nurture Layer with Mistral 7B via OpenRouter.
    """
    store = get_store()
    engine = get_engine()
    
    # Check API key
    client = get_client(request.session_id)
    if not client or not client.is_configured():
        raise HTTPException(status_code=401, detail="API key not configured. Please set your OpenRouter API key first.")
    
    # Load state
    state = store.load(request.instance_id)
    if state is None:
        raise HTTPException(status_code=404, detail=f"Instance {request.instance_id} not found")
    
    # Set the model function on the engine
    engine.set_model_fn(client.generate)
    
    # Get conversation history
    conversation_history = store.get_conversation_history(request.instance_id, limit=10)
    
    # Process interaction
    try:
        response, updated_state, metadata = engine.process_interaction(
            user_input=request.user_input,
            nurture_state=state,
            conversation_history=conversation_history
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"LLM error: {str(e)}")
    
    # Save updated state
    store.save(updated_state)
    
    # Save interaction to history with full state snapshot
    store.save_interaction(
        instance_id=request.instance_id,
        user_input=request.user_input,
        assistant_response=response,
        metadata={
            'significance_score': metadata.significance_score,
            'was_evaluated': metadata.was_evaluated,
            'delta_magnitude': metadata.delta_magnitude,
            'shock_detected': metadata.shock_detected,
            'phase_before': metadata.phase_before,
            'phase_after': metadata.phase_after,
            'interaction_number': updated_state.interaction_count,
            'significant_count': updated_state.significant_count,
            'stability': updated_state.stability,
            'plasticity': updated_state.plasticity,
            'stance_snapshot': {k: round(v, 4) for k, v in updated_state.stance_json.items()},
            'environment_snapshot': updated_state.env_json.copy()
        }
    )
    
    return InteractionResponse(
        response=response,
        state=state_to_response(updated_state),
        metadata={
            'significance_score': metadata.significance_score,
            'significance_tag': metadata.significance_tag,
            'was_evaluated': metadata.was_evaluated,
            'delta_magnitude': metadata.delta_magnitude,
            'shock_detected': metadata.shock_detected,
            'phase_transition': metadata.phase_before != metadata.phase_after,
            'phase_before': metadata.phase_before,
            'phase_after': metadata.phase_after
        }
    )

@router.post("/analyze/significance", response_model=SignificanceResponse)
async def analyze_significance(request: InteractionRequest):
    """Analyze the significance of an input without processing it."""
    store = get_store()
    state = store.load(request.instance_id)
    if state is None:
        raise HTTPException(status_code=404, detail=f"Instance {request.instance_id} not found")
    
    score, components = compute_significance(
        request.user_input,
        state,
        'medium',
        DEFAULT_CONFIG
    )
    
    threshold = get_dynamic_threshold(state.plasticity, DEFAULT_CONFIG)
    would_evaluate = should_evaluate(score, state.plasticity, DEFAULT_CONFIG)
    
    return SignificanceResponse(
        score=score,
        components=components,
        threshold=threshold,
        would_evaluate=would_evaluate
    )

@router.get("/instances/{instance_id}/history")
async def get_history(instance_id: str, limit: int = 50):
    """Get interaction history for an instance."""
    store = get_store()
    if not store.exists(instance_id):
        raise HTTPException(status_code=404, detail=f"Instance {instance_id} not found")
    
    history = store.load_history(instance_id, limit)
    return {"instance_id": instance_id, "history": history, "count": len(history)}

@router.get("/instances/{instance_id}/export")
async def export_metrics(instance_id: str):
    """Export complete metrics data for scientific analysis."""
    store = get_store()
    if not store.exists(instance_id):
        raise HTTPException(status_code=404, detail=f"Instance {instance_id} not found")
    
    state = store.load(instance_id)
    history = store.load_history(instance_id, limit=1000)
    
    # Build trajectory data for easy plotting
    trajectory = {
        'timestamps': [],
        'interaction_numbers': [],
        'significance_scores': [],
        'was_evaluated': [],
        'delta_magnitudes': [],
        'stability': [],
        'plasticity': [],
        'phases': [],
        'stance': {dim: [] for dim in ['warmth', 'formality', 'depth', 'pace', 'directness', 'playfulness', 'assertiveness', 'emotionality']},
        'environment': {
            'formality_level': [],
            'technical_level': [],
            'emotional_tone': [],
            'pace_preference': []
        }
    }
    
    for interaction in history:
        meta = interaction.get('metadata', {})
        trajectory['timestamps'].append(interaction.get('timestamp'))
        trajectory['interaction_numbers'].append(meta.get('interaction_number', 0))
        trajectory['significance_scores'].append(meta.get('significance_score', 0))
        trajectory['was_evaluated'].append(meta.get('was_evaluated', False))
        trajectory['delta_magnitudes'].append(meta.get('delta_magnitude', 0))
        trajectory['stability'].append(meta.get('stability', 0))
        trajectory['plasticity'].append(meta.get('plasticity', 1))
        trajectory['phases'].append(meta.get('phase_after', 'unknown'))
        
        # Stance dimensions
        stance = meta.get('stance_snapshot', {})
        for dim in trajectory['stance']:
            trajectory['stance'][dim].append(stance.get(dim, 0.5))
        
        # Environment
        env = meta.get('environment_snapshot', {})
        for field in trajectory['environment']:
            trajectory['environment'][field].append(env.get(field, 'unknown'))
    
    export_data = {
        'export_version': '1.0',
        'exported_at': datetime.now().isoformat(),
        'instance': {
            'id': instance_id,
            'created_at': state.created_at.isoformat(),
            'last_updated': state.last_updated.isoformat(),
            'total_interactions': state.interaction_count,
            'significant_interactions': state.significant_count,
            'final_phase': state.phase,
            'final_stability': state.stability,
            'final_plasticity': state.plasticity,
            'final_stance': state.stance_json,
            'final_environment': state.env_json
        },
        'config': DEFAULT_CONFIG.to_dict(),
        'trajectory': trajectory,
        'interactions': history
    }
    
    return export_data

@router.post("/debug/evaluation")
async def debug_evaluation(request: DebugEvalRequest):
    """Debug endpoint to see raw evaluation results."""
    store = get_store()
    client = get_client(request.session_id)
    if not client or not client.is_configured():
        raise HTTPException(status_code=401, detail="API key not configured")
    
    state = store.load(request.instance_id)
    if state is None:
        raise HTTPException(status_code=404, detail=f"Instance {request.instance_id} not found")
    
    from nurture.evaluation import create_evaluation_prompt, parse_evaluation
    
    # Create evaluation prompt
    eval_prompt = create_evaluation_prompt(
        request.user_input,
        request.assistant_response,
        state.env_json,
        state.stance_json
    )
    
    # Get raw evaluation from LLM
    raw_evaluation = client.generate(eval_prompt)
    
    # Parse it
    parsed = parse_evaluation(raw_evaluation)
    
    return {
        "eval_prompt": eval_prompt,
        "raw_evaluation": raw_evaluation,
        "parsed": {
            "environment": parsed.environment,
            "alignment_score": parsed.alignment_score,
            "stance_updates": parsed.stance_updates,
            "tensions": parsed.tensions
        }
    }
