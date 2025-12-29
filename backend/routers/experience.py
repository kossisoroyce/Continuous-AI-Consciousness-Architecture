from fastapi import APIRouter, HTTPException, BackgroundTasks
import logging
import os
from experience import ExperientialEngine
from system_config import DEFAULT_EXPERIENTIAL_CONFIG
from nurture.llm import set_client, get_client
from schemas import (
    ExperientialStateResponse, IntegratedInteractionResponse,
    IntegratedInteractionRequest
)
from dependencies import (
    get_store, get_engine, get_experiential_sessions,
    state_to_response, experiential_to_response
)

# Get API key from environment
ENV_OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")
ENV_DEFAULT_MODEL = os.getenv("DEFAULT_MODEL", "mistralai/mistral-7b-instruct:free")

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

router = APIRouter()

# Background task for state updates
async def background_update_interaction(
    instance_id: str,
    session_id: str,
    user_input: str,
    response: str,
    significance_tag: str,
    nurture_state_dict: dict, # Pass dict/id to reload or careful with object shared state
    exp_engine: ExperientialEngine
):
    try:
        store = get_store()
        engine = get_engine()
        
        # Reload nurture state to ensure fresh copy in background context involves IO
        # But to avoid race conditions in a simple setup, we use the passed object or reload
        # For safety/correctness in this architecture, let's use the passed state object 
        # assuming single-threaded async event loop.
        nurture_state = store.load(instance_id) 
        if not nurture_state:
            logger.error(f"Background update failed: Instance {instance_id} not found")
            return

        # Update Nurture State
        updated_nurture, metadata = engine.update_state(
            user_input=user_input,
            assistant_response=response,
            significance_tag=significance_tag,
            nurture_state=nurture_state
        )
        
        # Update Experiential State
        exp_metadata = exp_engine.process_interaction(
            user_input=user_input,
            assistant_response=response
        )
        
        # Save updated nurture state
        store.save(updated_nurture)
        
        # Save interaction to history
        store.save_interaction(
            instance_id=instance_id,
            user_input=user_input,
            assistant_response=response,
            metadata={
                'significance_score': metadata.significance_score,
                'was_evaluated': metadata.was_evaluated,
                'delta_magnitude': metadata.delta_magnitude,
                'phase_after': metadata.phase_after,
                'stability': updated_nurture.stability,
                'experiential': exp_metadata
            }
        )
        logger.info(f"Background update completed for session {session_id}")
        
    except Exception as e:
        logger.error(f"Error in background update for session {session_id}: {str(e)}")


@router.post("/experience/session")
async def create_experiential_session(instance_id: str, session_id: str):
    """
    Create a new experiential session linked to a nurture instance.
    """
    store = get_store()
    experiential_sessions = get_experiential_sessions()
    
    # Load nurture state to prime experiential engine
    nurture_state = store.load(instance_id)
    if nurture_state is None:
        raise HTTPException(status_code=404, detail=f"Nurture instance {instance_id} not found")
    
    # Create experiential engine with nurture integration
    exp_engine = ExperientialEngine(
        config=DEFAULT_EXPERIENTIAL_CONFIG,
        nurture_state=nurture_state
    )
    exp_engine.initialize_session(session_id=session_id)
    
    # Store in session dict
    experiential_sessions[session_id] = exp_engine
    
    return {
        "status": "created",
        "session_id": session_id,
        "instance_id": instance_id,
        "primed_from_nurture": True
    }

@router.get("/experience/session/{session_id}", response_model=ExperientialStateResponse)
async def get_experiential_session(session_id: str):
    """Get current experiential state for a session."""
    experiential_sessions = get_experiential_sessions()
    if session_id not in experiential_sessions:
        raise HTTPException(status_code=404, detail=f"Session {session_id} not found")
    
    exp_engine = experiential_sessions[session_id]
    return experiential_to_response(exp_engine)

