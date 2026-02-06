#!/usr/bin/env python3
"""
Under Attack Orchestrator
Part of 'under_attack_ddos' Defense System.

Responsibility: Consumes events from all detection layers, calculates Global Risk Score (GRS),
and determines the system's Operational Mode. Now supports Campaign Alerts.
"""

import sys
import os
import time
import json
import logging
import argparse
import signal
import queue
import threading
import subprocess
import shlex
from collections import defaultdict
from datetime import datetime, timezone
from intelligence.intelligence_engine import IntelligenceEngine
from alerts.alert_manager import AlertManager

# Ensure project root is in path
sys.path.append(os.path.join(os.path.dirname(__file__), ".."))
from forensics.pcap_recorder import PcapRecorder
from forensics.pcap_recorder import PcapRecorder
from ebpf.xdp_loader import XDPLoader
from mitigation.proxy_adapter import ProxyAdapter

# Third-party imports
try:
    import yaml
    from intelligence.intelligence_engine import IntelligenceEngine
except ImportError as e:
    print(f"CRITICAL: Missing required dependencies: {e}", file=sys.stderr)
    print("Please install: pip install pyyaml", file=sys.stderr)
    sys.exit(4)

# -----------------------------------------------------------------------------
# Identity & Constants
# -----------------------------------------------------------------------------
SCRIPT_NAME = "under_attack_orchestrator"
LAYER = "orchestration"
RESPONSIBILITY = "Global State Management & Decision Making"

# Default configuration (Fail-safe)
DEFAULT_CONFIG = {
    "orchestrator": {
        "window_size_seconds": 30,
        "weights": {
            "layer3": 0.4,
            "layer4": 0.3,
            "layer7": 0.3,
            "layer_game": 0.5,
            "correlation": 1.0  # High weight for pre-correlated alerts
        },
        "cross_layer_multiplier": 1.5,
        "thresholds": {
            "normal": {"max": 29},
            "monitor": {"min": 30, "max": 59},
            "under_attack": {"min": 60, "max": 89},
            "escalated": {"min": 90}
        },
        "cooldown_seconds": 300
    }
}

# -----------------------------------------------------------------------------
# Classes
# -----------------------------------------------------------------------------

class ConfigLoader:
    @staticmethod
    def load(path):
        if not os.path.exists(path):
            logging.error(f"Config file not found: {path}")
            return DEFAULT_CONFIG

        try:
            with open(path, 'r') as f:
                user_config = yaml.safe_load(f) or {}
            return user_config
        except Exception as e:
            logging.error(f"Failed to parse config: {e}")
            sys.exit(2)

class EventIngestor(threading.Thread):
    """Reads events from input source and pushes to processing queue."""
    def __init__(self, input_type, source, event_queue):
        super().__init__(daemon=True)
        self.input_type = input_type
        self.source = source
        self.event_queue = event_queue
        self.running = True

    def run(self):
        logging.info(f"Ingestor started. Source: {self.input_type}")
        if self.input_type == 'file':
            self._tail_file()
        elif self.input_type == 'stdin':
            self._read_stdin()

    def _tail_file(self):
        try:
            with open(self.source, 'r') as f:
                # Only seek to end if we are in continuous mode (long running)
                # For --once or batch processing, read from start.
                if not getattr(self, "once_mode", False):
                    f.seek(0, 2) 
                while self.running:
                    line = f.readline()
                    if not line:
                        time.sleep(0.1)
                        continue
                    self._process_line(line)
        except Exception as e:
            logging.error(f"File ingest error: {e}")

    def _read_stdin(self):
        try:
            for line in sys.stdin:
                if not self.running: break
                self._process_line(line)
        except Exception as e:
            logging.error(f"Stdin ingest error: {e}")

    def _process_line(self, line):
        try:
            if not line.strip(): return
            event = json.loads(line)
            self.event_queue.put(event)
        except json.JSONDecodeError:
            logging.warning(f"Invalid JSON received: {line[:50]}...")

    def stop(self):
        self.running = False

