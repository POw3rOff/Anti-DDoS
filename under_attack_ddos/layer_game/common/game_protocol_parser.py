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
from datetime import datetime, timezone

class GameProtocolParser(abc.ABC):
    def __init__(self, script_name, game_name, config_path=None, dry_run=False):
        self.script_name = script_name
        self.game_name = game_name
        self.dry_run = dry_run

        self._setup_logging()
        self.config = self._load_config(config_path)

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
            print(json.dumps(event))
            sys.stdout.flush()
            logging.warning(f"ALERT: {event_type} from {src_ip} (Severity: {severity})")
        except BrokenPipeError:
            # Handle broken pipe if stdout is closed (e.g. orchestrator died)
            sys.stderr.write("Broken pipe while emitting event.\n")

    @abc.abstractmethod
    def run(self):
        """Main execution loop. Must be implemented by subclasses."""
        pass
