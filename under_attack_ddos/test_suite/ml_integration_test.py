#!/usr/bin/env python3
"""
ML Integration Test
Verifies the Orchestrator-ML loop.
"""

import json
import time
import subprocess
import os
import sys

def generate_test_events(filename):
    events = []
    # 1. Normal traffic (noisy)
    for i in range(20):
        events.append({
            "timestamp": f"2026-02-06T03:20:{10+i:02d}Z",
            "source_entity": "1.2.3.4",
            "layer": "layer3",
            "event": "ip_stats",
            "data": {"len": 64 + (i % 10), "pps_observed": 100}
        })
    
    # 2. Anomaly traffic (Fixed size, regular intervals)
    # This should trigger Low Entropy and Robotic Heartbeat
    for i in range(30):
        events.append({
            "timestamp": f"2026-02-06T03:21:{i:02d}Z",
            "source_entity": "9.9.9.9",
            "layer": "layer4",
            "event": "syn_stats",
            "data": {"len": 64, "pps_observed": 50}
        })

    with open(filename, 'w') as f:
        for e in events:
            f.write(json.dumps(e) + "\n")

def run_test():
    test_file = "test_ml_events.jsonl"
    generate_test_events(test_file)
    
    cmd = [
        sys.executable, "orchestration/under_attack_orchestrator.py",
        "--config", "config/orchestrator.yaml",
        "--input", "file",
        "--input-file", test_file,
        "--ml-support",
        "--once",
        "--log-level", "DEBUG"
    ]
    
    print(f"Running command: {' '.join(cmd)}")
    env = os.environ.copy()
    env["PYTHONPATH"] = os.path.abspath(".")
    result = subprocess.run(cmd, capture_output=True, text=True, env=env)
    
    # Check for ML advisory in logs (stderr) or directives in stdout
    print("\n--- STDOUT (Directives) ---")
    print(result.stdout)
    print("\n--- STDERR (Logs) ---")
    print(result.stderr)
    
    # Validation logic
    ml_advisory_seen = "ML ADVISORY: Suspect 9.9.9.9" in result.stderr
    mitigation_seen = "block_ip" in result.stdout and "9.9.9.9" in result.stdout
    
    if ml_advisory_seen and mitigation_seen:
        print("\nSUCCESS: ML Integration Verified!")
        return True
    else:
        print("\nFAILURE: ML Integration test failed.")
        if not ml_advisory_seen: print("- ML Advisory was not emitted for 9.9.9.9")
        if not mitigation_seen: print("- Mitigation directive for 9.9.9.9 was not found")
        return False

if __name__ == "__main__":
    if run_test():
        sys.exit(0)
    else:
        sys.exit(1)
