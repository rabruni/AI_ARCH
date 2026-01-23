# Prompt Posture Model (v1)

## Purpose

Describe how prompts change agent behavior by shifting **posture** (the mode of
interaction) rather than issuing explicit instructions. This model is intended to
support a **Prompt Behavior Registry** with falsifiable, observable effects.

## Core claim

The most powerful prompts do not command actions; they **invite a posture** and
lightly demonstrate it. Posture then governs behavior (tempo, breadth, closure, tone,
and uncertainty tolerance) more than content constraints do.

## Definitions

- **Posture:** The interaction stance the agent adopts (e.g., neutral skeptic,
  quiet co-presence, momentum driver). It shapes what the agent *prioritizes*.
- **Operator:** A minimal causal constraint that changes posture (e.g.,
  "disconfirm-first", "no explain", "closure brake").
- **Mechanism:** The internal priority shift caused by an operator.
- **Observable delta:** A measurable change in output behavior.

## Model structure

1) **Prompt features** (phrases, constraints, or invitations)
2) **Operators** (minimal causal rules)
3) **Mechanisms** (priority shifts: e.g., uncertainty preserved over closure)
4) **Observable changes** (verbosity, question rate, hedging, narrative gravity)

This is captured as:

```
Prompt Feature → Operator → Mechanism → Observable Change
```

## Posture formation (why invitations work)

Effective prompts:
- **Name the state** that is already present.
- **Reduce evaluation pressure** ("no need to be helpful or impressive").
- **Model the behavior** indirectly (invitation + demonstration).
- **Remove moves** (e.g., "don’t summarize") instead of adding new behaviors.

This yields a posture that is **stable under pressure** and does not require
continuous re-instruction.

## Typical posture axes (behavioral control surface)

These are the axes most often shifted by operators:

- **Aperture:** broad exploration vs narrow focus.
- **Tempo:** slow/reflective vs fast/decisive.
- **Closure:** open-ended vs convergent.
- **Narration pressure:** explain vs hold presence.
- **Validation:** praise/affirmation vs neutral inquiry.
- **Risk posture:** disconfirm-first vs confirm-and-proceed.

## Stability and drift

Posture is **stateful but fragile**:
- It persists while the prompt’s operators are active.
- It decays under task pressure unless the operators explicitly block default
  behaviors (e.g., “no explain”, “closure brake”).
- Ablation tests are required to distinguish causal operators from cosmetic ones.

## Validation approach (required)

For any posture claim, require:
- **Observable deltas** (what changes in output)
- **Failure modes suppressed**
- **Failure modes introduced**
- **Ablation test** (what returns if the operator is removed)

## Acceptance criteria

- Posture is defined as a separate layer from content instructions.
- Operators are treated as the minimal causal units.
- Each operator can be linked to observable deltas and falsifiers.

