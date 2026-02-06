#!/usr/bin/env python3
import statistics

class BaselineLearningEngine:
    """
    Aprende padrões normais de tráfego (baseline) para detecção de anomalias.
    Mantém médias móveis simples de métricas chave.
    """
    def __init__(self, window_size=10):
        self.window_size = window_size
        self.history = {
            "l3_packets_in": [],
            "l4_tcp_conn": [],
            "l7_rps": []
        }
        self.baselines = {
            "l3_packets_in_avg": 0,
            "l3_packets_in_std": 0,
            "l4_tcp_conn_avg": 0,
            "l7_rps_avg": 0
        }

    def update(self, metrics_snapshot):
        """Recebe um dict com métricas agregadas do ciclo atual."""
        if "l3_packets" in metrics_snapshot:
            self._add_metric("l3_packets_in", metrics_snapshot["l3_packets"])

        if "l4_conn" in metrics_snapshot:
            self._add_metric("l4_tcp_conn", metrics_snapshot["l4_conn"])

        if "l7_reqs" in metrics_snapshot:
            self._add_metric("l7_rps", metrics_snapshot["l7_reqs"])

        self._recalc_baselines()

    def _add_metric(self, key, value):
        self.history[key].append(value)
        if len(self.history[key]) > self.window_size:
            self.history[key].pop(0)

    def _recalc_baselines(self):
        for key in self.history:
            if len(self.history[key]) > 1:
                avg = statistics.mean(self.history[key])
                std = statistics.stdev(self.history[key])
                self.baselines[f"{key}_avg"] = avg
                self.baselines[f"{key}_std"] = std

    def check_anomaly(self, metric_name, current_value, threshold_std=3):
        """Verifica se o valor atual desvia muito da baseline (Z-score)."""
        avg_key = f"{metric_name}_avg"
        std_key = f"{metric_name}_std"

        if avg_key not in self.baselines or std_key not in self.baselines:
            return False, 0.0

        avg = self.baselines[avg_key]
        std = self.baselines[std_key]

        if std == 0:
            return False, 0.0 # Sem variação histórica ou dados insuficientes

        z_score = (current_value - avg) / std
        is_anomaly = z_score > threshold_std
        return is_anomaly, z_score