@router.delete("/experience/session/{session_id}")
async def end_experiential_session(session_id: str):
    """
    End an experiential session and get persistent traces.
    """
    experiential_sessions = get_experiential_sessions()
    if session_id not in experiential_sessions:
        raise HTTPException(status_code=404, detail=f"Session {session_id} not found")
    
    exp_engine = experiential_sessions[session_id]
    traces, promotion_candidate = exp_engine.end_session()
    
    # Clean up
    del experiential_sessions[session_id]
    
    return {
        "status": "ended",
        "session_id": session_id,
        "persistent_traces": {
            "session_count": traces.session_count if traces else 0,
            "familiarity_score": traces.familiarity_score if traces else 0,
        },
        "promotion_candidate": promotion_candidate
    }

@router.post("/integrated/interact", response_model=IntegratedInteractionResponse)
async def integrated_interaction(
    request: IntegratedInteractionRequest,
    background_tasks: BackgroundTasks
):
    """
    Process an interaction through BOTH Nurture and Experiential layers.
    Uses detached execution: Returns response immediately, updates state in background.
    """
    logger.info(f"Processing interaction for session {request.session_id}: {request.user_input[:50]}...")
    
    store = get_store()
    engine = get_engine()
    experiential_sessions = get_experiential_sessions()
    
    # Set up OpenRouter client - use request key, then env key, then existing client
    api_key = request.openai_api_key or ENV_OPENAI_API_KEY
    if api_key:
        client = set_client(request.session_id, api_key)
    else:
        client = get_client(request.session_id)
        if not client or not client.is_configured():
            raise HTTPException(status_code=401, detail="OpenAI API key required. Set OPENAI_API_KEY in backend/.env")
    
    # Load nurture state
    nurture_state = store.load(request.instance_id)
    if nurture_state is None:
        raise HTTPException(status_code=404, detail=f"Instance {request.instance_id} not found")
    
    # Get or create experiential session
    if request.session_id not in experiential_sessions:
        exp_engine = ExperientialEngine(
            config=DEFAULT_EXPERIENTIAL_CONFIG,
            nurture_state=nurture_state
        )
        exp_engine.initialize_session(session_id=request.session_id)
        experiential_sessions[request.session_id] = exp_engine
    else:
        exp_engine = experiential_sessions[request.session_id]
        exp_engine.nurture_state = nurture_state  # Update nurture reference
    
    # Get experiential context
    exp_context = exp_engine.get_context_for_prompt(user_input=request.user_input)
    
    # Set the model function on the nurture engine
    engine.set_model_fn(client.generate)
    
    # Get conversation history
    conversation_history = store.get_conversation_history(request.instance_id, limit=10)
    
    # 1. Generate Response
    try:
        response, significance_tag, ctx = engine.generate_response(
            user_input=request.user_input,
            nurture_state=nurture_state,
            conversation_history=conversation_history,
            extra_context=exp_context
        )
        logger.info(f"Generated response length: {len(response)}")
        
        # Fallback for empty responses
        if not response or not response.strip():
            logger.warning(f"Empty response generated for input: {request.user_input[:50]}")
            response = "..." # Minimal acknowledgment
            # Attempt retry or just use fallback? User prompted "Generate minimal acknowledgment"
    except Exception as e:
        logger.error(f"LLM generation error: {str(e)}")
        raise HTTPException(status_code=500, detail=f"LLM error: {str(e)}")
    
    # 2. Schedule Background Update
    # We pass the ID and let the background task reload, or pass the object.
    # To avoid pickling issues or race conditions, reloading in background is safest usually, 
    # but here we might overwrite if high concurrency.
    # Given the constraint, we'll pass the necessary data.
    background_tasks.add_task(
        background_update_interaction,
        instance_id=request.instance_id,
        session_id=request.session_id,
        user_input=request.user_input,
        response=response,
        significance_tag=significance_tag,
        nurture_state_dict=None, # Not used currently as we reload
        exp_engine=exp_engine
    )

    # 3. Return Immediate Response (with PRE-UPDATE state)
    # The UI will see the new message, but the "Inspector" metrics will be from before the update.
    # This is the trade-off for speed requested by the user.
    
    return IntegratedInteractionResponse(
        response=response,
        nurture_state=state_to_response(nurture_state),
        experiential_state=experiential_to_response(exp_engine),
        metadata={
            'nurture': {
                'significance_score': 0.0, # Placeholder
                'was_evaluated': False,
                'phase': nurture_state.phase,
            },
            'experiential': {}, # Placeholder
            'model': request.model_name
        }
    )

