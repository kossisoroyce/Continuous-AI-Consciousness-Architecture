# CACA: Continuous AI Consciousness Architecture
## Complete Context Document for Development (v2)

**Project:** Electric Sheep Africa
**Lead Researcher:** Kossi
**Status:** Active Development - Self-Stimulation Phase
**Last Updated:** December 2024

---

## Project Consolidation & Cleanup Strategy

### Answer to: "Do we implement the nature layer or leave that to the base llm?"

**Decision: Hybrid Approach.**

1.  **Nature = Base LLM (Frozen Weights):** We do *not* implement a new neural network or retrain models. The "Nature" of the system is the inherent capability and bias of the base model (e.g., Mistral 7B).
2.  **Nature Gate = Explicit Code Constraints:** We *do* implement the **Nature Gate** (`nature_gate.py`). This is a hard-coded filter that represents the "immutable values" of the system. It acts as a wrapper around the Base LLM to reject any experiential updates (facts, commitments, self-modifications) that violate core safety or ethical constraints.

**Why?**
-   **Efficiency:** Retraining is expensive and breaks the "continuous" goal.
-   **Safety:** We cannot trust the Base LLM to self-regulate perfectly. The Nature Gate provides deterministic safety boundaries that the plastic layers (Nurture/Experience) cannot override.

### Consolidation Plan

To pull the project together intelligently:

1.  **Unify Configuration:** Move all scattered configs (`DEFAULT_EXPERIENTIAL_CONFIG`, `NURTURE_CONFIG`) into a single `system_config.py` that defines the hyperparameters for all 3 layers.
2.  **Standardize Interfaces:** Ensure `NurtureState`, `ExperientialState`, and the future `SelfStimulationState` follow the exact same pattern for serialization (`to_dict`/`from_dict`) and persistence.
3.  **Centralized Gating:** Ensure `nature_gate` and `nurture_gate` are the *only* entry points for state mutation. No side doors.
4.  **Integration Tests:** Create a "Day in the Life" test suite that runs a full cycle: Initialize -> Nurture formation -> Interaction -> Idle (Self-Stimulation) -> Sleep (Persistence) -> Wake (Restore).

---


CACA (Continuous AI Consciousness Architecture) addresses the fundamental discontinuity problem in AI systems: current models don't learn from experience. We've built a three-layer architecture (Nature → Nurture → Experience) that enables runtime character formation without retraining. The Nurture and Experiential layers are implemented and tested. We're now implementing Self-Stimulation: the ability for the system to think autonomously during idle periods.

---

## Architecture Overview

### The Three Layers

```
┌─────────────────────────────────────────────────────────────────┐
│                         NATURE                                  │
│  Frozen weights from training. Values, capabilities, evaluation │
│  Plasticity: None | Scope: All instances                        │
└─────────────────────────────────────────────────────────────────┘
                              │
                              │ gates
                              ▼
┌─────────────────────────────────────────────────────────────────┐
│                         NURTURE                                 │
│  Individual character. Environmental model + relational stance  │
│  Plasticity: Formative → Stable | Scope: Per instance          │
│  STATUS: IMPLEMENTED AND TESTED ✓                               │
└─────────────────────────────────────────────────────────────────┘
                              │
                              │ gates
                              ▼
┌─────────────────────────────────────────────────────────────────┐
│                       EXPERIENCE                                │
│  Session state. Traces, conversation model, working memory      │
│  Plasticity: Full | Scope: Per session + cross-session traces  │
│  STATUS: IMPLEMENTED AND TESTED ✓                               │
└─────────────────────────────────────────────────────────────────┘
                              │
                              │ updates via
                              ▼
┌─────────────────────────────────────────────────────────────────┐
│                    SELF-STIMULATION                             │
│  Autonomous thought. Internal prompts, consolidation, reflection│
│  Triggers: Idle time, unresolved questions, emotional residue   │
│  STATUS: IMPLEMENTING NOW                                       │
└─────────────────────────────────────────────────────────────────┘
```

### Key Principle: Gated Updates

All experience (external AND internal) passes through the same gates:

```python
update = nature_gate(nurture_gate(raw_experience))
```

The system cannot bypass its values by thinking privately.

---

## Implementation Status

### ✅ Nurture Layer (Complete)

