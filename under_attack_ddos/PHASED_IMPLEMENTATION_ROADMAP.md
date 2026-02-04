# Phased Implementation Roadmap

This document outlines the strategic execution plan for the `under_attack_ddos` system. It prioritizes stability and visibility before active automated defense.

**Team Size:** 1-3 Engineers
**Total Estimated Timeline:** 8-12 Weeks

---

## Phase 1: Foundation (The Bedrock)
**Goal:** Establish the runtime environment, standard libraries, and configuration management.

*   **Components:**
    *   `config/thresholds.yaml`, `config/runtime.yaml`, etc. (Schema implementation).
    *   `runtime/` directory setup with permissions.
    *   **Base Template:** Generic Python class for CLI scripts (Input, Analysis, Output).
    *   **Logging Wrapper:** Standardized JSON logger.
*   **Success Criteria:**
    *   A "Hello World" script can load config, run as a daemon, and log valid JSON.
    *   Git repository structure is enforced.
*   **Risks:** Over-engineering the base template.
    *   *Mitigation:* Keep the template minimal; add features only when needed by L3/L4.

---

## Phase 2: Layer 3 - Network Detection (The Eyes)
**Goal:** Gain visibility into volumetric traffic (bandwidth, PPS, ICMP) at the interface level.

*   **Components:**
    *   `l3_bandwidth_monitor.py`: Reads `/proc/net/dev`.
    *   `l3_icmp_monitor.py`: Parses ICMP counters.
    *   `l3_spoofing_detector.py`: Checks for bogons/martians.
*   **Success Criteria:**
    *   System detects a simulated 500Mbps UDP flood.
    *   Events `bandwidth_spike_detected` are emitted to STDOUT.
*   **Risks:** High CPU usage during packet inspection.
    *   *Mitigation:* Rely on kernel counters (`/proc`, `ethtool`) instead of raw packet capture where possible.

---

## Phase 3: Layer 4 - Transport Detection (The Filter)
**Goal:** Detect state-exhaustion attacks (SYN Floods, Connection slots).

*   **Components:**
    *   `l4_tcp_syn_monitor.py`: Tracks `SYN_RECV` states.
    *   `l4_udp_flood_monitor.py`: Baseline UDP port usage.
    *   `l4_state_monitor.py`: Tracks conntrack table usage.
*   **Success Criteria:**
    *   System identifies a SYN flood within 10 seconds.
    *   System alerts on Conntrack table saturation (90%).
*   **Risks:** False positives from legitimate high-traffic bursts.
    *   *Mitigation:* Implement "burst tolerance" in thresholds configuration.

---

## Phase 4: Layer 7 - Application Detection (The Brain)
**Goal:** Identify behavioral anomalies in HTTP/API traffic without impacting latency.

*   **Components:**
    *   `l7_request_rate_analyzer.py`: Adaptive RPM tracking.
    *   `l7_error_rate_monitor.py`: 5xx/4xx spike detection.
    *   `l7_log_parser.py`: Tail Nginx/Apache JSON logs.
*   **Success Criteria:**
    *   Detects "Slowloris" style attacks.
    *   Detects aggressive crawling/scraping.
*   **Risks:** Log parsing latency at high load.
    *   *Mitigation:* Use sampled logging or reading from shared memory/stub status if possible.

---

## Phase 5: Correlation & Intelligence (The Judge)
**Goal:** Aggregate discrete signals into actionable "Campaigns" and calculate Global Risk Score (GRS).

*   **Components:**
    *   `correlation_engine.py`: Sliding window event grouper.
    *   `intelligence_engine.py`: Risk Score calculator (0-100).
    *   `policy_manager.py`: Maps GRS to Modes (NORMAL, ELEVATED, HIGH, UNDER_ATTACK).
*   **Success Criteria:**
    *   L3 Bandwidth Spike + L4 SYN Flood = "Complex Volumetric Attack" Campaign.
    *   GRS accurately reflects system stress level.
*   **Risks:** "Flapping" between modes.
    *   *Mitigation:* Implement hysteresis (damping) in the decision logic.

---

## Phase 6: Mitigation (The Hammer)
**Goal:** Implement the tools to *act* on the Intelligence decisions.

*   **Components:**
    *   `mitigation_executor.py`: The root-privileged agent.
    *   Actions: `iptables_ban_ip`, `ipset_update`, `enable_syn_cookies`, `nginx_enable_captcha`.
    *   **Dry-Run Mode:** Critical for initial testing.
*   **Success Criteria:**
    *   System can automatically ban an IP in `ipset` when GRS > 60.
    *   System can enable global SYN cookies when GRS > 30.
    *   **Manual Override:** Kill-switch works instantly.
*   **Risks:** Locking out admins.
    *   *Mitigation:* Hardcoded whitelist for Mgmt Subnets applied *before* any dynamic rules.

---

## Phase 7: Orchestration & Observability (The Conductor)
**Goal:** Unify control and provide "War Room" visibility.

*   **Components:**
    *   `orchestrator.py`: Daemon managing the state machine.
    *   `dashboard_exporter.py`: Prometheus metrics endpoint.
    *   `alert_manager.py`: Integrations (Slack/PagerDuty).
    *   `cli_tool`: Human interface (`./uad status`, `./uad panic`).
*   **Success Criteria:**
    *   Grafana dashboard shows real-time GRS and Attack vectors.
    *   Single command activates `UNDER_ATTACK` mode globally.
*   **Risks:** Alert fatigue.
    *   *Mitigation:* Only page on Mode Changes, not individual events.
