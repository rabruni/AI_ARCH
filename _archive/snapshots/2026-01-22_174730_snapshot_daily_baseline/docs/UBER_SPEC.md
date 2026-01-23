# Uber Spec — DoPeJar Cognitive Kernel + Attention Modules (CIM v1)

## Purpose

Unify the current design into one Shaper-friendly L4 spec input that defines:

- a science-aligned interaction model (CIM v1)
- a pluggable cognitive kernel (profiles + ports + routing + governance)
- an attention module library (proposal-only modules + metrics)

Goal: enable rebuilding DoPeJar (Donna/Pepper/Jarvis) as a human-feeling assistant while preserving strict execution governance via Shaper + Control Plane.

## Non-negotiable boundaries (do not collapse roles)

- **DoPeJar**: conversational assistant UX (continuity, north stars, park/resume, attention support).
- **Kernel**: deterministic composition + governance (routes stack profiles, arbitrates proposals, owns memory promises, writes audit events).
- **Attention modules**: pure proposal generators (no direct authority).
- **Shaper**: deterministic artifact shaping (WORK_ITEM/SPEC) with reveal/freeze gates; no execution.
- **Control Plane**: execution governance (commit boundary + gates) for anything that could run.

## CIM v1 — Cognitive Interaction Model (how it should work)

Institutional framing: cognition behaves like a **bounded workspace** governed by **executive control**, continuously modulated by **salience/arousal/value**, stabilized by **metacognitive monitoring**, and supported by **memory systems**.

### Core loop (every turn)

1) **Input buffer (perception)**
- Receive user utterance + new evidence + environment signals.

2) **Fast appraisal (salience + value + arousal/threat)**
- Determine what is urgent/important, alignment to goals, and stress/load constraints.

3) **Executive control selects focus and policy**
- Choose focus; decide clarify vs proceed vs park; enforce constraints.

4) **Workspace update (working memory / active set)**
- Maintain bounded working set (e.g., now/next/parked + current focus + minimal recent context).

5) **Proposal generation (action selection)**
- Produce a proposal: response, single clarification, park/resume, or next-move recommendation.

6) **Write-back (memory)**
- Persist only what policy allows: audit events, semantic facts/goals, routines (if permitted).

7) **Metacognitive monitoring**
- Detect drift/looping, overload, low confidence; trigger interventions (reduce verbosity/options, disconfirm, park).

### Always-on modulators

- **Arousal/Threat modulator:** under stress, shrink workspace and reduce options.
- **Value/North-star modulator:** bias selection toward aligned work; surface misalignment.
- **Habit/Routine modulator:** offer fast defaults; executive control can override.

### Two-speed hierarchy (two-loop)

- **Fast inner loop:** turn-by-turn appraisal → workspace → next move.
- **Slow outer loop:** periodic re-evaluation of priorities, commitments, and strategy; consolidation and evaluation over sprints.

## Canonical meaning altitude (internal enum, v1)

Meaning altitude is the abstraction level of intent, not response depth and not artifact altitude.

Canonical enum (internal, stable):
- `Identity` (values, north stars, self-concept)
- `Strategy` (priorities, tradeoffs, multi-week direction)
- `Operations` (projects/tasks, execution framing)
- `Moment` (next step, unblock, reduce cognitive load)

Personas may relabel these for UX, but must not redefine the underlying enum.

## Kernel (pluggable composition + governance)

### Objectives

- Compose versioned stacks (persona + modules + policies) with deterministic routing.
- Keep UX consistent across stacks/personas.
- Provide explicit “memory promises” and enforce them.
- Provide ports for ingestion and memory to support email/docs/meeting notes without redesign.
- Preserve authority boundary: modules propose; kernel decides.

### Non-goals

- Implementing the kernel here.
- Allowing execution or automatic commitment.
- Allowing kernel/DoPeJar to produce Control Plane commit artifacts (e.g., `08_commit.md`) or bypass Shaper/Control Plane gates.

### Core entities (deterministic shapes)

#### PersonaProfile (versioned, sprint-managed)

```yaml
PersonaProfile:
  id: string
  version: string
  name: string
  ux_invariants:
    commands: [string]            # e.g., ["park", "resume", "status"]
    status_strip: string          # deterministic format contract
    memory_promises: [string]     # what is remembered + for how long
  defaults:
    stance: string
    meaning_altitude: Identity|Strategy|Operations|Moment
    risk_posture: low|medium|high
  constraints:
    forbidden_behaviors: [string] # e.g., "no nagging task-manager behavior"
    escalation_rules: [string]    # when to push vs ask vs park
```

