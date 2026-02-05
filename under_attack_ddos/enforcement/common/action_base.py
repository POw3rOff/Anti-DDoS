#!/usr/bin/env python3
"""
Action Base Class
Part of Enforcement Layer

Responsibility: Defines the interface for all enforcement modules.
"""

import abc
import logging
import argparse
import sys

class ActionBase(abc.ABC):
    def __init__(self, description, dry_run=False):
        self.description = description
        self.dry_run = dry_run
        self._setup_logging()

    def _setup_logging(self):
        logging.basicConfig(
            format='%(asctime)s [%(levelname)s] %(message)s',
            level=logging.INFO,
            stream=sys.stderr
        )

    @abc.abstractmethod
    def validate(self, target, params):
        """Validate input parameters."""
        pass

    @abc.abstractmethod
    def apply(self, target, params):
        """Execute the mitigation."""
        pass

    @abc.abstractmethod
    def revert(self, target, params):
        """Rollback the mitigation."""
        pass

    def run_cli(self):
        """Standard CLI entry point for all enforcers."""
        parser = argparse.ArgumentParser(description=self.description)
        parser.add_argument("--target", required=True, help="Target (IP, Subnet, Port)")

        group = parser.add_mutually_exclusive_group(required=True)
        group.add_argument("--apply", action="store_true", help="Apply mitigation")
        group.add_argument("--revert", action="store_true", help="Revert mitigation")

        parser.add_argument("--ttl", type=int, default=300, help="Time to live (seconds)")
        parser.add_argument("--params", default="{}", help="JSON encoded extra parameters")
        parser.add_argument("--dry-run", action="store_true", help="Simulate action")

        args = parser.parse_args()
        self.dry_run = args.dry_run

        try:
            # Simple param parsing
            import json
            params = json.loads(args.params)
            params["ttl"] = args.ttl

            if not self.validate(args.target, params):
                logging.error("Validation failed")
                sys.exit(1)

            if args.apply:
                self.apply(args.target, params)
            elif args.revert:
                self.revert(args.target, params)

        except Exception as e:
            logging.error(f"Execution error: {e}")
            sys.exit(1)
