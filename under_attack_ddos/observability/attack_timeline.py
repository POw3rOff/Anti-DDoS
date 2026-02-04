#!/usr/bin/env python3
"""
Attack Timeline Generator
Part of 'under_attack_ddos' Defense System.

Responsibility: Reconstructs incident timelines from dispersed system logs.
"""

import sys
import os
import json
import logging
import argparse
from datetime import datetime, timezone

# -----------------------------------------------------------------------------
# Identity & Constants
# -----------------------------------------------------------------------------
SCRIPT_NAME = "attack_timeline"
LAYER = "observability"
RESPONSIBILITY = "Forensic timeline reconstruction"

# -----------------------------------------------------------------------------
# Classes
# -----------------------------------------------------------------------------

class TimelineBuilder:
    def __init__(self, log_dir, time_range):
        self.log_dir = log_dir
        self.start_dt, self.end_dt = time_range
        self.events = []

    def load_logs(self):
        """Scans log directory for JSON event logs."""
        if not os.path.exists(self.log_dir):
            logging.error(f"Log directory not found: {self.log_dir}")
            return

        for filename in os.listdir(self.log_dir):
            if filename.endswith(".json.log"):
                self._parse_file(os.path.join(self.log_dir, filename))

    def _parse_file(self, filepath):
        try:
            with open(filepath, 'r') as f:
                for line in f:
                    if not line.strip(): continue
                    try:
                        event = json.loads(line)
                        ts_str = event.get('timestamp')
                        if not ts_str: continue

                        # Normalize timestamp
                        dt = datetime.fromisoformat(ts_str.replace('Z', '+00:00'))

                        if self.start_dt <= dt <= self.end_dt:
                            self.events.append({
                                "dt": dt,
                                "raw": event
                            })
                    except (json.JSONDecodeError, ValueError):
                        continue
        except Exception as e:
            logging.warning(f"Error reading {filepath}: {e}")

    def generate_report(self, fmt="text"):
        # Sort by time
        self.events.sort(key=lambda x: x['dt'])

        if fmt == "json":
            return self._to_json()
        return self._to_text()

    def _to_json(self):
        output = {
            "incident_report": {
                "generated_at": datetime.now(timezone.utc).isoformat(),
                "window": {
                    "start": self.start_dt.isoformat(),
                    "end": self.end_dt.isoformat()
                },
                "total_events": len(self.events),
                "timeline": [e['raw'] for e in self.events]
            }
        }
        return json.dumps(output, indent=2)

    def _to_text(self):
        lines = []
        lines.append("=" * 60)
        lines.append(f"ATTACK TIMELINE REPORT")
        lines.append(f"Window: {self.start_dt} to {self.end_dt}")
        lines.append("=" * 60)
        lines.append("")

        for e in self.events:
            dt_str = e['dt'].strftime("%Y-%m-%d %H:%M:%S UTC")
            raw = e['raw']

            # Polymorphic handling based on event source
            layer = raw.get('layer', 'UNKNOWN')
            event_type = raw.get('event', 'unknown_event')
            severity = raw.get('severity', 'INFO')

            msg = f"[{dt_str}] [{severity:<8}] [{layer}] {event_type}"

            # Add specific details
            if 'source_entity' in raw:
                msg += f" | Src: {raw['source_entity']}"
            if 'score' in raw: # Orchestrator decision
                msg += f" | Score: {raw['score']} State: {raw.get('state')}"

            lines.append(msg)

        if not self.events:
            lines.append("No events found in the specified window.")

        return "\n".join(lines)

# -----------------------------------------------------------------------------
# Main Entry Point
# -----------------------------------------------------------------------------
def main():
    parser = argparse.ArgumentParser(description=RESPONSIBILITY)

    # Required Flags
    parser.add_argument("--logs-dir", default="logs", help="Directory containing JSON logs")

    # Time Filters
    parser.add_argument("--from-time", help="Start time (ISO8601), default: 1 hour ago")
    parser.add_argument("--to-time", help="End time (ISO8601), default: now")

    # Output
    parser.add_argument("--output-format", choices=["text", "json"], default="text", help="Report format")

    args = parser.parse_args()

    # Logging Setup
    logging.basicConfig(level=logging.INFO, format='%(levelname)s: %(message)s', stream=sys.stderr)

    # Time Parsing logic
    now = datetime.now(timezone.utc)
    start_dt = datetime.min.replace(tzinfo=timezone.utc)
    end_dt = now

    if args.from_time:
        try:
            start_dt = datetime.fromisoformat(args.from_time.replace('Z', '+00:00'))
        except ValueError:
            logging.error("Invalid --from-time format. Use ISO8601 (e.g., 2023-10-27T10:00:00Z)")
            sys.exit(1)

    if args.to_time:
        try:
            end_dt = datetime.fromisoformat(args.to_time.replace('Z', '+00:00'))
        except ValueError:
            logging.error("Invalid --to-time format.")
            sys.exit(1)

    # Execution
    builder = TimelineBuilder(args.logs_dir, (start_dt, end_dt))
    builder.load_logs()
    print(builder.generate_report(args.output_format))

if __name__ == "__main__":
    main()
