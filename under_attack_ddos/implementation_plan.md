[2026-02-06] STATUS UPDATE
	•	Reference: ML Intelligence Layer
	•	New Status: COMPLETED
	•	Notes: ML-based anomaly detection implemented and integrated.

[2026-02-06] STATUS UPDATE
	•	Reference: Phase 7: Orchestration & Observability
	•	New Status: IN_PROGRESS
	•	Notes: Starting implementation of Alert Manager and CLI tool.

# Phase 7: Orchestration & Observability Implementation Plan

## Goal
Centralize system management and alerting. This phase implements the `AlertManager` for notifications and the `uad` CLI tool for operational control.

## Proposed Changes

### Alert Manager
- **`alerts/alert_manager.py`**: A new component that subscribes to high-severity events and triggers external notifications (e.g., Log file, Slack webhook mock).
- **Core logic**: Deduplication of alerts and severity-based routing.

### CLI Tool (`uad`)
- **`uad.py`**: A unified CLI for managing the suite.
- **Commands**:
  - `status`: Show GRS, state, and active mitigations.
  - `start`/`stop`: Manage systemd services.
  - `logs`: Tail system logs with color coding.
  - `panic`: Force system into `ESCALATED` mode and block everything.

#### [NEW] [minecraft_monitor.py](file:///C:/Users/valet/Desktop/Anti-DDoS/under_attack_ddos/layer_game/minecraft/minecraft_monitor.py)
- Detects Handshake/Status ping floods.

#### [NEW] [fivem_monitor.py](file:///C:/Users/valet/Desktop/Anti-DDoS/under_attack_ddos/layer_game/fivem/fivem_monitor.py)
- Monitors CitizenFX heartbeats and Enet traffic.

#### [NEW] [source_monitor.py](file:///C:/Users/valet/Desktop/Anti-DDoS/under_attack_ddos/layer_game/source/source_monitor.py)
- Replaces CS:GO monitor; protects all Source Engine games (A2S Query floods).

#### [NEW] [samp_monitor.py](file:///C:/Users/valet/Desktop/Anti-DDoS/under_attack_ddos/layer_game/samp/samp_monitor.py)
- Detects Join floods and malformed RakNet packets.

#### [NEW] [mta_monitor.py](file:///C:/Users/valet/Desktop/Anti-DDoS/under_attack_ddos/layer_game/mta/mta_monitor.py)
- Protects against Enet-based sync floods.

#### [NEW] [ts3_monitor.py](file:///C:/Users/valet/Desktop/Anti-DDoS/under_attack_ddos/layer_game/ts3/ts3_monitor.py)
- Detects TeamSpeak 3 handshake floods and reflection attempts.

#### [NEW] [unreal_monitor.py](file:///C:/Users/valet/Desktop/Anti-DDoS/under_attack_ddos/layer_game/unreal/unreal_monitor.py)
- Initial support for Unreal Engine 4/5 (Ark, Palworld) protocol anomalies.

#### [MODIFY] [task.md](file:///C:/Users/valet/.gemini/antigravity\brain\ed79bed1-8c85-4fc5-8cba-8ebcf8b5440e/task.md)
- Add tasks for Minecraft, FiveM, and CS:GO monitors.

### Orchestrator Integration
- Update `Orchestrator` to emit events to the `AlertManager` when state transitions or critical mitigations occur.

## Verification Plan

### Automated Tests
- CLI command unit tests (mocking subprocess calls).
- Alert deduplication verification.

### Manual Verification
1. Run `uad status` and verify output.
2. Trigger an alert and check the alert log/mock output.

---

# Phase 8: eBPF/XDP High-Performance Detection implementation_plan.md

## Goal
Migrate volumetric detection to the Linux Kernel using XDP for high-performance packet filtering and telemetry, reducing CPU overhead during large attacks.

## Proposed Changes

