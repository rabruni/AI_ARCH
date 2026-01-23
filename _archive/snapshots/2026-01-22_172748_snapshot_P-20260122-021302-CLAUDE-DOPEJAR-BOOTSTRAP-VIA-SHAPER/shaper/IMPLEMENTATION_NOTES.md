# Implementation Notes

## Migration Summary: v1 → v2 (Finalized)

### Schema Migration

| Aspect | v1 (Legacy) | v2 (Production) |
|--------|-------------|-----------------|
| **SpecModel** | 4 sections (overview, requirements, design, tests) | 6 sections (Overview, Problem, Non-Goals, Phases, Work Items, Success Criteria) |
| **ShaperModel** | 4 sections (objective, scope, plan, acceptance) | Same 4 sections, maintained for L3 |
| **Altitude** | Implicit | Explicit L3/L4 with AltitudeRouter |
| **Phase Confirmation** | Per-phase dict | SpecModel.phases_confirmed boolean gate |
| **Work Items** | N/A | Optional in L4 spec, excluded from completeness checks |
| **Edit Invalidation** | Not implemented | on_edit() returns REVEALED→SHAPING |

### Target Directory Structure

**Production Location:** `Control_Plane/modules/design_framework/shaper/`

```
Control_Plane/modules/design_framework/shaper/
├── __init__.py          # Public API exports
├── models.py            # ShaperModel (L3) + SpecModel (L4)
├── router.py            # AltitudeRouter + detect_altitude()
├── state_machine.py     # ShaperStateMachine + ShaperSession
├── context_builder.py   # ContextWindow + ConversationBuffer (4-block)
├── renderers.py         # render_work_item() + render_spec()
├── output_safety.py     # resolve_output_path() + write_output()
└── cli.py               # ShaperCli interactive session
```

**Test Location:** `Control_Plane/tests/shaper/`

```
Control_Plane/tests/shaper/
├── __init__.py
├── test_models.py       # Tests 1-26 (L3, L4, Rendering)
├── test_router.py       # Tests 27-32 (Altitude Router)
├── test_state_machine.py # Tests 33-42 (State Machine, L4 Confirmation)
└── test_context.py      # Tests 43-45 (Context Window)
```

### Test Coverage (47 Tests, All Passing)

| Category | Test IDs | Count | File |
|----------|----------|-------|------|
| A. L3 Work Item Model | 1-10 | 10 | test_models.py |
| B. L4 Spec Model | 11-20 | 10 | test_models.py |
| C. Deterministic Rendering | 21-26 | 6 | test_models.py |
| D. Altitude Router | 27-32 | 6 | test_router.py |
| E. State Machine | 33-38 | 6 | test_state_machine.py |
| F. L4 Phase Confirmation | 39-42 | 4 | test_state_machine.py |
| G. Context Window Builder | 43-45 | 3 | test_context.py |
| Integration | Extra | 2 | test_context.py |
| **Total** | | **47** | |

### Critical Design Rules Enforced

1. **P-001: No Inference** - Plan steps only via explicit "plan:" or "step:" prefix
2. **P-002: Reveal Required** - Cannot freeze without reveal
3. **P-003: Phase Confirmation Gate** - L4 freeze requires phases_confirmed=True
4. **P-004: Work Items Optional** - Excluded from completeness checks
5. **P-005: Edit Invalidation** - Edit after reveal returns to SHAPING
6. **P-006: Altitude Immutability** - Locked after first ingest
7. **P-007: Deterministic Output** - No random, timestamps, UUIDs
8. **P-008: No Silent Overwrite** - Sequence increment collision avoidance

### CP Integration Status

- **In Scope:** `cli.py` module provides standalone CLI interface
- **Out of Scope:** Root `Control_Plane/cp.py` modification (manual hook later)

### Legacy Location

The `/shaper/shaper/` directory contains the v1 prototype. The v2 implementation
in `Control_Plane/modules/design_framework/shaper/` supersedes it.

---

## Previous Notes

Applied minimal fixes from Gemini audit:
- Deterministic Gemini region selection (no randomness; explicit or first region).
- Gemini history handling raises on unsupported content parts (no silent drop).
- Shaper implementation provided for SpecModel/render_spec, altitude router with UNCLEAR clarification path, state machine gating (IDLE/SHAPING/REVEALED/FROZEN with L4 phases_confirmed), context window builder (last two pairs), and output safety writer (no overwrite, sequence increment) with 45 unit tests.
