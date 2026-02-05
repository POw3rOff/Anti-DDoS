# Distributed Anycast Anti-DDoS Architecture

## Overview
This architecture enables the `under_attack_ddos` system to operate across multiple geographically distributed Points of Presence (PoPs) using Anycast routing. It follows a "Hub-and-Spoke" model where Edge PoPs absorb attacks and a centralized Control Plane makes global decisions.

## Components

### `edge_agent/` (Runs on PoP)
- **`edge_daemon.py`**: The local brain of the PoP. Orchestrates local detection and enforcement.
- **`local_detector.py`**: Aggregates signals from local sensors (L3/L4/Game) and emits "Alerts" to the Core.
- **`xdp_controller.py`**: Manages the local eBPF/XDP maps for immediate packet dropping.

### `control_plane/` (Runs on Core)
- **`intent_sync.py`**: Handles the bidirectional synchronization of mitigation intents (Core -> Edge) and alerts (Edge -> Core).
- **`trust_model.py`**: Assigns scores to PoPs based on their signal quality. Prevents a compromised or buggy PoP from banning legit traffic globally.
- **`conflict_resolver.py`**: Resolves conflicting signals (e.g., PoP A says "Block", PoP B says "Allow").

### `routing/` (Runs on PoP)
- **`bgp_signaler.py`**: Interfaces with the BGP daemon (e.g., ExaBGP, Bird) to announce/withdraw routes based on PoP health.
- **`pop_health.py`**: Monitors local capacity (CPU, bandwidth). If the PoP is overwhelmed, it triggers a BGP withdrawal to shift traffic to other PoPs.

## Principles

1.  **Edge Autonomy**: Edge PoPs can block volumetric attacks (L3/L4) locally without waiting for Core instructions (Fail-Safe).
2.  **Core Authority**: Complex decisions (L7, Global Bans) are made by the Core and pushed to all Edges.
3.  **Trust-Based Consensus**: A single PoP cannot trigger a global ban unless it has a high Trust Score or multiple PoPs agree.
4.  **Graceful Degradation**: If the Core is unreachable, Edges fall back to aggressive local protection.

## Data Flow

1.  **Attack** -> Anycast -> **Edge PoP**.
2.  **Local Detector** identifies anomaly -> **XDP Controller** applies local temp block.
3.  **Edge Daemon** sends "Alert" to **Control Plane**.
4.  **Trust Model** validates alert -> **Conflict Resolver** confirms global policy.
5.  **Intent Sync** pushes "Global Block" to **All Edge PoPs**.
