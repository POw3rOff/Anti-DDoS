#!/usr/bin/env python3
"""
Mitigation Executor
Part of 'under_attack_ddos' Defense System.

Responsibility: Executes active defense actions (iptables, ipset) based on 
decisions from the Orchestrator.
"""

import sys
import os
import time
import json
import logging
import argparse
import signal
import subprocess
from datetime import datetime, timezone

# Third-party imports
try:
    import yaml
except ImportError as e:
    print(f"CRITICAL: Missing required dependencies: {e}", file=sys.stderr)
    print("Please install: pip install pyyaml", file=sys.stderr)
    sys.exit(4)

# -----------------------------------------------------------------------------
# Identity & Constants
# -----------------------------------------------------------------------------
SCRIPT_NAME = "mitigation_executor"
LAYER = "mitigation"
RESPONSIBILITY = "Enforce blocking rules and protocol hardening"

DEFAULT_CONFIG = {
    "mitigation": {
        "ipset_name": "uad_blacklist",
        "iptables_chain": "UAD_BLOCK",
        "whitelist": [],
        "cleanup_on_exit": True
    }
}

# -----------------------------------------------------------------------------
# Classes
# -----------------------------------------------------------------------------

class ConfigLoader:
    @staticmethod
    def load(path):
        if not os.path.exists(path):
            return DEFAULT_CONFIG
        try:
            with open(path, 'r') as f:
                return yaml.safe_load(f) or {}
        except Exception:
            return DEFAULT_CONFIG

class MitigationExecutor:
    def __init__(self, args, config):
        self.args = args
        self.config = config.get("mitigation", DEFAULT_CONFIG["mitigation"])
        self.running = True
        
        self.ipset_name = self.config.get("ipset_name", "uad_blacklist")
        self.iptables_chain = self.config.get("iptables_chain", "UAD_BLOCK")
        self.whitelist = set(self.config.get("whitelist", []))

        logging.info(f"Initialized {SCRIPT_NAME}. Chain: {self.iptables_chain}, IPSet: {self.ipset_name}")

    def _run_cmd(self, cmd):
        """Executes a system command."""
        if self.args.dry_run:
            logging.info(f"[DRY-RUN] Executing: {' '.join(cmd)}")
            return True
        
        try:
            subprocess.run(cmd, check=True, capture_output=True)
            return True
        except subprocess.CalledProcessError as e:
            logging.error(f"Command failed: {' '.join(cmd)} - Error: {e.stderr.decode().strip()}")
            return False
        except Exception as e:
            logging.error(f"Unexpected error running command: {e}")
            return False

    def setup_environment(self):
        """Initializes ipset and iptables chain."""
        logging.info("Setting up firewall environment...")
        
        # 1. Create ipset
        # hash:ip with a default timeout (optional, let the controller handle it)
        self._run_cmd(["ipset", "create", self.ipset_name, "hash:ip", "-!", "timeout", "0"])
        
        # 2. Create iptables chain
        self._run_cmd(["iptables", "-N", self.iptables_chain])
        
        # 3. Ensure the chain is linked to INPUT
        # We check if it's already there to avoid duplicates
        try:
            if not self.args.dry_run:
                subprocess.run(["iptables", "-C", "INPUT", "-j", self.iptables_chain], check=True, capture_output=True)
        except subprocess.CalledProcessError:
            # Rule doesn't exist, add it
            self._run_cmd(["iptables", "-I", "INPUT", "1", "-j", self.iptables_chain])

        # 4. Add the ipset match to the UAD_BLOCK chain
        try:
            if not self.args.dry_run:
                subprocess.run(["iptables", "-C", self.iptables_chain, "-m", "set", "--match-set", self.ipset_name, "src", "-j", "DROP"], check=True, capture_output=True)
        except subprocess.CalledProcessError:
            self._run_cmd(["iptables", "-A", self.iptables_chain, "-m", "set", "--match-set", self.ipset_name, "src", "-j", "DROP"])

    def cleanup(self):
        """Removes rules and ipsets (if configured)."""
        if not self.config.get("cleanup_on_exit", True):
            logging.info("Skipping cleanup as per configuration.")
            return

        logging.info("Cleaning up firewall rules...")
        # 1. Unlink from INPUT
        self._run_cmd(["iptables", "-D", "INPUT", "-j", self.iptables_chain])
        # 2. Flush and delete the chain
        self._run_cmd(["iptables", "-F", self.iptables_chain])
        self._run_cmd(["iptables", "-X", self.iptables_chain])
        # 3. Destroy the ipset
        self._run_cmd(["ipset", "destroy", self.ipset_name])

    def process_decision(self, decision):
        """Enforces a decision from the Orchestrator."""
        affected_sources = decision.get("affected_sources", [])
        state = decision.get("state", "NORMAL")
        
        # 1. Handle IP Blocking
        for source in affected_sources:
            ip = source.get("ip")
            if ip in self.whitelist:
                logging.info(f"Skipping whitelisted IP: {ip}")
                continue
            
            logging.info(f"Blocking IP: {ip} (Score: {source.get('score')})")
            self._run_cmd(["ipset", "add", self.ipset_name, ip, "-!", "timeout", "300"]) # 5 min default

            # eBPF Integration: Also block in XDP NIC level
            loader_path = os.path.join(os.path.dirname(__file__), "../ebpf/loader.py")
            self._run_cmd([sys.executable, loader_path, "--block", ip])

        # 2. Protocol Hardening based on state
        if state == "UNDER_ATTACK":
            self._enforce_aggressive_hardening()
        elif state == "DEFENSIVE":
            self._enforce_soft_hardening()
        else:
            self._enforce_baseline()

    def _enforce_aggressive_hardening(self):
        logging.info("Applying AGGRESSIVE hardening posture...")
        # Example: Enable global SYN cookies (redundant if kernel does it, but good to be explicit)
        if not self.args.dry_run:
            subprocess.run(["sysctl", "-w", "net.ipv4.tcp_syncookies=1"], check=False)
        else:
            logging.info("[DRY-RUN] sysctl -w net.ipv4.tcp_syncookies=1")

    def _enforce_soft_hardening(self):
        logging.info("Applying SOFT hardening posture...")
        # Example: Could adjust conntrack timeouts here

    def _enforce_baseline(self):
        logging.info("Restoring baseline posture.")

    def run_loop(self, input_source):
        logging.info(f"Starting {SCRIPT_NAME}. Waiting for decisions...")
        try:
            if input_source == 'stdin':
                for line in sys.stdin:
                    if not self.running: break
                    self._handle_input(line)
            else:
                with open(input_source, 'r') as f:
                    # If --once, read from beginning. Otherwise, tail.
                    if not self.args.once:
                        f.seek(0, 2)
                    
                    while self.running:
                        line = f.readline()
                        if not line:
                            if self.args.once: break
                            time.sleep(0.1)
                            continue
                        self._handle_input(line)
                        if self.args.once: 
                            self.running = False
                            break
        except KeyboardInterrupt:
            self.stop()

    def _handle_input(self, line):
        try:
            if not line.strip(): return
            logging.debug(f"Received input: {line.strip()}")
            decision = json.loads(line)
            self.process_decision(decision)
        except json.JSONDecodeError as e:
            logging.warning(f"Failed to decode JSON: {e}")
        except Exception as e:
            logging.error(f"Error handling input: {e}")
            import traceback
            logging.error(traceback.format_exc())

    def stop(self, signum=None, frame=None):
        logging.info("Stopping...")
        self.running = False

