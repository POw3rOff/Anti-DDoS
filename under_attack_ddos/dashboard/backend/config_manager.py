
import yaml
import os
import logging
import threading

class ConfigManager:
    def __init__(self, config_path):
        self.config_path = config_path
        self.lock = threading.Lock()

    def get_config(self):
        """Reads the current configuration."""
        if not os.path.exists(self.config_path):
            logging.error(f"Config file not found: {self.config_path}")
            return {}
        
        with self.lock:
            try:
                with open(self.config_path, 'r') as f:
                    return yaml.safe_load(f) or {}
            except Exception as e:
                logging.error(f"Failed to load config: {e}")
                return {}

    def update_config(self, new_config):
        """Updates the configuration file."""
        if not new_config:
            raise ValueError("Empty configuration provided")
        
        # Basic Validation (Schema check could go here)
        if "layer3" not in new_config:
             raise ValueError("Invalid Config: Missing 'layer3' section")

        with self.lock:
            try:
                with open(self.config_path, 'w') as f:
                    yaml.dump(new_config, f, default_flow_style=False)
                logging.info(f"Configuration updated at {self.config_path}")
                return True
            except Exception as e:
                logging.error(f"Failed to save config: {e}")
                raise e
