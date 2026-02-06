from collections import defaultdict
import time

class RiskScoringEngine:
    def __init__(self, decay_rate=0.1):
        self.scores = defaultdict(float)
        self.last_update = defaultdict(float)
        self.decay_rate = decay_rate

    def update_score(self, ip, points, reason=None):
        """
        Adds points to an IP's risk score.
        """
        current_time = time.time()

        # Apply decay based on time elapsed
        elapsed = current_time - self.last_update.get(ip, current_time)
        decay = elapsed * self.decay_rate
        self.scores[ip] = max(0, self.scores[ip] - decay)

        self.scores[ip] += points
        self.last_update[ip] = current_time

        return self.scores[ip]

    def get_score(self, ip):
        current_time = time.time()
        elapsed = current_time - self.last_update.get(ip, current_time)
        decay = elapsed * self.decay_rate
        return max(0, self.scores[ip] - decay)

if __name__ == "__main__":
    scorer = RiskScoringEngine()
    print(f"Score: {scorer.update_score('1.2.3.4', 10, 'Rapid requests')}")
    time.sleep(1)
    print(f"Score after decay: {scorer.get_score('1.2.3.4')}")