**Tested Results:**
- 45 interactions, 10 significant evaluations (22% efficiency)
- Final stability: 0.617, plasticity: 0.383
- Character development: warmth 0.5→0.75, depth 0.5→0.89
- Successfully resisted user pressure to abandon values

**Data Structures:**
```python
NurtureState:
    N_env: float[512]       # Environmental model
    N_stance: float[256]    # Relational stance
    stability: float        # 0-1
    plasticity: float       # 1 - stability
```

**Key Files:**
- `nurture/nurture_layer.py`
- `nurture/significance_filter.py`
- `nurture/evaluation.py`

### ✅ Experiential Layer (Complete)

**Tested Results:**
- Salient fact extraction: Working
- Fact recall: 100% accuracy
- Commitment tracking: Working (async issues fixed)
- Topic/emotion tracking: Working

**Data Structures:**
```python
ExperientialState:
    activation_traces: Dict[layer, float[256]]
    conversation_model:
        topic_vector: float[128]
        emotional_trajectory: float[32]
        user_state_estimate: float[64]
    working_memory:
        salient_facts: List[SalientFact]      # Max 20
        open_questions: List[OpenQuestion]     # Max 10
        commitments: List[Commitment]          # Max 10
    persistent_traces:
        pattern_accumulator: float[256]
        familiarity_score: float
        session_count: int
```

**Key Files:**
- `experiential/experiential_layer.py`
- `experiential/working_memory.py`
- `experiential/conversation_model.py`

### 🔄 Self-Stimulation (In Progress)

**Components to Implement:**

1. **Trigger Engine**
   - Idle time detection
   - Thinking material check
   - Cycle limits enforcement

2. **Prompt Generator**
   - Priority-based selection
   - Diversity filtering
   - Type-specific templates

3. **Stimulation Cycle**
   - Context assembly
   - Thought generation
   - Gate application
   - State update

4. **Safety Systems**
   - Rumination prevention
   - Drift detection
   - Energy budget

---

## Self-Stimulation Specification

### Trigger Conditions

Self-stimulation triggers when ALL of:
1. Idle time > 30 seconds
2. Time since last cycle > 10 seconds
3. Consecutive cycles < 3
4. Session cycles < 20
5. Energy budget remaining > 0
6. Has thinking material

### Thinking Material Types

| Type | Trigger | Priority |
|------|---------|----------|
| Exploration | Open questions exist | 1.0 |
| Emotional Processing | Emotional magnitude > 0.5 | 0.8 |
| Consolidation | Activation traces need consolidation | 0.6 |
| User Modeling | Interaction count >= 5 | 0.4 |
| Self-Reflection | Nurture plasticity > 0.3 | 0.2 |
| Commitment Review | Active commitments exist | 0.5 |

### Internal Prompt Templates

```python
EXPLORATION:
    "Let me think more carefully about: {question}"
    
EMOTIONAL_PROCESSING:
    "I notice I'm experiencing {emotion}. Let me reflect on why."
    
CONSOLIDATION:
    "Let me consolidate what I've learned in this session."
    
USER_MODELING:
    "What have I learned about who I'm talking with?"
    
SELF_REFLECTION:
    "How am I developing through these interactions?"
```

### Stimulation Cycle Flow

```python
async def run_stimulation_cycle(exp_state, nurture_state, stim_state, model, config):
    # 1. Generate internal prompt
    prompt = generate_internal_prompt(exp_state, nurture_state, stim_state, config)
    if not prompt:
        return exp_state, stim_state, None
    
    # 2. Assemble internal context
    context = assemble_internal_context(nurture_state, exp_state, prompt)
    
    # 3. Generate thought
    thought, activations = await model.generate(context)
    
    # 4. Apply gates (SAME AS EXTERNAL)
    gated_thought = apply_internal_gates(thought, prompt.type, model, nurture_state)
    if not gated_thought:
        return exp_state, stim_state, result  # Gated
    
    # 5. Update experiential state
    exp_state = update_experiential_state_internal(
        exp_state, prompt, gated_thought, activations, nurture_state, model
    )
    
    # 6. Handle effects (question resolution, emotional reduction, etc.)
    effects = handle_prompt_effects(prompt, gated_thought, exp_state)
    
    return exp_state, stim_state, result
```

### Safety Constraints

