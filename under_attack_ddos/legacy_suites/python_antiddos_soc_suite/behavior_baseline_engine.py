import statistics
from collections import deque

class BehaviorBaselineEngine:
    def __init__(self, window_size=100):
        self.request_counts = deque(maxlen=window_size)
        self.baseline_mean = 0
        self.baseline_stdev = 0

    def update(self, current_rps):
        """
        Updates the moving window and recalculates baseline statistics.
        """
        self.request_counts.append(current_rps)
        if len(self.request_counts) > 2:
            self.baseline_mean = statistics.mean(self.request_counts)
            self.baseline_stdev = statistics.stdev(self.request_counts)
        else:
            self.baseline_mean = current_rps
            self.baseline_stdev = 0

    def get_baseline(self):
        return {
            'mean_rps': self.baseline_mean,
            'stdev_rps': self.baseline_stdev
        }

if __name__ == "__main__":
    engine = BehaviorBaselineEngine()
    for i in range(10, 20):
        engine.update(i)
    print(engine.get_baseline())