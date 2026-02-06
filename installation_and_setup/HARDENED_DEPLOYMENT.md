# Hardened Deployment Guide

This document defines the strict security posture required for deploying `under_attack_ddos` in production. It assumes a modern Linux environment (Debian 11+ / RHEL 8+).

## 1. File & OS Hardening

**Principle:** Components run with the lowest possible privilege. Only the Mitigation Controller and L3/L4 Sniffers run as `root`.

### User & Group Model
*   `uad-core` (Group): Shared group for reading configs and writing logs.
*   `uad-monitor` (User): Runs L3/L4 monitors (needs `CAP_NET_RAW` or root).
*   `uad-orch` (User): Runs Orchestrator & Intelligence (No special privileges).
*   `uad-web` (User): Runs Dashboard & Web UI.

### Folder Permissions
| Path | Owner:Group | Mode | Purpose |
| :--- | :--- | :--- | :--- |
| `/opt/uad/` | `root:root` | `0755` | App binaries (Immutable) |
| `/opt/uad/config/` | `root:uad-core` | `0640` | Configuration (Read-only for app) |
| `/opt/uad/runtime/` | `uad-orch:uad-core` | `0770` | IPC Sockets & State Files |
| `/var/log/uad/` | `root:uad-core` | `1730` | Logs (Append-only recommended) |

## 2. Process Hardening (Systemd)

All services use `systemd` sandbox features.

### Example: `uad-orchestrator.service`
```ini
[Unit]
Description=Under Attack Orchestrator
After=network.target

[Service]
User=uad-orch
Group=uad-core
ExecStart=/opt/uad/venv/bin/python3 /opt/uad/orchestration/under_attack_orchestrator.py --config /opt/uad/config/orchestrator.yaml
# Hardening
ProtectSystem=strict
ProtectHome=yes
PrivateTmp=yes
NoNewPrivileges=yes
RestrictAddressFamilies=AF_UNIX
DevicePolicy=closed
# Restart Logic
Restart=always
RestartSec=3
WatchdogSec=10

[Install]
WantedBy=multi-user.target
```

## 3. Python Runtime Security

1.  **Virtualenv Isolation:** NEVER run in global python scope. Use `/opt/uad/venv`.
2.  **Dependency Pinning:** Use `requirements.txt` with hashes (`--require-hashes`).
3.  **Input Validation:**
    *   `yaml.safe_load()` ONLY.
    *   Strict JSON schema validation for all IPC messages.

## 4. Operational Controls & Fail-Safes

### The "Dead Man's Switch"
*   **Mechanism:** A systemd hardware watchdog or software timer.
*   **Action:** If Orchestrator hangs for >60s, the Mitigation Controller automatically reverts to `NORMAL` mode (Fail-Open) to prevent accidental DoS of valid traffic.

### Manual Override (The Red Button)
*   **Path:** `/opt/uad/runtime/OVERRIDE.lock`
*   **Effect:** When present, ALL automated mitigation stops immediately.
*   **Creation:** `sudo touch /opt/uad/runtime/OVERRIDE.lock`

## 5. Deployment Checklist

### Pre-Flight
- [ ] Users `uad-monitor` and `uad-orch` created.
- [ ] `/opt/uad` permissions verified (`namei -l /opt/uad/runtime`).
- [ ] Systemd units installed and enabled.
- [ ] Config files validated (`python3 -m py_compile ...` and schema check).

### Production Readiness
- [ ] `logrotate` configured for `/var/log/uad/*.log`.
- [ ] Monitoring agent (e.g., Prometheus Node Exporter) watching `uad-*.service` status.
- [ ] "Dry Run" mode enabled in `mitigation.yaml` for initial 24h.
