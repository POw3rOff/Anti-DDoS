# Intelligence & Decision Engine Design

This document defines the decision-making logic of the `under_attack_ddos` system. It translates correlated risks into actionable defense strategies, balancing service availability with protection.

## 1. Risk Scoring Model (The "Defcon" Level)

The system calculates a dynamic **Global Risk Score (GRS)** ranging from 0 to 100. This score is updated every second based on weighted inputs from the Correlation Engine.

**Formula Concept:**
`GRS = (L3_Weight * L3_Severity) + (L4_Weight * L4_Severity) + (L7_Weight * L7_Severity) + Multiplier(Correlation_Confidence)`

**Component Weights:**
*   **L3 Volumetric:** High impact on infrastructure. Weight: 0.4
*   **L4 State:** High impact on OS. Weight: 0.3
*   **L7 Resource:** High impact on CPU/DB. Weight: 0.3
*   **Multiplier:** If a Cross-Layer Campaign is confirmed (e.g., "Smokescreen Attack"), boost score by 1.5x.

## 2. Severity Levels (Defense Modes)

The GRS maps to four operational modes. The system transitions between these modes with hysteresis (damping) to prevent flapping.

| Mode | GRS Range | Operational State | Goal |
| :--- | :--- | :--- | :--- |
| **NORMAL** | 0 - 29 | Passive Monitoring | Baseline learning. Zero active mitigation. |
| **ELEVATED** | 30 - 59 | Active Sampling | Enable L7 challenges (JS/Cookie). Increased logging. Pre-computation of rules. |
| **HIGH** | 60 - 89 | Targeted Mitigation | Block specific bad IPs. Rate limit suspect subnets. Drop invalid packets aggressively. |
| **UNDER ATTACK** | 90 - 100 | Emergency Defense | "Save the ship." Drop non-essential traffic. Enforce strict CAPTCHA/Geo-blocking. Prioritize known good users (VIPs). |

## 3. Confidence Thresholds (Avoiding False Positives)

Before applying a specific mitigation action (e.g., banning an IP), the system evaluates the **Confidence Score** of the detection.

*   **Low Confidence (< 50%):** Do nothing or Log only.
*   **Medium Confidence (50-79%):** Apply "Soft" Mitigation.
    *   *Action:* Challenge (CAPTCHA, JS Calculation), Delay (Tarpit), Rate Limit.
*   **High Confidence (> 80%):** Apply "Hard" Mitigation.
    *   *Action:* Drop Packet, Reset Connection, Ban IP (temporary).

## 4. Decision Outputs (Action Directives)

The Intelligence Engine outputs **Directives** to the Mitigation Layer.

**Directive Format (JSON):**
```json
{
  "id": "directive-8821",
  "priority": "CRITICAL",
  "target_layer": "layer3",
  "action": "update_ipset",
  "params": {
    "set_name": "blacklist_high_confidence",
    "entries": ["192.168.1.5", "10.0.0.0/24"],
    "ttl_seconds": 300
  },
  "justification": "confirmed_syn_flood_source"
}
```

**Common Directives:**
1.  **`set_global_mode`**: Switches the entire system to `NORMAL`, `ELEVATED`, etc.
2.  **`update_dynamic_acl`**: Adds/Removes IPs from high-performance IP sets (ipset).
3.  **`adjust_rate_limit`**: Dynamically lowers the allowed RPM for an endpoint (e.g., `/login`).
4.  **`enable_challenge`**: Instructs the web server/reverse proxy to serve an interstitial challenge page.

## 5. Automated Recovery (Cool-down)

*   **Condition:** GRS stays below the threshold for the lower mode for > 5 minutes.
*   **Action:**
    1.  Downgrade Mode (e.g., `UNDER ATTACK` -> `HIGH`).
    2.  Flush temporary blacklists (allow re-evaluation).
    3.  Reset strict rate limits to baseline.
