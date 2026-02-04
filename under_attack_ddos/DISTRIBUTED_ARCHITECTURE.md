# Distributed Anti-DDoS Architecture (Multi-Node Design)

This document defines how the `under_attack_ddos` system scales horizontally from a single-node sensor to a distributed defense grid.

## 1. High-Level Architecture

We adopt a **Hub-and-Spoke (Federated)** model with autonomous edge capabilities.

### Roles
1.  **Edge Node (Data Plane):**
    *   Runs L3/L4/L7 Detectors + Mitigation Controller.
    *   Performs local mitigation immediately (autonomous).
    *   Sends events/stats to Core.
2.  **Core Node (Control Plane):**
    *   Runs Orchestrator + Intelligence Engine + Correlation.
    *   Aggregates risk scores from all Edges.
    *   Broadcasts global "UNDER ATTACK" state and shared blacklists.

### Communication
*   **Protocol:** gRPC or JSON-over-HTTPS (mTLS required).
*   **Discovery:** Static config list or Consul-based discovery.
*   **Security:** Mutual TLS (mTLS) for all inter-node traffic.

## 2. State Synchronization Strategy

### Global Mode (The "DEFCON" Level)
*   **Source of Truth:** Core Node.
*   **Propagation:** Push-based broadcast to Edges + Pull-based heartbeat from Edges.
*   **Conflict:** If Core is unreachable, Edge defaults to local decision (Safe Mode).

### Shared Intelligence (The "Blocklist")
*   **Distributed Set:** A Conflict-Free Replicated Data Type (CRDT) set for IP bans.
*   **Logic:**
    *   Edge A bans IP X locally.
    *   Edge A pushes "Ban IP X" event to Core.
    *   Core validates confidence -> Broadcasts "Ban IP X" to Edges B, C, D.

## 3. Event Aggregation

To prevent "Alert Floods" at the Core:

1.  **Edge Aggregation:** Edge nodes summarize events (e.g., "10k drops in 5s") before sending to Core.
2.  **Deduplication:** Core identifies if multiple edges report the *same* flow (e.g., multicast/broadcast attack) or *distinct* flows.
3.  **Correlation:**
    *   *Local:* Edge correlates L3+L7 for local IP.
    *   *Global:* Core correlates Subnet attacks across multiple Edges.

## 4. Operational Safety

### Split-Brain Handling
*   If Edge loses contact with Core:
    *   State: Switches to **Autonomous Mode**.
    *   Action: Continues mitigation based on local thresholds.
    *   Restriction: Cannot propagate bans to other nodes.

### Quorum
*   Global "UNDER ATTACK" mode requires >50% of Edges reporting high risk scores to trigger automatic cluster-wide mitigation (prevents one compromised sensor from sinking the fleet).

## 5. Implementation Phases

### Phase 1: Reporter Mode
*   Edge nodes send JSON stats to Core.
*   Core visualizes global traffic.
*   No distributed action.

### Phase 2: Central Command
*   Core can push "Manual Ban" directives to all Edges.
*   Core can toggle Global Mode manually.

### Phase 3: Automated Federation
*   Core automatically promotes local bans to global bans based on policy.
*   Full CRDT implementation for state syncing.

## 6. Message Bus (Conceptual)

We abstract the transport layer. Recommended stack:
*   **Transport:** NATS (lightweight, resilient) or Redis Pub/Sub.
*   **Topic Structure:**
    *   `uad.telemetry.{region}.{node_id}` (Stats)
    *   `uad.alerts.{node_id}` (High severity events)
    *   `uad.broadcast.control` (Global mode updates)
