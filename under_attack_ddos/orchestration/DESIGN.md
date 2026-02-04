# Global Orchestration Logic Design

This document defines how the `under_attack_ddos` system coordinates its distributed components, ensuring a cohesive response to threats without single points of failure.

## 1. State Management (The "Truth")

The system state is stored in a shared, high-performance, file-based structure in `runtime/` to avoid dependency on complex databases (keep it simple for emergencies).

**State File:** `runtime/global_state.json`
```json
{
  "mode": "NORMAL",
  "grs_score": 15,
  "updated_at": "2023-10-27T10:00:00Z",
  "active_campaigns": [],
  "mitigation_stage": 0
}
```

*   **Locking:** Uses atomic writes (write-to-temp-then-rename) or `flock` to prevent corruption.
*   **Watcher:** All scripts monitor this file for changes using `inotify` (Linux) or polling (fallback).

## 2. Notification System (The "Nervous System")

How components talk to each other:

1.  **Broadcast (Mode Change):**
    *   The **Intelligence Engine** updates `global_state.json`.
    *   It triggers a `kill -SIGUSR1` broadcast to all registered PID files in `runtime/*.pid`.
    *   **Reaction:** Scripts catch `SIGUSR1`, reload the state file, and adjust their sampling/mitigation behavior immediately.

2.  **Directives (Action):**
    *   Intelligence Engine writes actionable JSON files to `runtime/directives/queue/`.
    *   **Mitigation Agents** watch this directory, lock a file, execute the action, and move it to `runtime/directives/completed/`.

## 3. Activation Workflow (Enter "UNDER ATTACK")

1.  **Trigger:** Intelligence Engine calculates GRS > 90.
2.  **State Update:** Writes `"mode": "UNDER_ATTACK"` to `global_state.json`.
3.  **Signal:** Broadcasts `SIGUSR1` to all PIDs.
4.  **Verification:** Checks `observability` metrics to ensure mitigation is applying (e.g., dropped packet counts increasing).
5.  **Persistence:** Updates `/etc/issue` or MOTD to warn logged-in admins: "SYSTEM UNDER AUTOMATED DEFENSE."

## 4. Recovery Strategy (Back to Normal)

Recovery must be gradual to prevent re-triggering the attack (hysteresis).

1.  **Cool-down:** Intelligence Engine waits for GRS < 30 for 5 continuous minutes.
2.  **Downgrade:**
    *   `UNDER_ATTACK` -> `HIGH` (Wait 2 min)
    *   `HIGH` -> `ELEVATED` (Wait 2 min)
    *   `ELEVATED` -> `NORMAL`
3.  **Cleanup:**
    *   Broadcast `SIGUSR2` (Cleanup Signal).
    *   Mitigation scripts flush temporary ipsets and rate limits.
    *   State is updated to `NORMAL`.

## 5. Fail-Safe Mechanisms

*   **Watchdog:** A separate cron/systemd timer checks if `global_state.json` is older than 60 seconds.
    *   If stale: Assumes Intelligence Engine died.
    *   Action: Defaults to `ELEVATED` mode (safe middle ground) and restarts the engine service.
*   **Emergency Override:**
    *   Admin can run `./orchestrator.py --force-mode NORMAL` which creates a `runtime/OVERRIDE.lock` file.
    *   System ignores all sensors while lock exists.
