## 2025-02-20 - [Optimize log anomaly detector]
**Learning:** `datetime.now()` in a tight loop is expensive (~13.5% overhead combined with re.compile).
**Action:** Extract invariant time calculations to module level for batch processing scripts, but be wary of long-running processes.
