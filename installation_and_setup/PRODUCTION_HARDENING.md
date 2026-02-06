# Production Hardening Guide

This document defines the requirements and configurations for deploying the `under_attack_ddos` system in a high-security production environment.

## 1. Systemd Service Definitions

To ensure high availability, each component runs as a systemd service.

### `uad-orchestrator.service`
The brain of the system.
```ini
[Unit]
Description=Under Attack Orchestrator
After=network.target

[Service]
Type=simple
User=root
WorkingDirectory=/opt/under_attack_ddos
ExecStart=/usr/bin/python3 orchestration/under_attack_orchestrator.py --config config/orchestrator.yaml --daemon
Restart=always
RestartSec=5
# Security Hardening
ProtectSystem=full
ProtectHome=yes
PrivateTmp=yes

[Install]
WantedBy=multi-user.target
```

### `uad-l3-monitor.service`
The network eye. Requires raw socket access.
```ini
[Unit]
Description=Under Attack L3 Monitor
After=network.target

[Service]
Type=simple
User=root
# CAP_NET_RAW is essential for Scapy
AmbientCapabilities=CAP_NET_RAW CAP_NET_ADMIN
WorkingDirectory=/opt/under_attack_ddos
ExecStart=/usr/bin/python3 layer3/ip_flood_analyzer.py --config config/thresholds.yaml --mode normal --daemon
Restart=always
RestartSec=5

[Install]
WantedBy=multi-user.target
```

## 2. Folder Permissions Model

The principle of least privilege applies, though many components require root.

| Directory | Owner | Group | Perms | Rationale |
| :--- | :--- | :--- | :--- | :--- |
| `/opt/under_attack_ddos` | `root` | `root` | `0750` | Prevent non-root tampering. |
| `config/` | `root` | `root` | `0600` | Secrets/Thresholds protection. |
| `runtime/` | `root` | `root` | `0700` | IPC lock files and state. |
| `logs/` | `root` | `adm` | `0640` | Allow SOC auditors (adm group) to read logs. |

**Command:**
```bash
chown -R root:root /opt/under_attack_ddos
chmod 700 /opt/under_attack_ddos/runtime
chmod 600 /opt/under_attack_ddos/config/*.yaml
```

## 3. Logging Rotation Strategy

Logs can grow rapidly during an attack. We use `logrotate` to prevent disk exhaustion.

**Config:** `/etc/logrotate.d/under_attack_ddos`
```text
/opt/under_attack_ddos/logs/*.log {
    rotate 7
    daily
    missingok
    notifempty
    compress
    delaycompress
    # Size limit is crucial during floods
    maxsize 100M
    create 640 root adm
    postrotate
        /usr/bin/systemctl reload uad-orchestrator.service > /dev/null 2>/dev/null || true
    endscript
}
```

## 4. Fail-Safe Defaults

The code is designed to fail "Open" (allow traffic) or "Safe" (alert only) if configuration is missing.

*   **Missing Config:** Scripts default to internal hardcoded "Safe Mode" values (e.g., extremely high thresholds) to prevent accidental self-DoS.
*   **Daemon Crash:** Systemd `Restart=always` ensures rapid recovery.
*   **State Corruption:** If `runtime/global_state.json` is corrupted, the Orchestrator resets to `NORMAL` mode.

## 5. Secure Configuration Loading

*   **Validation:** All YAML files are validated against a schema at startup. Unknown keys cause a warning; missing required keys cause a fatal error (preventing startup with undefined behavior).
*   **Sanitization:** Paths in config are sanitized to prevent directory traversal if the config file is tampered with (though permissions should prevent this).
