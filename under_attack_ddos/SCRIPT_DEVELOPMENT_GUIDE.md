# Script Development Guide & Lifecycle Standard

This document provides the mandatory template and lifecycle for all CLI scripts in the `under_attack_ddos` project. Developers must adhere to this flow to ensure consistency and reliability.

## 1. Script Identity
Every script must define its identity constants at the top of the file:
*   `SCRIPT_NAME`: Unique identifier (e.g., `l3_bandwidth_monitor`).
*   `LAYER`: Operational layer (e.g., `layer3`, `mitigation`).
*   `RESPONSIBILITY`: Brief description of what this script detects or controls.

## 2. CLI Initialization
Scripts must use `argparse` to handle inputs.
*   **Required Flags:**
    *   `--config`: Path to YAML configuration.
    *   `--mode`: Execution mode (`normal`, `monitor`, `under_attack`).
*   **Optional Flags:**
    *   `--dry-run`: Simulation mode (mitigation only).
    *   `--daemon`: Run as a background service.
    *   `--once`: Run a single pass and exit.
    *   `--json`: Force JSON output on STDOUT.
*   **Validation:**
    *   Fail immediately if `--config` file is missing.
    *   Fail if `--daemon` and `--once` are both set.

## 3. Configuration Loading
*   **Reader:** Load the YAML file specified by `--config`.
*   **Defaults:** Merge loaded config onto a hardcoded dictionary of *safe defaults* (e.g., high thresholds, low drop rates).
*   **Reloads:**
    *   **One-shot:** Load once at startup.
    *   **Daemon:** Watch the config file (inotify/polling) and reload parameters dynamically without restarting the process.

## 4. Mode Handling
Scripts behave differently based on the requested `--mode`:
*   **NORMAL:**
    *   Use standard thresholds from `thresholds.yaml`.
    *   Standard sampling intervals (e.g., check every 5s).
*   **MONITOR:**
    *   **ReadOnly:** NEVER perform mitigation actions.
    *   Logging: Verbose.
*   **UNDER_ATTACK:**
    *   Use critical thresholds (stricter or looser depending on strategy).
    *   Aggressive sampling (e.g., check every 1s).
    *   Prioritize speed over precision.

## 5. Main Execution Loop
For daemons, this is the `while running:` loop.
1.  **Data Collection:** Read system signals (procfs, logs, sockets).
2.  **Normalization:** Convert raw data to standard metrics.
3.  **Analysis:** Compare metrics against the active Mode's thresholds.
4.  **Signal Extraction:** Identify anomalies (e.g., "SYN rate > Limit").
5.  **Event Generation:** Construct the JSON event object if an anomaly is found.

## 6. Output Handling
*   **STDOUT:** Strictly for machine-readable JSON events (if `--json` is set).
    *   Format: `{"timestamp": "...", "layer": "...", "event": "...", "severity": "...", "data": {...}}`
*   **STDERR:** Human-readable logs (INFO, WARN, ERROR) for debugging and status updates.
*   **Severity Levels:** `INFO`, `LOW`, `MEDIUM`, `HIGH`, `CRITICAL`.
*   **Timestamping:** All outputs must use ISO 8601 UTC.

## 7. Dry-Run Behavior
When `--dry-run` is active:
*   **Mitigation Scripts:** Calculate the action (e.g., "Would drop IP 1.2.3.4") but DO NOT execute the system call.
*   **Logging:** Log the *intended* action with a `[DRY-RUN]` prefix.
*   **Events:** Emit the event with a status of `simulated`.

## 8. Error Handling
*   **Recoverable:** (e.g., temporary read error on `/proc`). Log warning, retry, or skip cycle.
*   **Fatal:** (e.g., Config file deleted, Permission denied). Log critical error, cleanup, and exit.
*   **Exit Codes:**
    *   `0`: Success / Normal termination.
    *   `1`: Generic Error.
    *   `2`: Config Error.
    *   `3`: Permission Error (e.g., not root).

## 9. Graceful Shutdown
*   **Signal Handling:** Catch `SIGINT` (Ctrl+C) and `SIGTERM`.
*   **Cleanup Logic:**
    *   Stop the main loop.
    *   Remove PID files.
    *   Close sockets/file handles.
    *   (Mitigation only) Optionally flush temporary rules if configured to "clean on exit".
    *   Log "Shutting down...".
