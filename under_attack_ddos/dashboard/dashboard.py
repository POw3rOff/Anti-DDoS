#!/usr/bin/env python3
"""
SOC Dashboard (TUI)
Part of 'under_attack_ddos' Defense System.

Responsibility: Real-time visualization of system state, metrics, and logs.
Safe Mode: Read-only by default.
"""

import sys
import os
import json
import time
import asyncio
import logging
import argparse
from datetime import datetime

# Check for Textual
try:
    from textual.app import App, ComposeResult
    from textual.containers import Container, Grid, VerticalScroll
    from textual.widgets import Header, Footer, Static, RichLog, Sparkline, Label, Button
    from textual.reactive import reactive
    from textual import work
except ImportError:
    print("CRITICAL: Missing 'textual' library.", file=sys.stderr)
    print("Please install: pip install textual", file=sys.stderr)
    sys.exit(1)

# -----------------------------------------------------------------------------
# Constants
# -----------------------------------------------------------------------------
SCRIPT_NAME = "soc_dashboard"
CONFIG_PATH = "config/dashboard.yaml"

# -----------------------------------------------------------------------------
# Components
# -----------------------------------------------------------------------------

class StatePanel(Static):
    """Displays the Global Risk Score and Operational Mode."""

    mode = reactive("UNKNOWN")
    score = reactive(0.0)

    def compose(self) -> ComposeResult:
        yield Label("Global Risk Score", id="grs-label")
        yield Label("0", id="grs-value")
        yield Label("Operational Mode", id="mode-label")
        yield Label("INITIALIZING", id="mode-value")

    def watch_score(self, new_score: float) -> None:
        lbl = self.query_one("#grs-value", Label)
        lbl.update(f"{new_score:.1f}")

        # Color coding
        if new_score >= 90: lbl.classes = "critical"
        elif new_score >= 60: lbl.classes = "high"
        elif new_score >= 30: lbl.classes = "elevated"
        else: lbl.classes = "normal"

    def watch_mode(self, new_mode: str) -> None:
        lbl = self.query_one("#mode-value", Label)
        lbl.update(new_mode)

        # Color coding
        if new_mode == "UNDER_ATTACK": lbl.classes = "critical blink"
        elif new_mode == "HIGH": lbl.classes = "high"
        elif new_mode == "ELEVATED": lbl.classes = "elevated"
        else: lbl.classes = "normal"

class MetricSpark(Static):
    """Real-time sparkline for a specific metric."""
    def __init__(self, title, color="green"):
        super().__init__()
        self.title_text = title
        self.spark_color = color
        self.data = [0] * 60

    def compose(self) -> ComposeResult:
        yield Label(self.title_text)
        yield Sparkline(self.data, summary_function=max, color=self.spark_color)

    def add_point(self, value):
        self.data.pop(0)
        self.data.append(value)
        self.query_one(Sparkline).data = self.data

class LogPanel(VerticalScroll):
    """Auto-scrolling log viewer."""
    def compose(self) -> ComposeResult:
        yield RichLog(highlight=True, markup=True)

    def write(self, text):
        self.query_one(RichLog).write(text)

# -----------------------------------------------------------------------------
# Main Application
# -----------------------------------------------------------------------------

