# Tracing & Observability Design

## Purpose

Trace all messages and interactions through the 4-HRM system with:
- Unique trace IDs for request correlation
- Structured logging for debugging
- UI flag to toggle visibility
- Performance metrics

---

## Trace ID Format

```
{hrm}_{timestamp}_{random}

Examples:
- alt_1705180800_a3f2    # Altitude HRM operation
- foc_1705180800_b7c1    # Focus HRM operation
- rsn_1705180800_d4e5    # Reasoning HRM operation
- lrn_1705180800_f6g7    # Learning HRM operation
- mem_1705180800_h8i9    # Memory operation
- sys_1705180800_j0k1    # System operation
```

---

## Trace Event Structure

```python
@dataclass
class TraceEvent:
    trace_id: str              # Primary correlation ID
    parent_id: Optional[str]   # Parent trace (for nested operations)
    timestamp: datetime
    hrm_layer: str             # altitude|focus|reasoning|learning|memory|system
    operation: str             # read|write|transition|route|evaluate|execute
    component: str             # File/class that emitted
    input_summary: str         # Truncated input (max 100 chars)
    output_summary: str        # Truncated output (max 100 chars)
    duration_ms: int           # Operation duration
    status: str                # success|error|blocked
    metadata: dict             # Additional context
```

---

## Trace Points (Per HRM)

### Altitude HRM
| Operation | When | Trace Data |
|-----------|------|------------|
| `altitude.transition` | Level change | from_level, to_level, reason |
| `altitude.evaluate` | Plan evaluation | altitude, verdict, confidence |
| `altitude.plan` | Plan generation | altitude, intent, plan_summary |
| `altitude.execute` | Execution start | altitude, action_type |

### Focus HRM (HRM Routing)
| Operation | When | Trace Data |
|-----------|------|------------|
| `focus.stance_change` | Stance transition | from_stance, to_stance, gate |
| `focus.gate_check` | Gate evaluation | gate_type, decision, reason |
| `focus.lane_switch` | Lane change | from_lane, to_lane, reason |
| `focus.consent_check` | Consent evaluation | operation, allowed |
| `focus.route` | Signal routing | signal_type, bundle, agents |

### Reasoning HRM (Future)
| Operation | When | Trace Data |
|-----------|------|------------|
| `reasoning.classify` | Input classification | input_type, confidence |
| `reasoning.route` | Strategy selection | strategy, reason |
| `reasoning.escalate` | Escalation decision | from_level, to_level, trigger |

### Learning HRM (Future)
| Operation | When | Trace Data |
|-----------|------|------------|
| `learning.pattern_match` | Pattern recognized | pattern_code, confidence |
| `learning.pattern_add` | New pattern learned | pattern_code, source |
| `learning.pattern_trim` | Pattern pruned | pattern_code, reason |
| `learning.generalize` | Generalization | from_patterns, to_pattern |

### Memory
| Operation | When | Trace Data |
|-----------|------|------------|
| `memory.read` | Any read | namespace, key, tier |
| `memory.write` | Any write | namespace, key, tier, tokens_saved |
| `memory.promote` | Tier promotion | key, from_tier, to_tier |
| `memory.demote` | Tier demotion | key, from_tier, to_tier |

---

## Implementation

### 1. Tracer Singleton

```python
# shared/tracing/tracer.py

import os
import json
import logging
from datetime import datetime
from dataclasses import dataclass, asdict
from typing import Optional
from contextlib import contextmanager
import uuid

@dataclass
class TraceEvent:
    trace_id: str
    parent_id: Optional[str]
    timestamp: str
    hrm_layer: str
    operation: str
    component: str
    input_summary: str
    output_summary: str
    duration_ms: int
    status: str
    metadata: dict

class Tracer:
    _instance = None

    def __new__(cls):
        if cls._instance is None:
            cls._instance = super().__new__(cls)
            cls._instance._init()
        return cls._instance

    def _init(self):
        self.enabled = os.environ.get("DOPEJAR_TRACE", "0") == "1"
        self.logger = logging.getLogger("dopejar.trace")
        self._current_trace: Optional[str] = None
        self._trace_stack: list[str] = []

        # Configure logging if enabled
        if self.enabled:
            handler = logging.FileHandler("trace.jsonl")
            handler.setFormatter(logging.Formatter("%(message)s"))
            self.logger.addHandler(handler)
            self.logger.setLevel(logging.INFO)

    def generate_id(self, hrm: str) -> str:
        """Generate a trace ID."""
        ts = int(datetime.now().timestamp())
        rand = uuid.uuid4().hex[:4]
        return f"{hrm}_{ts}_{rand}"

    @contextmanager
    def span(self, hrm: str, operation: str, component: str, input_data: str = ""):
        """Context manager for tracing a span."""
        if not self.enabled:
            yield None
            return

        trace_id = self.generate_id(hrm)
        parent_id = self._trace_stack[-1] if self._trace_stack else None
        self._trace_stack.append(trace_id)

        start = datetime.now()
        status = "success"
        output = ""
        metadata = {}

        try:
            yield TraceContext(trace_id, lambda o, m: (output := o, metadata.update(m)))
        except Exception as e:
            status = "error"
            metadata["error"] = str(e)
            raise
        finally:
            duration = int((datetime.now() - start).total_seconds() * 1000)
            self._trace_stack.pop()

            event = TraceEvent(
                trace_id=trace_id,
                parent_id=parent_id,
                timestamp=start.isoformat(),
                hrm_layer=hrm,
                operation=operation,
                component=component,
                input_summary=input_data[:100],
                output_summary=str(output)[:100],
                duration_ms=duration,
                status=status,
                metadata=metadata
            )

            self.logger.info(json.dumps(asdict(event)))

    def event(self, hrm: str, operation: str, component: str,
              input_data: str = "", output_data: str = "",
              status: str = "success", metadata: dict = None):
        """Log a single trace event."""
        if not self.enabled:
            return

        event = TraceEvent(
            trace_id=self.generate_id(hrm),
            parent_id=self._trace_stack[-1] if self._trace_stack else None,
            timestamp=datetime.now().isoformat(),
            hrm_layer=hrm,
            operation=operation,
            component=component,
            input_summary=input_data[:100],
            output_summary=output_data[:100],
            duration_ms=0,
            status=status,
            metadata=metadata or {}
        )

        self.logger.info(json.dumps(asdict(event)))

class TraceContext:
    """Context for a trace span."""
    def __init__(self, trace_id: str, setter):
        self.trace_id = trace_id
        self._setter = setter

    def set_output(self, output: str, **metadata):
        self._setter(output, metadata)

# Global instance
tracer = Tracer()
```

