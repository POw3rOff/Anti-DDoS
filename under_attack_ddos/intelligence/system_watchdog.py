#!/usr/bin/env python3
"""
System Watchdog (Self-Protection)
Part of 'under_attack_ddos' Defense System.

Responsibility: Monitor the health and resource usage of defense components.
Prevents the defense system itself from becoming a DoS vector via resource exhaustion.
"""

import sys
import os
import time
import json
import logging
import argparse
import signal
import subprocess
import yaml

SCRIPT_NAME = "system_watchdog"

DEFAULT_CONFIG = {
    "watchdog": {
        "check_interval_seconds": 10,
        "limits": {
            "max_cpu_percent": 80.0,
            "max_memory_mb": 512
        },
        "monitored_processes": [
            "under_attack_orchestrator",
            "ip_flood_analyzer",
            "syn_flood_analyzer",
            "spoofing_detector"
        ]
    }
}

class Watchdog:
    def __init__(self, config_path, dry_run=False):
        self.config_path = config_path
        self.dry_run = dry_run
        self.running = True
        self.config = self._load_config()

    def _load_config(self):
        try:
            with open(self.config_path, 'r') as f:
                data = yaml.safe_load(f)
                return data.get("watchdog", DEFAULT_CONFIG["watchdog"])
        except Exception as e:
            logging.error(f"Config load error: {e}")
            return DEFAULT_CONFIG["watchdog"]

    def get_process_stats(self, proc_name):
        """
        Returns list of dicts {pid, cpu, mem_mb, cmd} for matching processes.
        Uses 'ps' command to be dependency-free (no psutil).
        """
        stats = []
        try:
            # ps -eo pid,%cpu,rss,args
            # RSS is in KB
            cmd = ["ps", "-eo", "pid,%cpu,rss,args"]
            result = subprocess.check_output(cmd, text=True).strip().split('\n')

            for line in result[1:]:
                parts = line.split(maxsplit=3)
                if len(parts) < 4: continue

                pid = int(parts[0])
                cpu = float(parts[1])
                mem_mb = int(parts[2]) / 1024.0
                cmdline = parts[3]

                if proc_name in cmdline and "system_watchdog" not in cmdline:
                    stats.append({
                        "pid": pid,
                        "cpu": cpu,
                        "mem_mb": mem_mb,
                        "cmd": cmdline
                    })
        except Exception as e:
            logging.error(f"Failed to query processes: {e}")
        return stats

    def check_resources(self):
        limits = self.config.get("limits", {})
        max_cpu = limits.get("max_cpu_percent", 80.0)
        max_mem = limits.get("max_memory_mb", 512)

        targets = self.config.get("monitored_processes", [])

        for target in targets:
            instances = self.get_process_stats(target)
            for inst in instances:
                violation = []
                if inst["cpu"] > max_cpu:
                    violation.append(f"CPU {inst['cpu']}% > {max_cpu}%")
                if inst["mem_mb"] > max_mem:
                    violation.append(f"MEM {inst['mem_mb']:.1f}MB > {max_mem}MB")

                if violation:
                    msg = f"Resource violation by {target} (PID {inst['pid']}): {', '.join(violation)}"
                    logging.warning(msg)
                    self._take_action(inst["pid"], target)

    def _take_action(self, pid, name):
        if self.dry_run:
            logging.info(f"[DRY-RUN] Would KILL process {name} (PID {pid})")
            return

        logging.info(f"KILLING runaway process {name} (PID {pid})")
        try:
            os.kill(pid, signal.SIGKILL)
            # Emit alert to stderr (orchestrator might catch it if piping)
            print(json.dumps({
                "layer": "intelligence",
                "event": "watchdog_kill",
                "source_entity": "localhost",
                "severity": "CRITICAL",
                "data": {"process": name, "pid": pid, "reason": "resource_exhaustion"}
            }))
            sys.stdout.flush()
        except Exception as e:
            logging.error(f"Failed to kill PID {pid}: {e}")

    def run(self):
        logging.info("Watchdog started.")
        while self.running:
            self.check_resources()
            time.sleep(self.config.get("check_interval_seconds", 10))

    def stop(self, signum=None, frame=None):
        self.running = False
        logging.info("Watchdog stopping.")

def main():
    parser = argparse.ArgumentParser(description=SCRIPT_NAME)
    parser.add_argument("--config", default="config/hardening.yaml", help="Path to config")
    parser.add_argument("--dry-run", action="store_true", help="Monitor only, do not kill")

    args = parser.parse_args()

    logging.basicConfig(level=logging.INFO, format='%(asctime)s [%(levelname)s] %(message)s', stream=sys.stderr)

    wd = Watchdog(args.config, args.dry_run)
    signal.signal(signal.SIGINT, wd.stop)
    signal.signal(signal.SIGTERM, wd.stop)

    wd.run()

if __name__ == "__main__":
    main()
