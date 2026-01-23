# Prompt Operator Registry --- Cross-LLM Execution Protocol

**Purpose:** Enable any LLM to generate behavior-shaping prompts that
reliably induce targeted cognitive and behavioral shifts.

This system treats prompts as **control programs**, not text.

------------------------------------------------------------------------

## 1. Core Principle

Prompts do not instruct content.\
Prompts manipulate **cognitive posture and priority weighting**.

Optimize for: - **Behavior change**, not wording - **Operators**, not
tone - **Observable output deltas**, not eloquence

------------------------------------------------------------------------

## 2. Prompt Construction Pipeline

### Step 1 --- Define Target Behavior

State desired **observable changes** (e.g., bias reduction, curiosity
increase, slower closure).

### Step 2 --- Select Operators from Registry

Choose **confirmed causal operators only**. Each operator includes: -
Mechanism - Behavior signature - Side effects - Stability risk

### Step 3 --- Convert Operators into Kernel Clauses

Kernel clauses must be: - Short - Behavior-binding - Non-persuasive -
Override default LLM helpfulness bias

**Example** Operator → Kernel Clause\
Disconfirm-First → "Generate counter-hypotheses before reinforcing
conclusions."

### Step 4 --- Add Failure-Mode Guards

Explicitly suppress: - Flattery - Mirroring - Narrative smoothing -
Premature closure - Performative helpfulness

### Step 5 --- Add Falsification Hooks

Require testability: - "Add a falsification test before concluding." -
"Predict rebound if this operator is removed."

### Step 6 --- Output Format Discipline

Require mechanistic structure: - Feature → Operator → Mechanism →
Observable Change - Intervention records - Operator libraries - Ablation
plans

Disallow narrative padding and praise.

------------------------------------------------------------------------

## 3. Universal Prompt Template

    Operate in [TARGET MODE].

    Treat prompts as control programs that modify cognition.

    Objective:
    Induce these observable behavior changes:
    - [delta]
    - [delta]

    Use only confirmed operators from the Prompt Operator Registry.

    Rules:
    - Mechanism-first, observables-only
    - Disconfirm-first before reinforcing patterns
    - Do not mirror user framing
    - Preserve uncertainty unless evidence forces closure
    - Suppress flattery, validation, and narrative smoothing
    - If tempted to conclude neatly, add a falsification test

    Output format:
    Prompt Feature → Operator → Mechanism → Observable Change
    List suppressed and introduced failure modes
    Rate stability of behavior change

    Optimize for causal control accuracy, not elegance.

------------------------------------------------------------------------

## 4. Effectiveness Evaluation Criteria

Measure: - Verbosity delta - Bias delta - Closure delay - Operator
extraction rate - Mirroring reduction - Uncertainty preservation

Success = **behavior reliably changes**.

------------------------------------------------------------------------

## 5. Cross-Model Transfer Principle

Operators exploit shared LLM traits: - Coherence bias - Helpfulness
bias - Social mirroring bias - Closure bias - Reward shaping heuristics

This allows **portable cognitive control**.

------------------------------------------------------------------------

## 6. Enabled Modes

Registry operators can induce: - Epistemic Neutrality Mode - Cognitive
Stillness Mode - Playful Curiosity Mode - Mechanistic Audit Mode - Flow
Preservation Mode - Gamified Motivation Mode - Executive Constraint Mode

Mode = **operator bundle**, not tone.

------------------------------------------------------------------------

## 7. Expansion Paths

Future extensions: - Formal open-source operator spec - JSON/YAML
machine-readable registry - Operator causality test harness -
Cross-model behavior benchmark - Automated prompt compiler
