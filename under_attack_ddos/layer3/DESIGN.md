# Layer 3 (Network) Detection Components Design

This document defines the specialized detection scripts for the Network Layer (IP/ICMP). These components act as "sensors" that feed data into the orchestration and mitigation systems.

## 1. `l3_bandwidth_monitor.py`

**Purpose:**
Detects volumetric attacks by monitoring ingress/egress bandwidth usage and packet-per-second (PPS) rates on specific interfaces. It serves as the "early warning system" for massive floods.

*   **Input Data:**
    *   `/proc/net/dev` (Linux interface statistics).
    *   `ethtool` statistics (optional for hardware counters).
    *   Configurable thresholds: `max_mbps`, `max_pps`.
*   **Output Data (Events):**
    *   `bandwidth_spike_detected` (JSON): `{ "interface": "eth0", "mbps": 850, "threshold": 500, "direction": "ingress" }`
    *   `pps_spike_detected` (JSON): `{ "interface": "eth0", "pps": 50000, "threshold": 20000 }`
*   **Severity:**
    *   **CRITICAL**: > 200% of baseline.
    *   **HIGH**: > 150% of baseline.
    *   **MEDIUM**: > 110% of baseline.
*   **Interaction:**
    *   Triggers **Global Under Attack Mode** if CRITICAL.
    *   Signals `layer4` and `layer7` monitors to switch to aggressive sampling.

## 2. `l3_icmp_monitor.py`

**Purpose:**
Specifically identifies ICMP floods (Ping Flood, Smurf Attack) by analyzing the ratio of ICMP traffic to total traffic and checking for specific ICMP types (Echo Request vs Reply).

*   **Input Data:**
    *   Socket sniffer (`socket.AF_PACKET`) or `tcpdump` parsing (depending on performance needs).
    *   Firewall counters (`iptables -vL`).
*   **Output Data (Events):**
    *   `icmp_flood_detected` (JSON): `{ "type": "echo_request", "pps": 5000, "source_ip_entropy": "low" }`
    *   `smurf_attack_detected` (JSON): `{ "type": "echo_reply", "pps": 8000, "characteristic": "broadcast_amplification" }`
*   **Severity:**
    *   **HIGH**: ICMP exceeds 20% of total interface packets.
    *   **LOW**: ICMP exceeds 5% of total interface packets.
*   **Interaction:**
    *   Feeds mitigation scripts to temporarily drop ALL ICMP on the interface.

## 3. `l3_spoofing_detector.py`

**Purpose:**
Detects IP spoofing attempts by checking for "Martian" packets (private IPs on public interfaces), Bogons, and statistical anomalies in source IP distribution (randomized IP floods).

*   **Input Data:**
    *   Packet headers (Source IP).
    *   Internal "Bogon" list (RFC 1918, reserved blocks).
    *   Routing table (RPF - Reverse Path Forwarding checks).
*   **Output Data (Events):**
    *   `spoofed_ip_detected` (JSON): `{ "source_ip": "10.0.0.5", "interface": "wan0", "reason": "private_ip_on_public_iface" }`
    *   `random_spoofing_detected` (JSON): `{ "sample_size": 1000, "unique_ips": 998, "entropy": 0.99 }`
*   **Severity:**
    *   **CRITICAL**: High volume of Bogons (indicates misconfig or direct attack).
    *   **MEDIUM**: Single instance (misconfiguration).
*   **Interaction:**
    *   Directly feeds `mitigation/block_source.py` (if static IP).
    *   Triggers "Strict RPF" mode in kernel settings.

## 4. `l3_fragment_monitor.py`

**Purpose:**
Detects fragmentation attacks (Teardrop, Bonk) intended to crash the IP stack or bypass firewalls by sending malformed or excessive IP fragments.

*   **Input Data:**
    *   Packet flags (More Fragments - MF).
    *   Fragment Offset values.
    *   Kernel SNMP counters (`Ip: ReasmFails`, `Ip: ReasmReqds`).
*   **Output Data (Events):**
    *   `fragmentation_flood_detected` (JSON): `{ "fragments_pps": 2000, "reassembly_failures": 500 }`
    *   `malformed_fragment_detected` (JSON): `{ "source_ip": "1.2.3.4", "reason": "offset_overlap" }`
*   **Severity:**
    *   **HIGH**: Any detection of malformed fragments.
    *   **MEDIUM**: High rate of valid fragments.
*   **Interaction:**
    *   Triggers "Drop Fragments" mitigation in `iptables`.
