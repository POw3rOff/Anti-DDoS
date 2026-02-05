# Enforcement Layer

This directory contains the "Actuators" of the Anti-DDoS system. These scripts execute the decisions made by the Global Orchestrator.

## Responsibility
*   **Execute:** Apply mitigation rules (iptables, tc, nginx).
*   **Track:** Manage the lifecycle (TTL) of active rules.
*   **Revert:** Automatically clean up expired rules.

## Architecture
*   **Dispatcher:** Reads JSON commands from `runtime/enforcement/` and routes them to the correct module.
*   **Modules:** Independent scripts for specific domains (Firewall, Traffic Control, App, Game).
*   **Common:** Shared logic for state tracking and base action definitions.

## Rules
1.  **Idempotency:** Calling `--apply` multiple times for the same target must be safe.
2.  **Reversibility:** Every action must have a corresponding `--revert`.
3.  **No Decisions:** These scripts do NOT decide *who* to block, only *how*.