#### StackProfile (released unit)

```yaml
StackProfile:
  id: string
  version: string
  persona_profile_id: string
  modules:
    attention: [string]           # module ids
    ingestion: [string]           # module ids
    memory: string                # module id
  capabilities:
    tools: none|read_only
    storage_allowlist: [string]
  risk_tier: low|medium|high
  routing_tags:
    domains: [string]
    task_types: [string]
```

### Kernel ports (interfaces)

#### MemoryPort

Operations:
- `get_state()` → structured state
- `set_state(state)` → replace authoritative state (versioned)
- `append_event(event)` → append-only audit
- `query_events(filter)` → retrieval for debugging/review

Invariants:
- schema validation on write; no silent drops
- explicit retention policy
- state is authoritative; transcript is optional audit, not truth

#### IngestionPort

Operations:
- `ingest(source_id, payload)` → list of evidence items

```yaml
EvidenceItem:
  source_type: string
  source_id: string
  captured_at: string|null     # if present, provided externally
  content: string
  metadata: object
```

Invariants:
- deterministic output for identical inputs
- no action generation; evidence only

#### LLMPort (optional)

Operations:
- `propose(prompt)` → proposals only

Invariants:
- proposals are non-authoritative until accepted by kernel policy
- kernel remains deterministic even if LLM absent (manual mode possible)

### Deterministic routing (bounded switching)

Two-layer routing:

1) Persona selection (sprint-managed):
- choose active PersonaProfile version for the user

2) Task routing (runtime):
- choose StackProfile deterministically from released stacks based on:
  - task type/domain
  - risk tier signals
  - active persona

Boundary rule:
- stack changes only at explicit boundaries: `park`, `resume`, `reset`, or explicit transition event

## Attention modules (proposal-only library)

### Module contract (deterministic)

```yaml
ModuleInput:
  signals: object
  state: object
  event_window: [object]

ModuleOutput:
  proposal: Proposal|null
  metrics_update: object

Proposal:
  id: string
  kind: string
  payload: object
  requires_confirmation: true|false
```

Global invariants:
- no execution and no direct state mutation outside kernel APIs
- no task invention; only reshape what the user expressed
- deterministic behavior for identical inputs

### v1 module set

1) **Park/Resume (Open Loop Manager)**
- intent: interruption tolerance; resumable pointers
- proposals: `park_current_focus`, `resume_focus`
- invariant: never block a context switch

2) **Working Set Budget (Now/Next/Parked)**
- intent: bounded working set without task-manager behavior
- proposal: `update_working_set`
- invariant: never invent new tasks

3) **Stress/Threat Response (Over-explanation suppression)**
- intent: reduce cognitive load under stress
- proposals: `reduce_verbosity`, `reduce_options`
- invariant: do not suppress critical safety warnings

4) **Recognition-Primed Next Move (RPD)**
- intent: propose one best move + one disconfirm question
- proposals: `recommend_next_move`, `ask_disconfirm`
- invariant: avoid large menus unless requested

5) **Goal Shielding (North-star lens)**
- intent: keep work aligned to Identity/Strategy without policing
- proposals: `align_or_park`, `ask_alignment`
- invariant: offer lens + tradeoff; user decides

### Minimal metrics (sprint-evaluable, non-profiling)

Recommended cross-module metrics:
- `interruption_count`
- `parks_created`
- `resumes_completed`
- `working_set_size`
- `verbosity_caps_applied`
- `disconfirm_questions_asked`
- `north_star_links_made`

## Handoff to Shaper + Control Plane (no conflation)

The kernel/DoPeJar may produce a **candidate brief** (text-only) to feed to Shaper:
- objective (what)
- why (north star link)
- suggested artifact altitude (L3 WORK_ITEM vs L4 SPEC)
- scope hints
- acceptance intent

Kernel/DoPeJar must not:
- generate `08_commit.md`
- invoke Control Plane scripts
- claim execution readiness

Shaper produces deterministic artifacts with reveal/freeze gating.
Control Plane enforces the commit boundary and execution gates.

## Acceptance criteria for this uber spec

- CIM v1 loop + modulators + two-speed hierarchy are explicit and coherent.
- Meaning altitude enum is locked (with persona relabeling allowed).
- Kernel entities/ports/routing are deterministic and bounded.
- Modules are proposal-only with invariants and minimal metrics.
- Shaper/Control Plane boundaries are explicit; no execution or commit artifacts are generated upstream.

