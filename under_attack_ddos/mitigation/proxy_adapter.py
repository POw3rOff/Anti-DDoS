
import os
import subprocess
import logging
import platform

class ProxyAdapter:
    """
    Mitigation Adapter for Reverse Proxies (Nginx).
    Manages the dynamic denylist file and triggers reloads.
    """
    def __init__(self, config_path="web_security/dynamic_denylist.conf"):
        self.config_path = config_path
        self.banned_ips = set()
        self._ensure_file()

    def _ensure_file(self):
        """Ensures the denylist file exists."""
        if not os.path.exists(self.config_path):
            try:
                os.makedirs(os.path.dirname(self.config_path), exist_ok=True)
                with open(self.config_path, 'w') as f:
                    f.write("# Dynamic Denylist\n")
            except Exception as e:
                logging.error(f"Failed to init proxy config: {e}")

    def block_ip(self, ip_address, verdict=1):
        """
        Adds an IP to the Nginx deny list and reloads.
        verdict: 1=Block (403), 2=Challenge (429)
        """
        # If IP is already banned with same verdict, skip
        if (ip_address, verdict) in self.banned_ips:
            return

        self.banned_ips.add((ip_address, verdict))
        try:
            # Append to file (Nginx format: '1.2.3.4 1;' or '1.2.3.4 2;')
            # 1 = Block, 2 = Challenge (mapped in nginx config)
            
            with open(self.config_path, 'a') as f:
                f.write(f"{ip_address} {verdict};\n")
            
            logging.info(f"PROXY: Added {ip_address} to list with verdict {verdict}.")
            self._reload_service()

        except Exception as e:
            logging.error(f"Failed to update proxy config: {e}")

    def _reload_service(self):
        """Reloads Nginx. Simulated on Windows."""
        if platform.system() == "Windows":
            logging.info("PROXY [SIMULATION]: 'nginx -s reload' check passed.")
            return

        # Real Linux Reload
        try:
            # Validate first
            subprocess.run(["nginx", "-t"], check=True, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
            # Reload
            subprocess.run(["systemctl", "reload", "nginx"], check=True)
            logging.info("PROXY: Nginx reloaded successfully.")
        except Exception as e:
            logging.error(f"PROXY RELOAD FAILED: {e}")
