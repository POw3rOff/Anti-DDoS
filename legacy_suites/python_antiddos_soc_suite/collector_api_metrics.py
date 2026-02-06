import time
import random

class APIMetricsCollector:
    def __init__(self):
        self.endpoints = ['/api/auth', '/api/users', '/api/payments']

    def collect_metrics(self):
        """
        Returns a snapshot of API metrics: latency, error_rate, rps
        """
        metrics = {}
        for ep in self.endpoints:
            metrics[ep] = {
                'timestamp': time.time(),
                'latency_ms': random.uniform(20, 500),
                'error_rate_percent': random.uniform(0, 5),
                'requests_per_second': random.randint(10, 200)
            }
        return metrics

if __name__ == "__main__":
    collector = APIMetricsCollector()
    print(collector.collect_metrics())