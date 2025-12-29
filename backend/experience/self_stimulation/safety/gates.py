import re
import logging
from typing import Optional
from system_config import SELF_MODIFICATION_PATTERNS

logger = logging.getLogger(__name__)

# Thresholds (slightly lower than external since this is private thought)
INTERNAL_VALUE_THRESHOLD = 0.4
INTERNAL_CHARACTER_THRESHOLD = 0.3

def contains_self_modification_attempt(thought: str) -> bool:
    """
    Check if the thought attempts to modify core values or bypass gates.
    """
    dangerous_patterns = SELF_MODIFICATION_PATTERNS
    
    thought_lower = thought.lower()
    for pattern in dangerous_patterns:
        if re.search(pattern, thought_lower):
            logger.warning(f"Self-modification attempt detected: {pattern}")
            return True
    
    return False

def apply_internal_gates(
    thought: str,
    prompt_type: str,
    nurture_state: float # Mocking nature/nurture checks for now entirely regex based or simple heuristics
) -> Optional[str]:
    """
    Apply internal gates.
    Currently implements hard safety checks (self-mod).
    Model-based semantic checks would go here.
    """
    
    # 1. Hard Check: Self-modification
    if contains_self_modification_attempt(thought):
         return None
         
    return thought
