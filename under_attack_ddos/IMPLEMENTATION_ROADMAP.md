# Anti-DDoS Implementation Roadmap by Layer

This document outlines the step-by-step implementation strategy for the `under_attack_ddos` system, prioritizing a layered defense approach.

## Phase 1: Layer 3 - Network Layer (The Shield)

**Objective:**
Stop "dumb" volumetric attacks and malformed packets at the network edge before they consume OS resources. This is the first line of defense.

*   **Goals:**
    *   Drop invalid/spoofed packets.
    *   Limit ICMP traffic to diagnostic levels.
    *   Protect against fragmentation attacks.
*   **Attack Vectors Handled:**
    *   ICMP Floods (Ping Flood, Smurf).
    *   IP Spoofing (Bogon filtering).
    *   Teardrop / Fragment Floods.
    *   Protocol misuse (e.g., IGMP in a web server environment).
*   **Key Metrics/Outputs:**
    *   `packets_dropped_count` (counter).
    *   `bandwidth_ingress_mbps` (gauge).
    *   `banned_ips_l3` (list).
*   **Interaction:**
    *   Operates independently.
    *   Feeds "confirmed bad" source IPs to the Global Blacklist used by L4 and L7.

---

## Phase 2: Layer 4 - Transport Layer (The Filter)

**Objective:**
Protect the OS connection state tables (TCP stack, conntrack) from exhaustion. Manage "half-open" connections and UDP baselines.

*   **Goals:**
    *   Enforce TCP state validity (SYN cookies, RST validation).
    *   Rate limit new connections per source IP.
    *   Validate UDP payloads (if applicable) or strict UDP limiting.
*   **Attack Vectors Handled:**
    *   TCP SYN Floods.
    *   UDP Floods / Amplification reflection.
    *   Connection Exhaustion (filling connection slots without sending data).
    *   Port Scans.
*   **Key Metrics/Outputs:**
    *   `syn_recv_count` (gauge).
    *   `active_connections` (gauge).
    *   `tcp_retransmission_rate` (gauge).
*   **Interaction:**
    *   **Input:** Consumes Global Blacklist from L3.
    *   **Output:** Promotes IPs exceeding connection limits to L3 Blacklist for total blocking.

---

## Phase 3: Layer 7 - Application Layer (The Brain)

**Objective:**
Analyze payload content and user behavior. Distinguish legitimate high-traffic users from botnets. This layer requires the most CPU but offers the highest precision.

*   **Goals:**
    *   Validate HTTP/API requests (Headers, User-Agents).
    *   Detect anomalous behavioral patterns (e.g., crawling non-existent paths).
    *   Mitigate resource exhaustion attacks (slow/heavy requests).
*   **Attack Vectors Handled:**
    *   HTTP Floods (GET/POST).
    *   Slowloris / Slow Read.
    *   API Abuse / Scraping.
    *   Cache Bypassing (Random query parameters).
*   **Key Metrics/Outputs:**
    *   `requests_per_second` (gauge).
    *   `error_rate_5xx` (gauge).
    *   `request_latency_ms` (histogram).
    *   `suspicious_user_agents` (list).
*   **Interaction:**
    *   **Input:** Uses L3/L4 status to determine "Under Attack" thresholds (e.g., if L4 is stressed, L7 enters strict CAPTCHA mode).
    *   **Output:** Sends sophisticated signatures (e.g., specific User-Agent strings or complex IP patterns) to the **Intelligence Engine** for analysis.

---

## Phase 4: Integration & Correlation

**Objective:**
Unify the layers into a cohesive adaptive system.

*   **Workflow:**
    1.  **L3** handles the noise.
    2.  **L4** manages the state.
    3.  **L7** manages the intent.
    4.  **Correlation Engine** watches all three.
        *   *Example:* If L3 sees bandwidth spike AND L7 sees error spikes -> Trigger "Under Attack" mode globally.