class CorrelationEngine:
    def __init__(self, config):
        self.config = config.get("orchestrator", DEFAULT_CONFIG["orchestrator"])
        self.window_size = self.config["window_size_seconds"]

        # In-memory state: {source_ip: [events...]}
        self.event_buffer = defaultdict(list)
        # Campaign State: [events...]
        self.active_campaigns = []
        # ML Advisories: [events...]
        self.ml_advisories = []

        self.lock = threading.Lock()

    def ingest(self, event):
        """Add event to buffer and prune old events."""
        with self.lock:
            now = time.time()
            event["_recv_time"] = now

            t = event.get("type", event.get("event"))

            # Special handling for signals
            if t == "campaign_alert":
                self.active_campaigns.append(event)
                self.active_campaigns = [c for c in self.active_campaigns if now - c["_recv_time"] <= 300]
                return
            
            if t == "ml_advisory" or event.get("source") == "ml_intelligence":
                self.ml_advisories.append(event)
                self.ml_advisories = [m for m in self.ml_advisories if now - m["_recv_time"] <= 300]
                return

            src = event.get("source_entity", "unknown")
            self.event_buffer[src].append(event)

            # Prune old events
            self.event_buffer[src] = [e for e in self.event_buffer[src]
                                      if now - e["_recv_time"] <= self.window_size]

    def get_snapshot(self):
        """Returns a snapshot for intelligence analysis."""
        with self.lock:
            # Clear empty buffers
            to_remove = [k for k, v in self.event_buffer.items() if not v]
            for k in to_remove: del self.event_buffer[k]
            
            return dict(self.event_buffer), list(self.active_campaigns), list(self.ml_advisories)

class MLProcessManager(threading.Thread):
    """
    Manages the lifecycle of the ML Online Inference subprocess.
    Pipes events to ML engine and reads advisories back.
    """
    def __init__(self, main_queue, log_level="INFO"):
        super().__init__(daemon=True)
        self.main_queue = main_queue
        self.log_level = log_level
        self.process = None
        self.running = True

    def run(self):
        script_path = os.path.abspath("ml_intelligence/inference/online_inference.py")
        cmd = [sys.executable, "-u", script_path, "--log-level", self.log_level]
        logging.info(f"Spawning ML Engine: {' '.join(cmd)}")
        
        try:
            self.process = subprocess.Popen(
                cmd,
                stdin=subprocess.PIPE,
                stdout=subprocess.PIPE,
                stderr=sys.stderr,
                text=True,
                bufsize=1
            )

            # Thread to read stdout from subprocess
            def _reader():
                logging.debug("ML Reader thread started")
                while self.running:
                    line = self.process.stdout.readline()
                    if not line: 
                        logging.debug("ML Process STDOUT closed.")
                        break
                    try:
                        advisory = json.loads(line)
                        logging.info(f"ML ADVISORY RECEIVED: {advisory.get('target_entity')} (Conf: {advisory.get('confidence')})")
                        self.main_queue.put(advisory)
                    except json.JSONDecodeError:
                        logging.debug(f"ML Process sent invalid JSON: {line}")
            
            reader_thread = threading.Thread(target=_reader, daemon=True)
            reader_thread.start()

            self.process.wait()
            logging.warning("ML Engine process terminated.")
        except Exception as e:
            logging.error(f"Failed to start ML Engine: {e}")

    def send_event(self, event):
        """Pipe an ingested event to the ML subprocess STDIN."""
        if self.process and self.process.stdin:
            try:
                line = json.dumps(event) + "\n"
                self.process.stdin.write(line)
                self.process.stdin.flush()
            except Exception as e:
                logging.debug(f"Failed to pipe event to ML: {e}")

    def stop(self):
        self.running = False
        if self.process:
            self.process.terminate()

