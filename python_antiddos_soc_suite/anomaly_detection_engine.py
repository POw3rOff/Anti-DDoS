class AnomalyDetectionEngine:
    def __init__(self, threshold_sigma=3):
        self.threshold_sigma = threshold_sigma

    def detect_anomaly(self, current_value, baseline_mean, baseline_stdev):
        """
        Detects if the current value is an anomaly based on Z-score.
        """
        if baseline_stdev == 0:
            return False, 0.0

        z_score = (current_value - baseline_mean) / baseline_stdev
        is_anomaly = abs(z_score) > self.threshold_sigma

        return is_anomaly, z_score

    def check_traffic(self, traffic_data, baseline_data):
        """
        High-level check of traffic data against baseline.
        """
        current_rps = traffic_data.get('rps', 0)
        mean = baseline_data.get('mean_rps', 0)
        stdev = baseline_data.get('stdev_rps', 1) # Avoid div by zero

        is_anomaly, score = self.detect_anomaly(current_rps, mean, stdev)
        return {
            'is_anomaly': is_anomaly,
            'severity_score': score,
            'details': f"Current RPS {current_rps} vs Baseline {mean:.2f} (Z={score:.2f})"
        }

if __name__ == "__main__":
    detector = AnomalyDetectionEngine()
    print(detector.detect_anomaly(100, 10, 2)) # Should be anomaly