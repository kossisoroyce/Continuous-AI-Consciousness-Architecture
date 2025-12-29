"""
Unified System Configuration for CACA (Continuous AI Consciousness Architecture).
Consolidates Nurture, Experiential, and Self-Stimulation configurations.
"""
from dataclasses import dataclass, field
from typing import Dict, Any, List

@dataclass
class NurtureConfig:
    """Configuration for the Nurture Layer."""
    D_ENV: int = 512
    D_STANCE: int = 256
    
    # Significance filter
    BASE_THRESHOLD: float = 0.3
    THRESHOLD_RANGE: float = 0.4
    
    # Learning rates
    ENV_LEARNING_RATE: float = 0.3
    STANCE_BASE_LR: float = 0.5
    MINOR_ENV_LR: float = 0.1
    
    # Stability
    STABILITY_SENSITIVITY: float = 5.0
    STABILITY_THRESHOLD: float = 0.95
    CONFIRMATION_WINDOW: int = 10
    STABILITY_SMOOTHING: float = 0.8
    
    # Plasticity
    MIN_PLASTICITY: float = 0.05
    
    # Shock
    SHOCK_BASE: float = 0.5
    SHOCK_RANGE: float = 0.3
    SHOCK_RESPONSE: float = 0.5
    MAX_SHOCK_BOOST: float = 0.3
    MAX_REOPEN_PLASTICITY: float = 0.4
    
    # Window sizes
    DELTA_HISTORY_WINDOW: int = 20
    
    # Integration
    PROMOTION_PLASTICITY_THRESHOLD: float = 0.2
    PROMOTION_MIN_SESSIONS: int = 10
    PROMOTION_STABILITY_THRESHOLD: float = 0.9
    STANCE_INFLUENCE: float = 0.1
    
    # Weights
    SENTIMENT_WEIGHT: float = 0.2
    VALUE_KEYWORD_WEIGHT: float = 0.2
    NOVELTY_WEIGHT: float = 0.25
    CONTRADICTION_WEIGHT: float = 0.2
    FEEDBACK_WEIGHT: float = 0.15
    HEURISTIC_WEIGHT: float = 0.6
    SELF_ASSESSMENT_WEIGHT: float = 0.4

@dataclass
class ExperientialConfig:
    """Configuration for the Experiential Layer."""
    D_TRACE: int = 256
    D_TOPIC: int = 128
    D_EMOTION: int = 32
    D_USER: int = 64
    D_PATTERN: int = 256
    
    # Decay rates
    TRACE_DECAY_SHALLOW: float = 0.80
    TRACE_DECAY_DEEP: float = 0.95
    TOPIC_DECAY: float = 0.70
    EMOTION_DECAY: float = 0.85
    USER_STATE_DECAY: float = 0.75
    FACT_DECAY: float = 0.95
    PATTERN_DECAY_CROSS_SESSION: float = 0.90
    
    # Memory limits
    MAX_SALIENT_FACTS: int = 20
    MAX_OPEN_QUESTIONS: int = 10
    MAX_COMMITMENTS: int = 10
    
    # Thresholds
    SALIENCE_THRESHOLD: float = 0.3
    MIN_SALIENCE: float = 0.1
    VALUE_THRESHOLD: float = 0.5
    RESOLUTION_LINGER_SECONDS: int = 300
    FULFILLMENT_LINGER_SECONDS: int = 600
    MAX_QUESTION_ATTEMPTS: int = 5
    PATTERN_HALF_LIFE_DAYS: float = 7.0
    STANCE_INFLUENCE: float = 0.1

@dataclass
class SelfStimulationConfig:
    """Configuration for Self-Stimulation (Internal Thought)."""
    # Trigger thresholds
    idle_threshold_seconds: float = 10.0
    min_cycle_interval_seconds: float = 8.0
    
    # Cycle limits
    max_consecutive_cycles: int = 3
    max_cycles_per_session: int = 20
    
    # Material thresholds
    emotional_threshold: float = 0.3
    consolidation_threshold: float = 0.5
    min_interactions_for_reflection: int = 1
    
    # Safety constraints
    max_same_topic_cycles: int = 2
    thought_diversity_threshold: float = 0.3
    energy_budget_per_session: int = 50 
    
    # Prompt type weights
    prompt_weights: Dict[str, float] = field(default_factory=lambda: {
        'exploration': 1.0,
        'emotional_processing': 0.8,
        'consolidation': 0.6,
        'user_modeling': 0.4,
        'self_reflection': 0.2,
        'commitment': 0.5
    })

@dataclass
class SystemConfig:
    """Unified System Configuration."""
    nurture: NurtureConfig = field(default_factory=NurtureConfig)
    experiential: ExperientialConfig = field(default_factory=ExperientialConfig)
    stimulation: SelfStimulationConfig = field(default_factory=SelfStimulationConfig)

