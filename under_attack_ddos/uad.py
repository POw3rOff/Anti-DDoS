#!/usr/bin/env python3
"""
'uad' CLI Tool - Unified Interface for under_attack_ddos.
Part of Phase 7: Orchestration & Observability.
"""

import sys
import argparse
import json
import os
import subprocess
import time
from datetime import datetime
from intelligence.enrichment import GeoIPEnricher

STATE_FILE = "runtime/global_state.json"
SERVICES = [
    "uad-orchestrator",
    "uad-l3-analyzer",
    "uad-l4-analyzer",
    "uad-executor",
    "uad-exporter"
]

def get_status():
    """Reads the current system status."""
    if not os.path.exists(STATE_FILE):
        print("System status: UNKNOWN (State file missing)")
        return

    try:
        with open(STATE_FILE, 'r') as f:
            state = json.load(f)
        
        print("\n=== Under Attack DDoS System Status ===")
        print(f"Operational Mode: {state.get('mode', 'N/A')}")
        print(f"Global Risk Score: {state.get('grs_score', 'N/A')}")
        print(f"Last Update: {state.get('last_update', 'N/A')}")
        
        campaigns = state.get("campaigns", [])
        print(f"Active Campaigns: {len(campaigns)}")
        for i, camp in enumerate(campaigns):
             print(f"  [{i+1}] {camp.get('name', 'Unknown')}: {camp.get('type', 'Unknown')} (Conf: {camp.get('confidence', 'N/A')})")
        
        print("========================================\n")
    except Exception as e:
        print(f"Error reading status: {e}")

def manage_services(action):
    """Starts, stops, or restarts the system services."""
    print(f"Performing {action} on all services...")
    # This is a platform-dependent action (systemd for Linux)
    # On Windows, we'd use 'sc' or similar, but the production target is Linux
    for svc in SERVICES:
        print(f"  {action.capitalize()}ing {svc}...")
        # Mocking for now to avoid execution errors on local environment
        # subprocess.run(["sudo", "systemctl", action, svc])
        pass
    print("Action completed (Mocked).")

def show_logs():
    """Tails the system logs."""
    log_file = "logs/orchestrator.log"
    if not os.path.exists(log_file):
        print(f"Log file {log_file} not found.")
        return
    
    # Platform-specific log tailing
    if sys.platform == "win32":
        print(f"Showing last 20 lines of {log_file} (Tail -f not available natively):")
        with open(log_file, "r") as f:
            lines = f.readlines()
            for line in lines[-20:]:
                print(line.strip())
    else:
        print(f"Tailing {log_file} (Ctrl+C to stop)...")
        try:
            subprocess.run(["tail", "-f", log_file])
        except KeyboardInterrupt:
            print("\nDetached from logs.")

def panic_mode():
    """Forces the system into maximum defense mode."""
    print("!!! PANIC MODE ACTIVATED !!!")
    print("  -> Escalating system state to ESCALATED")
    print("  -> Blocking all non-whitelisted traffic (Simulated)")
    
    # Send signal to orchestrator via lock file
    os.makedirs("runtime", exist_ok=True)
    with open("runtime/OVERRIDE.lock", "w") as f:
        f.write("ESCALATED")
    print("Panic signal sent. Global Orchestrator will react on next tick.")

def lookup_ip(ip):
    """Enriches an IP address with Geo/ASN data."""
    enricher = GeoIPEnricher()
    data = enricher.enrich(ip)
    
    print(f"\n=== IP Intelligence: {ip} ===")
    print(f"  Country: {data.get('country', 'Unknown')}")
    print(f"  City:    {data.get('city', 'Unknown')}")
    print(f"  ASN:     {data.get('asn', 'Unknown')}")
    print(f"  Org:     {data.get('org', 'Unknown')}")
    print("================================\n")


def main():
    parser = argparse.ArgumentParser(description="UAD Command Line Interface")
    subparsers = parser.add_subparsers(dest="command", help="Available commands")

    subparsers.add_parser("status", help="Show current system status")
    
    svc_parser = subparsers.add_parser("service", help="Manage system services")
    svc_parser.add_argument("action", choices=["start", "stop", "restart", "status"], help="Action to perform")

    subparsers.add_parser("logs", help="Tail system logs")
    subparsers.add_parser("panic", help="Activate system-wide maximum defense")
    
    lookup_parser = subparsers.add_parser("lookup", help="Enrich IP with Geo/ASN data")
    lookup_parser.add_argument("ip", help="IP Address to lookup")

    args = parser.parse_args()

    if args.command == "status":
        get_status()
    elif args.command == "service":
        manage_services(args.action)
    elif args.command == "logs":
        show_logs()
    elif args.command == "panic":
        panic_mode()
    elif args.command == "lookup":
        lookup_ip(args.ip)
    else:
        parser.print_help()

if __name__ == "__main__":
    main()
