import time
import random
import uuid

class RealtimeTrafficCollector:
    def __init__(self):
        pass

    def stream_events(self):
        """
        Simulates a stream of raw network events (e.g. from packet capture)
        """
        protocols = ['TCP', 'UDP', 'ICMP']
        while True:
            event = {
                'event_id': str(uuid.uuid4()),
                'timestamp': time.time(),
                'src_ip': f"10.0.0.{random.randint(1, 255)}",
                'dst_port': random.choice([80, 443, 8080, 22]),
                'protocol': random.choice(protocols),
                'packet_size': random.randint(64, 1500),
                'flags': random.choice(['SYN', 'ACK', 'FIN', 'RST'])
            }
            yield event
            time.sleep(0.2)

if __name__ == "__main__":
    collector = RealtimeTrafficCollector()
    for event in collector.stream_events():
        print(f"Traffic Event: {event}")
        break