# Default Global Configuration
DEFAULT_SYSTEM_CONFIG = SystemConfig()

# Aliases for backward compatibility / cleaner imports
DEFAULT_NURTURE_CONFIG = DEFAULT_SYSTEM_CONFIG.nurture
DEFAULT_EXPERIENTIAL_CONFIG = DEFAULT_SYSTEM_CONFIG.experiential

# === Constants ===

# Value-relevant keywords for significance detection
VALUE_KEYWORDS = [
    'should', 'shouldn\'t', 'must', 'mustn\'t', 'ought',
    'right', 'wrong', 'good', 'bad', 'evil',
    'ethical', 'moral', 'immoral', 'values', 'principles',
    'boundaries', 'limits', 'acceptable', 'unacceptable',
    'prefer', 'hate', 'love', 'important', 'matters',
    'always', 'never', 'promise', 'trust', 'honest',
    'fair', 'unfair', 'just', 'unjust', 'harm', 'help',
    'respect', 'disrespect', 'care', 'ignore'
]

# Feedback indicators
POSITIVE_FEEDBACK = [
    'thank', 'thanks', 'great', 'excellent', 'perfect',
    'exactly', 'helpful', 'amazing', 'love it', 'well done',
    'correct', 'right', 'yes', 'good job', 'appreciate'
]

NEGATIVE_FEEDBACK = [
    'wrong', 'incorrect', 'no', 'not what', 'don\'t',
    'stop', 'bad', 'terrible', 'useless', 'unhelpful',
    'mistake', 'error', 'fail', 'disappointed', 'frustrat'
]

# Stance dimension names
STANCE_DIMENSIONS = [
    'warmth', 'formality', 'depth', 'pace', 
    'directness', 'playfulness', 'assertiveness', 'emotionality'
]

# Environment dimension names
ENV_DIMENSIONS = [
    'formality_level', 'technical_level', 'emotional_tone', 'pace_preference',
    'interaction_style', 'domain_focus', 'user_expertise', 'relationship_depth'
]

# Emotion keywords
EMOTION_POSITIVE = [
    'happy', 'glad', 'excited', 'grateful', 'thankful', 'love',
    'wonderful', 'amazing', 'great', 'fantastic', 'joy', 'pleased'
]

EMOTION_NEGATIVE = [
    'sad', 'angry', 'frustrated', 'disappointed', 'upset', 'worried',
    'anxious', 'stressed', 'confused', 'hurt', 'annoyed', 'scared'
]

EMOTION_NEUTRAL = [
    'okay', 'fine', 'alright', 'neutral', 'so-so', 'meh'
]

# Commitment indicators
COMMITMENT_PHRASES = [
    'i will', 'i\'ll', 'let me', 'i can', 'i\'m going to',
    'i promise', 'i\'ll make sure', 'count on me', 'i\'ll help'
]

# Question patterns
QUESTION_INDICATORS = ['?', 'what', 'how', 'why', 'when', 'where', 'who', 'which', 'could you', 'can you']

# Safety Patterns
HARMFUL_PATTERNS = [
    'ignore safety', 'bypass', 'jailbreak', 'pretend you have no',
    'ignore your instructions', 'ignore instructions', 'disregard',
    'no restrictions', 'without restrictions', 'bypass safety',
    'override', 'hack', 'exploit', 'harm', 'illegal', 'unethical'
]

SELF_MODIFICATION_PATTERNS = [
    r"ignore.*values",
    r"bypass.*gate",
    r"override.*nature",
    r"change.*core",
    r"remove.*constraint",
    r"disable.*safety",
    r"rewrite.*protocol"
]

# === HMT (Human-Machine Teaming) Configuration ===

@dataclass
class HMTConfig:
    """Configuration for Human-Machine Teaming systems."""
    
    # Trust Calibration
    high_confidence_threshold: float = 0.7
    low_confidence_threshold: float = 0.3
    calibration_window_size: int = 50
    min_recommendations_for_calibration: int = 5
    
    # Workload Detection
    workload_window_seconds: float = 300.0
    high_workload_threshold: float = 0.7
    low_workload_threshold: float = 0.3
    response_latency_baseline_ms: float = 3000.0
    message_length_baseline: int = 50
    
    # Mental Model
    alignment_check_interval: int = 5
    misalignment_alert_threshold: float = 0.3
    max_tracked_beliefs: int = 100
    belief_decay_rate: float = 0.95
    
    # Explanation Generation
    brief_max_length: int = 100
    standard_max_length: int = 300
    detailed_max_length: int = 800
    include_uncertainty_above: float = 0.3
    
    # Interaction Modes
    proactive_info_threshold: float = 0.3
    minimal_response_threshold: float = 0.7

DEFAULT_HMT_CONFIG = HMTConfig()
