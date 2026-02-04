# Testing & Validation Strategy

This document defines the quality assurance and safety protocols for the `under_attack_ddos` system. Given the nature of automated defense, testing must prioritize safety and reversibility.

## 1. Unit-Level Validation (The "Dry Dock")

Before any script touches a live interface, it must pass these checks.

### CLI & Configuration
*   **Argument Parsing:** Verify scripts fail gracefully with invalid flags (e.g., `--mode chaos`).
*   **Config Loading:**
    *   Test behavior when `config/thresholds.yaml` is missing (Must fail safe or use defaults).
    *   Test behavior with malformed YAML (Must exit with code 2).
*   **Mode Switching:** Verify internal variables update correctly when `global_state.json` changes.

### Logic & Safety
*   **Root Check:** Scripts requiring privileges must exit immediately if run as non-root (unless `--dry-run`).
*   **Dry-Run Integrity:** Verify that `--dry-run` NEVER executes system calls (iptables, ipset). It must only log intentions.

## 2. Integration Testing (The "Harbor")

Testing how components interact via the shared filesystem.

### Event Exchange
*   **Scenario:** L3 Monitor detects a spike.
*   **Check:** Verify `runtime/events/l3_*.json` is created.
*   **Check:** Verify Correlation Engine picks up the file and logs ingestion.

### State Synchronization
*   **Scenario:** Orchestrator updates `runtime/global_state.json` to `ELEVATED`.
*   **Check:** Verify all running daemons log "Reloading state: ELEVATED" within 5 seconds.

## 3. Simulation Testing (The "Sea Trials")

**Goal:** Validate detection logic without launching actual attacks.

### Artificial Traffic Patterns
Instead of generating floods, we modify the *thresholds* to meet the traffic.
*   **Method:** Temporarily lower `thresholds.yaml` to absurdly low values (e.g., `pps_ingress: 10`).
*   **Action:** Generate normal `ping` or `curl` traffic.
*   **Validation:** System should flag this "normal" traffic as an anomaly due to the low threshold.
*   **Benefit:** Tests the entire pipeline without stressing the network.

### False Positive Scenarios
*   **Burst Test:** Simulate a valid user opening 50 tabs (high connection rate).
*   **Expectation:** System triggers `soft_mitigation` (CAPTCHA) but DOES NOT `hard_mitigation` (Ban).

## 4. Performance & Stability

### Resource Limits
*   **CPU Cap:** No single script should exceed 10% CPU usage.
*   **Memory Leak:** Run scripts for 24h. Memory usage must remain flat.
*   **Sniffer Safety:** Verify `scapy` sniffers use `store=0` to prevent RAM exhaustion.

### Daemon Behavior
*   **Log Rotation:** Verify logs in `logs/` interact correctly with `logrotate` (no open file handle errors).
*   **Watchdog:** Kill a detector process manually. Verify systemd/orchestrator restarts it.

## 5. Failure Handling (The "Lifeboats")

### Component Crash
*   **Scenario:** `intelligence_engine.py` crashes.
*   **Result:** Detectors must continue logging events to disk. Mitigation must hold last known good state or expire temporary bans (Fail-Open).

### Config Corruption
*   **Scenario:** `thresholds.yaml` becomes corrupted during a write.
*   **Result:** Scripts should log the error and continue running with *previous* memory-loaded config, or fallback to internal defaults.

## 6. Rollback Strategy (The "Emergency Stop")

How to restore order when automation goes wrong.

### Rapid Disengagement
1.  **Global Kill Switch:**
    *   Command: `./orchestrator.py --force-mode NORMAL`
    *   Action: Writes override lock, signals all components to stop mitigation immediately.
2.  **Network Flush:**
    *   Script: `mitigation/flush_all_rules.sh`
    *   Action: Flushes all `under_attack` chains in iptables and destroys temporary ipsets.

### Service Restoration
1.  **Stop Daemons:** `systemctl stop under_attack_*.service`
2.  **Verify Connectivity:** Check SSH and Web access.
3.  **Analyze Logs:** Review `logs/system.json.log` to identify why the system misbehaved.
