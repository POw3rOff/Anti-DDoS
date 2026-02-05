#!/usr/bin/env python3
"""
eBPF Program Loader
Part of 'under_attack_ddos' Defense System.

Responsibility: Compiles (if needed) and loads eBPF programs into the kernel.
Pins maps to /sys/fs/bpf for persistence.
"""

import sys
import os
import argparse
import logging
import subprocess
import time

SCRIPT_NAME = "ebpf_loader"
BPF_FS_PATH = "/sys/fs/bpf/under_attack_ddos"

def check_requirements():
    if os.geteuid() != 0:
        logging.error("Root required to load eBPF programs.")
        sys.exit(1)

    # Check for clang/llvm
    try:
        subprocess.check_call(["clang", "--version"], stdout=subprocess.DEVNULL)
    except:
        logging.error("Clang not found. Cannot compile BPF programs.")
        # In a real deploy, we might ship pre-compiled .o files
        sys.exit(1)

def compile_program(src_path, obj_path):
    logging.info(f"Compiling {src_path} -> {obj_path}...")
    # Basic clang command for BPF
    cmd = [
        "clang", "-O2", "-target", "bpf",
        "-c", src_path, "-o", obj_path
    ]
    subprocess.check_call(cmd)

def load_program(obj_path, interface, section="xdp"):
    logging.info(f"Loading {obj_path} on {interface} ({section})...")
    # Using bpftool to load
    # bpftool prog load <file> <fs_path> [type <type>] [map name <name> pinned <path>]
    # This is a simplified wrapper.
    try:
        cmd = ["bpftool", "prog", "load", obj_path, f"/sys/fs/bpf/prog_{os.path.basename(obj_path)}", "type", "xdp"]
        subprocess.check_call(cmd)

        # Attach to interface (pseudo-code logic for generic loader)
        # bpftool net attach xdp id <id> dev <dev>
        # We need the ID.

        logging.info("Program loaded (simulated logic for bpftool wrapper).")
    except Exception as e:
        logging.error(f"Failed to load: {e}")

def main():
    parser = argparse.ArgumentParser(description=SCRIPT_NAME)
    parser.add_argument("--interface", default="eth0", help="Interface to attach to")
    parser.add_argument("--compile-only", action="store_true", help="Only compile, don't load")
    parser.add_argument("--src", required=True, help="Path to .bpf.c file")

    args = parser.parse_args()
    logging.basicConfig(level=logging.INFO, format='%(asctime)s [%(levelname)s] %(message)s', stream=sys.stderr)

    check_requirements()

    base_name = os.path.basename(args.src).replace(".c", ".o")
    obj_path = f"under_attack_ddos/kernel_ebpf/build/{base_name}"
    os.makedirs(os.path.dirname(obj_path), exist_ok=True)

    try:
        compile_program(args.src, obj_path)
    except Exception as e:
        logging.error(f"Compilation failed: {e}")
        sys.exit(1)

    if not args.compile_only:
        load_program(obj_path, args.interface)

if __name__ == "__main__":
    main()
