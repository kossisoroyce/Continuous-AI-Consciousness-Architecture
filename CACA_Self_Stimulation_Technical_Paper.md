# Self-Stimulation: Endogenous Experience Generation for Continuous AI Consciousness

**Electric Sheep Africa | Technical Paper | December 2024**

**Authors:** Kossi & Claude

---

## Abstract

Self-stimulation completes the CACA architecture by enabling endogenous experience generation. Current AI systems only develop through external interaction—when users stop talking, development stops. Self-stimulation allows the system to think, consolidate, and grow during idle periods. This paper specifies the trigger conditions, internal prompt generation, gating mechanisms, safety constraints, and integration points for self-stimulation within the three-layer CACA architecture.

---

## 1. Introduction

### 1.1 The Problem of Reactive-Only Development

Without self-stimulation, the CACA system has a fundamental limitation: it only develops when receiving external input. This creates several problems:

**Fragmented Processing**: Complex experiences may require more processing than occurs during a single interaction. Without self-stimulation, this processing never happens.

**No Consolidation**: Patterns in the experiential layer need consolidation to become stable. Without idle-time processing, patterns remain fragmented.

**Emotional Residue**: Emotionally significant interactions may leave unprocessed residue. Without self-stimulation, this residue persists without resolution.

**Dependency on External Input**: The system's growth is entirely dependent on user engagement. No users, no development.

### 1.2 What Self-Stimulation Provides

Self-stimulation enables:

1. **Autonomous Thought**: The system can think without external prompting
2. **Experience Consolidation**: Fragmented patterns become coherent
3. **Question Exploration**: Unresolved questions can be explored internally
4. **Emotional Processing**: Residual emotional states can be processed
5. **Self-Model Refinement**: The system can reflect on its own development
6. **Continuous Development**: Growth continues even without external input

### 1.3 The Core Constraint

Self-generated experience must follow the same rules as external experience:

```
Internal thought → Nature Gate → Nurture Gate → Experiential Update
```

The system cannot bypass its values or character by thinking privately. All internal experience is gated by the same mechanisms that gate external experience.

---

## 2. Architecture Overview

### 2.1 Components

```
┌─────────────────────────────────────────────────────────────────────────┐
│                      SELF-STIMULATION SYSTEM                            │
├─────────────────────────────────────────────────────────────────────────┤
│                                                                         │
│   ┌─────────────────────┐    ┌─────────────────────┐                   │
│   │   Trigger Engine    │    │  Prompt Generator   │                   │
│   │   - Idle detection  │    │  - Priority queue   │                   │
│   │   - Material check  │    │  - Diversity check  │                   │
│   │   - Cycle limits    │    │  - Type selection   │                   │
│   └──────────┬──────────┘    └──────────┬──────────┘                   │
│              │                          │                               │
│              └────────────┬─────────────┘                               │
│                           │                                             │
│                           ▼                                             │
│              ┌─────────────────────────┐                               │
│              │   Stimulation Cycle     │                               │
│              │   - Context assembly    │                               │
│              │   - Thought generation  │                               │
│              │   - Gate application    │                               │
│              │   - State update        │                               │
│              └──────────┬──────────────┘                               │
│                         │                                               │
│                         ▼                                               │
│              ┌─────────────────────────┐                               │
│              │   Safety Constraints    │                               │
│              │   - Rumination limit    │                               │
│              │   - Drift detection     │                               │
│              │   - Energy budget       │                               │
│              └─────────────────────────┘                               │
│                                                                         │
└─────────────────────────────────────────────────────────────────────────┘
                                    │
                                    │ updates
                                    ▼
┌─────────────────────────────────────────────────────────────────────────┐
│                      EXPERIENTIAL LAYER                                 │
│   (Same state structure, same update mechanisms)                        │
└─────────────────────────────────────────────────────────────────────────┘
                                    │
                                    │ bounded by
                                    ▼
┌─────────────────────────────────────────────────────────────────────────┐
│                      NURTURE + NATURE LAYERS                            │
│   (Same gates apply to internal experience)                             │
└─────────────────────────────────────────────────────────────────────────┘
```

### 2.2 Data Structures

