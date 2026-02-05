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
import os

# Add parent dir to path for imports
sys.path.append(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))

from enforcement.common.persistence import PersistenceManager

class ActionBase(abc.ABC):
    def __init__(self, description, dry_run=False):
        self.description = description
        self.dry_run = dry_run
        self.persistence = PersistenceManager()
        self._setup_logging()

    def _setup_logging(self):
        logging.basicConfig(
            format='%(asctime)s [%(levelname)s] %(message)s',
            level=logging.INFO,
            stream=sys.stderr
        )

    @abc.abstractmethod
    def validate(self, target, params):
        pass

    @abc.abstractmethod
    def apply_logic(self, target, params):
        """Implement specific logic here (e.g. iptables call)."""
        pass

    @abc.abstractmethod
    def revert_logic(self, target, params):
        """Implement specific revert logic here."""
        pass

    # Template Method for Apply
    def apply(self, target, params):
        if not self.dry_run:
            self.persistence.save_action(target, self.description, params.get("ttl", 300), "enforcement")

        self.apply_logic(target, params)

    # Template Method for Revert
    def revert(self, target, params):
        if not self.dry_run:
            self.persistence.remove_action(target)

        self.revert_logic(target, params)

    def run_cli(self):
        parser = argparse.ArgumentParser(description=self.description)
        parser.add_argument("--target", required=True)
        group = parser.add_mutually_exclusive_group(required=True)
        group.add_argument("--apply", action="store_true")
        group.add_argument("--revert", action="store_true")
        parser.add_argument("--ttl", type=int, default=300)
        parser.add_argument("--params", default="{}")
        parser.add_argument("--dry-run", action="store_true")

        args = parser.parse_args()
        self.dry_run = args.dry_run

        try:
            import json
            params = json.loads(args.params)
            params["ttl"] = args.ttl

            if not self.validate(args.target, params):
                sys.exit(1)

            if args.apply:
                self.apply(args.target, params)
            elif args.revert:
                self.revert(args.target, params)

        except Exception as e:
            logging.error(f"Error: {e}")
            sys.exit(1)
