# under_attack_ddos

**under_attack_ddos** is a modular, scalable, defensive system designed to detect and mitigate attacks across multiple network layers. It employs a distributed architecture with a central orchestrator, cross-layer correlation, and specific game protocol protections.

# Cyber Gamers Linux Security Suite

This project is organized into modular components, each responsible for specific layers of defense or system management:

- **`orchestration/`**: The core of the system. Contains `under_attack_orchestrator.py`, which manages the system state (NORMAL, MONITOR, UNDER_ATTACK, ESCALATED) based on a Global Risk Score (GRS).
- **`layer3/`**: Network layer defenses. Includes `ip_flood_analyzer.py`, `l3_spoofing_detector.py` (for Bogons/Martians), and bandwidth monitoring to handle volumetric attacks.
- **`layer4/`**: Transport layer defenses. Focuses on UDP flood monitoring (`l4_udp_flood_monitor.py`) and SYN flood analysis.
- **`layer7/`**: Application layer defenses. Analyzes request rates (`l7_request_rate_analyzer.py`) to mitigate HTTP/application floods.
- **`layer_game/`**: Game-aware defense layer. Includes specific protocol parsers and monitors for games (e.g., Metin2, Rust) and a generic game correlation engine.
- **`ml_intelligence/`**: Machine Learning layer. Contains anomaly detection models (`isolation_forest`, `ensemble`), feature extraction (`flow_features`), and bridges to the orchestrator.
- **`correlation/`**: Cross-layer correlation engine. Aggregates events from all layers to identify complex attack campaigns.
- **`mitigation/`**: Active response module. Includes `mitigation_controller.py` for executing defense playbooks.
- **`observability/`**: Monitoring tools. Includes `attack_timeline.py` for tracking attack history.
- **`dashboard/`**: CLI-based dashboard (`dashboard.py`) for real-time system monitoring.
- **`config/`**: Centralized configuration files (YAML) for all modules.
- **`test_suite/`**: Functional tests and chaos simulators (`chaos_ddos_simulator.py`).
- **`web_security/`**: Integration designs for proxy protection.
- **`ebpf/`**: Architectural designs for eBPF-based high-performance filtering.
- **`intelligence/`**: System design documentation for intelligence modules.

## Core Architecture

The system operates on a **Hub-and-Spoke** model where independent detection modules (layers) emit JSON events to a central **Orchestrator**.

### Orchestration & Global Risk Score
The `Orchestrator` ingests events, calculates a **Global Risk Score (GRS)**, and transitions the system between states:
- **NORMAL**: Routine monitoring.
- **MONITOR**: Elevated scrutiny.
- **UNDER_ATTACK**: Active mitigation engaged.
- **ESCALATED**: Maximum defense posture.

### Game Layer
Unlike generic solutions, `under_attack_ddos` includes a dedicated `layer_game` that understands specific game protocols (e.g., Metin2 login handshakes), allowing for precise anomaly detection without affecting legitimate players.

### ML Intelligence
The `ml_intelligence` module provides advanced anomaly detection using isolation forests and ensemble models to identify low-and-slow attacks that static thresholds might miss.

## 🚀 Guia Rápido (Quick Start)

The system is designed to be run as a collection of services. The entry point for the control plane is the Orchestrator:

```bash
python3 under_attack_ddos/orchestration/under_attack_orchestrator.py --config under_attack_ddos/config/orchestrator.yaml
```

Detectors can be run independently or piped into the orchestrator:

```bash
# Example: Running the L3 Flood Analyzer
python3 under_attack_ddos/layer3/ip_flood_analyzer.py

# Example: Running the L3 Spoofing Detector
python3 under_attack_ddos/layer3/l3_spoofing_detector.py
```

## Configuration

All configuration is managed in `config/`. Key files include:
- `orchestrator.yaml`: Global settings and state thresholds.
- `thresholds.yaml`: Detection limits for various layers.
- `mitigation.yaml`: Rules for active response.

## Development

- **Tests**: Run the test suite via `test_suite/`.
- **Roadmap**: See `IMPLEMENTATION_ROADMAP.md` and `PHASED_IMPLEMENTATION_ROADMAP.md` for project status.