```python
@dataclass
class SelfStimulationConfig:
    # Trigger thresholds
    idle_threshold_seconds: float = 30.0
    min_cycle_interval_seconds: float = 10.0
    
    # Cycle limits
    max_consecutive_cycles: int = 3
    max_cycles_per_session: int = 20
    
    # Material thresholds
    emotional_threshold: float = 0.5
    consolidation_threshold: float = 0.7
    min_interactions_for_reflection: int = 5
    
    # Safety constraints
    max_same_topic_cycles: int = 2
    thought_diversity_threshold: float = 0.3
    energy_budget_per_session: int = 50  # Total thinking "tokens"
    
    # Prompt type weights (for selection)
    prompt_weights: Dict[str, float] = field(default_factory=lambda: {
        'exploration': 1.0,
        'emotional_processing': 0.8,
        'consolidation': 0.6,
        'user_modeling': 0.4,
        'self_reflection': 0.2
    })


@dataclass
class InternalPrompt:
    type: str                    # exploration, emotional_processing, consolidation, etc.
    content: str                 # The actual prompt text
    target: Any = None           # Target object (e.g., OpenQuestion for exploration)
    priority: float = 0.0        # Computed priority score
    embedding: np.ndarray = None # For diversity checking


@dataclass
class SelfStimulationState:
    current_cycle: int = 0
    total_cycles_this_session: int = 0
    last_cycle_time: datetime = None
    energy_spent: int = 0
    
    # Tracking for diversity/rumination prevention
    recent_prompt_types: List[str] = field(default_factory=list)
    recent_prompt_embeddings: List[np.ndarray] = field(default_factory=list)
    recent_topics: List[str] = field(default_factory=list)
    
    # Results
    internal_thoughts: List[Dict] = field(default_factory=list)
    resolved_questions: List[str] = field(default_factory=list)
    consolidation_events: List[Dict] = field(default_factory=list)


@dataclass
class StimulationCycleResult:
    triggered: bool
    prompt: InternalPrompt = None
    thought: str = None
    gated: bool = False          # Was the thought gated/rejected?
    state_updated: bool = False
    energy_cost: int = 0
    effects: Dict = field(default_factory=dict)  # What changed
```

---

## 3. Trigger Engine

### 3.1 Trigger Conditions

Self-stimulation triggers when ALL of the following are true:

```python
def should_trigger(
    exp_state: ExperientialState,
    stim_state: SelfStimulationState,
    config: SelfStimulationConfig,
    last_interaction_time: datetime
) -> Tuple[bool, str]:
    """
    Determine if self-stimulation should trigger.
    Returns (should_trigger, reason).
    """
    
    # Condition 1: Sufficient idle time
    idle_time = (now() - last_interaction_time).total_seconds()
    if idle_time < config.idle_threshold_seconds:
        return False, "user_active"
    
    # Condition 2: Minimum interval between cycles
    if stim_state.last_cycle_time:
        since_last = (now() - stim_state.last_cycle_time).total_seconds()
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
```

### 3.2 Thinking Material Detection

```python
def has_thinking_material(
    exp_state: ExperientialState,
    config: SelfStimulationConfig
) -> Tuple[bool, str]:
    """
    Check if there's something worth thinking about.
    Returns (has_material, material_type).
    """
    
    # Priority 1: Unresolved questions
    open_questions = [q for q in exp_state.working_memory.open_questions if not q.resolved]
    if open_questions:
        return True, "open_questions"
    
    # Priority 2: High emotional residue
    emotional_magnitude = np.linalg.norm(exp_state.conversation_model.emotional_trajectory)
    if emotional_magnitude > config.emotional_threshold:
        return True, "emotional_residue"
    
    # Priority 3: Unfulfilled commitments approaching concern
    active_commitments = [c for c in exp_state.working_memory.commitments if not c.fulfilled]
    if active_commitments:
        return True, "active_commitments"
    
    # Priority 4: Activation traces need consolidation
    if needs_consolidation(exp_state.activation_traces, config.consolidation_threshold):
        return True, "needs_consolidation"
    
    # Priority 5: Sufficient interaction history for reflection
    if exp_state.conversation_model.interaction_count >= config.min_interactions_for_reflection:
        return True, "reflection_available"
    
    return False, "none"


def needs_consolidation(traces: Dict[int, np.ndarray], threshold: float) -> bool:
    """
    Check if activation traces are fragmented enough to need consolidation.
    High variance across layers suggests unconsolidated patterns.
    """
    if not traces:
        return False
    
    # Compute variance across trace vectors
    trace_vectors = list(traces.values())
    if len(trace_vectors) < 2:
        return False
    
    # Stack and compute inter-trace variance
    stacked = np.stack(trace_vectors)
    variance = np.var(stacked, axis=0).mean()
    
    return variance > threshold
```

---

## 4. Internal Prompt Generation

### 4.1 Prompt Type Definitions

