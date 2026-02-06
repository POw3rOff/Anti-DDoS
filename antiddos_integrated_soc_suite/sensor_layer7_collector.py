#!/usr/bin/env python3
import time
import re
import json
import random

class SensorLayer7Collector:
    """
    Coleta eventos de Layer 7 (HTTP/API/WebSocket).
    Em um cenário real, leria logs do Nginx/Apache ou receberia dados via socket.
    Aqui simularemos a leitura de logs de acesso.
    """
    def __init__(self, log_path="/var/log/nginx/access.log"):
        self.log_path = log_path
        self.simulated_mode = True # Se True, gera dados aleatórios para teste

    def parse_log_line(self, line):
        """Extrai IP, método, URL, código de status de uma linha de log comum."""
        # Exemplo simples de regex para Common Log Format
        regex = r'^(\S+) \S+ \S+ \[.*\] "(\S+) (\S+) \S+" (\d+) (\d+)'
        match = re.search(regex, line)
        if match:
            return {
                "src_ip": match.group(1),
                "method": match.group(2),
                "url": match.group(3),
                "status": int(match.group(4)),
                "size": int(match.group(5))
            }
        return None

    def collect_simulated(self):
        """Gera tráfego HTTP simulado para testes do pipeline."""
        methods = ["GET", "POST", "HEAD"]
        urls = ["/api/login", "/", "/search", "/admin"]
        statuses = [200, 200, 200, 404, 500, 301]

        events = []
        # Gera entre 0 e 5 eventos por ciclo
        for _ in range(random.randint(0, 5)):
            events.append({
                "src_ip": f"192.168.1.{random.randint(1, 255)}",
                "method": random.choice(methods),
                "url": random.choice(urls),
                "status": random.choice(statuses),
                "user_agent": "Mozilla/5.0 (Simulated)",
                "timestamp": time.time()
            })
        return events

    def collect(self):
        """Retorna lista de requisições recentes."""
        # Em produção, implementaria um 'tail' no arquivo de log
        if self.simulated_mode:
            return {
                "layer": 7,
                "timestamp": time.time(),
                "events": self.collect_simulated()
            }
        return {"layer": 7, "events": []}

if __name__ == "__main__":
    sensor = SensorLayer7Collector()
    print(json.dumps(sensor.collect(), indent=2))
