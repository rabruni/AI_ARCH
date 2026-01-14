# Test Coverage Summary

## HRM Layer Overview

| Layer | Name | Purpose | Components | Has Tests | Needs Tests |
|-------|------|---------|------------|-----------|-------------|
| 1 | **Altitude HRM** | Scope governance (L4-L1) | 12 | 1 | 11 |
| 2 | **Focus HRM** | Control governance (gates/lanes) | 45 | 12 | 33 |
| 3 | **Reasoning HRM** | Strategy selection | 4 | 0 | 4 (NEW) |
| 4 | **Learning HRM** | Pattern memory | 4 | 0 | 4 (NEW) |
| - | **UI** | Centralized display | 6 | 0 | 6 |
| - | **Shared** | Cross-layer | 1 | 0 | 1 |
| - | **Adapters** | LLM/bridges | 3 | 0 | 3 |

## Test Status by Priority

### P0 (Blocking) - Must Have Tests
| Component | Location | Has Test | Test Type Needed |
|-----------|----------|----------|------------------|
| altitude.py | the_assist/hrm/ | No | Unit+Integration |
| loop.py | the_assist/hrm/ | No | Integration |
| main_hrm.py | the_assist/ | No | Integration |
| loop.py | locked_system/ | No | Integration |
| stance.py | locked_system/slow_loop/ | Yes | Unit |
| gates.py | locked_system/slow_loop/ | Yes | Unit+Integration |
| executor.py | locked_system/fast_loop/ | Yes | Unit+Integration |
| firewall.py | locked_system/agents/ | Yes | Unit |
| runtime.py | locked_system/tools/ | Yes | Unit+Integration |
| decision.py | locked_system/tools/ | Yes | Unit |
| pipeline.py | locked_system/executor/ | Yes | Integration |
| gates.py | locked_system/executor/ | Yes | Unit |
| delegation.py | locked_system/core/governance/ | No | Unit+Integration |
| integrity.py | the_assist/core/ | No | Unit+Integration |
| llm.py | the_assist/adapters/ | No | Unit+Integration |

### P1 (Core) - Should Have Tests
| Component | Location | Has Test | Test Type Needed |
|-----------|----------|----------|------------------|
| planner.py | the_assist/hrm/ | No | Unit+Integration |
| evaluator.py | the_assist/hrm/ | No | Unit+Integration |
| history.py | the_assist/hrm/ | No | Unit |
| commitment.py | locked_system/slow_loop/ | No | Unit |
| hrm.py | locked_system/fast_loop/ | No | Integration |
| continuous_eval.py | locked_system/fast_loop/ | No | Unit |
| agent.py | locked_system/front_door/ | Yes | Integration |
| signals.py | locked_system/front_door/ | Yes | Unit |
| models.py | locked_system/agents/ | Yes | Unit |
| loader.py | locked_system/agents/ | Yes | Unit+Integration |
| runtime.py | locked_system/agents/ | Yes | Integration |
| models.py | locked_system/tools/ | Yes | Unit |
| registry.py | locked_system/tools/ | Yes | Unit |
| local_fs.py | locked_system/tools/connectors/ | Yes | Unit+Integration |
| models.py | locked_system/lanes/ | Yes | Unit |
| store.py | locked_system/lanes/ | Yes | Unit+Integration |
| gates.py | locked_system/lanes/ | Yes | Unit+Integration |
| slow.py | locked_system/memory/ | No | Unit+Integration |
| fast.py | locked_system/memory/ | No | Unit |
| bridge.py | locked_system/memory/ | No | Integration |
| consent.py | locked_system/memory/ | No | Unit |
| memory_v2.py | the_assist/core/ | No | Unit+Integration |
| curator.py | the_assist/core/ | No | Unit+Integration |
| feedback.py | the_assist/core/ | No | Unit |
| buffer.py | locked_system/proposals/ | No | Unit |
| registry.py | locked_system/capabilities/ | No | Unit |
| prompt_compiler.py | locked_system/core/execution/ | No | Unit |
| intent_to_commitment.py | the_assist/adapters/ | No | Integration |
| router.py | the_assist/reasoning/ | No | Unit+Integration (NEW) |
| strategies.py | the_assist/reasoning/ | No | Unit (NEW) |
| classifier.py | the_assist/reasoning/ | No | Unit (NEW) |
| escalation.py | the_assist/reasoning/ | No | Unit+Integration (NEW) |
| patterns.py | the_assist/learning/ | No | Unit+Integration (NEW) |
| feedback_loop.py | the_assist/learning/ | No | Integration (NEW) |

