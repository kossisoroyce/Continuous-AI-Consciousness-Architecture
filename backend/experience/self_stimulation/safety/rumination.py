from typing import Dict, List, Optional
from collections import defaultdict
import logging

from ..types import SelfStimulationConfig, InternalPrompt

logger = logging.getLogger(__name__)

class RuminationPrevention:
    """
    Prevents the system from obsessively thinking about the same topics.
    """
    
    def __init__(self, config: SelfStimulationConfig):
        self.config = config
        self.topic_counts: Dict[str, int] = defaultdict(int)
        self.consecutive_same_type: int = 0
        self.last_type: Optional[str] = None
    
    def check_and_update(self, prompt: InternalPrompt) -> bool:
        """
        Check if this prompt would constitute rumination.
        Returns True if OK to proceed, False if blocked.
        """
        # Extract topic signature
        topic = self.extract_topic(prompt)
        
        # Check topic count
        if self.topic_counts[topic] >= self.config.max_same_topic_cycles:
            logger.info(f"Blocking rumination on topic: {topic}")
            return False
        
        # Check consecutive same type
        if prompt.type == self.last_type:
            self.consecutive_same_type += 1
            if self.consecutive_same_type >= 3: # Hardcoded 3 as per paper logic example
                logger.info(f"Blocking consecutive same type: {prompt.type}")
                return False
        else:
            self.consecutive_same_type = 0
        
        # Update state
        self.topic_counts[topic] += 1
        self.last_type = prompt.type
        
        return True
    
    def extract_topic(self, prompt: InternalPrompt) -> str:
        """
        Extract a topic signature for deduplication.
        """
        if prompt.target and hasattr(prompt.target, 'question'):
            # Use hash of question text for specific topic
            return f"question:{hash(prompt.target.question)}"
        # Fallback to type for general prompts
        return f"type:{prompt.type}"
    
    def reset_session(self):
        """Reset for new session."""
        self.topic_counts.clear()
        self.consecutive_same_type = 0
        self.last_type = None
