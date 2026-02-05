## 2026-02-04 - Enforce TokenBucket Invariants
**Rule:** TokenBucket parameters (capacity, fill_rate) and consumption amount must be non-negative.
**Gap:** `TokenBucket` class in `layer7_anti_ddos_suite/adaptive_rate_limit_engine.py` allowed negative values, leading to impossible states (negative capacity) or logical errors (consuming negative tokens refilled the bucket).
**Fix:** Added validation checks in `__init__` and `consume` to raise `ValueError` for invalid inputs.
**Lesson:** Utility classes used in security contexts must validate their inputs strictly to prevent bypasses or instability, especially when parameters are dynamically calculated.

## 2026-02-04 - Enforce Orchestrator Config Invariants
**Rule:** Time intervals and rate limits must be positive; weights must be non-negative.
**Gap:** `under_attack_orchestrator.py` ConfigLoader accepted any values, risking infinite loops or logic errors with negative rates.
**Fix:** Added `_validate_config` to `ConfigLoader` to enforce strict positivity on critical parameters.
**Lesson:** Configuration loading is an input boundary; treat config files as untrusted user input.
