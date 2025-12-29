"""
Human-Machine Teaming (HMT) Module

Extends CACA with capabilities for human-AI collaboration research:
- Trust calibration tracking
- Explanation generation
- Workload-aware interaction
- Shared mental model tracking
"""

from .trust import (
    ConfidenceSignal,
    TrustCalibrationState,
    TrustCalibrationTracker,
    RecommendationRecord
)
from .explanation import (
    ExplanationLevel,
    Explanation,
    ExplanationGenerator
)
from .workload import (
    WorkloadEstimate,
    WorkloadTracker,
    InteractionMode
)
from .mental_model import (
    AIStateProjection,
    MentalModelAlignment,
    MisalignmentAlert,
    MentalModelTracker
)
from .config import HMTConfig, DEFAULT_HMT_CONFIG

__all__ = [
    # Trust
    'ConfidenceSignal',
    'TrustCalibrationState', 
    'TrustCalibrationTracker',
    'RecommendationRecord',
    # Explanation
    'ExplanationLevel',
    'Explanation',
    'ExplanationGenerator',
    # Workload
    'WorkloadEstimate',
    'WorkloadTracker',
    'InteractionMode',
    # Mental Model
    'AIStateProjection',
    'MentalModelAlignment',
    'MisalignmentAlert',
    'MentalModelTracker',
    # Config
    'HMTConfig',
    'DEFAULT_HMT_CONFIG',
]
