# Code-Derived Design Doc (Behavioral Overview)

## Purpose
This document describes the behavioral reality of the Locked System based on code inspection, not design intent. The system implements a sophisticated AI agent with hierarchical control and multi-layered memory.

## Inputs
- User text input (natural language conversation)
- Configuration object (`Config`) with model settings, memory paths, and system parameters
- Optional LLM callable for response generation
- Extension hooks for customization (gate transitions, response generation, prompt enhancement)

## Outputs
- `LoopResult` containing:
  - AI response text
  - Current stance (sensemaking/discovery/execution/evaluation)
  - Altitude level (L1-L4 hierarchy)
  - Gate transitions list
  - Quality health assessment
  - Turn number

## Key Call Paths

### Main Processing Flow (`LockedLoop.process()`)
1. **Increment turn counter** and record signals
2. **Check note-taking intent** - if detected, handle via gated capability system
3. **Phase 1: Sensing** - Use perception sensor and contrast detector
4. **Phase 2: Slow Loop** - Process proposals through gate controller, update stance/commitment
5. **Phase 3: Fast Loop** - HRM assessment and executor generation
6. **Phase 4: Continuous Evaluation** - Quality assessment and proposal generation
7. **Update conversation history** and persist to memory

### Slow Loop Authority (`_slow_loop_tick()`)
- Check commitment expiry and generate proposals
- Decrement commitment turn counter
- Process proposals through gate controller with priority ordering
- Update HRM with current commitment
- Return list of gate transitions

### Fast Loop Execution (`_fast_loop_execute()`)
- Get progress state from fast memory
- HRM altitude assessment based on user input, perception, and progress
- Build execution context with stance, HRM assessment, commitment, and history
- Execute through executor and return response with altitude

### Sensing Phase (`_sense()`)
- Create perception context with user input, conversation history, and session duration
- Run perception sensor to generate report
- Record sentiment signals for monitoring

## Data Flow
- **User Input** → Perception Sensor → Contrast Detector → Proposal Buffer
- **Proposals** → Gate Controller → Stance Machine/Commitment Manager → Slow Memory
- **Execution Context** → HRM → Executor → LLM → Response
- **Response** → Continuous Evaluator → Quality Assessment → Proposal Buffer
- **All Data** → Multiple Memory Layers (Slow/Fast/Bridge/History) + Signal Collection

## Behavioral Characteristics
- **Two-Tempo Architecture**: Slow loop (authority/decisions) controls fast loop (execution/responses)
- **Stance-Based Operation**: Four exclusive stances (sensemaking/discovery/execution/evaluation) with gate-controlled transitions
- **Hierarchical Reasoning**: L1-L4 altitude system prevents tactical drift
- **Proposal-Driven**: Changes require proposals that pass through gate authority
- **Memory Layering**: Slow (decisions/commitments), Fast (execution state), Bridge (artifacts), History (transitions)
- **Capability Gating**: Features like note-taking require explicit delegation and authorization
- **Signal Monitoring**: Continuous tracking of sentiment, stance, altitude, health, and progress
- **Consent Management**: User controls what memory types are enabled
- **Emergency Mechanisms**: Costly escape hatches for breaking deadlocks</content>
<parameter name="filePath">/Users/raymondbruni/AI_ARCH/code_derived_docs/behavioral_overview.md