# Layer G - Game Protocol Defense Structure

This document defines the architecture for the "Layer G" (Game) defense module within the `under_attack_ddos` system. This layer focuses on application-specific protocols for game servers, starting with Metin2.

## 1. Directory Tree

```text
Anti-DDoS/
└─ under_attack_ddos/
   └─ layer_game/              # Root of Layer G
      ├── STRUCTURE.md         # This file
      ├── common/              # Shared logic for all game parsers
      │   ├── __init__.py
      │   └── game_protocol_parser.py # Abstract base class for protocol parsers
      └── metin2/              # Plugin for Metin2
          ├── __init__.py
          ├── config.yaml      # Game-specific thresholds (e.g., login rate)
          ├── metin2_login_monitor.py    # Detects authentication floods
          └── metin2_protocol_anomaly.py # Detects malformed/out-of-order packets
```

## 2. File Responsibilities

### Common
*   **`common/game_protocol_parser.py`**:
    *   Defines the interface for all game plugins.
    *   Provides utility functions for hex dumping, byte stream buffering, and common socket operations.
    *   Ensures all plugins emit JSON events in the standard system format.

### Metin2 Plugin
*   **`metin2/config.yaml`**:
    *   Configuration file defining thresholds for login attempts per second, maximum packet size, and allowed protocol versions.
    *   Example: `max_login_pps: 5`, `strict_handshake: true`.

*   **`metin2/metin2_login_monitor.py`**:
    *   **Responsibility:** Monitors the specific handshake sequence used by the Metin2 client/server.
    *   **Logic:** Tracks the rate of `AUTH_LOGIN` packets. If a source IP sends excessive login requests without completing the sequence, it triggers a `game_auth_flood` event.
    *   **Input:** Live packet capture (via Scapy or similar) filtered on the game port (default 11002/13000).

*   **`metin2/metin2_protocol_anomaly.py`**:
    *   **Responsibility:** Deep packet inspection (DPI) for protocol validity.
    *   **Logic:** Validates that packet headers match the expected Metin2 magic bytes and length fields. Detects fuzzing attacks or "crashers" sending garbage data.
    *   **Output:** Emits `game_protocol_violation` events.

## 3. Architecture Rules

1.  **Plugin-Based:** Each game gets its own directory. No game-specific code in `common/`.
2.  **Decoupled:** Scripts do **not** import game server binaries or read game database files directly. They operate solely on network traffic (OOB - Out of Band) or logs.
3.  **Event-Driven:** Scripts must emit JSON events to STDOUT (piped to Orchestrator) or to `runtime/events/`.
    *   *Format:* `{"layer": "game", "game": "metin2", "event": "auth_flood", "src_ip": "...", "severity": "HIGH"}`
4.  **Safe Mode:** All scripts must support `--dry-run` and default to **passive monitoring**.

## 4. Expansion Plan

To add a new game (e.g., Rust):
1.  Create `layer_game/rust/`.
2.  Implement `rust_rcon_monitor.py` (inheriting from `game_protocol_parser.py`).
3.  Add `rust/config.yaml`.
