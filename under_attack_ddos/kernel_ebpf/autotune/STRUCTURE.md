# eBPF Auto-Tuning Layer

## Overview
The Autotune layer dynamically adjusts eBPF/XDP thresholds based on real-time feedback from the Global Orchestrator. It acts as a control loop to optimize the trade-off between sensitivity and false positives without requiring BPF program reloads.

## Components

### `policy_model.py`
Determines *what* to change based on attack signals.
- Inputs: Current Load, Attack Confidence, False Positive Rate (estimated).
- Outputs: Target Thresholds (PPS, Burst).
- Logic:
  - **Attack Surge**: Decrease thresholds to catch more traffic (sensitivity ++).
  - **High Load / FP**: Increase thresholds to reduce noise (specificity ++).
  - **Cooldown**: Gradually reset to baseline.

### `safety_guard.py`
Ensures changes are safe.
- Enforces hard min/max bounds for all parameters.
- Prevents oscillation (hysteresis).
- Provides "Emergency Reset" functionality.

### `threshold_controller.py`
The Actuator.
- Writes values to the pinned BPF `config_map`.
- Interfaces with the kernel via `bpftool` or direct map access.

### `orchestrator/feedback_emitter.py`
The Sensor/Driver.
- Integrated into the Global Orchestrator.
- Calculates the "Stress Score" of the system.
- Emits tuning directives to the Controller.

## Data Flow
1. Orchestrator detects high CPU or packet loss -> Emits "High Stress" signal.
2. `feedback_emitter` suggests increasing UDP drop threshold to shed load.
3. `safety_guard` validates the new threshold (e.g., ensures it's not too high to be useless).
4. `threshold_controller` writes the new value to `config_map` index 2.
5. `xdp_udp_guard` immediately uses the new threshold for the next packet.
