from datetime import datetime
from typing import Tuple
import numpy as np

from ..state import ExperientialState
from .types import SelfStimulationConfig, SelfStimulationState

def should_trigger(
    exp_state: ExperientialState,
    stim_state: SelfStimulationState,
    config: SelfStimulationConfig,
    last_interaction_time: datetime
) -> Tuple[bool, str]:
    """Determine if self-stimulation should trigger."""
    
    now = datetime.now()
    
    # Condition 1: Sufficient idle time
    idle_time = (now - last_interaction_time).total_seconds()
    if idle_time < config.idle_threshold_seconds:
        return False, "user_active"
    
    # Condition 2: Minimum interval between cycles
    if stim_state.last_cycle_time:
        since_last = (now - stim_state.last_cycle_time).total_seconds()
        if since_last < config.min_cycle_interval_seconds:
            return False, "too_soon"
    
    # Condition 3: Haven't exceeded consecutive cycle limit
    if stim_state.current_cycle >= config.max_consecutive_cycles:
        return False, "max_consecutive_reached"
    
    # Condition 4: Haven't exceeded session cycle limit
    if stim_state.total_cycles_this_session >= config.max_cycles_per_session:
        return False, "max_session_reached"
    
    # Condition 5: Have energy budget remaining
    if stim_state.energy_spent >= config.energy_budget_per_session:
        return False, "energy_exhausted"
    
    # Condition 6: Have material to think about
    has_material, material_type = has_thinking_material(exp_state, config)
    if not has_material:
        return False, "no_material"
    
    return True, material_type

def has_thinking_material(
    exp_state: ExperientialState,
    config: SelfStimulationConfig
) -> Tuple[bool, str]:
    """Check if there's something worth thinking about."""
    
    # Priority 1: Unresolved questions
    open_questions = [q for q in exp_state.working_memory.open_questions if not q.resolved]
    if open_questions:
        return True, "open_questions"
    
    # Priority 2: High emotional residue
    if exp_state.conversation_model.emotional_trajectory is not None:
        emotional_magnitude = np.linalg.norm(exp_state.conversation_model.emotional_trajectory)
        if emotional_magnitude > config.emotional_threshold:
            return True, "emotional_residue"
    
    # Priority 3: Unfulfilled commitments approaching concern
    active_commitments = [c for c in exp_state.working_memory.commitments if not c.fulfilled]
    if active_commitments:
        return True, "active_commitments"
    
    # Priority 4: General consolidation (if session has activity)
    icount = exp_state.conversation_model.interaction_count
    if icount >= 0:
        return True, "consolidation"
    
    print(f"No thinking material. Interaction count: {icount}")
    return False, "none"
