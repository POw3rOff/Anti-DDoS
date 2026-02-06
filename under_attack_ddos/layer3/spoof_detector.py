
import logging
import ipaddress

class SpoofDetector:
    """
    Layer 3: Anti-Spoofing.
    Detects Bogon (Private/Reserved) IPs and Martian packets.
    """
    def __init__(self):
        # List of reserved subnets that should NOT appear on public internet interfaces
        self.bogon_ranges = [
            ipaddress.ip_network("10.0.0.0/8"),
            ipaddress.ip_network("172.16.0.0/12"),
            ipaddress.ip_network("192.168.0.0/16"),
            ipaddress.ip_network("127.0.0.0/8"),
            ipaddress.ip_network("0.0.0.0/8"),
            ipaddress.ip_network("169.254.0.0/16"),
            ipaddress.ip_network("224.0.0.0/4"),
            ipaddress.ip_network("240.0.0.0/4")
        ]

    def is_spoofed(self, ip_str):
        """Returns True if the IP is likely spoofed (Bogon)."""
        try:
            ip = ipaddress.ip_address(ip_str)
            for network in self.bogon_ranges:
                if ip in network:
                    return True
        except ValueError:
            return True # Invalid IP is treated as spoofed/malformed
        return False
