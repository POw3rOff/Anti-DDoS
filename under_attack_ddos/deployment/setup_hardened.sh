#!/bin/bash
# Under Attack DDoS - Hardened Setup Script
# Responsibility: Configures users, groups, and permissions for production.

set -e

echo "[*] Starting Hardened Environment Setup..."

# 1. Create Users & Groups
echo "[*] Creating system users and groups..."
groupadd -f uad-core
id -u uad-orch >/dev/null 2>&1 || useradd -r -s /bin/false -g uad-core uad-orch
id -u uad-monitor >/dev/null 2>&1 || useradd -r -s /bin/false -g uad-core uad-monitor

# 2. Directory Structure
echo "[*] Setting up directory structure in /opt/uad..."
mkdir -p /opt/uad/runtime
mkdir -p /var/log/uad

# 3. Permissions
echo "[*] Configuring permissions..."
# Core binaries/source: Root-owned, world-readable
chown -R root:root /opt/uad
# Config: Secret, only group uad-core can read
chown -R root:uad-core /opt/uad/config
chmod -R 640 /opt/uad/config
chmod 750 /opt/uad/config

# Runtime: Orchestrator needs to write sockets/state
chown uad-orch:uad-core /opt/uad/runtime
chmod 770 /opt/uad/runtime

# Logs: Shared append-only (sticky bit)
chown root:uad-core /var/log/uad
chmod 1730 /var/log/uad

# 4. Capabilities (Optional alternative to root for monitors)
# Requires 'libcap2-bin'
if command -v setcap >/dev/null 2>&1; then
    echo "[*] Setting Linux Capabilities for Python runtime..."
    # Allow python in venv to bind raw sockets and manage BPF
    # Note: XDP attachment still often requires full root depending on kernel
    setcap 'cap_net_raw,cap_net_admin+ep' $(readlink -f /opt/uad/.venv/bin/python3)
fi

# 5. Systemd Installation
echo "[*] To install services, run:"
echo "    sudo cp /opt/uad/deployment/*.service /etc/systemd/system/"
echo "    sudo systemctl daemon-reload"
echo "    sudo systemctl enable uad-orchestrator uad-l3-analyzer uad-l4-analyzer uad-executor uad-exporter"

echo "[+] Setup Complete. Deployment ready."
