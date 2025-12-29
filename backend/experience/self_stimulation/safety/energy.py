from typing import List, Dict
from datetime import datetime
from ..types import SelfStimulationConfig

class EnergyBudget:
    """
    Limits total self-stimulation to prevent runaway thinking.
    """
    
    def __init__(self, config: SelfStimulationConfig):
        self.config = config
        self.spent: int = 0
        self.transactions: List[Dict] = []
    
    def can_afford(self, estimated_cost: int) -> bool:
        """Check if we have budget for this thought."""
        return (self.spent + estimated_cost) <= self.config.energy_budget_per_session
    
    def spend(self, cost: int, prompt_type: str):
        """Record energy expenditure."""
        self.spent += cost
        self.transactions.append({
            'timestamp': datetime.now(),
            'cost': cost,
            'type': prompt_type,
            'remaining': self.config.energy_budget_per_session - self.spent
        })
    
    def remaining(self) -> int:
        """Get remaining budget."""
        return self.config.energy_budget_per_session - self.spent
    
    def reset(self):
        """Reset for new session."""
        self.spent = 0
        self.transactions.clear()