# -----------------------------------------------------------------------------
# Main Entry Point
# -----------------------------------------------------------------------------
def main():
    parser = argparse.ArgumentParser(description=RESPONSIBILITY)
    parser.add_argument("--config", required=True, help="Path to YAML configuration")
    parser.add_argument("--input", default="stdin", choices=["stdin", "file"], help="Input source")
    parser.add_argument("--input-file", help="Path to input file (if input=file)")
    parser.add_argument("--dry-run", action="store_true", help="Simulate actions")
    parser.add_argument("--once", action="store_true", help="Run once and exit")
    parser.add_argument("--log-level", default="INFO", choices=["DEBUG", "INFO", "WARNING", "ERROR"], help="Log verbosity")

    args = parser.parse_args()

    # Root Check
    is_root = False
    try:
        is_root = (os.getuid() == 0)
    except AttributeError:
        # Windows doesn't have getuid, but for dry-run validation it's fine.
        is_root = False

    if not is_root and not args.dry_run:
        print("CRITICAL: This script must be run as root to manage firewall rules.", file=sys.stderr)
        sys.exit(3)

    if args.input == "file" and not args.input_file:
        print("Error: --input-file required when input is 'file'", file=sys.stderr)
        sys.exit(1)

    logging.basicConfig(
        level=getattr(logging, args.log_level),
        format='%(asctime)s [%(levelname)s] %(message)s',
        datefmt='%Y-%m-%dT%H:%M:%SZ',
        stream=sys.stderr
    )

    config = ConfigLoader.load(args.config)
    executor = MitigationExecutor(args, config)

    # Signal Handling
    def handle_exit(signum, frame):
        executor.stop()
        executor.cleanup()
        sys.exit(0)

    signal.signal(signal.SIGINT, handle_exit)
    signal.signal(signal.SIGTERM, handle_exit)

    # Startup
    executor.setup_environment()
    
    # Execution
    executor.run_loop(args.input if args.input == 'stdin' else args.input_file)

if __name__ == "__main__":
    main()