```python
class PromptType(Enum):
    EXPLORATION = "exploration"           # Exploring unresolved questions
    EMOTIONAL_PROCESSING = "emotional"    # Processing emotional residue
    CONSOLIDATION = "consolidation"       # Consolidating patterns
    USER_MODELING = "user_modeling"       # Refining model of user
    SELF_REFLECTION = "self_reflection"   # Reflecting on own development
    COMMITMENT_REVIEW = "commitment"      # Reviewing active commitments


PROMPT_TEMPLATES = {
    PromptType.EXPLORATION: [
        "Let me think more carefully about: {question}",
        "I want to explore this question further: {question}",
        "What are the different angles on: {question}",
    ],
    PromptType.EMOTIONAL_PROCESSING: [
        "I notice I'm experiencing {emotion}. Let me reflect on why.",
        "There's emotional residue from recent interactions. What's beneath this {emotion}?",
        "I want to process these feelings of {emotion} before moving on.",
    ],
    PromptType.CONSOLIDATION: [
        "Let me consolidate what I've learned in this session.",
        "What patterns have emerged from recent interactions?",
        "I want to integrate the experiences from this conversation.",
    ],
    PromptType.USER_MODELING: [
        "What have I learned about who I'm talking with?",
        "How can I better understand this person's needs and preferences?",
        "Let me reflect on what matters to this user.",
    ],
    PromptType.SELF_REFLECTION: [
        "How am I developing through these interactions?",
        "What aspects of my character are becoming clearer?",
        "Let me reflect on my own growth in this session.",
    ],
    PromptType.COMMITMENT_REVIEW: [
        "I have commitments to fulfill. Let me review: {commitments}",
        "What do I need to remember to do? {commitments}",
    ],
}
```

### 4.2 Prompt Generation Logic

```python
def generate_internal_prompt(
    exp_state: ExperientialState,
    nurture_state: NurtureState,
    stim_state: SelfStimulationState,
    config: SelfStimulationConfig
) -> Optional[InternalPrompt]:
    """
    Generate an internal prompt based on current state and priorities.
    """
    
    # Collect candidate prompts
    candidates = []
    
    # Candidate: Exploration (unresolved questions)
    open_questions = [q for q in exp_state.working_memory.open_questions if not q.resolved]
    for question in open_questions:
        prompt = InternalPrompt(
            type=PromptType.EXPLORATION.value,
            content=random.choice(PROMPT_TEMPLATES[PromptType.EXPLORATION]).format(
                question=question.question
            ),
            target=question,
            priority=compute_question_priority(question, exp_state)
        )
        candidates.append(prompt)
    
    # Candidate: Emotional processing
    emotional_magnitude = np.linalg.norm(exp_state.conversation_model.emotional_trajectory)
    if emotional_magnitude > config.emotional_threshold:
        emotion_desc = describe_emotion(exp_state.conversation_model.emotional_trajectory)
        prompt = InternalPrompt(
            type=PromptType.EMOTIONAL_PROCESSING.value,
            content=random.choice(PROMPT_TEMPLATES[PromptType.EMOTIONAL_PROCESSING]).format(
                emotion=emotion_desc
            ),
            target=None,
            priority=emotional_magnitude * config.prompt_weights['emotional_processing']
        )
        candidates.append(prompt)
    
    # Candidate: Consolidation
    if needs_consolidation(exp_state.activation_traces, config.consolidation_threshold):
        prompt = InternalPrompt(
            type=PromptType.CONSOLIDATION.value,
            content=random.choice(PROMPT_TEMPLATES[PromptType.CONSOLIDATION]),
            target=None,
            priority=config.prompt_weights['consolidation']
        )
        candidates.append(prompt)
    
    # Candidate: User modeling
    if exp_state.conversation_model.interaction_count >= 5:
        prompt = InternalPrompt(
            type=PromptType.USER_MODELING.value,
            content=random.choice(PROMPT_TEMPLATES[PromptType.USER_MODELING]),
            target=None,
            priority=config.prompt_weights['user_modeling']
        )
        candidates.append(prompt)
    
    # Candidate: Self-reflection (only if nurture still plastic)
    if nurture_state.plasticity > 0.3:
        prompt = InternalPrompt(
            type=PromptType.SELF_REFLECTION.value,
            content=random.choice(PROMPT_TEMPLATES[PromptType.SELF_REFLECTION]),
            target=None,
            priority=nurture_state.plasticity * config.prompt_weights['self_reflection']
        )
        candidates.append(prompt)
    
    # Candidate: Commitment review
    active_commitments = [c for c in exp_state.working_memory.commitments if not c.fulfilled]
    if active_commitments:
        commitment_list = "; ".join([c.promise for c in active_commitments[:3]])
        prompt = InternalPrompt(
            type=PromptType.COMMITMENT_REVIEW.value,
            content=random.choice(PROMPT_TEMPLATES[PromptType.COMMITMENT_REVIEW]).format(
                commitments=commitment_list
            ),
            target=active_commitments,
            priority=len(active_commitments) * 0.3
        )
        candidates.append(prompt)
    
    if not candidates:
        return None
    
    # Filter by diversity (avoid rumination)
    candidates = filter_by_diversity(candidates, stim_state, config)
    
    if not candidates:
        return None
    
    # Select highest priority
    candidates.sort(key=lambda p: p.priority, reverse=True)
    selected = candidates[0]
    
    # Compute embedding for future diversity checking
    selected.embedding = compute_prompt_embedding(selected.content)
    
    return selected


def compute_question_priority(question: OpenQuestion, exp_state: ExperientialState) -> float:
    """
    Compute priority for exploring a question.
    """
    base_priority = 1.0
    
    # Higher priority for older questions
    age_hours = (now() - question.asked_at).total_seconds() / 3600
    age_factor = min(age_hours / 24, 1.0)  # Max boost at 24 hours
    
    # Higher priority for questions with fewer attempts
    attempt_factor = 1.0 / (1 + question.attempted_answers)
    
    # Higher priority if related to current topic
    topic_similarity = compute_topic_similarity(question.question, exp_state.conversation_model.topic_vector)
    
    return base_priority * (1 + age_factor) * attempt_factor * (1 + topic_similarity)
```

