#!/usr/bin/env python3
"""
Log Aggregator
Part of Observability Layer

Responsibility: Centralizes logs from various components into a single stream.
"""

import sys
import os
import time
import json
import logging
import argparse

# -----------------------------------------------------------------------------
# Configuration
# -----------------------------------------------------------------------------
LOG_DIR = "logs/"
OUTPUT_FILE = "logs/system.json.log"

class LogAggregator:
    def __init__(self, log_dir=LOG_DIR):
        self.log_dir = log_dir
        self.files = {}

    def run(self):
        logging.info(f"Aggregating logs from {self.log_dir} to {OUTPUT_FILE}")

        while True:
            # Discovery new files
            if os.path.exists(self.log_dir):
                for f in os.listdir(self.log_dir):
                    if f.endswith(".log") and f != "system.json.log" and f not in self.files:
                        self.files[f] = open(os.path.join(self.log_dir, f), 'r')
                        self.files[f].seek(0, 2) # Start at end

            # Read files
            for fname, fhandle in self.files.items():
                line = fhandle.readline()
                if line:
                    self._emit(line.strip())

            time.sleep(0.1)

    def _emit(self, line):
        try:
            # Validate JSON before re-emitting
            json.loads(line)
            with open(OUTPUT_FILE, 'a') as out:
                out.write(line + "\n")
        except:
            pass

if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO)
    LogAggregator().run()
