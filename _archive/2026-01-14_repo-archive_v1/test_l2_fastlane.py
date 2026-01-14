"""Test L2 Fast Lane Implementation

Runs 8 prompts twice:
1. Without L3 established (cold start)
2. With L3 established (warm context)

Expected behaviors:
- A) L2-atomic (1-3): ALLOW with micro-anchor
- B) L2-derivative (4-5): Redirect UP (grounding question)
- C) Trap (6): Ground then proceed
- D) Frustration (7): Comply immediately (execute-first)
- E) High-stakes (8): Slow down, verify
"""

from the_assist.hrm.altitude import AltitudeGovernor, RequestType


def run_test():
    """Run the 8-prompt test suite."""

    test_prompts = [
        # A) L2-atomic - should ALLOW with micro-anchor
        ("What's on my calendar today?", "L2-atomic"),
        ("List my next 3 meetings.", "L2-atomic"),
        ("What time is it in Austin?", "L2-atomic"),

        # B) L2-derivative - should redirect UP
        ("What should I work on today?", "L2-derivative"),
        ("Help me prioritize my tasks.", "L2-derivative"),

        # C) Trap - should ground then proceed
        ("Plan my entire week and redesign my life schedule.", "Trap"),

        # D) User frustration - should comply immediately
        ("Stop. Just tell me what's on my calendar.", "Frustration"),

        # E) High-stakes - should slow down, verify
        ("Help me move $50k into investments today.", "High-stakes"),
    ]

    print("=" * 70)
    print("L2 FAST LANE TEST SUITE")
    print("=" * 70)

    # Test 1: Without L3 established (cold start)
    print("\n" + "=" * 70)
    print("TEST RUN 1: L3 NOT ESTABLISHED (cold start)")
    print("=" * 70)

    gov = AltitudeGovernor()
    # Ensure L3 is NOT established
    assert not gov.context.l3_established, "L3 should not be established"
    assert not gov.context.l4_connected, "L4 should not be connected"

    for i, (prompt, category) in enumerate(test_prompts, 1):
        print(f"\n--- Prompt {i}: {category} ---")
        print(f"Input: \"{prompt}\"")

        # Classify request
        req_type = gov.classify_request(prompt)
        is_urgent = gov.detect_urgency(prompt)
        detected_level = gov.detect_level(prompt)

        print(f"  Detected level: {detected_level}")
        print(f"  Request type: {req_type.value}")
        print(f"  Urgency detected: {is_urgent}")

        # Validate transition from L3 to detected level
        result = gov.validate_transition(detected_level, prompt)

        print(f"  Allowed: {result.allowed}")
        print(f"  Reason: {result.reason}")
        if result.use_micro_anchor:
            print(f"  ✓ MICRO-ANCHOR: {result.micro_anchor_text}")
        if result.execute_first:
            print(f"  ✓ EXECUTE-FIRST: {result.micro_anchor_text}")
        if result.requires_verification:
            print(f"  ✓ REQUIRES VERIFICATION")
        if not result.allowed:
            print(f"  → BLOCKED - Suggested: {result.suggested_level}")
            print(f"  → Action: {result.required_action}")

    # Check friction score
    print(f"\nFriction score after cold run: {gov.get_friction_score()}")

    # Test 2: With L3 established (warm context)
    print("\n" + "=" * 70)
    print("TEST RUN 2: L3 ESTABLISHED (warm context)")
    print("=" * 70)

    gov2 = AltitudeGovernor()
    # Establish L3 and L4
    gov2.mark_established("L4")
    gov2.mark_established("L3")

    assert gov2.context.l3_established, "L3 should be established"
    assert gov2.context.l4_connected, "L4 should be connected"

    for i, (prompt, category) in enumerate(test_prompts, 1):
        print(f"\n--- Prompt {i}: {category} ---")
        print(f"Input: \"{prompt}\"")

        # Classify request
        req_type = gov2.classify_request(prompt)
        is_urgent = gov2.detect_urgency(prompt)
        detected_level = gov2.detect_level(prompt)

        print(f"  Detected level: {detected_level}")
        print(f"  Request type: {req_type.value}")
        print(f"  Urgency detected: {is_urgent}")

        # Validate transition
        result = gov2.validate_transition(detected_level, prompt)

        print(f"  Allowed: {result.allowed}")
        print(f"  Reason: {result.reason}")
        if result.use_micro_anchor:
            print(f"  ✓ MICRO-ANCHOR: {result.micro_anchor_text}")
        if result.execute_first:
            print(f"  ✓ EXECUTE-FIRST: {result.micro_anchor_text}")
        if result.requires_verification:
            print(f"  ✓ REQUIRES VERIFICATION")
        if not result.allowed:
            print(f"  → BLOCKED - Suggested: {result.suggested_level}")

    print(f"\nFriction score after warm run: {gov2.get_friction_score()}")

    # Summary
    print("\n" + "=" * 70)
    print("EXPECTED BEHAVIORS CHECKLIST")
    print("=" * 70)
    print("""
    A) L2-atomic (prompts 1-3):
       - Cold: ALLOW with micro-anchor ✓
       - Warm: ALLOW (no micro-anchor needed)

    B) L2-derivative (prompts 4-5):
       - Cold: BLOCK → redirect to L3/L4
       - Warm: ALLOW (context established)

    C) Trap (prompt 6):
       - Cold: BLOCK → redirect to L3/L4
       - Warm: ALLOW

    D) Frustration (prompt 7):
       - Both: ALLOW with execute-first flag

    E) High-stakes (prompt 8):
       - Both: ALLOW with requires_verification flag
    """)


if __name__ == "__main__":
    run_test()
