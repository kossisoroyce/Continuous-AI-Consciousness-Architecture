from datetime import datetime
import os
from fastapi import APIRouter, HTTPException, Depends
from schemas import ApiKeyRequest
from system_config import DEFAULT_NURTURE_CONFIG as DEFAULT_CONFIG
from nurture.llm import set_client, get_client, remove_client, get_ollama_client

# Check for environment API key
ENV_OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")

router = APIRouter()

@router.get("/")
async def root():
    """Root endpoint with API info."""
    return {
        "name": "Nurture Layer API",
        "version": "0.1.0",
        "description": "Runtime Character Formation for AI Systems",
        "endpoints": {
            "instances": "/instances",
            "interact": "/interact",
            "analyze": "/analyze/significance"
        }
    }

@router.get("/health")
async def health():
    """Health check endpoint."""
    return {"status": "healthy", "timestamp": datetime.now().isoformat()}

@router.get("/config")
async def get_config():
    """Get the current configuration."""
    return DEFAULT_CONFIG.to_dict()

@router.post("/api-key")
async def set_api_key(request: ApiKeyRequest):
    """Set OpenAI API key for a session."""
    try:
        client = set_client(request.session_id, request.api_key)
        # Test the key with a simple call
        client.generate("Say 'OK' if you can hear me.", system_prompt="Respond with only 'OK'.")
        return {"status": "success", "message": "API key configured successfully"}
    except Exception as e:
        remove_client(request.session_id)
        raise HTTPException(status_code=400, detail=f"Invalid API key: {str(e)}")

@router.get("/api-key/{session_id}")
async def check_api_key(session_id: str):
    """Check if API key is set for a session or in environment."""
    # If environment variable is set, auto-configure the session client
    if ENV_OPENAI_API_KEY:
        client = get_client(session_id)
        if not client or not client.is_configured():
            set_client(session_id, ENV_OPENAI_API_KEY)
        return {"configured": True, "source": "environment"}
    
    # Otherwise check session-specific client
    client = get_client(session_id)
    return {"configured": client is not None and client.is_configured(), "source": "session"}

@router.delete("/api-key/{session_id}")
async def clear_api_key(session_id: str):
    """Clear API key for a session."""
    remove_client(session_id)
    return {"status": "cleared"}

@router.get("/ollama/status")
async def ollama_status():
    """Check if Ollama is available and list models."""
    try:
        import requests
        response = requests.get("http://localhost:11434/api/tags", timeout=2)
        if response.status_code == 200:
            models = [m["name"] for m in response.json().get("models", [])]
            return {"available": True, "models": models}
    except:
        pass
    return {"available": False, "models": []}