class Orchestrator:
    def __init__(self, args, config):
        self.args = args
        self.config = config
        self.running = True
        self.queue = queue.Queue()

        # Components
        source = args.input_file if args.input == 'file' else None
        self.ingestor = EventIngestor(args.input, source, self.queue)
        if args.once:
            self.ingestor.once_mode = True
        self.correlation_engine = CorrelationEngine(config)
        self.intelligence_engine = IntelligenceEngine(config)
        self.alert_manager = AlertManager(config)

        # ML Engine
        self.ml_manager = None
        if getattr(args, "ml_support", False):
            self.ml_manager = MLProcessManager(self.queue, args.log_level)

        # Forensics
        self.pcap_recorder = PcapRecorder()

        # eBPF/XDP (Phase 22)
        # Check if enabled in config (defaulting to True for now to test simulation)
        self.ebpf_enabled = True 
        if self.ebpf_enabled:
            self.xdp = XDPLoader(interface="eth0", mode=args.mode) # args.mode might not be right, checking logic... defaults to simulate if on windows anyway

        # Proxy Adapter (Phase 25)
        self.proxy_adapter = ProxyAdapter()

        # State dump file
        self.state_file = "runtime/global_state.json"
        os.makedirs(os.path.dirname(self.state_file), exist_ok=True)

    def run(self):
        logging.info(f"Starting {SCRIPT_NAME}. Mode: {self.args.mode}")

        self.ingestor.start()
        if self.ml_manager:
            self.ml_manager.start()

        try:
            while self.running:
                # 1. Process Queue
                try:
                    while True:
                        event = self.queue.get_nowait()
                        self.correlation_engine.ingest(event)
                        # Process raw events for alerting
                        self.alert_manager.process_event(event)

                        # Pipe events to ML if supported
                        if self.ml_manager and event.get("source") != "ml_intelligence":
                            self.ml_manager.send_event(event)
                except queue.Empty:
                    pass

                # 2. Extract Intelligence
                source_events, campaigns, ml_adv = self.correlation_engine.get_snapshot()
                grs, active_sources, layers = self.intelligence_engine.calculate_grs(source_events, campaigns, ml_adv)
                
                # 3. Check for State Change
                new_state = self.intelligence_engine.determine_state(grs)
                
                # 4. Generate & Emit Directives 
                # (We emit if there's a state change or if there are active mitigations needed)
                directives = self.intelligence_engine.generate_directives(grs, active_sources, campaigns)
                
                if directives:
                    for d in directives:
                        self._emit_directive(d)
                        # Process generated directives for alerting
                        self.alert_manager.process_event(d)
                    
                    # Update global state file with the latest "state_change" directive info
                    state_dir = [d for d in directives if d["type"] == "state_change"]
                    if state_dir:
                        self._update_state_file(state_dir[0])

                # 3. Sleep
                time.sleep(1.0)

                if self.args.once and self.queue.empty() and not self.ingestor.is_alive():
                    # If ML is active, give it a tiny moment to finish flushing its buffer
                    if self.ml_manager:
                        time.sleep(2.0)
                        if self.queue.empty():
                            self.running = False
                    else:
                        self.running = False

        except KeyboardInterrupt:
            self.stop()
        except Exception as e:
            logging.error(f"Runtime error: {e}", exc_info=True)
            sys.exit(1)

    def _emit_directive(self, directive):
        print(json.dumps(directive))
        sys.stdout.flush()
        sys.stdout.flush()
        if directive["type"] == "state_change":
            state = directive["state"]
            logging.info(f"STATE CHANGE >>> {state} (Score: {directive['score']})")
            
            # Automated Forensics
            if state in ["UNDER_ATTACK", "ESCALATED"]:
                filename = self.pcap_recorder.start_capture(duration=300) # Record for 5 mins
                if filename:
                    logging.warning(f"FORENSICS: Started PCAP capture {filename}")
            elif state in ["NORMAL", "MONITOR"]:
                if self.pcap_recorder.stop_capture():
                    logging.info("FORENSICS: Stopped PCAP capture (State Normalized)")

        elif directive["type"] == "mitigation_directive":
            logging.warning(f"MITIGATION >>> {directive['action']} {directive['target']} ({directive['justification']})")
            
            # Integrated XDP Blocking
            if self.ebpf_enabled and directive["action"] == "ban_ip":
                ip = directive["target"]
                self.xdp.add_banned_ip(ip)

            # Integrated Proxy Blocking (Phase 25)
            if directive["action"] == "ban_ip":
                self.proxy_adapter.block_ip(directive["target"])

    def _update_state_file(self, directive):
        """Writes current state to runtime file for Dashboard."""
        try:
            with open(self.state_file, 'w') as f:
                state_dump = {
                    "mode": directive["state"],
                    "grs_score": directive["score"],
                    "last_update": directive["timestamp"],
                    "campaigns": self.correlation_engine.active_campaigns # Pass raw objects or names
                }
                json.dump(state_dump, f)
        except Exception as e:
            logging.error(f"Failed to write state file: {e}")

    def stop(self, signum=None, frame=None):
        logging.info("Stopping...")
        self.running = False
        self.ingestor.stop()
        if self.ml_manager:
            self.ml_manager.stop()

# -----------------------------------------------------------------------------
# Main Entry Point
# -----------------------------------------------------------------------------
def main():
    parser = argparse.ArgumentParser(description=RESPONSIBILITY)
    parser.add_argument("--config", required=True, help="Path to YAML configuration")
    parser.add_argument("--input", default="stdin", choices=["stdin", "file"], help="Input source")
    parser.add_argument("--input-file", help="Path to input file (if input=file)")
    parser.add_argument("--mode", default="normal", choices=["normal", "monitor", "under_attack"], help="Initial mode")
    parser.add_argument("--daemon", action="store_true", help="Run as background service")
    parser.add_argument("--once", action="store_true", help="Run single pass and exit")
    parser.add_argument("--ml-support", action="store_true", help="Enable ML-based anomaly detection")
    parser.add_argument("--log-level", default="INFO", choices=["DEBUG", "INFO", "WARNING", "ERROR"], help="Log verbosity")

    args = parser.parse_args()

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
    orchestrator = Orchestrator(args, config)

    signal.signal(signal.SIGINT, orchestrator.stop)
    signal.signal(signal.SIGTERM, orchestrator.stop)

    orchestrator.run()

if __name__ == "__main__":
    main()