### eBPF Component Enhancements
- **[MODIFY] [xdp_main.c](file:///C:/Users/valet/Desktop/Anti-DDoS/under_attack_ddos/ebpf/src/xdp_main.c)**: Ensure all protocol headers are correctly parsed and metrics are per-packet/per-byte accurate.
- **[MODIFY] [loader.py](file:///C:/Users/valet/Desktop/Anti-DDoS/under_attack_ddos/ebpf/loader.py)**: Implement a robust polling mechanism that can be imported by other Python components to read maps.

### Sensor Integration
- **[MODIFY] [ip_flood_analyzer.py](file:///C:/Users/valet/Desktop/Anti-DDoS/under_attack_ddos/layer3/ip_flood_analyzer.py)**: Add a flag `--use-ebpf` to switch from Scapy sniffing to reading `map_source_stats` from the BPF manager.
- **[MODIFY] [syn_flood_analyzer.py](file:///C:/Users/valet/Desktop/Anti-DDoS/under_attack_ddos/layer4/syn_flood_analyzer.py)**: Add support for reading `map_syn_stats` from BPF to detect SYN floods at line rate.

### Mitigation Integration
- **[MODIFY] [mitigation_executor.py](file:///C:/Users/valet/Desktop/Anti-DDoS/under_attack_ddos/mitigation/mitigation_executor.py)**: Update the block logic to also call `ebpf_loader.py --block <IP>` (or direct map manipulation) to ensure IPs are dropped at the NIC level.

## Verification Plan

### Automated Tests
- Verify that `xdp_main.c` compiles via `ebpf/loader.py --dry-run`.
- Benchmark CPU usage: Scapy-only vs eBPF-enabled sensors under high load.

### Manual Verification
1. Load the XDP program: `python ebpf/loader.py --load --interface eth0`.
2. Generate synthetic SYN flood traffic.
3. Verify `syn_flood_analyzer.py --use-ebpf` detects the flood and triggers a block directive.
4. Verify the IP is added to both `ipset` and the eBPF `map_blacklist`.

---

# Phase 9: ML Intelligence Maturity implementation_plan.md

## Goal
Transform the skeletal ML layer into a functional anomaly detection engine capable of identifying "low-and-slow" attacks and coordinated botnet behavior.

## Proposed Changes

### Feature Engineering
- **[MODIFY] [flow_features.py](file:///C:/Users/valet/Desktop/Anti-DDoS/under_attack_ddos/ml_intelligence/features/flow_features.py)**: Optimize windowed statistical calculations (entropy, variance, jitter) and ensure robustness against sparse data.

### Model Refinement
- **[MODIFY] [isolation_forest.py](file:///C:/Users/valet/Desktop/Anti-DDoS/under_attack_ddos/ml_intelligence/models/isolation_forest.py)**: Replace hardcoded rules with a dynamic thresholding mechanism (e.g., Z-score based or simplified isolation logic) to handle evolving traffic patterns.
- **[MODIFY] [spatial_features.py](file:///C:/Users/valet/Desktop/Anti-DDoS/under_attack_ddos/ml_intelligence/features/spatial_features.py)**: Implement basic IP proximity analysis to detect subnet-wide campaigns.

### System Integration
- **[MODIFY] [online_inference.py](file:///C:/Users/valet/Desktop/Anti-DDoS/under_attack_ddos/ml_intelligence/inference/online_inference.py)**: Refine the stream processing loop to correctly map sensor events to feature vectors and handle high-throughput event processing.
- **[MODIFY] [under_attack_orchestrator.py](file:///C:/Users/valet/Desktop/Anti-DDoS/under_attack_ddos/orchestration/under_attack_orchestrator.py)**: Implement a collector flag to pipe events into the ML inference engine.

## Verification Plan

### Automated Tests
- Unit tests for feature extraction accuracy.
- Validation of the "IsAnomaly" flag against synthetic botnet trace data.

### Manual Verification
1. Start the Orchestrator with ML support: `python orchestration/under_attack_orchestrator.py --ml-support`.
2. Inject a "fixed packet size" low-rate attack.
3. Verify that the ML Engine emits a `distributed_botnet_suspected` advisory.
4. Confirm that the Orchestrator increases the Global Risk Score (GRS) based on the ML advisory.
 Boris? No, Antigravity.
 Boris? No, Antigravity.
