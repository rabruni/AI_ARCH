# Requirements

- Artifact-first authority: frozen artifacts are the source of intent.
- No execution during shaping: shaping produces text artifacts only.
- Determinism: artifacts must not include timestamps/UUIDs/randomness.
- No silent overwrite of outputs: new outputs must be uniquely named.
- Phase confirmation gate (L4): phases are not accepted unless explicitly confirmed.
