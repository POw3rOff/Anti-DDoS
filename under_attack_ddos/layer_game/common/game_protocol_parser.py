#!/usr/bin/env python3
"""
Common Game Protocol Parser Base Class
Part of Layer G (Game Protocol Defense)

Responsibility: Provides shared infrastructure for all game-specific monitors,
including configuration loading, logging setup, and standardized event emission.
"""

import sys
import os
import json
import logging
import yaml
import abc
import re
from datetime import datetime, timezone

# Ensure project root is in path for imports
sys.path.append(os.path.join(os.path.dirname(__file__), "../../"))
from intelligence.enrichment import GeoIPEnricher

class GameProtocolParser(abc.ABC):
    def __init__(self, script_name, game_name, config_path=None, dry_run=False):
        self.script_name = script_name
        self.game_name = game_name
        self.dry_run = dry_run

        self._setup_logging()
        self.config = self._load_config(config_path)
        self.enricher = GeoIPEnricher()
        
        # Deep Inspection Rules (Loaded from config in real scenario)
        self.packet_regex = self.config.get("deep_inspec_regex", None)
        if self.packet_regex:
            try:
                self.packet_regex = re.compile(self.packet_regex)
            except re.error as e:
                logging.error(f"Invalid regex for deep inspection: {self.packet_regex}. Error: {e}")
                self.packet_regex = None


        logging.info(f"Initialized {self.script_name} for {self.game_name}. Dry-run: {self.dry_run}")

    def _setup_logging(self):
        """Sets up standard logging to STDERR."""
        logging.basicConfig(
            format='%(asctime)s [%(levelname)s] %(message)s',
            level=logging.INFO,
            stream=sys.stderr
        )

    def _load_config(self, path):
        """Loads configuration from YAML file."""
        if not path:
            return {}

        try:
            with open(path, 'r') as f:
                return yaml.safe_load(f) or {}
        except Exception as e:
            logging.error(f"Failed to load config from {path}: {e}")
            return {}

    def emit_event(self, event_type, src_ip, severity, data=None):
        """
        Emits a structured JSON event to STDOUT.

        Args:
            event_type (str): The specific event name (e.g., 'auth_flood').
            src_ip (str): The source IP address.
            severity (str): Severity level (LOW, MEDIUM, HIGH, CRITICAL).
            data (dict, optional): Additional context data.
        """
        if data is None:
            data = {}

        # Ensure 'status' is present in data
        if "status" not in data:
            data["status"] = "simulated" if self.dry_run else "active"

        # Enrich Context
        enrichment = self.enricher.enrich(src_ip)
        if enrichment.get("country") != "Unknown":
            data["context"] = enrichment
            country_tag = f" [{enrichment.get('country')} {enrichment.get('asn')}]"
        else:
            country_tag = ""

        event = {
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "layer": "game",
            "game": self.game_name,
            "event": event_type,
            "src_ip": src_ip,
            "severity": severity,
            "data": data
        }

        try:
            # Original print to stdout for orchestrator consumption
            print(json.dumps(event))
            sys.stdout.flush()
            # Log to stderr for debugging/monitoring
            logging.warning(f"ALERT: {event_type} from {src_ip}{country_tag} (Severity: {severity})")
        except BrokenPipeError:
            # Handle broken pipe if stdout is closed (e.g. orchestrator died)
            sys.stderr.write("Broken pipe while emitting event.\n")
        
        return event # Return the event dictionary for potential further use or testing

    def deep_inspect(self, payload_bytes):
        """
        Phase 24: Protocol Deep Inspection.
        Validates payload against strict protocol rules.
        Returns check_passed (bool), reason (str).
        """
        # 1. Length Check
        if len(payload_bytes) > self.config.get("max_payload_size", 1400):
            return False, "payload_too_large"
        
        # 2. Magic Byte Check (Example for common games)
        magic = self.config.get("magic_bytes", None) # e.g. b'\xff\xff\xff\xff' for Source
        if magic:
            # Assuming magic is configured as bytes, e.g., b'\xff\xff\xff\xff'
            if not payload_bytes.startswith(magic):
                return False, "invalid_magic_bytes"

        # 3. Regex Check (if configured)
        if self.packet_regex:
            # Decode bytes to string for regex matching, assuming UTF-8 or similar
            # This might need adjustment based on actual protocol encoding
            try:
                payload_str = payload_bytes.decode('utf-8', errors='ignore')
                if not self.packet_regex.match(payload_str):
                    return False, "regex_mismatch"
            except UnicodeDecodeError:
                return False, "payload_decode_error"

        return True, "ok"

    @abc.abstractmethod
    def run(self):
        """Main execution loop. Must be implemented by subclasses."""
        pass