### 2. Usage Examples

```python
# In altitude.py
from shared.tracing import tracer

class AltitudeGovernor:
    def transition(self, from_level: int, to_level: int, reason: str):
        with tracer.span("alt", "transition", "altitude.py",
                        f"L{from_level}→L{to_level}") as ctx:
            # ... do transition
            if ctx:
                ctx.set_output(f"success", reason=reason)

# In gates.py (Focus HRM)
from shared.tracing import tracer

class GateController:
    def check_gate(self, gate_type: str, context: dict) -> bool:
        tracer.event(
            hrm="foc",
            operation="gate_check",
            component="gates.py",
            input_data=gate_type,
            output_data="allowed" if allowed else "denied",
            metadata={"context": context}
        )
        return allowed

# In memory manager
from shared.tracing import tracer

class MemoryManager:
    def write(self, namespace: str, key: str, data: dict):
        with tracer.span("mem", "write", "manager.py",
                        f"{namespace}.{key}") as ctx:
            # ... do write
            if ctx:
                ctx.set_output("written", tokens_saved=45)
```

---

## UI Integration

### Environment Flag
```bash
# Enable tracing
export DOPEJAR_TRACE=1
python -m the_assist.main

# Disable (default)
export DOPEJAR_TRACE=0
```

### CLI Flag
```bash
# Add to run.sh
python -m the_assist.main --trace

# Or via config
# config/settings.yaml
tracing:
  enabled: true
  output: trace.jsonl
  level: info  # debug|info|warn
```

### Real-time Display (Optional)
```python
# In UI module - only show if flag enabled
if os.environ.get("DOPEJAR_TRACE") == "1":
    print(f"[TRACE] {event.hrm_layer}.{event.operation}: {event.input_summary}")
```

---

## Trace Output Format

### JSONL File (trace.jsonl)
```jsonl
{"trace_id":"alt_1705180800_a3f2","parent_id":null,"timestamp":"2026-01-13T14:00:00","hrm_layer":"altitude","operation":"transition","component":"altitude.py","input_summary":"L3→L2","output_summary":"success","duration_ms":5,"status":"success","metadata":{"reason":"user requested tactical"}}
{"trace_id":"foc_1705180801_b7c1","parent_id":"alt_1705180800_a3f2","timestamp":"2026-01-13T14:00:01","hrm_layer":"focus","operation":"gate_check","component":"gates.py","input_summary":"WriteApprovalGate","output_summary":"allowed","duration_ms":2,"status":"success","metadata":{"user_consent":true}}
{"trace_id":"mem_1705180802_c8d2","parent_id":"foc_1705180801_b7c1","timestamp":"2026-01-13T14:00:02","hrm_layer":"memory","operation":"write","component":"manager.py","input_summary":"altitude.session","output_summary":"written","duration_ms":3,"status":"success","metadata":{"tokens_saved":45,"tier":"warm"}}
```

### Console Output (when --trace flag)
```
[alt] transition: L3→L2 → success (5ms)
  └─[foc] gate_check: WriteApprovalGate → allowed (2ms)
      └─[mem] write: altitude.session → written (3ms) [saved 45 tokens]
```

---

## Trace Analysis Tools

### 1. Trace Viewer CLI
```bash
# View recent traces
python -m shared.tracing.viewer --last 100

# Filter by HRM
python -m shared.tracing.viewer --hrm altitude

# Filter by status
python -m shared.tracing.viewer --status error

# Show trace tree for a request
python -m shared.tracing.viewer --trace-id alt_1705180800_a3f2
```

### 2. Performance Summary
```bash
python -m shared.tracing.stats

# Output:
# HRM Layer Stats (last 1000 events):
# - altitude: 150 ops, avg 8ms, 2 errors
# - focus: 400 ops, avg 3ms, 0 errors
# - memory: 450 ops, avg 2ms, 1 error
#
# Slowest operations:
# 1. alt_transition: 45ms (L4→L2 skip)
# 2. mem_write: 23ms (cold tier archive)
```

---

## Integration Order

1. **Create shared/tracing/**: tracer.py, viewer.py, stats.py
2. **Add to Altitude HRM**: altitude.py, loop.py, evaluator.py
3. **Add to Focus HRM**: gates.py, stance.py, executor.py
4. **Add to Memory**: manager.py (when created)
5. **Add UI flag**: run.sh, settings.py, formatter.py

---

## Success Criteria

- [ ] All HRM transitions emit trace events
- [ ] All gate checks emit trace events
- [ ] All memory operations emit trace events
- [ ] Trace output is valid JSONL
- [ ] Parent/child correlation works
- [ ] UI flag toggles visibility
- [ ] Performance overhead <1ms per event
- [ ] Trace viewer CLI works
