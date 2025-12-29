import random
import numpy as np
from typing import Optional

from ..state import ExperientialState
from nurture.state import NurtureState
from .types import InternalPrompt, SelfStimulationState, SelfStimulationConfig, PromptType, PROMPT_TEMPLATES

def generate_internal_prompt(
    exp_state: ExperientialState,
    nurture_state: NurtureState,
    stim_state: SelfStimulationState,
    config: SelfStimulationConfig
) -> Optional[InternalPrompt]:
    """Generate an internal prompt based on current state and priorities."""
    
    candidates = []
    
    # Candidate: Exploration
    open_questions = [q for q in exp_state.working_memory.open_questions if not q.resolved]
    for question in open_questions:
        # Simple random choice for now
        template = random.choice(PROMPT_TEMPLATES[PromptType.EXPLORATION])
        prompt = InternalPrompt(
            type=PromptType.EXPLORATION.value,
            content=template.format(question=question.question),
            target=question,
            priority=1.0 # Simplified priority
        )
        candidates.append(prompt)
    
    # Candidate: Emotional processing
    if exp_state.conversation_model.emotional_trajectory is not None:
        emotional_magnitude = np.linalg.norm(exp_state.conversation_model.emotional_trajectory)
        if emotional_magnitude > config.emotional_threshold:
            emotion_desc = "intense emotion" # Placeholder for complex desc
            template = random.choice(PROMPT_TEMPLATES[PromptType.EMOTIONAL_PROCESSING])
            prompt = InternalPrompt(
                type=PromptType.EMOTIONAL_PROCESSING.value,
                content=template.format(emotion=emotion_desc),
                priority=emotional_magnitude * config.prompt_weights['emotional_processing']
            )
            candidates.append(prompt)

    # Candidate: Commitment review
    active_commitments = [c for c in exp_state.working_memory.commitments if not c.fulfilled]
    if active_commitments:
        commitment_list = "; ".join([c.promise for c in active_commitments[:3]])
        template = random.choice(PROMPT_TEMPLATES[PromptType.COMMITMENT_REVIEW])
        prompt = InternalPrompt(
            type=PromptType.COMMITMENT_REVIEW.value,
            content=template.format(commitments=commitment_list),
            target=active_commitments,
            priority=len(active_commitments) * 0.3
        )
        candidates.append(prompt)

    # Candidate: Consolidation
    if exp_state.conversation_model.interaction_count >= 1:
        template = random.choice(PROMPT_TEMPLATES[PromptType.CONSOLIDATION])
        prompt = InternalPrompt(
            type=PromptType.CONSOLIDATION.value,
            content=template,
            priority=config.prompt_weights['consolidation']
        )
        candidates.append(prompt)

    if not candidates:
        return None
        
    # Filter by diversity (Rumination Prevention)
    # Simple check: Don't repeat same type too many times consecutively
    if stim_state.recent_prompt_types:
        last_type = stim_state.recent_prompt_types[-1]
        recent_count = stim_state.recent_prompt_types[-3:].count(last_type)
        if recent_count >= config.max_same_topic_cycles:
             candidates = [c for c in candidates if c.type != last_type]
    
    if not candidates:
        return None

    # Sort and select
    candidates.sort(key=lambda p: p.priority, reverse=True)
    return candidates[0]
