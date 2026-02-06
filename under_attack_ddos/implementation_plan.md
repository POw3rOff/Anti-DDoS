# Implementation Plan - Phase 7: Observability and Management

This plan outlines the implementation of the Alert Manager and the Global CLI Tool (Human Interface) for the `under_attack_ddos` system, completing Phase 7 of the roadmap.

## User Review Required

> [!IMPORTANT]
> - The Alert Manager will require Slack Webhook URLs, SMTP credentials, or PagerDuty API keys to be functional. These should be provided by the user in `config/observability.yaml`.
> - The CLI tool `uad` will require root privileges for some commands (e.g., `panic` mode which may interact with system firewalls).

## Proposed Changes

### Configuration
#### [NEW] [observability.yaml](file:///c:/Users/valet/Desktop/Anti-DDoS/under_attack_ddos/config/observability.yaml)
Create a new configuration file for alerting channels and templates.
#### [MODIFY] [orchestrator.yaml](file:///c:/Users/valet/Desktop/Anti-DDoS/under_attack_ddos/config/orchestrator.yaml)
Add a reference to the alerting configuration.

---

### Alert Manager Component
#### [NEW] [alert_manager.py](file:///c:/Users/valet/Desktop/Anti-DDoS/under_attack_ddos/observability/alert_manager.py)
A new module responsible for:
- Monitoring `runtime/global_state.json` or receiving signals from the Orchestrator.
- Sending notifications to Slack, Email, and PagerDuty based on severity and mode changes.
- Rate limiting alerts to avoid fatigue (e.g., maximum one alert per mode change).

---

### Orchestration Integration
#### [MODIFY] [under_attack_orchestrator.py](file:///c:/Users/valet/Desktop/Anti-DDoS/under_attack_ddos/orchestration/under_attack_orchestrator.py)
Enhance the orchestrator to trigger the Alert Manager during `state_change` events.

---

### Management Interface (CLI)
#### [NEW] [uad.py](file:///c:/Users/valet/Desktop/Anti-DDoS/under_attack_ddos/uad.py)
A unified CLI tool for human operators:
- `uad status`: Shows current GRS and Mode (TUI-lite or text).
- `uad logs`: Tails the most relevant logs.
- `uad panic`: Immediately triggers `UNDER_ATTACK` mode and blocks non-VIP traffic.
- `uad health`: Checks if all detection and orchestration services are running.

## Verification Plan

### Automated Tests
- **Unit Tests for Alert Manager**: Create `test_suite/test_alert_manager.py` using `unittest.mock` to verify Slack and SMTP logic without sending real traffic.
  ```bash
  python -m unittest test_suite/test_alert_manager.py
  ```
- **Integration Test**: Create a simulation script that triggers a mode change in the Orchestrator and verifies that a mock Alert Manager receives the event.

### Manual Verification
- Run `python uad.py status` to check system visibility.
- Run `python uad.py panic` and verify `runtime/global_state.json` reflects the change.
- Verify log output of `alert_manager.py` when a simulated attack occurs.