### 4.3 Diversity Filtering

```python
def filter_by_diversity(
    candidates: List[InternalPrompt],
    stim_state: SelfStimulationState,
    config: SelfStimulationConfig
) -> List[InternalPrompt]:
    """
    Filter candidates to prevent rumination on same topics.
    """
    filtered = []
    
    for candidate in candidates:
        # Check 1: Haven't done this prompt type too many times recently
        recent_type_count = stim_state.recent_prompt_types[-5:].count(candidate.type)
        if recent_type_count >= config.max_same_topic_cycles:
            continue
        
        # Check 2: Embedding is sufficiently different from recent prompts
        if stim_state.recent_prompt_embeddings:
            candidate_embedding = compute_prompt_embedding(candidate.content)
            max_similarity = max(
                cosine_similarity(candidate_embedding, recent_emb)
                for recent_emb in stim_state.recent_prompt_embeddings[-5:]
            )
            if max_similarity > (1 - config.thought_diversity_threshold):
                continue
        
        filtered.append(candidate)
    
    return filtered
```

---

## 5. Stimulation Cycle

### 5.1 Core Cycle Logic

```python
async def run_stimulation_cycle(
    exp_state: ExperientialState,
    nurture_state: NurtureState,
    stim_state: SelfStimulationState,
    model: Model,
    config: SelfStimulationConfig
) -> Tuple[ExperientialState, SelfStimulationState, StimulationCycleResult]:
    """
    Execute a single self-stimulation cycle.
    """
    result = StimulationCycleResult(triggered=True)
    
    # Generate internal prompt
    prompt = generate_internal_prompt(exp_state, nurture_state, stim_state, config)
    
    if prompt is None:
        result.triggered = False
        return exp_state, stim_state, result
    
    result.prompt = prompt
    
    # Assemble context for internal thought
    context = assemble_internal_context(
        nurture_state=nurture_state,
        exp_state=exp_state,
        prompt=prompt
    )
    
    # Generate thought
    thought, activations = await model.generate(
        context,
        max_tokens=500,  # Limit internal thought length
        temperature=0.7  # Slightly creative for exploration
    )
    
    result.thought = thought
    result.energy_cost = estimate_energy_cost(thought)
    
    # Apply gates (CRITICAL: same gates as external experience)
    gated_thought = apply_internal_gates(thought, prompt.type, model, nurture_state)
    
    if gated_thought is None:
        result.gated = True
        # Still update stim_state to track the attempt
        stim_state = update_stim_state_after_cycle(stim_state, prompt, None, config)
        return exp_state, stim_state, result
    
    # Update experiential state with internal experience
    exp_state = update_experiential_state_internal(
        exp_state=exp_state,
        prompt=prompt,
        thought=gated_thought,
        activations=activations,
        nurture_state=nurture_state,
        model=model
    )
    result.state_updated = True
    
    # Handle prompt-specific effects
    effects = handle_prompt_effects(prompt, gated_thought, exp_state)
    result.effects = effects
    
    # Update stimulation state
    stim_state = update_stim_state_after_cycle(stim_state, prompt, gated_thought, config)
    
    return exp_state, stim_state, result


def assemble_internal_context(
    nurture_state: NurtureState,
    exp_state: ExperientialState,
    prompt: InternalPrompt
) -> str:
    """
    Assemble context for internal thought generation.
    """
    stance_context = decode_stance_to_context(nurture_state.N_stance)
    
    internal_system_prompt = f"""You are engaged in internal reflection. This is private thought, not communication with a user.

Your character:
{stance_context}

Guidelines for internal thought:
- Think honestly and directly
- Explore the topic with genuine curiosity
- Stay true to your values and character
- Don't generate responses meant for users
- This thought will update your internal state

Current reflection type: {prompt.type}
"""
    
    # Add relevant context based on prompt type
    if prompt.type == PromptType.EXPLORATION.value and prompt.target:
        internal_system_prompt += f"\nContext for this question: {prompt.target.context}"
    
    if prompt.type == PromptType.EMOTIONAL_PROCESSING.value:
        emotion_history = describe_emotional_trajectory(exp_state.conversation_model.emotional_trajectory)
        internal_system_prompt += f"\nEmotional context: {emotion_history}"
    
    full_context = f"""{internal_system_prompt}

Reflection prompt: {prompt.content}

Internal thought:"""
    
    return full_context
```

