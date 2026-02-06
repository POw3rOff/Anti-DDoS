
import os

# --- Paths ---
PROJECT_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
CONFIG_DIR = os.path.join(PROJECT_ROOT, "config")
LOGS_DIR = os.path.join(PROJECT_ROOT, "logs")
RUNTIME_DIR = os.path.join(PROJECT_ROOT, "runtime")
DATA_DIR = os.path.join(PROJECT_ROOT, "data")
DATA_CAPTURES_DIR = os.path.join(DATA_DIR, "captures")

# --- Files ---
STATE_FILE = os.path.join(RUNTIME_DIR, "global_state.json")
LOCK_FILE = os.path.join(RUNTIME_DIR, "OVERRIDE.lock")
THRESHOLDS_CONFIG = os.path.join(CONFIG_DIR, "thresholds.yaml")
MITIGATION_CONFIG = os.path.join(CONFIG_DIR, "mitigation.yaml")

# --- States ---
class SystemState:
    NORMAL = "NORMAL"
    MONITOR = "MONITOR"
    UNDER_ATTACK = "UNDER_ATTACK"
    ESCALATED = "ESCALATED"

# --- Layers ---
class Layer:
    L3 = "layer3"
    L4 = "layer4"
    L7 = "layer7"
    GAME = "layer_game"
    INTELLIGENCE = "intelligence"
    ORCHESTRATION = "orchestration"

# --- Services ---
SERVICES = [
    "uad-orchestrator",
    "uad-l3-analyzer",
    "uad-l4-analyzer",
    "uad-executor",
    "uad-exporter"
]
