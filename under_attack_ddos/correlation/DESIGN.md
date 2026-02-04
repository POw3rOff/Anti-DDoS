# Cross-Layer Correlation Engine Design

This document defines the logic for the "Brain" of the Anti-DDoS system. The Correlation Engine consumes discrete events from L3, L4, and L7 to confirm attack campaigns and reduce false positives.

## 1. Event Normalization (The Common Language)

Before correlation, all events must be converted into a standard format.

**Standard Field Schema:**
*   `timestamp` (ISO 8601 UTC)
*   `layer` (L3, L4, L7)
*   `source_entity` (IP, Subnet, or SessionID)
*   `target_entity` (Interface, Port, or URL)
*   `event_type` (e.g., `syn_flood`, `http_error_spike`)
*   `severity_score` (0-100 normalized integer)

*Logic:*
A "translator" module will ingest JSON logs from the layer-specific scripts and map them to this schema.

## 2. Correlation Time Windows

Attacks happen in bursts. We use **Sliding Windows** to group events.

*   **Micro-Window (10s):** Immediate bursts. Connects an L3 bandwidth spike to an L4 SYN flood instantly.
*   **Macro-Window (5m):** Campaign detection. Connects "low-and-slow" L7 probing (Phase 1) to a later volumetric L3 attack (Phase 2).
*   **Decay:** Events older than the Macro-Window fade in relevance (weighting multiplier decreases from 1.0 to 0.0).

## 3. Entity Correlation Strategies

The engine groups events by shared entities to find the "One Actor, Many Vectors" pattern.

### Strategy A: Vertical Correlation (Single IP, Multi-Layer)
*   **Pattern:** IP X sends UDP flood (L3) AND high connection rate (L4) AND scrapes API (L7).
*   **Action:** If `Sum(Severity)` > Threshold, declare **Confirmed Multi-Vector Attacker**.
*   **Benefit:** Catches sophisticated bots that try to "jam" the firewall while scraping data.

### Strategy B: Horizontal Correlation (Distributed Botnet)
*   **Pattern:** 500 different IPs all trigger `http_error_spike` (L7) on `/login` within 10 seconds.
*   **Action:** If `Count(Unique Sources)` > Threshold, declare **Distributed Credential Stuffing**.
*   **Response:** Shift mitigation from "Block IP" to "Enable CAPTCHA" or "Rate Limit /login globally".

### Strategy C: Subnet Aggregation
*   **Pattern:** 50 IPs from the same `/24` subnet trigger "medium" severity alerts.
*   **Logic:** `Sum(Severity of /24)` > Threshold.
*   **Action:** Block the entire CIDR block temporarily.

## 4. Attack Pattern Identification (Signatures)

Pre-defined logic rules to identify specific attack campaigns:

| Campaign Name | Pattern Logic |
| :--- | :--- |
| **"Smokescreen Attack"** | **Condition:** Critical L3 Volumetric Event (DDoS) **AND** High L7 Admin Page Access.<br>**Interpretation:** Attacker floods network to distract SOC while brute-forcing admin panel. |
| **"Scanner-to-Exploit"** | **Condition:** L4 Port Scan (past 5m) **AND** L7 500 Error (now).<br>**Interpretation:** Attacker found open port and crashed the service. |
| **"Slow-Burn Exhaustion"** | **Condition:** No L3/L4 Alerts **AND** Rising L7 Latency **AND** High Duration Connections.<br>**Interpretation:** Slowloris attack bypassing volumetric filters. |

## 5. Output to Orchestration

The output of the Correlation Engine is a **Campaign Alert**, not just a raw event.

**Format:**
```json
{
  "campaign_id": "uuid-1234",
  "type": "Smokescreen Attack",
  "confidence": "HIGH",
  "primary_vector": "L3_UDP_Flood",
  "secondary_vector": "L7_Admin_Bruteforce",
  "affected_entities": ["192.168.1.5", "192.168.1.6"],
  "recommended_action": "isolate_management_network"
}
```
