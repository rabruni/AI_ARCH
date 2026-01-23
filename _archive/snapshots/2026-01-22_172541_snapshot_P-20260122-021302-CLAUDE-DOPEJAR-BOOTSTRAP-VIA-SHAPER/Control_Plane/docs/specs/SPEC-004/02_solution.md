# Solution — Kernel (SPEC-004)

Introduce a **Pluggable Cognitive Kernel** with:

1. **Profiles**
   - `PersonaProfile`: user-facing persona + UX invariants + default governance parameters (versioned, released by sprint).
   - `StackProfile`: a concrete module set (attention modules, memory policy, ingestion policy) + capability envelope + risk tier.

2. **Kernel “Ports” (stable interfaces)**
   - `MemoryPort`: authoritative state store + event log API with explicit retention/consent policy.
   - `IngestionPort`: converts external sources into normalized evidence items (no direct actions).
   - `LLMPort`: optional text-generation backend; provides proposals only; cannot commit state directly.
   - `ToolPort`: optional read-only tools; requires explicit delegation and audit.
   - `UIPort`: consistent interaction shell that renders status and accepts commands.

3. **Routing**
   - A deterministic routing policy chooses the active `StackProfile` (persona + task type + risk tier).
   - Runtime routing is limited to selecting from released stack profiles. Mid-session hot swaps are disallowed; change requires reset/transition.

4. **Governance invariants**
   - Authority separation (proposals vs decisions).
   - Commitment/parking semantics to support human interruptions without losing context.
   - Deterministic event semantics and metrics to evaluate stacks and modules.
