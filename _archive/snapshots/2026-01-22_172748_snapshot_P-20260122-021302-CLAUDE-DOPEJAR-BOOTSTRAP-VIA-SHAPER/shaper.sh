#!/bin/bash
# Shaper CLI - Interactive artifact shaping (L3 work items, L4 specs)

echo "═══════════════════════════════════════════════════════════"
echo "  SHAPER v2 - Altitude-Aware Artifact Shaper"
echo "═══════════════════════════════════════════════════════════"
echo ""
echo "  Altitudes:"
echo "    L3 = Work Item (objective, scope, plan, acceptance)"
echo "    L4 = Spec (overview, problem, non-goals, phases, success)"
echo ""
echo "  Triggers:"
echo "    'show me what you have' → reveal current state"
echo "    'freeze it'             → finalize and save artifact"
echo ""
echo "  Prefixes:"
echo "    objective: / scope: / plan: / acceptance:  (L3)"
echo "    overview: / problem: / non-goal: / phase: / success:  (L4)"
echo "    ID: / Title: / Status: / ALTITUDE:  (metadata)"
echo ""
echo "═══════════════════════════════════════════════════════════"
echo ""

# Run the shaper
python3 Control_Plane/cp.py shape "$@"