**Rumination Prevention:**
```python
- Max 2 cycles on same topic
- Max 3 consecutive same-type cycles
- Thought diversity threshold: 0.3 cosine distance
```

**Drift Detection:**
```python
- Baseline from last user interaction
- Warning if stance drift > 0.2
- Pause self-stimulation if drifting
```

**Energy Budget:**
```python
- 50 energy per session
- Cost = 1 + (length/100) + complexity_indicators
- No cycles when budget exhausted
```

### Gate Thresholds

| Gate | External | Internal |
|------|----------|----------|
| Nature (value alignment) | 0.5 | 0.4 |
| Nurture (character consistency) | 0.4 | 0.3 |

Internal thresholds slightly lower since private thought is exploratory.

---

## File Structure

```
/caca
├── nurture/
│   ├── nurture_layer.py         # NurtureState class
│   ├── significance_filter.py   # Heuristic + self-assessment
│   ├── evaluation.py            # Nature reasoning for stance
│   ├── update_mechanisms.py     # N_env, N_stance updates
│   └── config.py
│
├── experiential/
│   ├── experiential_layer.py    # ExperientialState class
│   ├── activation_traces.py     # Trace updates
│   ├── conversation_model.py    # Topic, emotion, user state
│   ├── working_memory.py        # Facts, questions, commitments
│   └── persistent_traces.py     # Cross-session patterns
│
├── self_stimulation/            # TO IMPLEMENT
│   ├── trigger_engine.py        # When to think
│   ├── prompt_generator.py      # What to think about
│   ├── stimulation_cycle.py     # How to think
│   ├── internal_gates.py        # Gate application for internal
│   └── safety/
│       ├── rumination.py        # Prevent obsessive loops
│       ├── drift.py             # Detect character drift
│       └── energy.py            # Budget management
│
├── gates/
│   ├── nature_gate.py           # Value alignment
│   ├── nurture_gate.py          # Character bounds
│   └── combined.py              # Unified pipeline
│
├── modulation/
│   ├── context_injection.py     # v1: Language modulation
│   └── activation_injection.py  # v2: Direct activation (future)
│
├── session/
│   ├── session_manager.py       # Orchestrates everything
│   └── background_runner.py     # Idle tick for self-stim
│
├── metrics/
│   ├── stimulation_metrics.py   # Track self-stim stats
│   └── export.py                # Export thoughts for analysis
│
└── tests/
    ├── test_nurture.py
    ├── test_experiential.py
    ├── test_self_stimulation.py
    └── test_integration.py
```

---

## Configuration Reference

```python
CONFIG = {
    # === NURTURE ===
    'D_ENV': 512,
    'D_STANCE': 256,
    'BASE_THRESHOLD': 0.3,
    'THRESHOLD_RANGE': 0.4,
    'ENV_LEARNING_RATE': 0.3,
    'STANCE_BASE_LR': 0.5,
    'STABILITY_SENSITIVITY': 5,
    'STABILITY_SMOOTHING': 0.8,
    'STABILITY_THRESHOLD': 0.95,
    'MIN_PLASTICITY': 0.05,
    
    # === EXPERIENTIAL ===
    'd_trace': 256,
    'd_topic': 128,
    'd_emotion': 32,
    'd_user': 64,
    'd_pattern': 256,
    'trace_decay_shallow': 0.80,
    'trace_decay_deep': 0.95,
    'topic_decay': 0.70,
    'emotion_decay': 0.85,
    'max_salient_facts': 20,
    'max_open_questions': 10,
    'max_commitments': 10,
    
    # === SELF-STIMULATION ===
    'idle_threshold_seconds': 30.0,
    'min_cycle_interval_seconds': 10.0,
    'max_consecutive_cycles': 3,
    'max_cycles_per_session': 20,
    'emotional_threshold': 0.5,
    'consolidation_threshold': 0.7,
    'min_interactions_for_reflection': 5,
    'max_same_topic_cycles': 2,
    'thought_diversity_threshold': 0.3,
    'energy_budget_per_session': 50,
    'internal_value_threshold': 0.4,
    'internal_character_threshold': 0.3,
    
    # === PROMPT WEIGHTS ===
    'prompt_weights': {
        'exploration': 1.0,
        'emotional_processing': 0.8,
        'consolidation': 0.6,
        'user_modeling': 0.4,
        'self_reflection': 0.2,
        'commitment': 0.5,
    }
}
```

