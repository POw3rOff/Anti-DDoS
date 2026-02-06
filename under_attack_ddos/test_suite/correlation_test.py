#!/usr/bin/env python3
import json
import sys
import os
import time
import subprocess
from datetime import datetime, timezone

def test_cross_layer_correlation():
    print("Starting Correlation Test...")
    
    # Path to correlation engine
    correlator_path = os.path.abspath("correlation/cross_layer_correlation_engine.py")
    
    # Simulate L4 Event
    l4_event = {
        "timestamp": datetime.now(timezone.utc).isoformat(),
        "layer": "layer4",
        "event": "SYN Flood Suspect",
        "src_ip": "10.0.0.1",
        "severity": "HIGH"
    }
    
    # Simulate L7 Event (Slowloris)
    l7_event = {
        "timestamp": datetime.now(timezone.utc).isoformat(),
        "layer": "layer7",
        "event": "Slowloris Attack Detected",
        "source_entity": "10.0.0.1",
        "severity": "MEDIUM"
    }

    # Prepare input
    test_input = json.dumps(l4_event) + "\n" + json.dumps(l7_event) + "\n"
    
    # Run correlator
    process = subprocess.Popen(
        [sys.executable, correlator_path],
        stdin=subprocess.PIPE,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        text=True
    )
    
    stdout, stderr = process.communicate(input=test_input)
    
    print("--- Correlator Output ---")
    print(stdout)
    
    # Validation
    found_linkage = False
    for line in stdout.splitlines():
        try:
            alert = json.loads(line)
            if alert.get("campaign_name") == "Slow-and-Network Linkage" and alert.get("target_entity") == "10.0.0.1":
                found_linkage = True
                print("SUCCESS: Slow-and-Network Linkage detected!")
        except:
            continue
            
    if not found_linkage:
        print("FAILURE: Multi-vector campaign not detected.")
        sys.exit(1)

    # Subnet Test
    print("\nStarting Subnet Campaign Test...")
    subnet_events = []
    for i in range(1, 10):
        subnet_events.append({
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "layer": "layer3",
            "event": "IP Flood",
            "src_ip": f"192.168.1.{i}",
            "severity": "HIGH" # 10 points each -> 90 points total for /24
        })
    
    subnet_input = "\n".join([json.dumps(e) for e in subnet_events]) + "\n"
    process = subprocess.Popen(
        [sys.executable, correlator_path],
        stdin=subprocess.PIPE,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        text=True
    )
    stdout, stderr = process.communicate(input=subnet_input)
    
    print("--- Correlator Subnet Output ---")
    print(stdout)
    
    found_subnet = False
    for line in stdout.splitlines():
        try:
            alert = json.loads(line)
            if alert.get("campaign_name") == "Subnet-wide Botnet Activity":
                found_subnet = True
                print(f"SUCCESS: Subnet campaign detected for {alert.get('target_entity')}!")
        except:
            continue
            
    if not found_subnet:
        print("FAILURE: Subnet campaign not detected.")
        sys.exit(1)

if __name__ == "__main__":
    test_cross_layer_correlation()
