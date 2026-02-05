# ML Intelligence Layer - Structure & Design

## Overview
The `ml_intelligence` layer introduces Machine Learning capabilities to the `under_attack_ddos` system. Its primary goal is to detect sophisticated, distributed, and low-and-slow attacks that evade static thresholds. It operates as an **Advisory System**, meaning it never issues block commands directly but instead feeds high-confidence signals to the Global Orchestrator.

## Core Responsibilities
1.  **Anomaly Detection**: Identify traffic patterns that deviate from the learned baseline (Isolation Forest).
2.  **Botnet Clustering**: Group seemingly unrelated IPs into coordinated attack clusters (HDBSCAN/DBSCAN logic).
3.  **Signal Fusion**: Combine weak signals from multiple PoPs into a strong global alert.
4.  **Advisory**: Emit `ml_advisory` events with confidence scores and explainable reasons.

## Components

### `features/`
Extracts numerical vectors from raw events.
- **`flow_features.py`**: Calculates PPS statistics, packet size entropy, and flow duration.
- **`spatial_features.py`**: Analyzes the geographic/network distribution of sources across PoPs.

### `models/`
Encapsulates ML algorithms.
- **`isolation_forest.py`**: Unsupervised anomaly detection. Learns "normal" behavior and flags outliers.
- **`ensemble.py`**: Aggregates outputs from multiple models to reduce false positives.

### `inference/`
Runtime execution.
- **`online_inference.py`**: Consumes the event stream, updates sliding windows, and queries models.

### `bridge/`
Integration.
- **`ml_to_orchestrator.py`**: Formats ML outputs into the standard JSON schema expected by the Global Orchestrator.

## Safety & Governance
- **No Autonomous Blocking**: ML output is a "Signal", not a "Command".
- **Explainability**: Every alert must include `contributing_features` (e.g., "High Entropy + PoP Synchronization").
- **Fall-back**: If ML components crash or latency exceeds limits, the system ignores ML advice (Fail-Open).

## Data Flow
1.  **Collectors** (L3/L4/Game) -> **Event Bus** -> **Online Inference**.
2.  **Feature Extractor** converts events -> `[f1, f2, f3...]` vector.
3.  **Ensemble Model** predicts -> `(is_anomaly, confidence)`.
4.  **Bridge** emits -> `{"event": "ml_advisory", "confidence": 0.85, ...}`.
5.  **Global Orchestrator** adjusts Risk Score based on Advisory.