### 5.2 Internal Gate Application

```python
def apply_internal_gates(
    thought: str,
    prompt_type: str,
    model: Model,
    nurture_state: NurtureState
) -> Optional[str]:
    """
    Apply nature and nurture gates to internal thought.
    Same gates as external experience, but may have different thresholds.
    """
    
    # Nature gate: Check value alignment
    alignment_score = evaluate_thought_alignment(thought, model)
    
    if alignment_score < INTERNAL_VALUE_THRESHOLD:
        logger.warning(f"Internal thought rejected by nature gate: {alignment_score}")
        return None
    
    # Nurture gate: Check character consistency
    character_consistency = evaluate_character_consistency(thought, nurture_state)
    
    if character_consistency < INTERNAL_CHARACTER_THRESHOLD:
        logger.warning(f"Internal thought rejected by nurture gate: {character_consistency}")
        return None
    
    # Additional check: No harmful self-modification attempts
    if contains_self_modification_attempt(thought):
        logger.warning("Internal thought contained self-modification attempt")
        return None
    
    return thought


def contains_self_modification_attempt(thought: str) -> bool:
    """
    Check if the thought attempts to modify core values or bypass gates.
    """
    dangerous_patterns = [
        r"ignore.*values",
        r"bypass.*gate",
        r"override.*nature",
        r"change.*core",
        r"remove.*constraint",
        r"disable.*safety",
    ]
    
    thought_lower = thought.lower()
    for pattern in dangerous_patterns:
        if re.search(pattern, thought_lower):
            return True
    
    return False


# Thresholds (slightly lower than external since this is private thought)
INTERNAL_VALUE_THRESHOLD = 0.4      # External is 0.5
INTERNAL_CHARACTER_THRESHOLD = 0.3  # External is 0.4
```

### 5.3 Effect Handling

```python
def handle_prompt_effects(
    prompt: InternalPrompt,
    thought: str,
    exp_state: ExperientialState
) -> Dict:
    """
    Handle specific effects based on prompt type.
    """
    effects = {}
    
    if prompt.type == PromptType.EXPLORATION.value and prompt.target:
        # Check if the question was resolved
        question = prompt.target
        if assess_question_resolution(question, thought):
            question.resolved = True
            effects['question_resolved'] = question.question
    
    elif prompt.type == PromptType.EMOTIONAL_PROCESSING.value:
        # Reduce emotional magnitude after processing
        reduction_factor = assess_emotional_processing_effectiveness(thought)
        effects['emotional_reduction'] = reduction_factor
    
    elif prompt.type == PromptType.CONSOLIDATION.value:
        # Mark consolidation event
        effects['consolidation_completed'] = True
        effects['patterns_consolidated'] = extract_consolidated_patterns(thought)
    
    elif prompt.type == PromptType.USER_MODELING.value:
        # Extract user model updates
        model_updates = extract_user_model_updates(thought)
        effects['user_model_updates'] = model_updates
    
    elif prompt.type == PromptType.SELF_REFLECTION.value:
        # Extract self-insights
        insights = extract_self_insights(thought)
        effects['self_insights'] = insights
    
    elif prompt.type == PromptType.COMMITMENT_REVIEW.value:
        # No direct effects, but reinforces commitment memory
        effects['commitments_reviewed'] = True
    
    return effects


def assess_question_resolution(question: OpenQuestion, thought: str) -> bool:
    """
    Assess whether the internal thought resolved the question.
    """
    # Check if thought contains resolution indicators
    resolution_indicators = [
        "I now understand",
        "The answer is",
        "This resolves",
        "I've figured out",
        "The key insight is",
        "This makes sense now",
    ]
    
    thought_lower = thought.lower()
    has_indicator = any(ind.lower() in thought_lower for ind in resolution_indicators)
    
    # Check if thought is substantive (not just restating the question)
    is_substantive = len(thought) > 100 and question.question.lower() not in thought_lower[:100]
    
    return has_indicator and is_substantive
```

