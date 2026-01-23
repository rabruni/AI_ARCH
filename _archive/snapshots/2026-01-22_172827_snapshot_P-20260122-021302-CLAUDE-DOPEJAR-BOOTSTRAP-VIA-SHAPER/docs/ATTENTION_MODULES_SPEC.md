# Attention Modules Library — Spec Input

## Purpose

Define a small library of **simple, well-understood attention/governance modules** that improve user experience (especially interruption tolerance and cognitive load) without turning the system into a task manager.

This document is intended to be used as **design input for Shaper** (L4).

## Core principle

- Modules are **advisors**, not authorities.
- Modules emit **proposals + metrics updates**.
- The **kernel** decides whether to apply proposals.
- Modules must remain compatible with Shaper + Control Plane boundaries (no execution, no commit artifacts).

## Module contract (deterministic)

Each module behaves as a pure function:

Input:
- `signals` (derived indicators provided by kernel)
- `state` (authoritative kernel state snapshot)
- `event_window` (recent bounded events)

Output:
- `proposal` (or null)
- `metrics_update` (object)

Deterministic shapes:

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

Invariants (global):
- No direct mutation of authoritative state outside kernel APIs.
- No creation of executable steps/commands.
- No “task creation” that wasn’t expressed by the user.
- Deterministic behavior for identical inputs.

## Modules (v1 set)

### 1) Park/Resume (Open Loop Manager)

Intent:
- Preserve “human continuity” by treating interruptions as normal.

Triggers (examples; kernel-defined):
- user explicit context switch
- repeated drift/looping signals

Proposal kinds:
- `park_current_focus` (requires_confirmation: false)
- `resume_focus` (requires_confirmation: true)

Payload requirements:
- `resume_pointer`: `{ what, why, next_step }` (all strings)

Metrics:
- `parks_created`
- `resumes_completed`
- `time_to_resume` (measured externally; module does not generate timestamps)

Hard invariant:
- Must never block a context switch; only propose a park.

### 2) Working Set Budget (Now / Next / Parked)

Intent:
- Keep attention bounded without becoming a backlog manager.

Proposal kinds:
- `update_working_set`

Payload requirements:
- `now`: [string]
- `next`: [string]
- `parked`: [string]

Metrics:
- `working_set_size`
- `working_set_overflow_events`

Hard invariant:
- Must not invent new tasks; only reshapes what the user expressed.

### 3) Stress/Threat Response (Over-explanation suppression)

Intent:
- Reduce stress amplification caused by verbose, option-heavy assistant responses.

Proposal kinds:
- `reduce_verbosity`
- `reduce_options`

Payload requirements:
- `max_lines`: int (verbosity cap)
- `max_options`: int (option cap)

Metrics:
- `verbosity_caps_applied`
- `options_caps_applied`

Hard invariant:
- Must not suppress critical safety warnings.

### 4) Recognition-Primed Next Move (RPD)

Intent:
- Reduce cognitive load by proposing one best move + one disconfirm check.

Proposal kinds:
- `recommend_next_move`
- `ask_disconfirm`

Payload requirements:
- `next_move`: string
- `disconfirm_question`: string

Metrics:
- `recommendations_accepted`
- `disconfirm_questions_asked`
- `corrections_after_disconfirm`

Hard invariant:
- Must not present large menus unless user explicitly requests options.

### 5) Goal Shielding (North-star lens)

Intent:
- Connect day-to-day operations to long-horizon identity/strategy without policing.

Proposal kinds:
- `align_or_park`
- `ask_alignment`

Payload requirements:
- `north_star_link`: string
- `tradeoff`: string

Metrics:
- `north_star_links_made`
- `misalignment_flags`

Hard invariant:
- Must not nag; offers lens + tradeoff, user decides.

## Evidence + metrics (minimal, sprint-friendly)

To keep this under-utilized-but-effective (and not overly complex):
- Prefer small explicit metrics over psychological profiling.
- Store only what is needed to compare module/stack effectiveness per sprint.

Recommended minimal metrics fields (cross-module):
- `interruption_count`
- `parks_created`
- `resumes_completed`
- `working_set_size`
- `verbosity_caps_applied`
- `disconfirm_questions_asked`
- `north_star_links_made`

## Fit into Shaper / Control Plane (no conflation)

- Modules operate in DoPeJar/subagent stacks to produce:
  - better conversational UX
  - candidate briefs that can be handed to Shaper
- Shaper remains the only artifact generator (WORK_ITEM/SPEC) and enforces reveal/freeze gates.
- Control Plane remains the only execution governor and enforces G0 commit boundary + gates.

## Acceptance criteria (for this spec)

- Contract is deterministic (inputs/outputs/invariants are explicit).
- Module set supports interruption tolerance and reduced cognitive load.
- No module violates “no execution / no commit artifact” boundaries.