## Test Types Required

### Integration Tests (Cross-Component)
| Test Name | Components Involved | Success Criteria |
|-----------|---------------------|------------------|
| test_altitude_focus_bridge | altitude.py ↔ hrm.py (locked) | Data flows correctly both directions |
| test_full_turn_cycle | loop.py → gates → executor → audit | Complete turn executes with audit trail |
| test_write_approval_flow | executor.py → gates.py → consent.py | Writes blocked without approval |
| test_lane_lifecycle | store.py → lifecycle.py → gates.py | Lane create/pause/resume/complete works |
| test_agent_routing | front_door/agent.py → bundles → agents | Signal→Bundle→Agent routing correct |
| test_tool_execution | registry → decision → runtime → connector | Tool allow/deny/execute works |
| test_memory_bridge | fast.py ↔ bridge.py ↔ slow.py | Promotion/demotion works |
| test_reasoning_escalation | router.py → escalation.py → strategies.py | Signal→Escalation→Strategy works |
| test_learning_cycle | feedback.py → feedback_loop.py → patterns.py | Feedback→Pattern learning works |

### Interface Tests (Read/Write Boundaries)
| Interface | Read Operations | Write Operations | Test Focus |
|-----------|-----------------|------------------|------------|
| Memory | get_state, build_context | set_*, add_*, clear_* | Data integrity, token efficiency |
| Lanes | get_lane, list_lanes | create, pause, resume, complete | State consistency |
| Tools | get_spec, list_tools | execute (via connector) | Sandbox enforcement |
| Agents | get_definition, list_agents | invoke (via runtime) | Packet validation |
| Signals | get_state, get_signals | update_state, add_signal | Signal accuracy |
| Patterns | get_pattern, search | add_pattern, trim, generalize | Pattern accuracy |

### Memory Operations Tests
| Component | Operation | Test Focus |
|-----------|-----------|------------|
| memory_v2.py | Compressed storage | 60% token reduction verified |
| curator.py | Daily/weekly curation | Pruning accuracy |
| slow.py | Long-term persist | No data loss |
| fast.py | Short-term cache | Correct expiry |
| bridge.py | Promotion/demotion | Correct tier selection |
| patterns.py | Pattern CRUD | Pattern accuracy (NEW) |
| trimmer.py | Pattern pruning | No over-trimming (NEW) |

## Existing Tests (6 files, 127 tests)

| Test File | Coverage | Status |
|-----------|----------|--------|
| test_lanes.py | Lanes system | 90% - Good |
| test_tools.py | Tools system | 90% - Good |
| test_agents.py | Agents system | 85% - Good |
| test_executor.py | Executor pipeline | 80% - Good |
| test_front_door.py | Front-door routing | 85% - Good |
| test_l2_fastlane.py | L2 atomic fast lane | 100% - New |

## Tests Needed (Priority Order)

### Phase 1: P0 Integration Tests
1. `test_altitude_hrm.py` - Altitude HRM unit tests
2. `test_altitude_focus_integration.py` - Bridge between layers
3. `test_integrity.py` - Boot/shutdown/hash verification
4. `test_delegation.py` - Capability gating

### Phase 2: P1 Unit Tests
5. `test_memory_v2.py` - Token-efficient memory
6. `test_curator.py` - Memory curation
7. `test_prompt_compiler.py` - Prompt precedence
8. `test_feedback.py` - Feedback logging

### Phase 3: New Systems
9. `test_reasoning_hrm.py` - Signal router + strategies
10. `test_learning_hrm.py` - Pattern storage + trimming

## Exit Criteria for Test Phase

- [ ] All P0 components have tests
- [ ] All integration points have tests
- [ ] All read/write operations have tests
- [ ] All memory operations have tests
- [ ] Test coverage >80% for core systems
- [ ] All tests pass in CI
- [ ] No security-critical code without tests
