## 2026-02-05 - Handshake State Hardening
**Pattern:** Fake clients advancing protocol state with zero-payload or short packets.
**Learning:** The previous state machine advanced unconditionally upon receiving any packet. This allowed "zombie" connections to appear authenticated by sending 3 bytes of garbage.
**Prevention:** Enforce strict payload minimum lengths for each state transition (`STATE_INIT` > 4B, `KEY` > 32B, `AUTH` > 16B).
