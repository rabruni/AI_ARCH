# Design — Attention Modules (SPEC-005)

## 1) Module contract shape (conceptual)

Each module is a pure function:

Input:
- `signals` (user state, drift indicators, progress)
- `state` (current commitment, stance, meaning altitude)
- `event_window` (recent events; bounded)

Output:
- `proposal` (what to do next, or what to ask)
- `metrics_update` (counters, scores)

Kernel decides whether to apply the proposal.

Deterministic shapes (YAML/JSON-equivalent):

```yaml
ModuleInput:
  signals: object
  state: object
  event_window: [object]   # bounded by kernel policy

ModuleOutput:
  proposal: Proposal|null
  metrics_update: object

Proposal:
  id: string
  kind: park_current_focus|resume_focus|update_working_set|reduce_verbosity|reduce_options|recommend_next_move|ask_disconfirm|align_or_park|ask_alignment
  payload: object
  requires_confirmation: true|false
```

## 2) Modules

### A) Park/Resume (Open Loop Manager)

Purpose:
- Handle interruptions without interrogation.

Triggers:
- explicit context switch (“I need to do X now”)
- repeated drift signals

Outputs:
- `proposal: park_current_focus`
- `resume_pointer`: what/why/next step

Metrics:
- interruption success rate (parked then resumed)
- time-to-resume

Invariant:
- Must never block a context switch; only propose a park action.

### B) Working Set Budget (Now/Next/Parked)

Purpose:
- Keep attention bounded without becoming a task manager.

Outputs:
- `proposal: update_working_set`

Metrics:
- working set size (target ≤ 3)
- user friction events when >3

Invariant:
- Must never create “new tasks” on its own; only reshapes what the user already expressed.

### C) Stress/Threat Response (Over-explanation suppression)

Purpose:
- Prevent stress amplification caused by verbose, option-heavy responses.

Inputs:
- sentiment/urgency signals, frustration patterns

Outputs:
- `proposal: reduce_verbosity` (cap response length)
- `proposal: reduce_options` (single recommended next move)

Metrics:
- reduction in negative sentiment after intervention

Invariant:
- Must not suppress critical safety warnings.

### D) Recognition-Primed Next Move

Purpose:
- Reduce cognitive load by proposing one best move and one disconfirm question.

Outputs:
- `proposal: recommend_next_move`
- `proposal: ask_disconfirm`

Metrics:
- decision time (turns to commit)
- correction rate (how often user rejects)

Invariant:
- Must not present large menus of options unless explicitly requested.

### E) Goal Shielding (North-star lens)

Purpose:
- Connect operations to strategy/identity.

Outputs:
- `proposal: align_or_park`
- `proposal: ask_alignment` (only when misalignment is high)

Metrics:
- proportion of committed work linked to a north star
- drift incidents per session

Invariant:
- Must not “police” the user; offers lens and tradeoffs, user decides.

## 3) How modules fit Shaper/Control Plane without conflation

- Modules operate in DoPeJar and subagent stacks to produce candidate briefs.
- Shaper remains the artifact generator and must maintain reveal/confirm/freeze gates.
- Control Plane remains the execution validator and must maintain G0 commit boundary.

## 4) Minimal evidence + metrics contract

To keep modules simple and under-utilized-but-effective:
- Prefer small, explicit metrics over “psychological profiling”.
- Store only what is needed to evaluate modules per sprint.

Minimal metrics fields (examples):
- `interruption_count`
- `parks_created`
- `resumes_completed`
- `working_set_size`
- `verbosity_caps_applied`
- `disconfirm_questions_asked`
- `north_star_links_made`
