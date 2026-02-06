#!/usr/bin/env python3
"""
eBPF/XDP Loader & Map Manager
Part of 'under_attack_ddos' Defense System.

Responsibility: Compiles C bytecode, loads it into the kernel/XDP, 
and provides a CLI for map manipulation (blocking/stats).
"""

import sys
import os
import time
import json
import argparse
import logging
import signal
import socket
import struct

# Third-party imports
try:
    from bcc import BPF
except ImportError:
    # Allow running in dry-run mode without BCC for platform compatibility
    BPF = None

# -----------------------------------------------------------------------------
# Identity & Constants
# -----------------------------------------------------------------------------
SCRIPT_NAME = "ebpf_loader"
LAYER = "ebpf"
SOURCE_PATH = os.path.join(os.path.dirname(__file__), "src/xdp_main.c")

# -----------------------------------------------------------------------------
# Classes
# -----------------------------------------------------------------------------

class eBPFManager:
    def __init__(self, args):
        self.args = args
        self.bpf = None
        self.interface = args.interface

    def load(self):
        """Compiles and attaches the BPF program."""
        if not BPF:
            logging.error("BCC (python3-bpfcc) not found. Cannot load XDP.")
            return False

        try:
            logging.info(f"Compiling BPF source from {SOURCE_PATH}...")
            self.bpf = BPF(src_file=SOURCE_PATH)
            
            fn = self.bpf.load_func("xdp_dispatcher", BPF.XDP)
            logging.info(f"Attaching XDP program to {self.interface}...")
            self.bpf.attach_xdp(self.interface, fn, 0)
            return True
        except Exception as e:
            logging.error(f"Failed to load BPF: {e}")
            return False

    def unload(self):
        """Detaches the XDP program."""
        if not BPF: return
        try:
            logging.info(f"Detaching XDP from {self.interface}...")
            self.bpf.remove_xdp(self.interface, 0)
        except Exception as e:
            logging.error(f"Failed to unload BPF: {e}")

    def get_source_stats(self):
        """Reads per-IP stats from the hash map."""
        if self.args.dry_run or not self.bpf:
            return self._mock_source_stats()

        stats_map = self.bpf.get_table("map_source_stats")
        results = {}
        
        for k, v in stats_map.items():
            ip_str = socket.inet_ntoa(struct.pack("I", k.value))
            results[ip_str] = {
                "packets": v.rx_packets,
                "bytes": v.rx_bytes
            }
        
        # Optional: Clear map after reading to prevent memory exhaustion
        # stats_map.clear() 
        
        return results

    def get_syn_stats(self):
        """Reads per-IP SYN counts from the hash map."""
        if self.args.dry_run or not self.bpf:
            return self._mock_syn_stats()

        stats_map = self.bpf.get_table("map_syn_stats")
        results = {}
        
        for k, v in stats_map.items():
            ip_str = socket.inet_ntoa(struct.pack("I", k.value))
            results[ip_str] = v.value
        
        return results

    def _mock_syn_stats(self):
        return {
            "10.0.0.1": 1500,
            "10.0.0.2": 250
        }

    def _mock_source_stats(self):
        return {
            "1.2.3.4": {"packets": 5000, "bytes": 300000},
            "5.6.7.8": {"packets": 1500, "bytes": 75000}
        }

    def get_stats(self):
        """Reads L3 stats from the per-cpu array map."""
        if self.args.dry_run or not self.bpf:
            return self._mock_stats()

        stats_map = self.bpf.get_table("map_l3_stats")
        results = {}
        
        # Protocol mapping from common_maps.h
        proto_map = {0: "TCP", 1: "UDP", 2: "ICMP", 3: "OTHER"}
        
        for k, v in stats_map.items():
            proto_name = proto_map.get(k.value, f"PROTO_{k.value}")
            # PERCPU_ARRAY sums automatically in newer BCC, otherwise we iterate
            packets = sum([cpu.rx_packets for cpu in v])
            bytes_val = sum([cpu.rx_bytes for cpu in v])
            
            results[proto_name] = {
                "packets": packets,
                "bytes": bytes_val
            }
        
        return results

    def block_ip(self, ip_str):
        """Adds an IP to the blacklist map (LPM Trie)."""
        if self.args.dry_run or not self.bpf:
            logging.info(f"[DRY-RUN] Blocking IP in eBPF: {ip_str}")
            return

        try:
            blacklist = self.bpf.get_table("map_blacklist")
            # Convert IP to network byte order integer
            ip_int = struct.unpack("I", socket.inet_aton(ip_str))[0]
            
            # LPM Trie key requires prefixlen (32 for single IP)
            # The BCC LPM Key helper handles the prefixlen + data layout
            key = blacklist.Key(32, ip_int)
            blacklist[key] = ctypes.c_uint32(1)
            
            logging.info(f"IP {ip_str} added to eBPF blacklist.")
        except Exception as e:
            logging.error(f"Failed to block IP: {e}")

    def _mock_stats(self):
        return {
            "TCP": {"packets": 12345, "bytes": 6789000},
            "UDP": {"packets": 543, "bytes": 12000},
            "ICMP": {"packets": 12, "bytes": 640},
            "OTHER": {"packets": 0, "bytes": 0}
        }

# -----------------------------------------------------------------------------
# Main Entry Point
# -----------------------------------------------------------------------------
def main():
    parser = argparse.ArgumentParser(description="eBPF/XDP Loader")
    parser.add_argument("--interface", help="Network interface (e.g. eth0)")
    parser.add_argument("--load", action="store_true", help="Load and attach BPF")
    parser.add_argument("--unload", action="store_true", help="Unload BPF")
    parser.add_argument("--stats", action="store_true", help="Read metrics")
    parser.add_argument("--syn-stats", action="store_true", help="Read SYN metrics")
    parser.add_argument("--source-stats", action="store_true", help="Read per-source L3 metrics")
    parser.add_argument("--block", help="Block specific IP")
    parser.add_argument("--json", action="store_true", help="Output stats in JSON format")
    parser.add_argument("--dry-run", action="store_true", help="Simulate behavior")
    parser.add_argument("--log-level", default="INFO", help="Log level")

    args = parser.parse_args()

    logging.basicConfig(level=args.log_level, format='%(asctime)s [%(levelname)s] %(message)s')

    manager = eBPFManager(args)

    if args.load:
        if not args.interface:
            print("Error: --interface required for --load")
            sys.exit(1)
        manager.load()
        # Keep alive if not just stats or other quick commands
        if not (args.stats or args.block):
            try:
                while True: time.sleep(1)
            except KeyboardInterrupt:
                manager.unload()

    elif args.unload:
        manager.unload()

    if args.block:
        manager.block_ip(args.block)

    if args.stats:
        stats = manager.get_stats()
        if args.json:
            print(json.dumps(stats))
        else:
            for proto, val in stats.items():
                print(f"{proto}: {val['packets']} pkts, {val['bytes']} bytes")

    if args.syn_stats:
        stats = manager.get_syn_stats()
        if args.json:
            print(json.dumps(stats))
        else:
            for ip, count in stats.items():
                print(f"IP {ip}: {count} SYNs")

    if args.source_stats:
        stats = manager.get_source_stats()
        if args.json:
            print(json.dumps(stats))
        else:
            for ip, val in stats.items():
                print(f"IP {ip}: {val['packets']} pkts, {val['bytes']} bytes")

if __name__ == "__main__":
    main()
