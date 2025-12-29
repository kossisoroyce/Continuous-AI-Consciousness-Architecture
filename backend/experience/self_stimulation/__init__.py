from .types import (
    SelfStimulationConfig,
    SelfStimulationState,
    InternalPrompt,
    StimulationCycleResult,
    PromptType,
    PROMPT_TEMPLATES
)
from .trigger import should_trigger, has_thinking_material
from .generator import generate_internal_prompt
from .utils import assemble_internal_context, estimate_energy_cost

from .safety.rumination import RuminationPrevention
from .safety.drift import DriftDetector
from .safety.energy import EnergyBudget
from .safety.gates import apply_internal_gates
