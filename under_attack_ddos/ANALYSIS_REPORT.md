
# Project Analysis Report: Anti-DDoS System

## 1. Executive Summary
The project has a robust, modular architecture with clear separation of duties (Detection, Orchestration, Mitigation). Recent hardening phases (e16-26) have significantly improved capabilities. However, minor inconsistencies and one critical configuration error were detected.

## 2. Critical Issues (Must Fix)
1.  **Duplicate Key in `config/thresholds.yaml`**:
    -   The `layer4` key is defined twice (Lines 19 and 39). This causes the parser to overwrite the first block (basic thresholds) with the second block (hardening settings), effectively disabling basic L4 detection thresholds.
    -   **Fix**: Merge the two `layer4` blocks.

2.  **State Enum Mismatch**:
    -   `config/mitigation.yaml` defines states as `normal`, `defensive`, `high_alert`.
    -   `orchestration/orchestrator.py` uses `NORMAL`, `MONITOR`, `UNDER_ATTACK`, `ESCALATED`.
    -   **Risk**: If `mitigation.py` relies on this config for state transitions, it may fail or behave unpredictably.

## 3. Architecture & Code Quality
### Strengths
-   **Modularity**: Excellent separation between L3/L4/L7 and Game layers.
-   **Abstraction**: `GameProtocolParser` (ABC) ensures consistency across game monitors.
-   **Testing**: `test_suite/` is comprehensive (18 tests covering most features).
-   **Simulation**: Windows-compatible simulation for eBPF and Nginx is a huge plus for development speed.

### Weaknesses / Technical Debt
-   **Hardcoded Values**:
    -   `l7_request_rate_analyzer.py`: Static file extensions (`.css`, `.js`) are hardcoded.
    -   `uad.py`: Path to logs and state file are hardcoded values.
-   **Logging Inconsistency**:
    -   Some modules configure `logging` to stderr.
    -   Others use `sys.stdout` for IPC (Events) and `logging` for debug.
    -   **Recommendation**: Standardize on a `Logger` class that handles both structured JSON (Stdout) and human logs (Stderr/File).
-   **Documentation Scatter**:
    -   Docs are split between Root (`README.md`, `task.md`) and subfolders (`web_security/PROXY_INTEGRATION_DESIGN.md`).
    -   **Recommendation**: Centralize `docs/` folder.

## 4. Layer-Specific Analysis

### Layer 7 & Web Security
-   **Phase 25/26 Integration**: The Proxy Adapter and Challenge Logic are well implemented.
-   **Nginx Templates**: `nginx_format.conf` and `challenge_template.conf` are clean.

### Game Layer
-   **Structure**: Clean sub-folder structure per game.
-   **Logic**: `game_correlation_engine.py` uses a solid sliding window approach.
-   **Coverage**: Need to ensure `detectors` for all 13 folders exist. (Checked `metin2` and `common` only).

### Orchestrator
-   **Logic**: Central brain is complex but readable.
-   **eBPF**: Loader handles Windows simulation gracefully.

## 5. Recommendations (Next Steps)

### Immediate Stabilization (Phase 27)
1.  **Fix Config**: Merge `layer4` in `thresholds.yaml`.
2.  **Align States**: Update `mitigation.yaml` to match Orchestrator enums.
3.  **Requirements**: Add `fastapi` and `uvicorn` to `requirements.txt`.

### Future Improvements
-   **Centralized Constants**: Create `config/consts.py`.
-   **Unified Logging**: Create `common/logger.py`.
-   **Docs Consolidation**: Move non-essential `.md` files to `docs/`.
