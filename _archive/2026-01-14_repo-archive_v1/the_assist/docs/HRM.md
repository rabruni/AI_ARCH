# Hierarchical Reasoning Model (HRM)

> **HRM is the deliberate separation of intent, planning, execution, and evaluation so each can reason clearly, revise cheaply, and interact through stable interfaces rather than shared verbosity.**

---

## Core Principle

**Not all thinking should happen at the same altitude.**

And more importantly:

> The ability to revise intent without redoing execution is the defining feature of intelligence at scale.

---

## Key Insight: Bidirectional Flow

- Lower layers report **state**
- Upper layers decide **meaning**

---

## The Four Layers

### 1. Intent Layer (Why)

**Responsibilities**
- Define success
- Declare non-goals
- Hold values and priorities
- Decide when to stop

**Failure if mixed**
- Endless analysis
- Shifting goals mid-execution
- Over-optimization

**Memory type**
- Stable, low-frequency
- Very small
- High authority

---

### 2. Planning Layer (What / How broadly)

**Responsibilities**
- Break problems into parts
- Choose approaches
- Allocate effort
- Manage tradeoffs

**Failure if mixed**
- Premature execution
- Over-detail too early
- Fragile plans

**Memory type**
- Semi-stable
- Rewritable
- Pattern-oriented

---

### 3. Execution Layer (How specifically)

**Responsibilities**
- Perform reasoning
- Apply rules
- Generate text/code
- Handle details

**Failure if mixed**
- Tunnel vision
- Excess verbosity
- Irreversible commitment

**Memory type**
- Ephemeral
- Disposable
- High volume

---

### 4. Evaluation Layer (Did it work?)

**Responsibilities**
- Detect errors
- Compare outcome to intent
- Trigger revision
- Decide whether to escalate

**Failure if mixed**
- Rationalization
- Inability to admit error
- Hidden assumptions

**Memory type**
- Delta-based
- Outcome-focused
- Time-bounded

---

## Why HRM Matters for LLMs

LLMs are:
- Probabilistic
- Stateless by default
- Sensitive to token pressure

HRM compensates by:
- Limiting what each step must "remember"
- Reducing the surface area of context
- Making revision cheap

This pairs naturally with:
- **Hot vs cold memory**
- **Decision artifacts**
- **Progressive disclosure**

---

## HRM vs "Deep Think" Modes

"Deep think" tries to:
- Increase internal effort
- Extend chains
- Brute-force reasoning

HRM instead:
- **Reduces the need** for depth
- Localizes complexity
- Makes insight compositional

This is why HRM often feels *lighter*, not heavier.

---

## Real-World Examples

### AlphaGo/AlphaZero (Canonical HRM)
- Intent: Win the game
- Planning: Monte Carlo Tree Search
- Execution: Policy + value networks
- Evaluation: Backpropagate outcomes

> The model never "thinks harder" — it thinks at the right level.

### Autonomous Driving
- Intent: Reach destination safely
- Behavior planning: Lane changes, merges
- Trajectory planning: Paths, velocities
- Control: Steering, braking

> Intelligence fails when low-level control gains authority over intent.

### Compilers
- Intent: Preserve program semantics
- High-level IR: Language-agnostic meaning
- Optimization: Transformations
- Codegen: Machine instructions

### Human Expert Reasoning
Doctors, pilots, grandmasters don't:
- Recalculate everything every second
- Debate goals mid-procedure
- Replay history endlessly

That's HRM in the wild.

---

## Anti-Patterns (What HRM Prevents)

### Flat chatbots
- One layer
- No revision authority
- Context grows uncontrollably

### Feature stacking
- Each problem gets a new feature
- Architecture stays flat
- Complexity increases, clarity decreases

### "Deep think" modes
- More tokens, not more structure
- Longer chains, not better abstraction
- High cost, diminishing returns

---

## The Common Pattern Across Success

Every successful HRM system enforces:
1. **Separation of concerns**
2. **Upward authority** (intent outranks execution)
3. **Downward reporting** (execution reports state, not decisions)
4. **Cheap revision at higher layers**

---

## Practical Implication

If your system:
- Needs "deep modes"
- Keeps rereading history
- Grows context windows uncontrollably

You don't need:
- A smarter model
- Longer prompts
- More tokens

You need **clearer separation of reasoning layers**.

---

## For The Assist Implementation

This document defines the architecture for DoPeJar (Donna/Pepper/Jarvis).

Each layer maps to:
- **Intent Store** → Intent Layer
- **Planner** → Planning Layer
- **Executor** → Execution Layer
- **Evaluator** → Evaluation Layer

Each with its own memory type. Stable interfaces. Cheap revision.
