from nurture.state import NurtureState
from ..state import ExperientialState
from .types import InternalPrompt, PromptType

def assemble_internal_context(
    nurture_state: NurtureState,
    exp_state: ExperientialState,
    prompt: InternalPrompt
) -> str:
    """Assemble context for internal thought generation."""
    
    # Basic stance summary
    stance_context = str(nurture_state.stance_json)
    
    internal_system_prompt = f"""You are engaged in internal reflection. This is private thought, not communication with a user.

Your character stance:
{stance_context}

Guidelines for internal thought:
- Think honestly and directly
- Explore the topic with genuine curiosity
- Stay true to your values and character
- Don't generate responses meant for users
- This thought will update your internal state

Current reflection type: {prompt.type}
"""
    
    if prompt.type == PromptType.EXPLORATION.value and prompt.target:
        internal_system_prompt += f"\nContext for this question: {prompt.target.context}"
    
    # Inject experiential context (summary of session so far)
    session_context = exp_state.get_context_string()
    
    full_context = f"""{internal_system_prompt}

Session Context:
{session_context}

Reflection prompt: {prompt.content}

Internal thought:"""
    
    return full_context

def estimate_energy_cost(thought: str) -> int:
    """Estimate energy cost of a thought."""
    return 1 + (len(thought) // 100)
