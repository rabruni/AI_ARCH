# Startup & Entry Paths

## Purpose
This document describes how the Locked System starts up and processes requests, based on code inspection of entry points and initialization sequences.

## Inputs
- Command-line arguments (optional config path)
- Environment variables (ANTHROPIC_API_KEY)
- Configuration file (optional YAML)

## Outputs
- Running LockedLoop instance
- Interactive CLI session or single response
- Log files and memory persistence

## Key Call Paths

### Primary Entry Point (`main.py`)
```python
# locked_system/main.py
from locked_system.cli.main import main
if __name__ == "__main__":
    main()
```

### CLI Main Flow (`cli/main.py`)
1. **Load environment** (dotenv if available)
2. **Parse arguments** (config path, message, JSON output)
3. **Load configuration** (defaults or YAML file)
4. **Create LLM callable** (Claude or placeholder)
5. **Initialize LockedLoop** with config and LLM
6. **Run mode**: interactive or single message

### LockedLoop Initialization (`loop.py`)
1. **Store configuration** and extension hooks
2. **Initialize memory layers** (slow, fast, bridge, history)
3. **Initialize proposal buffer**
4. **Initialize slow loop components** (stance, commitment, gate controller)
5. **Initialize fast loop components** (HRM, executor, continuous eval)
6. **Initialize sensing** (perception, contrast)
7. **Initialize delegation manager**
8. **Initialize capabilities** (note capture with authorization)
9. **Initialize signals subsystem** (collector, computer, display)
10. **Initialize consent manager**
11. **Load conversation history** (if consent allows)

## Startup Sequence Details

### Configuration Loading
```python
# From cli/main.py
config = Config()
if args.config:
    config = Config.from_yaml(args.config)
```

### LLM Setup
```python
# From cli/main.py create_llm()
if os.environ.get("ANTHROPIC_API_KEY"):
    # Use Claude API
    llm_callable = claude_llm
else:
    # Use placeholder
    llm_callable = _create_placeholder_llm()
```

### Memory Initialization
```python
# From loop.py __init__()
self.slow_memory = SlowMemory(self.config.memory_dir / "slow")
self.fast_memory = FastMemory(self.config.memory_dir / "fast")
self.bridge_memory = BridgeMemory(self.config.memory_dir / "bridge")
self.history = History(self.config.memory_dir / "history")
```

### Component Wiring
```python
# Slow loop components
self.stance = StanceMachine()
self.commitment = CommitmentManager(self.slow_memory)
self.gate_controller = GateController(self.stance, self.commitment, ...)

# Fast loop components
self.hrm = HRM()
self.executor = Executor(self.fast_memory, llm_callable)
self.continuous_eval = ContinuousEvaluator(self.proposal_buffer)
```

## Interactive Session Flow (`run_interactive()`)
1. **Initialize session logger** and chat UI
2. **Check consent** on first run (conversation/signals/preferences)
3. **Show header** with LLM status
4. **Enter main loop**:
   - Get user input via UI
   - Process through `LockedLoop.process()`
   - Display response
   - Handle commands (:quit, :clear, :state, etc.)
5. **Cleanup** on exit (save logs, close UI)

## Single Message Flow
1. **Create LockedLoop** instance
2. **Call `process()`** with user message
3. **Output result** (JSON or text format)
4. **Exit**

## Key Code Evidence
- **Entry point**: `locked_system/main.py` (lines 1-8)
- **CLI logic**: `locked_system/cli/main.py` `main()` function
- **Loop init**: `locked_system/loop.py` `LockedLoop.__init__()` (lines 70-140)
- **Interactive mode**: `cli/main.py` `run_interactive()` (lines 120-200)
- **Configuration**: `locked_system/config.py` `Config` class and YAML loading

## Extension Points
- **LLM callable**: Can be replaced for testing or different models
- **Hooks**: `on_gate_transition`, `on_response_generated`, `prompt_enhancer`
- **Capabilities**: Note capture and other features can be added via delegation
- **Memory backends**: Different storage implementations possible

## Error Handling
- **API failures**: Falls back to placeholder LLM
- **Config errors**: Uses defaults with validation warnings
- **Memory issues**: Continues with reduced functionality
- **Consent denied**: Disables memory persistence gracefully</content>
<parameter name="filePath">/Users/raymondbruni/AI_ARCH/code_derived_docs/startup_entry_paths.md