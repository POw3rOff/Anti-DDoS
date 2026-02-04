# Observability & Monitoring Design

This document defines how the SOC team visualizes and analyzes the `under_attack_ddos` system during peacetime and active combat. The goal is to provide **Situational Awareness** without overwhelming the operator.

## 1. Metrics Schema (The "Pulse")

We expose high-level aggregated metrics for dashboards (Prometheus/Grafana style).

| Metric Name | Type | Labels | Description |
| :--- | :--- | :--- | :--- |
| `uad_global_risk_score` | Gauge | `none` | Current system DEFCON level (0-100). |
| `uad_active_connections` | Gauge | `state` (syn_recv, estab, etc) | Current TCP connection pool status. |
| `uad_mitigation_events` | Counter | `layer`, `action` | Total mitigations applied (e.g., dropped packets). |
| `uad_traffic_ingress_mbps` | Gauge | `interface` | Inbound bandwidth utilization. |
| `uad_l7_requests_per_sec` | Gauge | `status_code` | Web traffic volume and error rates. |
| `uad_threat_actors_banned` | Gauge | `reason` | Count of currently active bans in ipsets. |

## 2. Structured Logs (The "Black Box")

All components log to `logs/system.json.log` for machine ingestion (ELK/Graylog/Loki).

**Standard Log Format:**
```json
{
  "ts": "2023-10-27T10:05:00Z",
  "level": "INFO",
  "component": "layer4_monitor",
  "msg": "SYN flood detection threshold exceeded",
  "context": {
    "pps_observed": 50000,
    "pps_threshold": 10000,
    "action_taken": "enable_syn_cookies"
  },
  "trace_id": "attack-campaign-8821"
}
```

## 3. Attack Timelines (The "War Room" View)

During an attack, operators need a chronological narrative. The **Orchestration Engine** maintains a live timeline file: `logs/current_campaign.md`.

**Example Content:**
*   **10:00:00 UTC** - [WARN] L3 Monitor detects UDP spike (800 Mbps). GRS: 45.
*   **10:00:15 UTC** - [ALERT] L4 Monitor detects SYN Flood. GRS: 65. System enters **HIGH** mode.
*   **10:00:16 UTC** - [ACTION] Applied `iptables_drop_udp` and `syn_cookie_force`.
*   **10:05:00 UTC** - [INFO] Traffic stabilizing. GRS: 50.

*Value:* This allows the SOC to answer "What happened?" immediately without querying raw logs.

## 4. Alerting Principles

Alerts must be actionable. We follow the "RED Method" (Rate, Errors, Duration) adaptation for Security.

1.  **Page/SMS:** Only for **Mode Changes** (e.g., `NORMAL` -> `HIGH`).
    *   *Why:* Requires human verification of the "Under Attack" state.
2.  **Ticket/Email:** For **Persistent Anomalies** in `ELEVATED` mode.
    *   *Why:* Indicates potential slow-attack or misconfiguration.
3.  **Dashboard Only:** Individual `mitigation_events`.
    *   *Why:* Seeing "100 IPs banned" is noise; seeing "Risk Score 95" is a signal.

## 5. Dashboard Layout Concept

*   **Top Row (Status):** Huge "DEFCON" indicator (Green/Yellow/Red). Current GRS Score.
*   **Middle Row (Impact):** Traffic Graph (Ingress vs Egress) + Latency Graph.
*   **Bottom Row (Defense):** Table of "Top Banned ASNs" and "Recent Mitigation Actions".
