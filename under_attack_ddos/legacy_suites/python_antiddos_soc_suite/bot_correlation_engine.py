from collections import defaultdict

class BotCorrelationEngine:
    def __init__(self):
        # Maps signature (e.g., User-Agent + Path) to list of IPs
        self.signatures = defaultdict(set)

    def analyze_request(self, request_data):
        """
        Ingests a request and looks for patterns.
        """
        ip = request_data.get('ip')
        ua = request_data.get('user_agent', 'unknown')
        path = request_data.get('path', '/')

        # Simple signature: User-Agent + Target Path
        signature = f"{ua}|{path}"
        self.signatures[signature].add(ip)

    def find_botnets(self, min_ips=5):
        """
        Returns signatures that are shared by many unique IPs (potential botnet).
        """
        suspect_signatures = []
        for sig, ips in self.signatures.items():
            if len(ips) >= min_ips:
                suspect_signatures.append({
                    'signature': sig,
                    'unique_ips_count': len(ips),
                    'ips': list(ips)[:10] # Show sample
                })
        return suspect_signatures

if __name__ == "__main__":
    engine = BotCorrelationEngine()
    for i in range(10):
        engine.analyze_request({'ip': f'10.0.0.{i}', 'user_agent': 'EvilBot', 'path': '/login'})
    print(engine.find_botnets(min_ips=5))