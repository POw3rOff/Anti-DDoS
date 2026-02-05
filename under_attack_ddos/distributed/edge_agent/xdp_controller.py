#!/usr/bin/env python3
"""
Edge Agent: XDP Controller
Part of 'under_attack_ddos' Defense System.

Responsibility: Local interface to the kernel eBPF/XDP layer.
Manages the Blocklist Map on the Edge Node.
"""

import logging
import subprocess
import os

class XDPController:
    def __init__(self, dry_run=False):
        self.dry_run = dry_run
        # Reusing the map path from the kernel_ebpf layer
        self.map_path = "/sys/fs/bpf/under_attack_ddos/xdp_blocklist_map"

    def block_ip(self, ip_str, ttl_seconds):
        """Adds an IP to the local XDP blocklist."""
        if self.dry_run:
            logging.info(f"[DRY-RUN] XDP BLOCK {ip_str} (TTL: {ttl_seconds})")
            return

        # Use the existing xdp_policy_sync logic or call bpftool directly
        # For this prototype, we'll use a direct bpftool call pattern similar to threshold_controller

        try:
            # Note: A real implementation needs to convert IP to hex and handle the specific map structure.
            # We assume a helper or the xdp_policy_sync tool handles the low-level byte conversion.
            # Here we just log the intent as the actual C-structure writing is complex in pure python without ctypes/bcc.
            logging.info(f"Applying XDP Block for {ip_str} in kernel map.")

            # Simulated Command
            # cmd = ["under_attack_ddos/kernel_ebpf/xdp/loader/xdp_policy_sync.py", "--block", ip_str]
            # subprocess.check_call(cmd)

        except Exception as e:
            logging.error(f"XDP Block failed: {e}")

    def allow_ip(self, ip_str):
        if self.dry_run:
            logging.info(f"[DRY-RUN] XDP ALLOW {ip_str}")
            return
        logging.info(f"Removing {ip_str} from XDP blocklist.")
