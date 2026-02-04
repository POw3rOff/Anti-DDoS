# CLI Standard Specification for "under_attack_ddos"

This document defines the mandatory Command-Line Interface (CLI) pattern that ALL scripts in the project must follow. This ensures consistency, automatability, and ease of integration.

## 1. Mandatory CLI Arguments

All scripts must use `argparse` (Python) and support the following arguments:

| Flag | Short | Type | Default | Description |
|------|-------|------|---------|-------------|
| `--config` | `-c` | Path | `config/{script_name}.yaml` | Path to the YAML configuration file. |
| `--mode` | `-m` | Enum | `monitor` | Operation mode: `normal`, `monitor`, or `under_attack`. |
| `--log-level` | `-l` | Enum | `INFO` | Logging verbosity: `DEBUG`, `INFO`, `WARNING`, `ERROR`. |
| `--dry-run` | `-n` | Bool | `False` | Simulate actions without applying changes (read-only). |
| `--daemon` | `-d` | Bool | `False` | Run continuously as a background process/service. |
| `--once` | `-1` | Bool | `False` | Run a single execution pass and exit (useful for cron/debugging). |
| `--json` | `-j` | Bool | `False` | Force standard output to be structured JSON (for SIEM/pipeline). |

**Note:** `--daemon` and `--once` are mutually exclusive. If neither is specified, the script should default to the behavior most appropriate for its function (usually `--once` for scanners, `--daemon` for watchers), but explicit flags are preferred.

## 2. Supported Modes

Scripts must adjust their behavior based on the selected mode:

*   **`normal`**: Standard operation. Balanced checks, standard mitigation thresholds.
*   **`monitor`** (Passive): Observation only. Collect metrics and logs. **NEVER** apply active mitigations (firewall bans, service stops) in this mode. Implicitly implies `--dry-run` for mitigation actions.
*   **`under_attack`** (Aggressive): High alert. Aggressive sampling rates, lowered detection thresholds, immediate mitigation actions. Prioritize availability over precision (higher false positive tolerance).

## 3. Configuration Handling

1.  **Source:** Configuration **MUST** be loaded from a YAML file.
2.  **Precedence:**
    1.  Command line argument: `--config /custom/path.yaml`
    2.  Environment Variable: `UAD_{SCRIPT_NAME}_CONFIG`
    3.  Default location: `../config/{script_name}.yaml` (relative to script)
3.  **Validation:** Scripts must validate the config schema at startup and fail fast (Exit Code 2) if invalid.

## 4. Standard Output & Logging

To ensure scripts can be piped to other tools (SIEM, Dashboards, jq):

*   **STDOUT (Standard Output):**
    *   Reserved for **structured data** (JSON events/results) when `--json` is enabled.
    *   If not `--json`, human-readable status summaries are acceptable here.
*   **STDERR (Standard Error):**
    *   Reserved for **operational logs** (Startup messages, errors, debugging info).
    *   Use the standard Python `logging` module.

### Startup Banner (STDERR)
Every script must print a standard banner to STDERR upon startup (unless `--json` is strict):

```text
[INFO] Starting <script_name> v1.0.0
[INFO] Mode: <mode> | Dry-Run: <True/False> | PID: <pid>
[INFO] Config loaded from: <path_to_config>
```

### Event Output (STDOUT + JSON)
When an event occurs (e.g., IP banned, attack detected), output a single-line JSON object:

```json
{"timestamp": "2023-10-27T10:00:00Z", "source": "layer3_filter", "event": "ip_ban", "target_ip": "192.168.1.50", "reason": "syn_flood_threshold_exceeded", "mode": "under_attack", "action": "iptables_drop"}
```

## 5. Exit Codes

Adhere to standard Linux exit codes:

*   **0**: Success / Clean exit.
*   **1**: Generic runtime error.
*   **2**: Configuration error (missing file, invalid YAML).
*   **3**: Permission denied (e.g., script requires root but run as user).
*   **4**: Dependency missing (e.g., `iptables` binary not found).
*   **130**: Terminated by user (SIGINT/Ctrl+C).

## 6. Linux-First Mindset

*   **Root Checks:** If the script modifies system state (iptables, sysctl), check for `EUID == 0` at startup. Fail with Exit Code 3 if not root.
*   **Signal Handling:** Gracefully handle `SIGTERM` and `SIGINT` to close sockets and release locks before exiting.
*   **PID Files:** If running with `--daemon`, create a PID file in `runtime/`.
