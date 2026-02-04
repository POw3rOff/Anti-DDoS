# Base Template Design for Anti-DDoS Scripts

This document outlines the architectural blueprint for all Python scripts in the `under_attack_ddos` project. Every script must adhere to this internal flow to ensure stability, safety, and consistency.

## 1. Internal Architecture

Each script should be structured as a primary Class (e.g., `Layer3Filter`) rather than a loose collection of functions.

### Responsibilities
1.  **Input Handler:** Parses CLI args and loads/validates YAML config.
2.  **Context Manager:** Handles resources (sockets, file locks) and ensures cleanup.
3.  **Analyzer:** The core logic engine (e.g., packet inspection, log parsing).
4.  **Mitigator:** The action engine (e.g., iptables calls, API rate limits).
5.  **Reporter:** Outputs JSON events and operational logs.

## 2. Execution Flow

### Phase 1: Initialization (Startup)
1.  **Signal Handling:** Register handlers for `SIGINT` and `SIGTERM` immediately.
2.  **CLI Parsing:** Parse arguments strictly using the defined standard.
3.  **Root Check:** If the script capability requires privileges, verify `EUID == 0`.
4.  **Config Loading:**
    *   Load YAML from disk.
    *   **Validate Schema:** Check for required keys/types.
    *   **Merge Defaults:** Overlay config on top of safe internal defaults.
5.  **Environment Check:** Verify dependencies (e.g., presence of `iptables`, `ipset`, `ss`).
6.  **PID Management:** If `--daemon`, check/write PID file.

### Phase 2: Main Loop (The "Pulse")
The script enters a `while not shutdown_event.is_set():` loop.

1.  **Health Check:** Ensure critical resources (e.g., log handles, sockets) are alive.
2.  **Data Acquisition:** Read a batch of data (packets, log lines, conntrack entries).
3.  **Analysis:**
    *   Apply logic based on `--mode` (e.g., strict thresholds for `under_attack`).
    *   *Optimized Path:* Fail fast for benign traffic to reduce CPU load.
4.  **Decision Making:**
    *   If threat detected -> Generate `Event`.
    *   Check `--dry-run`. If `True`, log `[DRY-RUN]` action and skip mitigation.
5.  **Mitigation (If Active):**
    *   Execute system command (e.g., `iptables -A ...`).
    *   Verify command success (check return code).
6.  **Reporting:**
    *   Emit JSON event to STDOUT.
    *   Log operational details to STDERR.
7.  **Sleep/Throttle:** Sleep for configured interval to prevent CPU starvation.

### Phase 3: Shutdown (Cleanup)
Triggered by Signal or Error.

1.  **Stop Ingestion:** Stop reading new data.
2.  **Release Locks:** Remove PID file.
3.  **State Dump:** (Optional) Save current counters/state to disk for resume.
4.  **Exit:** Return 0 (Success) or 1 (Error).

## 3. Safety Mechanisms (Production Ready)

### The "Do No Harm" Principle
*   **Whitelist First:** Every script must support a `whitelist` (IP/CIDR) in config. This whitelist is checked **before** any logic. Whitelisted entities are **never** touched.
*   **Failsafe:** If the script crashes, it must **fail open** (stop filtering) rather than blocking legitimate traffic, unless explicitly configured to "fail closed".
*   **Rate Limited Mitigation:** The Mitigator component must implement a "safety valve" (e.g., max 100 bans per minute) to prevent cascading failures or self-DoS.

## 4. Class Structure Outline

*   `ConfigLoader`: Validates and supplies settings.
*   `SignalHandler`: Manages graceful stops.
*   `Logger`: Wraps standard logging (STDERR) and Event emitter (STDOUT).
*   `CoreLogic`: Abstract base class for specific implementations.
    *   `run()`: Main entry point.
    *   `_analyze()`: Internal logic.
    *   `_mitigate()`: Internal action.
