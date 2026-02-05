#!/usr/bin/env python3
"""
Feedback Emitter
Part of 'under_attack_ddos' Defense System.

Responsibility: Integrated into Orchestrator.
Calculates system stress and emits tuning directives to the Autotune Controller.
"""

import logging
import json
import time

class FeedbackEmitter:
    def __init__(self, policy_model, controller):
        self.policy = policy_model
        self.controller = controller
        self.last_check = 0
        self.interval = 5 # seconds

    def process_feedback(self, metrics):
        """
        metrics: { 'cpu_load': float, ... }
        """
        now = time.time()
        if now - self.last_check < self.interval:
            return
        self.last_check = now

        # Get Adjustments from Policy Model
        # (Mocking current_state as 'NORMAL' for now, this would come from orchestrator state)
        adjustments = self.policy.suggest_tuning("NORMAL", metrics)

        for param, adj_str in adjustments.items():
            # Get current value (cached in controller)
            current = self.controller.current_values.get(param)
            if not current: continue

            new_val = self.policy.calculate_new_value(current, adj_str)

            if new_val != current:
                logging.info(f"Autotune: Adjusting {param} {current} -> {new_val} ({adj_str})")
                self.controller.apply_update(param, new_val)

# Simulation/Test harness if run directly
if __name__ == "__main__":
    from under_attack_ddos.kernel_ebpf.autotune.policy_model import PolicyModel
    from under_attack_ddos.kernel_ebpf.autotune.threshold_controller import ThresholdController

    logging.basicConfig(level=logging.INFO)

    # Mock
    model = PolicyModel()
    ctrl = ThresholdController(dry_run=True)
    emitter = FeedbackEmitter(model, ctrl)

    # Simulate High Load
    logging.info("Simulating High Load Event...")
    metrics = {"cpu_load": 0.9}
    emitter.process_feedback(metrics)

    # Simulate Low Load
    logging.info("Simulating Recovery...")
    metrics = {"cpu_load": 0.1}
    emitter.process_feedback(metrics)