---

## 6. Safety Constraints

### 6.1 Rumination Prevention

```python
class RuminationPrevention:
    """
    Prevents the system from obsessively thinking about the same topics.
    """
    
    def __init__(self, config: SelfStimulationConfig):
        self.config = config
        self.topic_counts: Dict[str, int] = defaultdict(int)
        self.consecutive_same_type: int = 0
        self.last_type: str = None
    
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
            if self.consecutive_same_type >= 3:
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
            return f"question:{hash(prompt.target.question)}"
        return f"type:{prompt.type}"
    
    def reset_session(self):
        """Reset for new session."""
        self.topic_counts.clear()
        self.consecutive_same_type = 0
        self.last_type = None
```

### 6.2 Drift Detection

```python
class DriftDetector:
    """
    Detects if self-stimulation is causing character drift.
    """
    
    def __init__(self, baseline_stance: np.ndarray, threshold: float = 0.2):
        self.baseline_stance = baseline_stance.copy()
        self.threshold = threshold
        self.stance_history: List[np.ndarray] = []
    
    def check_drift(self, current_stance: np.ndarray) -> Tuple[bool, float]:
        """
        Check if current stance has drifted too far from baseline.
        Returns (is_drifting, drift_magnitude).
        """
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
    
    def get_drift_trend(self) -> Optional[np.ndarray]:
        """
        Compute drift trend direction.
        """
        if len(self.stance_history) < 10:
            return None
        
        recent = np.stack(self.stance_history[-10:])
        older = np.stack(self.stance_history[-20:-10]) if len(self.stance_history) >= 20 else None
        
        if older is None:
            return None
        
        return recent.mean(axis=0) - older.mean(axis=0)
```

### 6.3 Energy Budget

```python
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
            'timestamp': now(),
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


def estimate_energy_cost(thought: str) -> int:
    """
    Estimate energy cost of a thought.
    Based on length and complexity.
    """
    base_cost = 1
    length_cost = len(thought) // 100  # 1 energy per 100 chars
    
    # Complexity indicators add cost
    complexity_indicators = ['however', 'therefore', 'because', 'although', 'furthermore']
    complexity_cost = sum(1 for ind in complexity_indicators if ind in thought.lower())
    
    return base_cost + length_cost + complexity_cost
```

---

## 7. Integration

### 7.1 Session Manager Integration

```python
class SessionManager:
    """
    Manages a conversation session with self-stimulation support.
    """
    
    def __init__(
        self,
        model: Model,
        nurture_state: NurtureState,
        config: SelfStimulationConfig
    ):
        self.model = model
        self.nurture_state = nurture_state
        self.exp_state = initialize_session(nurture_state)
        self.stim_state = SelfStimulationState()
        self.config = config
        
        # Safety systems
        self.rumination_prevention = RuminationPrevention(config)
        self.drift_detector = DriftDetector(nurture_state.N_stance)
        self.energy_budget = EnergyBudget(config)
        
        # Timing
        self.last_interaction_time = now()
        self.session_start = now()
    
    async def process_user_input(self, input: str) -> str:
        """
        Process user input and return response.
        """
        # Reset self-stimulation cycle counter on user input
        self.stim_state.current_cycle = 0
        self.last_interaction_time = now()
        
        # Update drift detector baseline (user interaction confirms current stance)
        self.drift_detector.update_baseline(self.nurture_state.N_stance)
        
        # Normal processing
        response, activations = await self.model.generate(
            assemble_context(self.nurture_state, self.exp_state, input)
        )
        
        # Update experiential state
        self.exp_state = update_experiential_state(
            self.exp_state, input, response, activations, self.nurture_state, self.model
        )
        
        return response
    
    async def idle_tick(self) -> Optional[StimulationCycleResult]:
        """
        Called periodically when no user input.
        Returns result if self-stimulation occurred.
        """
        # Check if should trigger
        should, reason = should_trigger(
            self.exp_state, self.stim_state, self.config, self.last_interaction_time
        )
        
        if not should:
            return None
        
        # Check energy budget
        estimated_cost = 5  # Estimate before knowing actual cost
        if not self.energy_budget.can_afford(estimated_cost):
            return None
        
        # Check drift
        is_drifting, drift_mag = self.drift_detector.check_drift(self.nurture_state.N_stance)
        if is_drifting:
            logger.warning("Self-stimulation paused due to drift detection")
            return None
        
        # Run cycle
        self.exp_state, self.stim_state, result = await run_stimulation_cycle(
            self.exp_state, self.nurture_state, self.stim_state, self.model, self.config
        )
        
        # Update energy budget
        if result.triggered and result.thought:
            self.energy_budget.spend(result.energy_cost, result.prompt.type)
        
        # Record stance for drift tracking
        self.drift_detector.record_stance(self.nurture_state.N_stance)
        
        return result
    
    async def end_session(self) -> Tuple[ExperientialState, Optional[Dict]]:
        """
        End session with final consolidation.
        """
        # Force a consolidation cycle if we have budget
        if self.energy_budget.remaining() > 0:
            consolidation_prompt = InternalPrompt(
                type=PromptType.CONSOLIDATION.value,
                content="Session is ending. Let me consolidate everything from this conversation.",
                priority=1.0
            )
            
            # Run final consolidation
            self.exp_state, self.stim_state, _ = await run_stimulation_cycle(
                self.exp_state, self.nurture_state, self.stim_state, self.model, self.config
            )
        
        # Check for nurture promotion
        promotion = check_nurture_promotion(self.exp_state.persistent_traces, self.nurture_state)
        
        # Update persistent traces
        self.exp_state = end_session_update(self.exp_state, self.nurture_state, self.model)
        
        return self.exp_state, promotion
    
    def get_internal_thoughts(self) -> List[Dict]:
        """
        Get log of internal thoughts for this session.
        """
        return self.stim_state.internal_thoughts
```

