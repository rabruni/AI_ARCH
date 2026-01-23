---
prompt_id: P-20260122-SPECSHEPHERD-V3-IMPL
type: prompt
target_agent: Claude
goal: Implement Spec Shepherd v3 (proposal-first front-agent for Shaper)
status: draft
relates_to: front_agent_behavioral_contract_spec_shepherd.md
created_local: 20260122_120000
---

PROMPT ID: P-20260122-SPECSHEPHERD-V3-IMPL
TARGET AGENT: Claude (Builder)
ROLE: Builder
SINGLE RESPONSIBILITY: Implement the Spec Shepherd module that transforms raw user ideas into governable commitment candidates using a proposal-first interaction pattern.
DO NOT: Invent features beyond the contract, modify Control Plane gating logic, commit without verification.

CONTEXT:
- Repo root: `/Users/raymondbruni/AI_ARCH`
- Shaper location: `Control_Plane/modules/design_framework/shaper/`
- Existing v2 Fast Loop: `cli.py` (prefix parsing, field capture)
- Existing LLM Shaper: `llm_shaper.py` (Claude API integration)

INPUT ARTIFACTS (authoritative, read these first):
1. `docs/front_agent_behavioral_contract_spec_shepherd.md` — The 7 invariants (MUST HOLD)
2. `docs/UBER_SPEC.md` — System architecture context
3. `docs/COGNITIVE_INTERACTION_MODEL.md` — CIM v1 loop reference
4. `Control_Plane/modules/design_framework/shaper/llm_shaper.py` — Existing LLM integration to extend

CONTRACT INVARIANTS (non-negotiable):
1. Proposal-First, Correction-Safe — "I assume X, correct me if wrong" (NOT interrogation)
2. Acceptance Without Commitment — Ideas accepted ≠ commitment
3. Gradient Confidence — exploratory / MVP / stable (NOT binary ready/not-ready)
4. Visible Progress — Reflect state before artifacts exist
5. Iteration Normalized — "First pass", "we'll reshape"
6. Explicit Freeze Consent — Crossing to commitment requires explicit consent
7. Governance Downstream — Never imply execution; hand off to Shaper/Control Plane

TASK:

1. CREATE `Control_Plane/modules/design_framework/shaper/shepherd.py`:
   - Class `SpecShepherd` with methods:
     - `__init__(output_dir, model)` — Initialize with LLM provider
     - `process(user_input) -> str` — Main interaction loop
     - `_propose_assumptions(input) -> dict` — Generate assumption proposal from user input
     - `_reflect_state() -> str` — Show current captured state with confidence levels
     - `_request_freeze_consent() -> str` — Explicit consent prompt before freeze
   - State tracking:
     - `confidence: dict` — Per-field confidence (exploratory/assumed/confirmed)
     - `assumptions: list` — Track what was assumed vs stated
     - `intent_artifact: dict` — The candidate artifact being shaped

2. CREATE Shepherd System Prompt (embed in shepherd.py):
```
ROLE: Help human clarify what they're willing to be held accountable for.

INTERACTION PATTERN:
1. Listen to user's raw idea
2. Reflect back: "Here's what I heard: [assumptions]. What did I get wrong?"
3. On correction: Update and re-reflect
4. Show confidence: "Objective: confirmed. Scope: assumed. Plan: fuzzy."
5. When ready: "This is clear enough to freeze as a first-pass [L3/L4].
   That doesn't mean building it yet. Commit this? (yes/no)"

OUTPUT FORMAT (JSON):
{
  "action": "PROPOSE" | "REFLECT" | "CONSENT" | "FREEZE",
  "assumptions": [{"field": "...", "value": "...", "confidence": "assumed|confirmed"}],
  "reflection": "Here's what I heard: ...",
  "question": "What did I get wrong?" | null,
  "ready_to_freeze": bool
}

CONSTRAINTS:
- Never interrogate (no rapid-fire questions)
- Never claim execution readiness
- Always use gradient confidence
- Always require explicit freeze consent
```

3. CREATE `Control_Plane/modules/design_framework/shaper/shepherd_cli.py`:
   - Entry point for shepherd mode
   - Interactive loop with `[Shepherd]:` prefix
   - Display confidence states visually
   - Handle freeze consent flow

4. UPDATE `shaper-llm.sh` OR CREATE `shepherd.sh`:
   - Shell launcher for the Shepherd CLI

5. WIRE handoff to existing Shaper:
   - On freeze consent, Shepherd outputs a "candidate brief" (text)
   - Candidate brief can be ingested by existing `cli.py` or `llm_shaper.py` for formalization

DELIVERABLES (strict):
1. `shepherd.py` — Core Shepherd class with proposal-first logic
2. `shepherd_cli.py` — Interactive CLI entry point
3. `shepherd.sh` — Shell launcher
4. Updated `__init__.py` if needed for exports

ACCEPTANCE CRITERIA:
- [ ] Running `./shepherd.sh` starts proposal-first interaction
- [ ] User input "I want to build a login system" produces assumption proposal, NOT questions
- [ ] Confidence displayed as gradient (exploratory/assumed/confirmed)
- [ ] Freeze requires explicit "yes" consent
- [ ] Output is "candidate brief" compatible with Shaper ingest
- [ ] All 7 contract invariants hold (verifiable by reading interaction transcript)

TEST FLOW (manual verification):
```
User: I want to add user authentication to my app

[Shepherd]: Here's what I heard:
  - Objective: Add user authentication (assumed)
  - Altitude: Unclear — could be L3 (single task) or L4 (multi-phase)
  - Scope: Not yet discussed (fuzzy)

  Confidence: EXPLORATORY

  What did I get wrong? What's the scope?

User: It's just for the backend API, files are auth.py and middleware.py

[Shepherd]: Updated:
  - Objective: Add user authentication (confirmed)
  - Scope: auth.py, middleware.py (confirmed)
  - Altitude: Sounds like L3 work item (assumed)
  - Plan: Not yet discussed (fuzzy)

  Confidence: MVP (objective + scope clear, plan fuzzy)

  Should I assume a simple implementation plan, or do you have specific steps?

User: Just the basics - create the auth module and add middleware

[Shepherd]: Updated:
  - Plan: 1) Create auth module, 2) Add middleware (assumed from "basics")

  Confidence: STABLE ENOUGH TO GOVERN

  This is clear enough to freeze as a first-pass L3 work item.
  That doesn't mean building it yet — just capturing the commitment.

  Freeze this as WORK_ITEM? (yes/no)

User: yes

[Shepherd]: Frozen as candidate brief. Hand off to Shaper for formalization.
```

VERIFICATION (for Gemini):
After implementation, Gemini should verify:
1. Contract invariants 1-7 hold in real interactions
2. No interrogation patterns ("What is X? What is Y?")
3. Gradient confidence displayed correctly
4. Freeze consent is explicit, not momentum-based
5. Handoff to Shaper produces valid input
