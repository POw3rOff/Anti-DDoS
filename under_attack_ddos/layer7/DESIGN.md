# Layer 7 (Application) Detection Components Design

This document defines the advanced detection scripts for the Application Layer (HTTP/API). These components operate where "traffic" becomes "user intent," analyzing behavior rather than just volume.

## 1. `l7_behavioral_fingerprinter.py`

**Detection Logic Concept:**
Builds a temporary "reputation score" for active sessions based on navigation patterns. It compares user journeys against known "bot-like" behaviors (e.g., accessing `/login` without loading `/` first, linear browsing, zero dwell time).

*   **Inputs:**
    *   Web Server Access Logs (Nginx/Apache json format preferred).
    *   HTTP Headers (User-Agent, Referer, Accept-Language, JA3/TLS fingerprints if available).
*   **Outputs (Events):**
    *   `suspicious_bot_fingerprint`: `{ "session_id": "xyz", "score": 85, "reason": "non_standard_flow_sequence" }`
    *   `headless_browser_detected`: `{ "ip": "1.2.3.4", "confidence": "high", "indicator": "webdriver_header_anomaly" }`
*   **False-Positive Mitigation:**
    *   **Score Decay:** Scores naturally decrease over time; a user must be consistently "bad" to trigger.
    *   **Known Bot Whitelist:** Check User-Agents against `googlebot`, `bingbot` (and verify IP ownership via rDNS).

## 2. `l7_request_rate_analyzer.py`

**Detection Logic Concept:**
Implements "Adaptive Rate Limiting" rather than static thresholds. It calculates the standard deviation of request rates for specific resources (e.g., `/search`, `/login`) and flags deviations. It detects "low-and-slow" rate abuse that stays *just below* standard WAF limits.

*   **Inputs:**
    *   Request timestamps per IP/Session.
    *   URL/Endpoint paths.
    *   HTTP Method (POST/PUT weighted higher).
*   **Outputs (Events):**
    *   `resource_exhaustion_attempt`: `{ "target": "/api/v1/report", "rpm": 45, "baseline_rpm": 5, "severity": "HIGH" }`
    *   `burst_pattern_detected`: `{ "ip": "10.0.0.1", "pattern": "100_reqs_in_1s_then_sleep" }`
*   **False-Positive Mitigation:**
    *   **Burst Allowances:** Allow short bursts for legitimate user actions (e.g., opening 10 tabs).
    *   **Static Asset Exclusion:** Ignore requests for `.css`, `.js`, `.png` in rate calculations (focus on dynamic backend hits).

## 3. `l7_slow_attack_detector.py`

**Detection Logic Concept:**
Identifies "Slowloris" and "Slow Read" attacks where sockets are held open with minimal throughput. It monitors the *duration* of active connections relative to the bytes transferred.

*   **Inputs:**
    *   Web server "Active Connections" scoreboard (e.g., Nginx Stub Status / Apache Scoreboard).
    *   Orphaned socket timers from `ss` / `netstat`.
    *   Time-to-First-Byte (TTFB) and Request Completion Time metrics.
*   **Outputs (Events):**
    *   `slow_loris_suspected`: `{ "source_ip": "192.168.1.100", "duration_sec": 120, "bytes_sent": 50, "state": "sending_headers" }`
*   **False-Positive Mitigation:**
    *   **Minimum Data Rate Check:** Only flag if transfer rate is below a realistic threshold (e.g., < 10 bytes/sec) for a sustained period.
    *   **Mobile Network Tolerance:** Higher timeouts for IPs identified as mobile carrier networks (high latency/jitter).

## 4. `l7_api_misuse_detector.py`

**Detection Logic Concept:**
Focuses on semantic API abuse: ID enumeration (scraping), method misuse (POST on GET-only endpoints), and auth failure spikes. It looks for logic violations rather than just speed.

*   **Inputs:**
    *   HTTP Response Codes (401 Unauthorized, 403 Forbidden, 404 Not Found).
    *   API Endpoint Patterns (e.g., `/user/1001`, `/user/1002`, `/user/1003`).
    *   Payload size variations.
*   **Outputs (Events):**
    *   `enumeration_attack`: `{ "target": "/api/users/{id}", "distinct_ids_requested": 500, "time_window": "60s" }`
    *   `credential_stuffing`: `{ "target": "/login", "failed_attempts": 20, "unique_usernames": 20 }`
*   **False-Positive Mitigation:**
    *   **Error Rate Ratio:** Trigger only if Error/Success ratio > X% (users make typos, bots generate streams of errors).
    *   **Auth Token Binding:** Correlate failures to specific API tokens, not just IPs (handles NAT/Proxy scenarios).
