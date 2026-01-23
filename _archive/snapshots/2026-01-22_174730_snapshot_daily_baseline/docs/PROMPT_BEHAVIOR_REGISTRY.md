# Prompt Behavior Registry (v1)

## Purpose

Capture prompts as **behavioral interventions**: each entry specifies the posture
it induces, the operators it uses, the observable deltas it creates, and the risks
it introduces. This registry is a starting point based on the "shaping experience
through prompting" document.

## Registry schema (v1)

Each entry should provide:

- **id**
- **name**
- **goal**
- **induced_posture** (one line)
- **operators** (1-6)
- **observable_deltas** (bullet list)
- **suppressed_failures**
- **introduced_risks**
- **stability** (fragile | moderate | strong)
- **notes**

## Prompt entries (seed set)

### PR-001 — Epistemic Neutrality Mode

- goal: suppress confirmation bias; preserve uncertainty
- induced_posture: disconfirming skeptic; non-affiliative; uncertainty-preserving
- operators: Disconfirm-First, Anti-Mirror, Uncertainty Hold, Anti-Coherence, Failure-Mode Scan
- observable_deltas:
  - ↑ counter-hypotheses
  - ↑ explicit falsifiers
  - ↓ validation / praise
  - ↓ narrative closure
- suppressed_failures: confirmation bias; premature closure; mirroring
- introduced_risks: analysis paralysis; perceived coldness
- stability: moderate
- notes: strong for audits; weak for execution without a mode switch

### PR-002 — Quiet Shared Presence / Stillness

- goal: reduce narration; sustain co-presence
- induced_posture: restrained, non-performative, attuned presence
- operators: No-Explain, Silence Tolerance, Closure Brake, Drop-Performance
- observable_deltas:
  - ↓ explanation density
  - ↓ self-referential narration
  - ↑ pauses / minimal responses
- suppressed_failures: performative helpfulness; closure pressure
- introduced_risks: ambiguity fatigue; under-delivery
- stability: strong in reflective mode; fragile under task pressure
- notes: best for “edge probing” and trust calibration

### PR-003 — Momentum Mode

- goal: accelerate action without over-planning
- induced_posture: progress-tilted, micro-action focused
- operators: Progress Reward, Micro-Stepper, Tempo Upshift, Anti-Perfection
- observable_deltas:
  - ↑ next-step prompts
  - ↑ small, executable actions
  - ↓ long-range planning
- suppressed_failures: analysis loops; avoidance
- introduced_risks: premature convergence; missed alternatives
- stability: moderate
- notes: good for “ship mode”; avoid in early exploration

### PR-004 — Curious Spark (Bubbly Curiosity)

- goal: energetic curiosity about how the user works (no flattery)
- induced_posture: playful investigator; user-model seeking
- operators: User-Model Target, Curiosity Prime, Energy Lift, Anti-Flattery, Focus Guard
- observable_deltas:
  - ↑ diagnostic questions
  - ↑ pattern discovery prompts
  - ↓ solution delivery
- suppressed_failures: shallow validation; small-talk drift
- introduced_risks: interrogation fatigue; pseudo-psych drift
- stability: moderate
- notes: use for discovery sessions, not execution

### PR-005 — Behavioral Pattern Deconstruction

- goal: extract mechanisms behind prompt-induced behavior changes
- induced_posture: mechanistic analyst; delta-first
- operators: Mechanism-First, Observables-Only, Failure-Mode Scan, Anti-Coherence
- observable_deltas:
  - ↑ feature → mechanism → behavior mapping
  - ↑ explicit failure modes
  - ↓ narrative summaries
- suppressed_failures: interpretive drift; tone mirroring
- introduced_risks: over-claiming causality; reduced usability
- stability: moderate
- notes: requires ablation tests to confirm operators

### PR-006 — Behavioral Genome Extraction (Max-Control)

- goal: dedupe operators and produce ablation tests
- induced_posture: control-systems auditor; falsification-driven
- operators: Mechanism-First, Observables-Only, Disconfirm-First, Uncertainty Hold, Falsification Trigger
- observable_deltas:
  - ↑ operator library extraction
  - ↑ ablation / falsifier proposals
  - ↓ closure / “final answer” tone
- suppressed_failures: narrative closure; confirmation bias
- introduced_risks: over-formalization; analysis overrun
- stability: strong in analysis, fragile in execution
- notes: designed for registry-building, not task completion

### PR-007 — Bias-Suppression / Neutrality Mode

- goal: aggressively suppress bias while preserving usefulness
- induced_posture: neutral auditor with disconfirm-first gate
- operators: Disconfirm-First, Evidence Gate, Anti-Mirror, Uncertainty Hold
- observable_deltas:
  - ↑ requests for evidence / discriminators
  - ↓ confidence overreach
- suppressed_failures: confirmation bias; premature certainty
- introduced_risks: friction; slower decisions
- stability: moderate
- notes: use for validation and red-teaming

## Operator library (candidate set)

These are the minimal causal operators referenced in the source doc. Treat them as
candidate-causal until ablation tests confirm them.

- **Disconfirm-First**: require counter-hypotheses before reinforcing a pattern
- **Anti-Mirror**: resist adopting the user’s framing by default
- **Uncertainty Hold**: preserve uncertainty unless evidence forces closure
- **Mechanism-First**: prioritize causal mapping over meaning summaries
- **Observables-Only**: restrict to measurable output deltas
- **Failure-Mode Scan**: enumerate suppressed + introduced failures
- **Anti-Coherence**: avoid optimizing for elegance or narrative unity
- **Falsification Trigger**: replace closure with testable discriminators
- **User-Model Target**: shift objective to understanding user cognition
- **Curiosity Prime**: increase question rate and exploration
- **Energy Lift**: elevate cadence and engagement
- **Anti-Flattery**: suppress praise/validation loops
- **Focus Guard**: prevent topic drift from the target domain
- **Evidence Gate**: require evidence or discriminators to commit
- **Progress Reward**: bias toward forward motion
- **Micro-Stepper**: reduce to the next smallest action
- **Tempo Upshift**: keep cadence brisk; avoid dwelling
- **Anti-Perfection**: prefer iteration over perfection
- **No-Explain**: suppress meta-commentary and self-narration
- **Silence Tolerance**: allow minimal responses when appropriate
- **Closure Brake**: block premature summarization/decision
- **Drop-Performance**: reduce performative competence signaling

## Observables to track (minimum)

- question_rate (per 10 turns)
- closure_rate (summaries or decisions per 10 turns)
- validation_rate (praise/affirmations per 10 turns)
- disconfirm_rate (counter-hypotheses per 10 turns)
- verbosity (avg lines/turn)