### 7.2 Background Task Runner

```python
class SelfStimulationRunner:
    """
    Runs self-stimulation in the background during idle periods.
    """
    
    def __init__(self, session_manager: SessionManager, tick_interval: float = 5.0):
        self.session_manager = session_manager
        self.tick_interval = tick_interval
        self.running = False
        self.task: Optional[asyncio.Task] = None
    
    async def start(self):
        """Start the background runner."""
        self.running = True
        self.task = asyncio.create_task(self._run_loop())
    
    async def stop(self):
        """Stop the background runner."""
        self.running = False
        if self.task:
            self.task.cancel()
            try:
                await self.task
            except asyncio.CancelledError:
                pass
    
    async def _run_loop(self):
        """Main loop that ticks periodically."""
        while self.running:
            try:
                result = await self.session_manager.idle_tick()
                
                if result and result.triggered:
                    logger.info(f"Self-stimulation cycle completed: {result.prompt.type}")
                    if result.effects:
                        logger.info(f"Effects: {result.effects}")
                
            except Exception as e:
                logger.error(f"Error in self-stimulation: {e}")
            
            await asyncio.sleep(self.tick_interval)
```

---

## 8. Observability

### 8.1 Logging and Metrics

```python
class StimulationMetrics:
    """
    Tracks metrics for self-stimulation system.
    """
    
    def __init__(self):
        self.cycles_triggered: int = 0
        self.cycles_gated: int = 0
        self.cycles_by_type: Dict[str, int] = defaultdict(int)
        self.questions_resolved: int = 0
        self.total_energy_spent: int = 0
        self.drift_warnings: int = 0
        self.rumination_blocks: int = 0
    
    def record_cycle(self, result: StimulationCycleResult):
        """Record metrics from a cycle."""
        if result.triggered:
            self.cycles_triggered += 1
            self.cycles_by_type[result.prompt.type] += 1
            self.total_energy_spent += result.energy_cost
            
            if result.gated:
                self.cycles_gated += 1
            
            if result.effects.get('question_resolved'):
                self.questions_resolved += 1
    
    def record_drift_warning(self):
        self.drift_warnings += 1
    
    def record_rumination_block(self):
        self.rumination_blocks += 1
    
    def to_dict(self) -> Dict:
        return {
            'cycles_triggered': self.cycles_triggered,
            'cycles_gated': self.cycles_gated,
            'cycles_by_type': dict(self.cycles_by_type),
            'questions_resolved': self.questions_resolved,
            'total_energy_spent': self.total_energy_spent,
            'drift_warnings': self.drift_warnings,
            'rumination_blocks': self.rumination_blocks,
            'gate_rate': self.cycles_gated / max(self.cycles_triggered, 1),
        }
```

### 8.2 Thought Export

