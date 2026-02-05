#!/usr/bin/env python3
"""
XDP Loader CLI
Part of 'under_attack_ddos' Defense System.

Responsibility: Attach/Detach XDP programs to network interfaces.
"""

import sys
import os
import argparse
import logging
import subprocess

SCRIPT_NAME = "xdp_loader"

def run_command(cmd):
    try:
        logging.info(f"Exec: {' '.join(cmd)}")
        subprocess.check_call(cmd)
    except subprocess.CalledProcessError as e:
        logging.error(f"Command failed: {e}")
        sys.exit(1)

def compile_prog():
    # Helper to compile if .o missing (simplified)
    src = "under_attack_ddos/kernel_ebpf/xdp/xdp_ipv4_guard.bpf.c"
    obj = "under_attack_ddos/kernel_ebpf/xdp/build/xdp_ipv4_guard.o"

    os.makedirs(os.path.dirname(obj), exist_ok=True)

    cmd = [
        "clang", "-O2", "-target", "bpf",
        "-c", src, "-o", obj
    ]
    run_command(cmd)
    return obj

def attach(interface, mode, obj_path):
    # ip link set dev <iface> xdpgeneric obj <file> sec xdp
    # Native XDP is 'xdp', Generic (fallback) is 'xdpgeneric'

    xdp_mode = "xdp" # Native
    if mode == "skb": xdp_mode = "xdpgeneric"

    logging.info(f"Attaching XDP ({mode}) to {interface}...")
    cmd = [
        "ip", "link", "set", "dev", interface,
        xdp_mode, "obj", obj_path, "sec", "xdp"
    ]
    run_command(cmd)

def detach(interface):
    logging.info(f"Detaching XDP from {interface}...")
    # Try both modes to be sure
    try:
        subprocess.call(["ip", "link", "set", "dev", interface, "xdp", "off"])
        subprocess.call(["ip", "link", "set", "dev", interface, "xdpgeneric", "off"])
    except:
        pass

def main():
    parser = argparse.ArgumentParser(description=SCRIPT_NAME)
    parser.add_argument("--attach", help="Interface to attach")
    parser.add_argument("--detach", help="Interface to detach")
    parser.add_argument("--mode", choices=["native", "skb"], default="skb", help="XDP Mode (driver vs generic)")
    parser.add_argument("--compile", action="store_true", help="Force recompile")

    args = parser.parse_args()
    logging.basicConfig(level=logging.INFO, format='%(asctime)s [%(levelname)s] %(message)s', stream=sys.stderr)

    if os.geteuid() != 0:
        logging.error("Root required.")
        sys.exit(1)

    obj_path = "under_attack_ddos/kernel_ebpf/xdp/build/xdp_ipv4_guard.o"

    if args.compile or not os.path.exists(obj_path):
        obj_path = compile_prog()

    if args.detach:
        detach(args.detach)

    if args.attach:
        detach(args.attach) # Clean start
        attach(args.attach, args.mode, obj_path)

if __name__ == "__main__":
    main()
