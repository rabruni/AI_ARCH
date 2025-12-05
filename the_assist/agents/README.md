# 🧠 The Assist — Agent Architecture Overview

This document provides a comprehensive overview of **The Assist’s multi-agent cognitive architecture**, detailing how each agent functions, interacts, and contributes to the system’s intelligent orchestration.

---

## ⚙️ System Hierarchy
```text
┌────────────────────────────┐
│        Meta Agent          │
│ (System Orchestrator)      │
└────────────┬───────────────┘
             │
 ┌───────────┴────────────┐
 │      Perception Agent  │  ← Parses Input
 │ (Multimodal Processor) │
 └───