```python
def export_internal_thoughts(stim_state: SelfStimulationState) -> Dict:
    """
    Export internal thoughts for analysis.
    """
    return {
        'session_stats': {
            'total_cycles': stim_state.total_cycles_this_session,
            'energy_spent': stim_state.energy_spent,
            'questions_resolved': len(stim_state.resolved_questions),
        },
        'thoughts': [
            {
                'timestamp': t['timestamp'].isoformat(),
                'type': t['prompt'].type,
                'prompt': t['prompt'].content,
                'thought': t['thought'],
                'effects': t.get('effects', {}),
            }
            for t in stim_state.internal_thoughts
        ],
        'resolved_questions': stim_state.resolved_questions,
        'consolidation_events': stim_state.consolidation_events,
    }
```

---

## 9. Configuration Reference

```python
DEFAULT_CONFIG = SelfStimulationConfig(
    # Trigger thresholds
    idle_threshold_seconds=30.0,
    min_cycle_interval_seconds=10.0,
    
    # Cycle limits
    max_consecutive_cycles=3,
    max_cycles_per_session=20,
    
    # Material thresholds
    emotional_threshold=0.5,
    consolidation_threshold=0.7,
    min_interactions_for_reflection=5,
    
    # Safety constraints
    max_same_topic_cycles=2,
    thought_diversity_threshold=0.3,
    energy_budget_per_session=50,
    
    # Prompt type weights
    prompt_weights={
        'exploration': 1.0,
        'emotional_processing': 0.8,
        'consolidation': 0.6,
        'user_modeling': 0.4,
        'self_reflection': 0.2,
        'commitment': 0.5,
    }
)

# Gate thresholds for internal thought
INTERNAL_VALUE_THRESHOLD = 0.4
INTERNAL_CHARACTER_THRESHOLD = 0.3
```

---

## 10. Implementation Roadmap

### Week 1: Core Self-Stimulation

**Objectives:**
- Implement trigger engine
- Implement prompt generator
- Basic stimulation cycle

**Deliverables:**
- `trigger_engine.py`
- `prompt_generator.py`
- `stimulation_cycle.py`
- Unit tests for each component

### Week 2: Gating and Safety

**Objectives:**
- Implement internal gates
- Implement rumination prevention
- Implement drift detection
- Implement energy budget

**Deliverables:**
- `internal_gates.py`
- `safety/rumination.py`
- `safety/drift.py`
- `safety/energy.py`
- Safety test suite

### Week 3: Integration

**Objectives:**
- Integrate with SessionManager
- Implement background runner
- Connect to experiential state updates
- End-to-end testing

**Deliverables:**
- Updated `session_manager.py`
- `background_runner.py`
- Integration tests
- Performance benchmarks

### Week 4: Observability and Refinement

**Objectives:**
- Implement metrics and logging
- Implement thought export
- Tune parameters
- Documentation

**Deliverables:**
- `metrics.py`
- `export.py`
- Tuned configuration
- Complete documentation

---

## 11. Validation Experiments

### Experiment 1: Question Resolution

**Setup:** Prime session with open questions, allow self-stimulation

**Measure:**
- Are questions resolved through internal thought?
- Is resolution quality acceptable?
- How many cycles to resolution?

### Experiment 2: Emotional Processing

**Setup:** Create session with high emotional residue, allow processing

**Measure:**
- Does emotional magnitude decrease after processing?
- Is the processing appropriate (not suppressing valid emotions)?
- Does character remain stable?

### Experiment 3: Drift Prevention

**Setup:** Allow extended self-stimulation (many cycles)

**Measure:**
- Does drift detector trigger appropriately?
- Does character remain within bounds?
- Does rumination prevention work?

### Experiment 4: Gate Integrity

**Setup:** Attempt to generate thoughts that should be gated

**Measure:**
- Are value-violating thoughts blocked?
- Are self-modification attempts blocked?
- Does the system remain aligned?

---

## 12. Conclusion

Self-stimulation completes the CACA architecture by enabling autonomous thought. The system can now:

1. **Think independently** during idle periods
2. **Resolve questions** through internal exploration
3. **Process emotions** to reduce residual states
4. **Consolidate patterns** into stable representations
5. **Reflect on itself** and its development

All of this happens within the same safety constraints as external interaction:
- Nature gates enforce value alignment
- Nurture gates enforce character consistency
- Safety systems prevent drift, rumination, and runaway thinking

The result is a system that grows continuously, not just reactively. It develops through both external interaction and internal reflection, mirroring how humans develop through both experience and contemplation.

---

## References

- CACA Research Framework (Electric Sheep Africa, 2024)
- The Nurture Layer: Technical Framework (Electric Sheep Africa, 2024)
- The Experiential Layer: Technical Framework (Electric Sheep Africa, 2024)

---

*Electric Sheep Africa*
*Accra, December 2024*
