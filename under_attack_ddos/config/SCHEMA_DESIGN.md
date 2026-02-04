# Configuration Schema Design

This document defines the unified YAML configuration structure for the `under_attack_ddos` system. All scripts utilize these files to determine their behavior.

## 1. `thresholds.yaml` (The Limits)

Defines the numeric boundaries for what constitutes "normal" vs "abnormal" traffic.

```yaml
layer3:
  # Network interface bandwidth limits
  bandwidth_ingress_mbps:
    warning: 500
    critical: 850
  # Packet rate limits
  pps_ingress:
    warning: 50000
    critical: 100000
  # Protocol specific
  icmp_ratio_max: 0.10  # Max 10% of total packets
  fragment_rate_max: 100 # PPS

layer4:
  # TCP Connection limits
  syn_flood:
    syn_recv_max: 1000   # Max half-open connections
    syn_rate_pps: 200    # Max new SYNs/sec
  # UDP Baseline
  udp_flood:
    pps_max: 20000
  # Per-Source Limits
  connection_rate_per_ip:
    warning: 10
    limit: 50

layer7:
  # HTTP Request Rates
  requests_per_minute:
    global_baseline: 5000
    per_ip_baseline: 60
    per_ip_burst: 100
  # Error Rates
  error_rate_5xx_percent: 5.0
  # Slowloris
  min_data_rate_bytes_sec: 10
```

## 2. `policies.yaml` (The Logic)

Defines the decision-making matrix and mitigation strategies.

```yaml
decision_engine:
  # Weights for Global Risk Score (GRS) calculation
  weights:
    l3_score: 0.4
    l4_score: 0.3
    l7_score: 0.3

  # GRS Thresholds for Mode Switching
  modes:
    normal: { max_score: 29 }
    elevated: { min_score: 30, max_score: 59 }
    high: { min_score: 60, max_score: 89 }
    under_attack: { min_score: 90 }

mitigation_rules:
  # Confidence required to take action
  confidence_thresholds:
    soft_mitigation: 50  # e.g., Challenge/Rate Limit
    hard_mitigation: 80  # e.g., Drop/Ban

  # Fail-Safe: Max percentage of traffic to drop automatically
  safety_valve_drop_max_percent: 25

  # Whitelist handling
  whitelist_behavior: "bypass_all" # Options: bypass_all, bypass_l7_only
```

## 3. `runtime.yaml` (The State)

Controls the operational state and feature flags. This file is often modified by the Orchestrator.

```yaml
system_status:
  # Current operational mode
  current_mode: "NORMAL" # Options: NORMAL, ELEVATED, HIGH, UNDER_ATTACK
  manual_override: false

components:
  # Enable/Disable specific detection modules
  layer3_monitor: true
  layer4_monitor: true
  layer7_monitor: true
  mitigation_agent: true

timers:
  # How long to wait before downgrading mode
  cooldown_seconds: 300
  # How often to refresh intelligence data
  intelligence_refresh_interval: 10
```

## 4. `observability.yaml` (The Eyes)

Configures logging, metrics, and alerting integration.

```yaml
logging:
  # Global log level
  level: "INFO" # Options: DEBUG, INFO, WARNING, ERROR
  # Output format
  format: "json" # Options: json, text
  # File path
  path: "logs/system.json.log"

metrics:
  # Prometheus exposition
  enabled: true
  port: 9090
  path: "/metrics"

alerting:
  # Mapping GRS modes to alert channels
  channels:
    normal: []
    elevated: ["email"]
    high: ["email", "slack"]
    under_attack: ["email", "slack", "pagerduty"]

  # Message templates
  templates:
    mode_change: "System changed mode from {old} to {new}. GRS: {score}"
```
