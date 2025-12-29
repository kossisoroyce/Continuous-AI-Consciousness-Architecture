from dataclasses import dataclass, field
from typing import List, Dict, Any, Optional
from datetime import datetime
from enum import Enum
from system_config import SelfStimulationConfig

@dataclass
class InternalPrompt:
    type: str                    
    content: str                 
    target: Any = None           
    priority: float = 0.0        
    embedding: Any = None 

@dataclass
class SelfStimulationState:
    current_cycle: int = 0
    total_cycles_this_session: int = 0
    last_cycle_time: Optional[datetime] = None
    energy_spent: int = 0
    
    # Tracking for diversity/rumination prevention
    recent_prompt_types: List[str] = field(default_factory=list)
    recent_topics: List[str] = field(default_factory=list)
    
    # Results
    internal_thoughts: List[Dict] = field(default_factory=list)
    resolved_questions: List[str] = field(default_factory=list)

@dataclass
class StimulationCycleResult:
    triggered: bool
    prompt: Optional[InternalPrompt] = None
    thought: Optional[str] = None
    gated: bool = False          
    state_updated: bool = False
    energy_cost: int = 0
    effects: Dict = field(default_factory=dict)

class PromptType(Enum):
    EXPLORATION = "exploration"           
    EMOTIONAL_PROCESSING = "emotional"    
    CONSOLIDATION = "consolidation"       
    USER_MODELING = "user_modeling"       
    SELF_REFLECTION = "self_reflection"   
    COMMITMENT_REVIEW = "commitment"      

PROMPT_TEMPLATES = {
    PromptType.EXPLORATION: [
        "Let me think more carefully about: {question}",
        "I want to explore this question further: {question}",
        "What are the different angles on: {question}",
    ],
    PromptType.EMOTIONAL_PROCESSING: [
        "I notice I'm experiencing {emotion}. Let me reflect on why.",
        "There's emotional residue from recent interactions. What's beneath this {emotion}?",
        "I want to process these feelings of {emotion} before moving on.",
    ],
    PromptType.CONSOLIDATION: [
        "Let me consolidate what I've learned in this session.",
        "What patterns have emerged from recent interactions?",
        "I want to integrate the experiences from this conversation.",
    ],
    PromptType.USER_MODELING: [
        "What have I learned about who I'm talking with?",
        "How can I better understand this person's needs and preferences?",
        "Let me reflect on what matters to this user.",
    ],
    PromptType.SELF_REFLECTION: [
        "How am I developing through these interactions?",
        "What aspects of my character are becoming clearer?",
        "Let me reflect on my own growth in this session.",
    ],
    PromptType.COMMITMENT_REVIEW: [
        "I have commitments to fulfill. Let me review: {commitments}",
        "What do I need to remember to do? {commitments}",
    ],
}