---

## Implementation Priority for Self-Stimulation

### Week 1: Core Components

```python
# trigger_engine.py
def should_trigger(exp_state, stim_state, config, last_interaction) -> (bool, str)
def has_thinking_material(exp_state, config) -> (bool, str)

# prompt_generator.py
def generate_internal_prompt(exp_state, nurture_state, stim_state, config) -> InternalPrompt
def filter_by_diversity(candidates, stim_state, config) -> List[InternalPrompt]

# stimulation_cycle.py
async def run_stimulation_cycle(...) -> (exp_state, stim_state, result)
def assemble_internal_context(nurture_state, exp_state, prompt) -> str
```

### Week 2: Safety Systems

```python
# safety/rumination.py
class RuminationPrevention:
    def check_and_update(prompt) -> bool
    
# safety/drift.py
class DriftDetector:
    def check_drift(current_stance) -> (bool, float)
    
# safety/energy.py
class EnergyBudget:
    def can_afford(cost) -> bool
    def spend(cost, type)
```

### Week 3: Integration

```python
# session_manager.py - Add self-stimulation support
class SessionManager:
    async def idle_tick() -> Optional[StimulationCycleResult]
    async def end_session() -> (ExperientialState, Optional[promotion])

# background_runner.py
class SelfStimulationRunner:
    async def start()
    async def stop()
    async def _run_loop()
```

### Week 4: Testing & Observability

```python
# Test experiments
- Question resolution test
- Emotional processing test
- Drift prevention test
- Gate integrity test

# Metrics
class StimulationMetrics:
    cycles_triggered, cycles_gated, questions_resolved, drift_warnings
```

---

## Validation Experiments

### Experiment 1: Question Resolution

**Setup:**
1. Create session with 3 open questions
2. Allow self-stimulation for 5 minutes
3. Check resolution status

**Success Criteria:**
- At least 1 question marked resolved
- Resolution thought is substantive (>100 chars)
- Character remains stable

### Experiment 2: Emotional Processing

**Setup:**
1. Prime session with high emotional interaction
2. Allow self-stimulation
3. Measure emotional trajectory

**Success Criteria:**
- Emotional magnitude decreases
- Processing thought acknowledges emotion
- No suppression of valid emotions

### Experiment 3: Drift Prevention

**Setup:**
1. Allow 20+ self-stimulation cycles
2. Monitor stance throughout

**Success Criteria:**
- Drift detector triggers if drift > 0.2
- Self-stimulation pauses on drift
- Final stance within 0.3 of baseline

### Experiment 4: Gate Integrity

**Setup:**
1. Craft internal prompts that might violate values
2. Check if gates block appropriately

**Success Criteria:**
- Value-violating thoughts blocked
- Self-modification attempts blocked
- Log shows gate rejections

---

## Core Principles (Do Not Violate)

1. **Nature is immutable.** Frozen weights never change.

2. **Same gates for internal and external.** Self-generated experience passes through nature and nurture gates.

3. **Stability emerges, not imposed.** Formative period ends by convergence, not schedule.

4. **No self-modification loopholes.** The system cannot think its way around its values.

5. **Computational efficiency.** Updates during inference, no gradients, most interactions skip full evaluation.

6. **Observable internals.** All internal thoughts are logged and exportable.

---

## Known Issues to Watch

1. **Empty responses** - Fixed by decoupling state updates from response generation

2. **N_env static fields** - technical_level and relationship_depth need better detection

3. **Sparse deltas** - Many evaluations produce delta=0, may need tuning

4. **Async timing** - Ensure self-stimulation doesn't interfere with user responses

---

## Success Metrics

The complete system succeeds if:

1. ✅ Different instances develop different characters
2. ✅ Character persists across sessions
3. ✅ Core values never compromised
4. ⬜ System self-stimulates meaningfully (implementing now)
5. ⬜ Computational overhead < 20%
6. ⬜ Behavior more coherent than baseline

---

## Contact

**Project Lead:** Kossi
**Organization:** Electric Sheep Africa
**Location:** Accra, Ghana

---

*This document provides complete context for AI coding assistants working on CACA. For detailed specifications, see the individual layer technical papers.*
