#!/usr/bin/env python3
import sys
import os
import ctypes
import socket
import struct
import argparse

# Try to verify bcc availability
try:
    from bcc.libbcc import lib
except ImportError:
    print("Error: bcc not found. Install python3-bpfcc.")
    sys.exit(1)

PINNED_MAP_PATH = b"/sys/fs/bpf/uad/map_blacklist"

def update_map(ip_str):
    if not os.path.exists(PINNED_MAP_PATH):
        print(f"Error: Map file not found at {PINNED_MAP_PATH.decode()}. Is XDP loaded via loader.py?")
        return False

    # 1. Get the map file descriptor
    map_fd = lib.bpf_obj_get(PINNED_MAP_PATH)
    if map_fd < 0:
        print(f"Error: Could not open pinned map. Permission denied or invalid map.")
        return False

    # 2. Prepare Key (u32 IP) and Value (u32 count)
    # Map type is HASH, key is u32, value is u32.

    try:
        ip_int = struct.unpack("I", socket.inet_aton(ip_str))[0]
    except OSError:
        print(f"Error: Invalid IP address {ip_str}")
        return False

    # Using ctypes for the raw update call
    key = ctypes.c_uint32(ip_int)
    value = ctypes.c_uint32(1) # Initial packet count or flag

    # 3. Update the map (BPF_ANY = 0)
    ret = lib.bpf_map_update_elem(map_fd, ctypes.byref(key), ctypes.byref(value), 0)

    if ret != 0:
        print(f"Error: Failed to update map. Errno: {ctypes.get_errno()}")
        return False

    print(f"Successfully added {ip_str} to XDP blacklist.")
    return True

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Update persistent BPF map")
    parser.add_argument("ip", help="IP address to block")
    args = parser.parse_args()

    if os.getuid() != 0:
        print("Error: Must run as root.")
        sys.exit(1)

    update_map(args.ip)
