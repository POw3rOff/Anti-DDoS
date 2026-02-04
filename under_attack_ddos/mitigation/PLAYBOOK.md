# Mitigation Playbook: Progressive Defense Strategy

This document defines the layered response strategy for the `under_attack_ddos` system. Mitigation is applied in stages to minimize collateral damage to legitimate users.

## Stage 0: Observation (The Baseline)

*   **Mode:** `NORMAL`
*   **Trigger:** Default state. GRS < 30.
*   **Actions:**
    *   **L3/L4:** Passive monitoring only (update stats).
    *   **L7:** Log request headers.
    *   **Mitigation:** NONE.
*   **Rollback:** N/A.

## Stage 1: Soft Throttling (The Filter)

*   **Mode:** `ELEVATED`
*   **Trigger:** GRS 30-59 (e.g., unusual traffic spike, minor anomaly).
*   **Actions:**
    *   **L7:** Enable "JS Challenge" (interstitial page) for non-whitelisted IPs.
    *   **L4:** Enforce stricter SYN flood protection (SYN Cookies enabled).
    *   **Rate Limits:** Reduce burst allowance for `/login` and `/search` by 50%.
*   **Rollback:** Return to Stage 0 if GRS < 30 for 5 minutes.

## Stage 2: Aggressive Rate Limiting (The Shield)

*   **Mode:** `HIGH`
*   **Trigger:** GRS 60-89 (e.g., confirmed volumetric attack or credential stuffing).
*   **Actions:**
    *   **L3:** Drop fragments and invalid packets immediately.
    *   **L4:** Aggressive Connection Rate Limiting (e.g., max 5 new conn/s per IP).
    *   **L7:** Enforce CAPTCHA for all sessions not holding a valid high-trust cookie.
    *   **Geo-Fencing:** Block traffic from high-risk countries (configurable).
*   **Rollback:** Return to Stage 1 if GRS < 60 for 5 minutes.

## Stage 3: Blocking & Isolation (The Bunker)

*   **Mode:** `UNDER ATTACK`
*   **Trigger:** GRS > 90 (System saturation imminent).
*   **Actions:**
    *   **L3:** White-list only (VIPs, known good subnets). Drop all UDP (except DNS if needed).
    *   **L7:** Serve static "Under Maintenance" page to general public.
    *   **Circuit Breakers:** Disable heavy search/report APIs completely.
    *   **Aggressive Ban:** Ban any IP triggering *any* anomaly for 24 hours.
*   **Rollback:** Manual intervention preferred, or auto-downgrade to Stage 2 after 15 minutes of stability.

## Universal Rules
1.  **Dry-Run Support:** All stages must support a flag to *log* the action without enforcing it.
2.  **Fail-Open:** If a mitigation script crashes, it must clean up its iptables rules/bans to avoid permanent lockout.
3.  **Whitelist Supremacy:** IPs in `config/whitelist.yaml` are EXEMPT from all stages (except maybe Stage 3 limits if they are compromised).
