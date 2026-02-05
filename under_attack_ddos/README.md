# Under Attack DDoS Defense System

## 1. Vision & Architecture
A modular, distributed Anti-DDoS defense grid designed for Linux servers. It employs a Hub-and-Spoke architecture where autonomous Edge Nodes handle detection and local mitigation, while a central Core Node manages global state, intelligence, and orchestration.

**Core Philosophy:**
- **Fail-Open:** Never block legitimate traffic if a component crashes.
- **Layered Defense:** Specialized modules for L3 (Network), L4 (Transport), L7 (Application), and Game Protocols.
- **Intelligence-Driven:** Decisions based on a Global Risk Score (GRS) rather than static thresholds.

## 2. Directory Structure & Modules

- **`/layer3`**: Network volumetric detection.
  - `ip_flood_analyzer.py`: Detects packet floods (UDP/ICMP).
- **`/layer4`**: Transport state monitoring.
  - `syn_flood_analyzer.py`: Detects SYN floods and state exhaustion.
- **`/layer7`**: Application behavior analysis.
  - (Planned) Request rate analysis and log parsing.
- **`/layer_game`**: Game-protocol specific defense (Plugin system).
  - Currently supports: `metin2`.
- **`/orchestration`**: The central nervous system.
  - `under_attack_orchestrator.py`: Manages global state and coordinates modules.
  - `under_attack_mode.py`: CLI for manual mode control.
- **`/mitigation`**: Enforcement agents.
  - `mitigation_controller.py`: Applies rules (iptables/ipset) based on directives.
- **`/config`**: YAML-based configuration.
- **`/runtime`**: State files, sockets, and PIDs.

## 3. Operational Modes

The system operates in four hysteresis-damped modes based on the Global Risk Score (0-100):

| Mode | GRS | Description |
|---|---|---|
| **NORMAL** | 0-29 | Passive monitoring. Zero mitigation. |
| **ELEVATED** | 30-59 | Active sampling, increased logging. |
| **HIGH** | 60-89 | Targeted blocking, strict rate limits. |
| **UNDER_ATTACK** | 90+ | Emergency defense. Drop non-essential traffic. |

## 4. Documentation Index

For detailed design and implementation guides, refer to:

- **Architecture:** [Distributed Architecture](DISTRIBUTED_ARCHITECTURE.md)
- **Roadmap:** [Implementation Roadmap](IMPLEMENTATION_ROADMAP.md)
- **Deployment:**
  - [Hardened Deployment Guide](installation_and_setup/HARDENED_DEPLOYMENT.md)
  - [Production Hardening](installation_and_setup/PRODUCTION_HARDENING.md)
- **Layer Designs:**
  - [Layer 3 Design](layer3/DESIGN.md)
  - [Layer 4 Design](layer4/DESIGN.md)
  - [Layer 7 Design](layer7/DESIGN.md)
  - [Game Layer Structure](layer_game/STRUCTURE.md)
  - [eBPF Architecture](ebpf/ARCHITECTURE.md)
- **Core Systems:**
  - [Orchestration Design](orchestration/DESIGN.md)
  - [Intelligence Engine](intelligence/DESIGN.md)
  - [Mitigation Playbook](mitigation/PLAYBOOK.md)

## 5. Quick Start

### Prerequisites
- Python 3.9+
- Root privileges (for specific monitors)
- `iptables`, `ipset`, `tcpdump`

### Installation
1. Clone the repository to `/opt/under_attack_ddos`.
2. Install dependencies: `pip install -r requirements.txt`.
3. Configure `config/*.yaml` files.

### Running the Orchestrator
```bash
python3 orchestration/under_attack_orchestrator.py --config config/orchestrator.yaml --daemon
```

### Manual Control
```bash
# Check status
python3 orchestration/under_attack_mode.py status

# Force specific mode
python3 orchestration/under_attack_mode.py force UNDER_ATTACK
```

## 6. Known Inconsistencies & Notes

> **Note to Developers:** This codebase is currently in active development. Please be aware of the following discrepancies between documentation and implementation:

- **Installation Path:** Documentation may refer to `/opt/uad`. The canonical path is `/opt/under_attack_ddos`.
- **Script Names:**
  - Docs referencing `l3_bandwidth_monitor.py` -> Use `layer3/ip_flood_analyzer.py`.
  - Docs referencing `orchestrator.py` -> Use `orchestration/under_attack_orchestrator.py`.
- **L3 Detection:** While documentation mentions kernel counter reading, the current implementation (`ip_flood_analyzer.py`) utilizes Scapy for granular packet analysis.