@router.get("/experience/context/{session_id}")
async def get_experiential_context(session_id: str):
    """Get the current experiential context string for prompt injection."""
    experiential_sessions = get_experiential_sessions()
    if session_id not in experiential_sessions:
        raise HTTPException(status_code=404, detail=f"Session {session_id} not found")
    
    exp_engine = experiential_sessions[session_id]
    return {
        "session_id": session_id,
        "context": exp_engine.get_context_for_prompt(),
        "summary": exp_engine.get_state_summary()
    }

@router.get("/experience/facts/{session_id}")
async def get_session_facts(session_id: str):
    """Get salient facts from the current session."""
    experiential_sessions = get_experiential_sessions()
    if session_id not in experiential_sessions:
        raise HTTPException(status_code=404, detail=f"Session {session_id} not found")
    
    exp_engine = experiential_sessions[session_id]
    facts = exp_engine.state.working_memory.salient_facts
    
    return {
        "session_id": session_id,
        "facts": [f.to_dict() for f in facts],
        "count": len(facts)
    }

@router.get("/experience/questions/{session_id}")
async def get_session_questions(session_id: str):
    """Get open questions from the current session."""
    experiential_sessions = get_experiential_sessions()
    if session_id not in experiential_sessions:
        raise HTTPException(status_code=404, detail=f"Session {session_id} not found")
    
    exp_engine = experiential_sessions[session_id]
    questions = exp_engine.state.working_memory.open_questions
    
    return {
        "session_id": session_id,
        "questions": [q.to_dict() for q in questions],
        "open_count": len([q for q in questions if not q.resolved]),
        "resolved_count": len([q for q in questions if q.resolved])
    }

@router.get("/experience/commitments/{session_id}")
async def get_session_commitments(session_id: str):
    """Get commitments from the current session."""
    experiential_sessions = get_experiential_sessions()
    if session_id not in experiential_sessions:
        raise HTTPException(status_code=404, detail=f"Session {session_id} not found")
    
    exp_engine = experiential_sessions[session_id]
    commitments = exp_engine.state.working_memory.commitments
    
    return {
        "session_id": session_id,
        "commitments": [c.to_dict() for c in commitments],
        "active_count": len([c for c in commitments if not c.fulfilled]),
        "fulfilled_count": len([c for c in commitments if c.fulfilled])
    }

from typing import Optional
from pydantic import BaseModel

class PulseRequest(BaseModel):
    instance_id: str
    session_id: str
    openai_api_key: Optional[str] = None
    model_name: str = "mistralai/mistral-7b-instruct:free"

@router.post("/experience/pulse")
async def trigger_self_stimulation(request: PulseRequest):
    """
    Trigger a self-stimulation tick (heartbeat).
    Call this periodically when the user is idle.
    """
    experiential_sessions = get_experiential_sessions()
    
    if request.session_id not in experiential_sessions:
        logger.info(f"Session {request.session_id} not found during pulse. Auto-initializing.")
        store = get_store()
        nurture_state = store.load(request.instance_id)
        if nurture_state is not None:
            exp_engine = ExperientialEngine(
                config=DEFAULT_EXPERIENTIAL_CONFIG,
                nurture_state=nurture_state
            )
            exp_engine.initialize_session(session_id=request.session_id)
            experiential_sessions[request.session_id] = exp_engine
        else:
            return {"triggered": False, "reason": "instance_not_found"}
    
    exp_engine = experiential_sessions[request.session_id]
    
    # Get or create LLM Client - use request key, then env key, then existing client
    api_key = request.openai_api_key or ENV_OPENAI_API_KEY
    if api_key:
        client = set_client(request.session_id, api_key)
    else:
        client = get_client(request.session_id)
    
    if not client or not client.is_configured():
        return {"triggered": False, "reason": "no_llm_client"}
        
    # Run Tick
    print(f"DEBUG: Calling run_self_stimulation_tick for {request.session_id}")
    result = await exp_engine.run_self_stimulation_tick(client.generate)
    
    if result:
        triggered_type = result.get('type', 'gated' if result.get('gated') else 'unknown')
        logger.info(f"Self-stimulation triggered for {request.session_id}: {triggered_type}")
        return {"triggered": True, "result": result}
    else:
        return {"triggered": False, "reason": "conditions_not_met"}
