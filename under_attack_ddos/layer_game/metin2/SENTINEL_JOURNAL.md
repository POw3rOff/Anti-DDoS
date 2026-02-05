## 2026-02-05 - Grace Period Bypass
**Pattern:** Session monitoring bypass via frequent reconnections.
**Learning:** The `grace_period` (intended to allow handshake bursts) was implemented as a complete exemption from PPS checks. Attackers could flood packets by resetting the connection every 1.9 seconds, never triggering the >2s check.
**Prevention:** Always implement bounded checks for exemptions. Added `max_initial_pps` to enforce a ceiling even during grace periods.
