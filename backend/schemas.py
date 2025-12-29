from typing import Dict, Any, List, Optional
from pydantic import BaseModel

# Request Models
class CreateInstanceRequest(BaseModel):
    instance_id: Optional[str] = None

class InteractionRequest(BaseModel):
    instance_id: str
    user_input: str
    assistant_response: Optional[str] = None

class ApiKeyRequest(BaseModel):
    api_key: str
    session_id: str

class InteractionRequestWithSession(BaseModel):
    instance_id: str
    user_input: str
    session_id: str

class ControlInteractionRequest(BaseModel):
    """Request for control condition experiments."""
    user_input: str
    session_id: str
    condition: str  # 'raw', 'static_prompt', or 'nurture'
    conversation_history: List[Dict[str, str]] = []
    model_provider: str = "openai"  # 'openai', 'openrouter', or 'ollama'
    model_name: str = "mistral-7b"  # Model name for OpenRouter/Ollama
    openai_api_key: Optional[str] = None  # OpenRouter API key

class IntegratedInteractionRequest(BaseModel):
    """Request for integrated Nurture + Experience interaction."""
    instance_id: str
    session_id: str
    user_input: str
    openai_api_key: Optional[str] = None
    model_name: str = "mistralai/mistral-7b-instruct:free"

class DebugEvalRequest(BaseModel):
    instance_id: str
    user_input: str
    assistant_response: str
    session_id: str

# Response Models
class StateResponse(BaseModel):
    instance_id: str
    phase: str
    stability: float
    plasticity: float
    interaction_count: int
    significant_count: int
    stance: Dict[str, float]
    environment: Dict[str, Any]
    current_threshold: float
    created_at: str
    last_updated: str

class ExperientialStateResponse(BaseModel):
    session_id: str
    interaction_count: int
    topic_summary: str
    emotion_summary: str
    user_summary: str
    facts_count: int
    open_questions: int
    active_commitments: int
    session_familiarity: float
    total_sessions: int
    context_string: str
    internal_thoughts: List[Dict[str, Any]] = []

class InteractionResponse(BaseModel):
    response: str
    state: StateResponse
    metadata: Dict[str, Any]

class IntegratedInteractionResponse(BaseModel):
    response: str
    nurture_state: StateResponse
    experiential_state: ExperientialStateResponse
    metadata: Dict[str, Any]

class SignificanceResponse(BaseModel):
    score: float
    components: Dict[str, float]
    threshold: float
    would_evaluate: bool
