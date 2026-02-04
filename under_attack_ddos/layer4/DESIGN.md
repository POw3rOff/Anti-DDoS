# Layer 4 (Transport) Detection Components Design

This document defines the specialized detection scripts for the Transport Layer (TCP/UDP). These components focus on connection states, protocol abuse, and resource exhaustion at the OS level.

## 1. `l4_tcp_syn_monitor.py`

**Responsibility:**
Detects TCP SYN floods by monitoring the ratio of `SYN_RECV` states and half-open connections. It identifies attempts to exhaust the TCP backlog queue.

*   **Monitored Signals:**
    *   `/proc/net/snmp` (Tcp: RtoAlgorithm, ActiveOpens, PassiveOpens, AttemptFails, EstabResets, CurrEstab, InSegs, OutSegs, RetransSegs, InErrs, OutRsts, InCsumErrors).
    *   `/proc/net/netstat` (TcpExt: SyncookiesSent, SyncookiesFailed, ListenOverflows, ListenDrops).
    *   `ss -s` (Socket summary statistics).
*   **Output Event Format (JSON):**
    *   `syn_flood_detected`: `{ "syn_recv_count": 5000, "syncookies_sent_rate": 200, "listen_overflows": 50, "severity": "CRITICAL" }`
*   **Dependencies:**
    *   Standard Linux `/proc` filesystem.
    *   `ss` (iproute2) binary.

## 2. `l4_udp_flood_monitor.py`

**Responsibility:**
Detects volumetric UDP floods and amplification reflection attacks. Since UDP is stateless, it relies on baseline deviation and specific payload patterns if available (via potential future packet inspection, but primarily volumetric here).

*   **Monitored Signals:**
    *   `/proc/net/udp` (Queue sizes: `rx_queue`, `tx_queue`).
    *   `/proc/net/snmp` (Udp: InDatagrams, NoPorts, InErrors, OutDatagrams, RcvbufErrors, SndbufErrors).
    *   Interface packet counters (filtered for UDP protocol).
*   **Output Event Format (JSON):**
    *   `udp_flood_detected`: `{ "udp_pps": 80000, "drop_rate": 500, "rx_queue_avg": 4096, "severity": "HIGH" }`
    *   `udp_port_unreachable_storm`: `{ "icmp_port_unreach_rate": 200, "target_port": 53, "severity": "MEDIUM" }`
*   **Dependencies:**
    *   `/proc/net/udp`.
    *   `/proc/net/snmp`.

## 3. `l4_connection_rate_monitor.py`

**Responsibility:**
Monitors the rate of *new* connection attempts per second (CPS) globally and per source IP. Detects "slow" connection attacks or aggressive crawlers that establish full connections but do so too rapidly.

*   **Monitored Signals:**
    *   Conntrack table events (`conntrack -E` or `/proc/net/nf_conntrack` statistics).
    *   `netstat` / `ss` state transitions (Time-Wait / Close-Wait spikes).
*   **Output Event Format (JSON):**
    *   `high_connection_rate`: `{ "cps_global": 5000, "cps_peak_source": "203.0.113.4", "cps_source_val": 450, "severity": "HIGH" }`
    *   `zombie_connection_spike`: `{ "close_wait_count": 2000, "time_wait_count": 5000, "severity": "MEDIUM" }`
*   **Dependencies:**
    *   `conntrack` tools (must be installed).
    *   `ss` binary.

## 4. `l4_state_exhaustion_monitor.py`

**Responsibility:**
Prevents system-wide denial of service by monitoring global limiters: file descriptors, conntrack table usage, and ephemeral port exhaustion.

*   **Monitored Signals:**
    *   `/proc/sys/fs/file-nr` (Open file descriptors).
    *   `/proc/sys/net/netfilter/nf_conntrack_count` vs `nf_conntrack_max`.
    *   Ephemeral port usage (calculated from active connections in local port range).
*   **Output Event Format (JSON):**
    *   `conntrack_table_full`: `{ "current": 65000, "max": 65536, "usage_percent": 99.1, "severity": "CRITICAL" }`
    *   `file_descriptor_exhaustion`: `{ "current": 100000, "limit": 102400, "severity": "HIGH" }`
*   **Dependencies:**
    *   Standard Linux `/proc` filesystem interfaces.