class SOCDashboard(App):
    CSS = """
    Screen {
        layout: grid;
        grid-size: 2;
        grid-columns: 1fr 2fr;
        grid-rows: 1fr 2fr;
    }

    #header {
        column-span: 2;
        height: 3;
        dock: top;
    }

    StatePanel {
        background: $panel;
        border: solid $accent;
        padding: 1;
        row-span: 1;
    }

    #metrics-grid {
        layout: grid;
        grid-size: 2;
        border: solid $accent;
        background: $panel;
    }

    MetricSpark {
        padding: 1;
    }

    LogPanel {
        column-span: 2;
        border: solid $accent;
        background: $surface;
        height: 100%;
    }

    .normal { color: green; }
    .elevated { color: yellow; }
    .high { color: orange; }
    .critical { color: red; text-style: bold; }
    .blink { text-style: blink; }

    #grs-value {
        text-align: center;
        width: 100%;
        text-style: bold;
        font-size: 2; # Textual doesn't strictly support font-size like CSS but this is placeholder
    }
    """

    def __init__(self, args):
        super().__init__()
        self.args = args
        self.state_file = "runtime/global_state.json"
        self.log_file = "logs/system.json.log"

    def compose(self) -> ComposeResult:
        yield Header(show_clock=True)
        yield StatePanel(id="state-panel")

        with Container(id="metrics-grid"):
            yield MetricSpark("L3 Bandwidth (Mbps)", "blue")
            yield MetricSpark("L4 SYN Rate", "yellow")
            yield MetricSpark("L7 Request Rate", "green")
            yield MetricSpark("Active Bans", "red")

        yield LogPanel(id="log-panel")
        yield Footer()

    def on_mount(self) -> None:
        self.title = "Under Attack DDoS - SOC Dashboard"
        self.set_interval(1.0, self.update_state)
        self.set_interval(0.5, self.tail_logs)

        # Start file watchers
        if not self.args.demo:
            self.ensure_files()

    def ensure_files(self):
        # Create dummy files if missing to prevent crash
        if not os.path.exists(self.state_file):
            pass # Expect Orchestrator to create
        if not os.path.exists(self.log_file):
            pass

    @work(exclusive=True)
    async def update_state(self):
        if self.args.demo:
            await self.simulate_demo_state()
            return

        try:
            if os.path.exists(self.state_file):
                with open(self.state_file, 'r') as f:
                    state = json.load(f)

                panel = self.query_one(StatePanel)
                panel.score = state.get("grs_score", 0.0)
                panel.mode = state.get("mode", "UNKNOWN")
        except Exception:
            pass

    @work(exclusive=True)
    async def tail_logs(self):
        if self.args.demo:
            await self.simulate_demo_logs()
            return

        # Real implementation would use seek/tell.
        # For simplicity in this TUI prototype, we read last N lines.
        try:
            if os.path.exists(self.log_file):
                # Efficiently read last line (placeholder logic)
                with open(self.log_file, 'r') as f:
                    lines = f.readlines()
                    last_lines = lines[-5:]
                    for line in last_lines:
                        # Dedup logic would go here
                        self.query_one(LogPanel).write(line.strip())
        except Exception:
            pass

    # --- Demo Mode Logic ---
    async def simulate_demo_state(self):
        import random
        panel = self.query_one(StatePanel)

        # Random walk
        change = random.uniform(-5, 10)
        new_score = max(0, min(100, panel.score + change))
        panel.score = new_score

        if new_score > 90: panel.mode = "UNDER_ATTACK"
        elif new_score > 60: panel.mode = "HIGH"
        elif new_score > 30: panel.mode = "ELEVATED"
        else: panel.mode = "NORMAL"

        # Update metrics
        sparks = self.query(MetricSpark)
        for spark in sparks:
            spark.add_point(random.randint(10, 100))

    async def simulate_demo_logs(self):
        import random
        if random.random() < 0.3:
            log_panel = self.query_one(LogPanel)
            layers = ["L3", "L4", "L7", "ORCH"]
            msgs = ["Threshold exceeded", "New IP banned", "Analysis complete", "Heartbeat"]

            ts = datetime.now().strftime("%H:%M:%S")
            msg = f"[{ts}] [INFO] [{random.choice(layers)}] {random.choice(msgs)}"
            log_panel.write(msg)

# -----------------------------------------------------------------------------
# Launcher
# -----------------------------------------------------------------------------
def main():
    parser = argparse.ArgumentParser(description="SOC Dashboard")
    parser.add_argument("--config", default=CONFIG_PATH, help="Path to config")
    parser.add_argument("--demo", action="store_true", help="Run with mock data")
    args = parser.parse_args()

    app = SOCDashboard(args)
    app.run()

if __name__ == "__main__":
    main()
