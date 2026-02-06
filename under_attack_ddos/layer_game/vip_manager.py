
import time
import logging
import ipaddress
from collections import defaultdict

class VIPManager:
    """
    Game Layer: VIP Whitelist Manager.
    Allows authenticated players to bypass strict DDoS filters for a set duration.
    """
    def __init__(self, vip_duration=43200): # 12 hours
        self.whitelist = {} # {ip: expiration_timestamp}
        self.vip_duration = vip_duration

    def add_vip(self, ip_address):
        """Adds an IP to the VIP list. Validates IP format."""
        try:
            ipaddress.ip_address(ip_address)
        except ValueError:
            logging.error(f"VIP: Invalid IP address format: {ip_address}")
            return False

        expiration = time.time() + self.vip_duration
        self.whitelist[ip_address] = expiration
        logging.info(f"VIP: Added {ip_address} to whitelist until {expiration}")
        return True

    def is_vip(self, ip_address):
        """Checks if IP is currently VIP."""
        exp = self.whitelist.get(ip_address)
        if exp and time.time() < exp:
            return True
        elif exp:
            # Expired, clean up
            del self.whitelist[ip_address]
        return False
    
    def cleanup(self):
        """Removes expired entries."""
        now = time.time()
        expired = [ip for ip, exp in self.whitelist.items() if now > exp]
        for ip in expired:
            del self.whitelist[ip]
