import time
import json
import random
from collections import deque

class HTTPLogCollector:
    def __init__(self, log_file_path='/var/log/apache2/access.log', simulate=True):
        self.log_file_path = log_file_path
        self.simulate = simulate
        self.buffer = deque(maxlen=1000)

    def collect(self):
        """
        Generator that yields log entries.
        In simulation mode, it generates synthetic logs.
        """
        if self.simulate:
            methods = ['GET', 'POST', 'PUT', 'DELETE']
            paths = ['/login', '/api/v1/data', '/index.html', '/static/style.css', '/admin']
            ips = ['192.168.1.' + str(i) for i in range(1, 20)]

            while True:
                entry = {
                    'timestamp': time.time(),
                    'ip': random.choice(ips),
                    'method': random.choice(methods),
                    'path': random.choice(paths),
                    'status': random.choice([200, 200, 200, 404, 500, 403]),
                    'user_agent': 'Mozilla/5.0 (Simulation)'
                }
                self.buffer.append(entry)
                yield entry
                time.sleep(random.uniform(0.1, 0.5))
        else:
            # Real implementation would tail the file
            pass

    def get_recent_logs(self, n=10):
        return list(self.buffer)[-n:]

if __name__ == "__main__":
    collector = HTTPLogCollector()
    for log in collector.collect():
        print(f"Collected: {log}")
        break # Just run once for test