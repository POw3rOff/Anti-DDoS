# Kernel eBPF Layer - Structure & Design

## Overview
The `kernel_ebpf` layer serves as the **Data Plane Accelerator** for the Anti-DDoS system. It operates directly in the Linux kernel using Extended Berkeley Packet Filter (eBPF) programs (XDP/TC) to provide high-performance packet inspection, counting, and early filtering.

## Core Responsibilities
1.  **Early Detection**: Identify flood patterns (SYN, UDP, ICMP) at the NIC level (XDP) or Traffic Control (TC) ingress.
2.  **Telemetry**: Maintain high-performance per-IP and per-Port counters in BPF maps.
3.  **Signal Emission**: Emit lightweight signals (events) to user space via Perf/Ring Buffers when thresholds are exceeded.
4.  **Soft Enforcement**: Apply temporary, sampling-based mitigation (e.g., drop every Nth packet from suspicious source) *without* permanent blocking logic in the kernel.

## Directory Structure

### `common/`
Shared definitions for C programs.
- `maps.h`: Definitions of BPF maps (LRU Hashes, Arrays, Ring Buffers).
- `events.h`: C structs defining the layout of events sent to user space.

### `l3/`
Network Layer (IP/ICMP) programs.
- `ip_icmp_guard.bpf.c`: Handles ICMP floods and basic IP anomalies.

### `l4/`
Transport Layer (TCP/UDP) programs.
- `tcp_syn_guard.bpf.c`: Monitors TCP SYN rates, detects SYN floods.
- `udp_flood_guard.bpf.c`: Monitors UDP packet rates and length anomalies.

### `game/`
Application/Game specific logic.
- `game_port_tracker.bpf.c`: Monitors specific game ports (defined in maps) for PPS anomalies.

### `loader/`
Python scripts to manage the lifecycle of BPF programs.
- `ebpf_loader.py`: Loads compiled `.o` files into the kernel and pins maps.
- `pin_maps.py`: Manages the persistence of BPF maps in `/sys/fs/bpf`.

### `userspace/`
Bridge between Kernel and Orchestrator.
- `ebpf_event_bridge.py`: Consumes events from BPF Ring Buffers, normalizes them to JSON, and pipes them to the Global Orchestrator.

## Integration Flow
1.  **Packet Arrives** -> NIC -> **XDP Program** (L3/L4 Checks).
2.  **Counters Updated** -> BPF Maps (LRU Hash).
3.  **Threshold Check** -> If exceeded -> **Perf Event Emitted**.
4.  **User Space Bridge** -> Reads Event -> **JSON Conversion**.
5.  **Global Orchestrator** -> Decides Mitigation (e.g., Hard Block via iptables).
6.  **Mitigation** -> System executes `iptables` or updates BPF Block Map (future).

## Safety
- **Fail-Open**: If BPF programs crash or unload, traffic flows normally.
- **No Deep Packet Inspection**: Only headers are parsed to ensure privacy and performance.
- **Advisory**: The Kernel layer suggests; the User Space decides.
