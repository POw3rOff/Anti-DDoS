# Under Attack DDoS - Game Layer Integration Guide

This guide explains how to add support for a new game to the `layer_game` module.

## 1. Directory Structure

Each game must have its own directory under `layer_game/`:

```text
layer_game/
├── <game_name>/
│   ├── __init__.py
│   ├── config.yaml          # Game-specific thresholds
│   └── <game_name>_monitor.py # Main detection script
```

## 2. Using the Boilerplate

1.  Copy `layer_game/template/monitor_boilerplate.py` to your new directory.
2.  Rename it to something descriptive (e.g., `minecraft_monitor.py`).
3.  Update the `GAME_NAME` and `SCRIPT_NAME` constants.

## 3. Implementation Requirements

Your monitor class MUST:
- Inherit from `common.game_protocol_parser.GameProtocolParser`.
- Implement the `run()` method (usually using Scapy's `sniff()`).
- Implement the `packet_callback()` to analyze traffic.
- Call `self.emit_event()` when an anomaly is detected.

### Standard Severity Levels:
- **LOW**: Minor protocol violations (e.g., malformed packets with no impact).
- **MEDIUM**: Suspicious behavior (e.g., abnormally high packet rate).
- **HIGH**: Confirmed attack (e.g., brute-force attack or known crash exploit).

## 4. Standard Event Schema

The `emit_event` method automatically formats the JSON output required by the Orchestrator:

```json
{
  "timestamp": "2026-02-06T...",
  "layer": "game",
  "game": "rust",
  "event": "rcon_brute_force",
  "src_ip": "1.2.3.4",
  "severity": "HIGH",
  "data": {
    "login_pps": 5.2,
    "threshold": 1.0,
    "status": "active"
  }
}
```

## 5. Integration with Orchestrator

The Orchestrator automatically ingests events from STDOUT. When running your monitor as a service, ensure its output is piped to the central orchestrator ingestor.

```bash
# Example
python layer_game/rust/rust_rcon_monitor.py | python orchestration/under_attack_orchestrator.py
```
