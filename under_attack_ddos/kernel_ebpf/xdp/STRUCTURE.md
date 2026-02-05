# XDP Acceleration Layer - Structure & Design

## Overview
The `xdp` layer provides **eXpress Data Path** filtering capabilities for the Anti-DDoS system. It operates at the earliest possible hook point in the kernel (NIC driver level), allowing it to drop packets before the kernel allocates an `sk_buff`. This is essential for mitigating volumetric attacks (10Gbps+) that would otherwise overwhelm the CPU.

## Core Responsibilities
1.  **Line-Rate Dropping**: Filter packets based on a blocklist managed by user space.
2.  **Stateless Enforcement**: Decisions are based solely on packet headers (IP, UDP, Game Ports) and the blocklist map. No complex state tracking.
3.  **Safety First**: The system defaults to `XDP_PASS`. Packet drops occur ONLY if an IP is explicitly present in the blocklist map.

## Components

### Maps (`maps/`)
- `xdp_blocklist_map.h`: Defines the `blocklist_map` (Hash Map: IP -> Action).
    - Key: `__u32` (Source IP)
    - Value: `__u32` (Action: 0=PASS, 1=DROP)

### C Programs (`*.bpf.c`)
- `xdp_ipv4_guard.bpf.c`: The primary entry point. Parses Ethernet and IPv4 headers. Checks the blocklist map.
- `xdp_udp_guard.bpf.c`: Specialized logic for UDP floods (called by ipv4_guard).
- `xdp_game_port_guard.bpf.c`: Logic for protecting specific game ports (called by ipv4_guard).

### Loaders (`loader/`)
- `xdp_loader.py`: A Python CLI tool to compile, attach, and detach the XDP programs to a network interface.
    - Usage: `./xdp_loader.py --attach eth0 --mode enforce`
- `xdp_policy_sync.py`: A bridge script that reads mitigation intents (from the Orchestrator) and updates the XDP blocklist map.

## Decision Flow
1.  **Orchestrator** detects a high-volume attack.
2.  **Orchestrator** issues a `block_ip` command with `mechanism: xdp`.
3.  **xdp_policy_sync.py** receives this command and inserts the IP into the BPF Map.
4.  **XDP Program** sees the IP in the map and returns `XDP_DROP`.

## Safety Constraints
- **Capacity**: Map size is limited (e.g., 100,000 entries) to prevent memory exhaustion.
- **Fail-Open**: If the XDP program is unloaded or encounters an error, traffic flows to the kernel stack (`XDP_PASS`).
- **No DPI**: Deep Packet Inspection is avoided to ensure the program finishes within the stringent XDP time budget.
