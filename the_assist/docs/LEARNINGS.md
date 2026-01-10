# HRM Development Learnings

Lightweight capture. Fail fast, learn fast.

---

## Session: 2026-01-10

### What happened
- Started with multi-agent architecture (perception + hrm agents)
- Hit same wall as everyone: features to fix architecture
- User pushed for true HRM, provided framework documentation
- Rebuilt with 4 clean layers

### Key learnings

**L1: Intent must be explicit**
- "Partner" was stated but not enforced
- Non-goals weren't defined → allowed drift
- Fix: Intent Store with authority, not just data

**L2: Separation prevents pollution**
- Mixed concerns = rationalization
- Planner evaluating itself = blind spots
- Fix: Fresh context per layer (Chinese walls)

**L3: State vs Meaning**
- Executor was deciding meaning, not reporting state
- Led to tunnel vision, topic fixation
- Fix: Executor reports facts, upper layers interpret

**L4: Revision must be cheap**
- Couldn't revise plan without replaying execution
- Made iteration expensive
- Fix: Layers with stable interfaces

### Pattern detected
```
Symptom: Feature stacking without progress
Cause: Architecture problem being patched with features
Signal: Same issue returns despite "fix"
Resolution: Step back to layer separation
```

### What to watch for
- [ ] Am I stating intent at session start?
- [ ] Am I planning before executing?
- [ ] Am I reporting state, not just output?
- [ ] Am I evaluating against intent, not just "did it work"?

---

## Format for future entries

```
## Session: YYYY-MM-DD

### What happened
[2-3 lines max]

### Key learnings
[Bullets, not prose. Code/pattern format preferred.]

### Pattern detected
[If recurring pattern, capture in structured format]

### What to watch for
[Checklist for next session]
```
