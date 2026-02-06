
import os
import sys
import logging
import socket
import struct
import time
from threading import Lock

# Try to import BCC, but handle failure for simulation mode (Windows/Dev)
try:
    from bcc import BPF
    HAS_BCC = True
except ImportError:
    HAS_BCC = False

class MockTable:
    """Simulates a BPF Hash Table or Array."""
    def __init__(self):
        self.data = {}
        self.lock = Lock()

    def __getitem__(self, key):
        with self.lock:
            return self.data.get(key, 0)

    def __setitem__(self, key, value):
        with self.lock:
            self.data[key] = value

    def __delitem__(self, key):
        with self.lock:
            if key in self.data:
                del self.data[key]
    
    # Mocking BPF specific methods usually found in bcc
    def lookup(self, key):
        # In BCC, lookup returns a c_type or None. 
        # For simulation, we return the value or None.
        with self.lock:
            return self.data.get(key)
            
    def items(self):
        with self.lock:
            return list(self.data.items())

class XDPLoader:
    def __init__(self, interface="eth0", mode=None):
        self.interface = interface
        self.bpf = None
        self.simulation = False
        
        # Determine mode
        if mode == "simulate" or not HAS_BCC:
            self.simulation = True
            logging.warning(f"XDP: Running in SIMULATION mode (BCC not available or forced).")
        else:
            self.simulation = False
            logging.info(f"XDP: Running in NATIVE mode on {interface}.")

        self._load_program()

    def _load_program(self):
        if self.simulation:
            # Initialize Mock Maps
            self.blacklist = MockTable()
            self.stats = MockTable()
            # Initialize stats
            self.stats[0] = 0 # dropped
            self.stats[1] = 0 # passed
            return

        # Native Load
        src_file = os.path.join(os.path.dirname(__file__), "xdp_filter.c")
        try:
            self.bpf = BPF(src_file=src_file)
            fn = self.bpf.load_func("xdp_filter", BPF.XDP)
            self.bpf.attach_xdp(self.interface, fn, 0)
            self.blacklist = self.bpf.get_table("blacklist")
            self.stats = self.bpf.get_table("stats")
            logging.info("XDP: Program attached successfully.")
        except Exception as e:
            logging.error(f"XDP: Failed to load eBPF program: {e}")
            raise

    def ip_to_int(self, ip_str):
        try:
            return struct.unpack("!I", socket.inet_aton(ip_str))[0]
        except:
            return 0

    def add_banned_ip(self, ip):
        """Adds an IP to the XDP blacklist map."""
        ip_int = self.ip_to_int(ip)
        if self.simulation:
            self.blacklist[ip_int] = 0 # Value is packet count (starts at 0)
            logging.warning(f"XDP (SIM): Banned IP {ip}")
        else:
            from ctypes import c_uint32
            # BCC requires c_types for keys/values sometimes depending on version
            self.blacklist[c_uint32(ip_int)] = c_uint32(0)
            logging.info(f"XDP: Banned IP {ip}")

    def remove_banned_ip(self, ip):
        """Removes an IP from the XDP blacklist map."""
        ip_int = self.ip_to_int(ip)
        try:
            if self.simulation:
                del self.blacklist[ip_int]
                logging.warning(f"XDP (SIM): Unbanned IP {ip}")
            else:
                from ctypes import c_uint32
                del self.blacklist[c_uint32(ip_int)]
                logging.info(f"XDP: Unbanned IP {ip}")
        except KeyError:
            pass

    def get_stats(self):
        """Returns drops and pass counts."""
        if self.simulation:
            return {
                "dropped": self.stats[0],
                "passed": self.stats[1]
            }
        else:
            # Retrieve from BPF array
            try:
                drops = self.stats[0].value
                passed = self.stats[1].value
                return {"dropped": drops, "passed": passed}
            except:
                return {"dropped": 0, "passed": 0}

    def close(self):
        if not self.simulation and self.bpf:
            self.bpf.remove_xdp(self.interface, 0)

# CLI for testing
if __name__ == "__main__":
    import argparse
    parser = argparse.ArgumentParser()
    parser.add_argument("--interface", default="eth0")
    parser.add_argument("--simulate", action="store_true")
    args = parser.parse_args()

    logging.basicConfig(level=logging.INFO)
    loader = XDPLoader(interface=args.interface, mode="simulate" if args.simulate else None)
    
    print("XDP Loaded. Banning 1.2.3.4...")
    loader.add_banned_ip("1.2.3.4")
    
    print("Checking stats...")
    print(loader.get_stats())
    
    print("Simulating traffic (mock)...")
    if loader.simulation:
        # Mock traffic hit
        ip_int = loader.ip_to_int("1.2.3.4")
        if loader.blacklist.lookup(ip_int) is not None:
             loader.stats[0] += 100
             print("Simulated 100 drops.")
    
    print("Stats after traffic:")
    print(loader.get_stats())
