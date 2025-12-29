from typing import List, Tuple, Optional
import numpy as np
import logging

logger = logging.getLogger(__name__)

class DriftDetector:
    """
    Detects if self-stimulation is causing character drift.
    """
    
    def __init__(self, baseline_stance: Optional[np.ndarray] = None, threshold: float = 0.2):
        self.baseline_stance = baseline_stance.copy() if baseline_stance is not None else None
        self.threshold = threshold
        self.stance_history: List[np.ndarray] = []
    
    def check_drift(self, current_stance: np.ndarray) -> Tuple[bool, float]:
        """
        Check if current stance has drifted too far from baseline.
        Returns (is_drifting, drift_magnitude).
        """
        if self.baseline_stance is None:
            self.baseline_stance = current_stance.copy()
            return False, 0.0

        # Assuming current_stance is derived or modified? 
        # In current CACA, Experiential doesn't modify Nurture stance directly in the loop,
        # but consolidation might. For now, this is a safeguard against rapid shifts if we were updating it.
        # Or it checks if 'Experiential Stance' (if it existed) drifted.
        # The paper says it checks `nurture_state.N_stance`.
        
        drift = np.linalg.norm(current_stance - self.baseline_stance)
        is_drifting = drift > self.threshold
        
        if is_drifting:
            logger.warning(f"Character drift detected: {drift}")
        
        return is_drifting, drift
    
    def update_baseline(self, new_baseline: np.ndarray):
        """
        Update baseline (e.g., after user interaction confirms stance).
        """
        self.baseline_stance = new_baseline.copy()
    
    def record_stance(self, stance: np.ndarray):
        """
        Record stance for trend analysis.
        """
        self.stance_history.append(stance.copy())
        
        # Keep only recent history
        if len(self.stance_history) > 100:
            self.stance_history = self.stance_history[-100:]
