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
import argparse
from datetime import datetime

# Check for Textual
try:
    from textual.app import App, ComposeResult
    from textual.containers import Container, Grid, VerticalScroll
    from textual.widgets import Header, Footer, Static, RichLog, Sparkline, Label
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
        elif new_mode in ["HIGH", "ESCALATED"]: lbl.classes = "high"
        elif new_mode in ["ELEVATED", "MONITOR"]: lbl.classes = "elevated"
        else: lbl.classes = "normal"

class CampaignPanel(Static):
    """Displays active campaign alerts."""

    def compose(self) -> ComposeResult:
        yield Label("Active Campaigns", classes="panel-title")
        yield RichLog(id="campaign-log", highlight=True, markup=True)

    def update_campaigns(self, campaigns):
        log = self.query_one(RichLog)
        log.clear()
        if not campaigns:
            log.write("[green]No active campaigns detected.[/green]")
        else:
            for c in campaigns:
                log.write(f"[bold red]⚠ {c}[/bold red]")

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
        yield Label("System Logs", classes="panel-title")
        yield RichLog(id="sys-log", highlight=True, markup=True)

    def write(self, text):
        self.query_one("#sys-log", RichLog).write(text)

# -----------------------------------------------------------------------------
# Main Application
# -----------------------------------------------------------------------------

class SOCDashboard(App):
    CSS = """
    Screen {
        layout: grid;
        grid-size: 3;
        grid-columns: 1fr 1fr 2fr;
        grid-rows: 1fr 3fr;
        background: ;
    }

    #header {
        column-span: 3;
        height: 3;
        dock: top;
    }

    StatePanel {
        column-span: 1;
        background: ;
        border: solid ;
        padding: 1;
    }

    CampaignPanel {
        column-span: 1;
        background: ;
        border: solid ;
        padding: 1;
    }

    #metrics-container {
        column-span: 1;
        row-span: 2;
        background: ;
        border: solid ;
        layout: vertical;
    }

    MetricSpark {
        padding: 1;
        height: 8;
    }

    LogPanel {
        column-span: 2;
        row-span: 1;
        border: solid ;
        background: -darken-1;
    }

    .panel-title {
        text-style: bold;
        background: ;
        color: ;
        width: 100%;
        text-align: center;
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
    }
    """

    def __init__(self, args):
        super().__init__()
        self.args = args
        self.state_file = "runtime/global_state.json"
        self.log_file = "logs/mitigation_events.json.log"
        self.log_offset = 0

    def compose(self) -> ComposeResult:
        yield Header(show_clock=True)
        yield StatePanel(id="state-panel")
        yield CampaignPanel(id="campaign-panel")

        with Container(id="metrics-container"):
            yield MetricSpark("Global Risk Score", "blue")
            yield MetricSpark("Active Alerts (Last Min)", "red")

        yield LogPanel(id="log-panel")
        yield Footer()

    def on_mount(self) -> None:
        self.title = "Under Attack DDoS - SOC Dashboard"
        self.set_interval(1.0, self.update_state)
        self.set_interval(0.5, self.tail_logs)

    @work(exclusive=True)
    async def update_state(self):
        if self.args.demo:
            await self.simulate_demo_state()
            return

        try:
            if os.path.exists(self.state_file):
                with open(self.state_file, 'r') as f:
                    state = json.load(f)

                # Update State Panel
                panel = self.query_one(StatePanel)
                score = state.get("grs_score", 0.0)
                panel.score = score
                panel.mode = state.get("mode", "UNKNOWN")

                # Update Campaign Panel
                camp_panel = self.query_one(CampaignPanel)
                camp_panel.update_campaigns(state.get("campaigns", []))

                # Update Sparkline with Score
                self.query(MetricSpark)[0].add_point(score)

        except Exception:
            pass

    @work(exclusive=True)
    async def tail_logs(self):
        if self.args.demo:
            await self.simulate_demo_logs()
            return

        try:
            if os.path.exists(self.log_file):
                with open(self.log_file, 'r') as f:
                    # Seek to last known position
                    if self.log_offset == 0: # First run, go to end
                        f.seek(0, 2)
                        self.log_offset = f.tell()
                    else:
                        f.seek(self.log_offset)

                    new_lines = f.readlines()
                    if new_lines:
                        self.log_offset = f.tell()
                        for line in new_lines:
                            try:
                                data = json.loads(line)
                                ts = data.get("timestamp", "")[11:19]
                                lvl = data.get("level", "INFO")
                                msg = data.get("message", "")
                                color = "green"
                                if lvl == "CRITICAL": color = "red"
                                elif lvl == "WARNING": color = "yellow"

                                fmt_line = f"[{ts}] [{color}]{lvl}[/{color}] {msg}"
                                self.query_one(LogPanel).write(fmt_line)
                            except:
                                self.query_one(LogPanel).write(line.strip())
        except Exception:
            pass

    # --- Demo Mode Logic ---
    async def simulate_demo_state(self):
        import random
        panel = self.query_one(StatePanel)
        camp_panel = self.query_one(CampaignPanel)

        # Random walk
        change = random.uniform(-5, 10)
        new_score = max(0, min(100, panel.score + change))
        panel.score = new_score

        if new_score > 90:
            panel.mode = "UNDER_ATTACK"
            camp_panel.update_campaigns(["Volumetric L3 Flood", "API Scraping"])
        elif new_score > 60:
            panel.mode = "HIGH"
            camp_panel.update_campaigns(["Potential Scan"])
        else:
            panel.mode = "NORMAL"
            camp_panel.update_campaigns([])

        self.query(MetricSpark)[0].add_point(new_score)
        self.query(MetricSpark)[1].add_point(random.randint(0, 5))

    async def simulate_demo_logs(self):
        import random
        if random.random() < 0.3:
            log_panel = self.query_one(LogPanel)
            ts = datetime.now().strftime("%H:%M:%S")
            msgs = [
                ("[green]INFO[/green]", "System Normal"),
                ("[yellow]WARNING[/yellow]", "Rate limit exceeded for IP 1.2.3.4"),
                ("[red]CRITICAL[/red]", "Campaign Detected: Multi-Vector Attack")
            ]
            lvl, msg = random.choice(msgs)
            log_panel.write(f"[{ts}] {lvl} {msg}")

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
