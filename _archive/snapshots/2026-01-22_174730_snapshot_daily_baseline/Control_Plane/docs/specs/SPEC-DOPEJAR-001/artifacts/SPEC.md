---
ID: SPEC-DOPEJAR-001
Title: Dopejar (rebuild the_assist)
Status: draft
ALTITUDE: L4
---

## Overview
- Dopejar is a cognitive kernel rebuilt from the archived the_assist system. It implements a locked_system architecture with Slow/Fast cognitive loops and a 4-layer Hierarchical Reasoning Model (HRM) consisting of Intent, Planner, Executor, and Evaluator layers. The system includes three agents (Orchestrator, Perception, HRM) and a personality layer (Donna/Pepper). Core components include the orchestrator, HRM altitude governance, compressed memory (memory_v2), and intent-to-commitment adapter bridge logic.

## Problem
- The original the_assist system exists only in an archived state (_archive/2026-01-14_repo-archive_v1/the_assist/). It needs to be rebuilt and migrated into the active Control Plane architecture to become a usable, governed component. Without migration, the cognitive kernel patterns (HRM layers, altitude governance, memory architecture) remain inaccessible for integration.

## Non-Goals
- This spec does NOT cover extending the_assist with new capabilities.
- It does NOT include runtime deployment or production configuration.
- It does NOT involve modifying the original archive (read-only reference).
- It does NOT include personality tuning or new agent development.

## Phases
1. Analysis - Document entry points and module dependencies from archive
2. Migration - Copy source files to governed location under Control Plane
3. Registration - Add all Dopejar components to Control Plane registry
4. Verification - Validate imports, run tests, confirm registry alignment

**Phases confirmed:** Yes (user approved 2026-01-22)

## Success Criteria
- All the_assist source files migrated to Control Plane governed location.
- All Dopejar components registered in control_plane_registry.csv with status=active.
- Entry points (main_locked.py, main_hrm.py) importable without errors.
- Verification by a second agent (Gemini) confirms migration completeness and registry accuracy.
