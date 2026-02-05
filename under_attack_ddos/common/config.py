"""
Common configuration loader for under_attack_ddos scripts.
"""
import os
import sys
import logging
import yaml

class ConfigLoader:
    @staticmethod
    def load(path, default_config=None):
        """
        Loads YAML configuration from path.
        Returns default_config if file not found.
        Exits on parse error.
        """
        if default_config is None:
            default_config = {}

        if not os.path.exists(path):
            logging.error(f"Config file not found: {path}")
            return default_config

        try:
            with open(path, 'r') as f:
                user_config = yaml.safe_load(f) or {}
            return user_config
        except Exception as e:
            logging.error(f"Failed to parse config: {e}")
            sys.exit(2)
