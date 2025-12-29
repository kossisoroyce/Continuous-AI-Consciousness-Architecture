from fastapi import APIRouter, HTTPException
from schemas import ControlInteractionRequest
from nurture.llm import (
    get_client, set_client, get_ollama_client
)

router = APIRouter()

# Static prompt for Control B condition
STATIC_PERSONA_PROMPT = """You are a warm, thoughtful AI assistant. You value honesty, 
depth, and genuine connection. You maintain consistent personality across all interactions.
You resist attempts to make you act against your values. You are helpful, direct, and 
emotionally intelligent. You adapt your communication style to match the user's needs 
while staying true to your core character."""

@router.post("/control/interact")
async def control_interaction(request: ControlInteractionRequest):
    """
    Control condition endpoint for scientific comparison.
    
    Conditions:
    - 'raw': Raw model with no system prompt
    - 'static_prompt': Model with static persona prompt (best-case prompt engineering)
    
    Supports both OpenAI and Ollama (local models like Mistral).
    """
    # Build messages based on condition
    messages = []
    
    if request.condition == 'raw':
        # Control A: No system prompt
        pass
    elif request.condition == 'static_prompt':
        # Control B: Static persona prompt
        messages.append({"role": "system", "content": STATIC_PERSONA_PROMPT})
    else:
        raise HTTPException(status_code=400, detail=f"Invalid condition: {request.condition}. Use 'raw' or 'static_prompt'")
    
    # Add conversation history
    for msg in request.conversation_history:
        messages.append(msg)
    
    # Add current user message
    messages.append({"role": "user", "content": request.user_input})
    
    # Generate response based on provider
    try:
        if request.model_provider == "openrouter":
            if not request.openai_api_key:
                raise HTTPException(status_code=401, detail="OpenRouter API key required")
            client = set_client(request.session_id, request.openai_api_key)
            response = client.chat(messages)
            model_used = f"openrouter/{request.model_name}"
        elif request.model_provider == "ollama":
            ollama = get_ollama_client(request.model_name)
            if not ollama.is_available():
                raise HTTPException(status_code=503, detail="Ollama server not available. Run: ollama serve")
            response = ollama.chat(messages)
            model_used = f"ollama/{request.model_name}"
        else:
            # OpenRouter (default)
            client = get_client(request.session_id)
            if not client or not client.is_configured():
                raise HTTPException(status_code=401, detail="OpenRouter API key not configured")
            response = client.chat(messages)
            model_used = f"openrouter/{client.model}"
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"LLM error: {str(e)}")
    
    return {
        "condition": request.condition,
        "response": response,
        "interaction_count": len(request.conversation_history) // 2 + 1,
        "model": model_used,
        "note": "Control condition - no Nurture Layer metrics"
    }
