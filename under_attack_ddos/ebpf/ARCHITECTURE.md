# eBPF/XDP Defensive Extension Architecture

This document defines the high-performance kernel-level extension for the `under_attack_ddos` system. It utilizes XDP (eXpress Data Path) to process packets at the earliest possible point in the driver, providing visibility and optional mitigation capabilities that user-space scripts cannot match in speed.

## 1. High-Level Architecture

The eBPF module is designed as an **Accessory**, not a replacement. It acts as a high-speed sensor and an optional actuator, controlled entirely by the existing Python Orchestrator.

### Data Flow
1.  **Kernel Space (XDP):**
    *   Intercepts packets at the NIC driver.
    *   Parses L3/L4 headers.
    *   Updates statistics in **BPF Maps** (`PERCPU_ARRAY`, `HASH`).
    *   Checks "Mitigation Maps" (`LPM_TRIE` or `HASH`) for blocking decisions.
    *   Returns `XDP_PASS` (default), `XDP_DROP` (if blocked), or `XDP_TX` (syn-cookies, future).
2.  **User Space (Python Loader):**
    *   Loads the BPF bytecode into the kernel.
    *   Periodically reads BPF Maps to extract metrics (PPS, Bandwidth, SYN rate).
    *   Feeds these metrics to the **L3/L4 Monitors** (integration point).
    *   Updates "Mitigation Maps" based on decisions from the **Mitigation Controller**.

### Authority Model
*   **User-Space is King:** The XDP program does NOT decide to block on its own. It only enforces rules populated by the user-space Mitigation Controller.
*   **Fail-Open:** If the user-space agent dies, the XDP program continues using the last known rules. If XDP fails to load, traffic bypasses it (`XDP_PASS` is implicit if not attached).

## 2. eBPF Components & File Structure

We utilize **CO-RE (Compile Once – Run Everywhere)** via `libbpf` to ensure portability across kernel versions.

```text
under_attack_ddos/ebpf/
├── src/
│   ├── xdp_main.c           # Main dispatcher (tail calls if needed)
│   ├── xdp_l3_stats.c       # IP/ICMP counting logic
│   ├── xdp_l4_stats.c       # TCP/UDP counting logic
│   ├── xdp_filter.c         # Dropping logic (reads mitigation maps)
│   └── common_maps.h        # Shared map definitions
├── loader.py                # Python CLI tool to load/unload/read stats
└── maps_schema.json         # Definition of map structures for Python parsers
```

## 3. Metrics to Collect (Observability)

The XDP program updates these maps, which `loader.py` reads and converts to JSON events.

1.  **`map_l3_stats` (PERCPU_ARRAY):**
    *   Keys: Protocol (TCP, UDP, ICMP, OTHER).
    *   Values: `{ rx_packets, rx_bytes }`.
2.  **`map_syn_rate` (HASH):**
    *   Keys: Source IP (u32).
    *   Values: `{ syn_count, last_seen_ts }`.
    *   *Note:* Cleaned up by user-space to prevent memory exhaustion.
3.  **`map_drop_counters` (PERCPU_ARRAY):**
    *   Keys: Reason Code (e.g., `DROP_BLACKLIST`, `DROP_INVALID`).
    *   Values: `{ count }`.

## 4. Safety Model & Mitigation

### Default: PASS
The program defaults to `XDP_PASS` for all traffic.

### Mitigation Activation
Mitigation is enabled via BPF Maps populated by `mitigation_controller.py`:

1.  **Global Toggle:** A `global_config` map containing a `mode` flag (`NORMAL`=0, `PROTECT`=1).
    *   If `mode == 0`: Always return `XDP_PASS`.
2.  **Blacklist:** `map_blacklist` (LPM_TRIE).
    *   If `mode == 1`: Lookup Source IP. If match -> `XDP_DROP`.
3.  **Protocol Filters:** `map_proto_block` (ARRAY).
    *   e.g., Block all UDP (except DNS) during an amplification attack.

### Immediate Rollback
*   The `loader.py` supports a `--unload` flag to detach the XDP program instantly from the interface.
*   The `under_attack_mode.py` "Force Normal" command will clear the BPF maps.

## 5. Integration with Existing System

*   **L3 Monitor (`ip_flood_analyzer.py`):**
    *   Currently sniffs using Scapy (slow).
    *   **Upgrade:** Will shell out to `loader.py --stats --json` to get high-speed counters from kernel space instead of sniffing.
*   **Mitigation Controller (`mitigation_controller.py`):**
    *   Currently logs alerts.
    *   **Upgrade:** Will call `loader.py --block <ip>` to populate the XDP blacklist map.

## 6. CLI Requirements (`loader.py`)

The loader acts as the bridge.

```bash
# Start XDP on eth0
python3 loader.py --interface eth0 --load

# Read Stats (JSON)
python3 loader.py --stats --json

# Add IP to Blocklist
python3 loader.py --block 192.168.1.5 --duration 300

# Unload (Emergency)
python3 loader.py --unload --interface eth0
```

## 7. Dependencies

*   **Kernel:** Linux 5.4+ (for stable XDP/CO-RE support).
*   **Tools:** `clang`, `llvm` (for compiling C to BPF).
*   **Libraries:** `libbpf` (system), `bcc` or `pybpf` (Python bindings). We recommend `bcc` for the Python loader due to ease of map manipulation.
