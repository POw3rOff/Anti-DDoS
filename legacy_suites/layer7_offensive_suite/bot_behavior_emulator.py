#!/usr/bin/env python3
import sys
import argparse
import time
import random
import urllib.request
import urllib.error
import threading

# Configuração de cores
class Colors:
    HEADER = '\033[95m'
    OKBLUE = '\033[94m'
    OKGREEN = '\033[92m'
    WARNING = '\033[93m'
    FAIL = '\033[91m'
    ENDC = '\033[0m'

# Assinaturas de Bots Conhecidos (Simulação)
BOT_SIGNATURES = {
    "googlebot": {
        "User-Agent": "Mozilla/5.0 (compatible; Googlebot/2.1; +http://www.google.com/bot.html)",
        "Accept": "*/*"
    },
    "bingbot": {
        "User-Agent": "Mozilla/5.0 (compatible; bingbot/2.0; +http://www.bing.com/bingbot.htm)",
        "Accept": "*/*"
    },
    "scraper_basic": {
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) Scraper/1.0",
        "Accept": "text/html"
    },
    "curl_user": {
        "User-Agent": "curl/7.64.1",
        "Accept": "*/*"
    }
}

stats = {
    "requests": 0,
    "success": 0,
    "errors": 0
}
running = True

def bot_task(url, bot_type, min_delay, max_delay):
    global stats, running

    headers = BOT_SIGNATURES.get(bot_type, BOT_SIGNATURES["scraper_basic"])

    while running:
        try:
            req = urllib.request.Request(url)
            for k, v in headers.items():
                req.add_header(k, v)

            # Simular comportamento humano ou bot (delay variável)
            delay = random.uniform(min_delay, max_delay)
            time.sleep(delay)

            with urllib.request.urlopen(req, timeout=10) as response:
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
        print(f"\r{Colors.OKBLUE}[*] Bot Emulation ({stats['requests']} reqs) | Success: {stats['success']} | Errors: {stats['errors']}{Colors.ENDC}", end="")
        time.sleep(1)

def main():
    global running
    parser = argparse.ArgumentParser(description="Emulador de Comportamento de Bots")
    parser.add_argument("url", help="URL alvo")
    parser.add_argument("--type", choices=BOT_SIGNATURES.keys(), default="scraper_basic", help="Tipo de bot para emular")
    parser.add_argument("--threads", type=int, default=5, help="Número de threads simultâneas")
    parser.add_argument("--min-delay", type=float, default=1.0, help="Delay mínimo entre requisições (s)")
    parser.add_argument("--max-delay", type=float, default=5.0, help="Delay máximo entre requisições (s)")
    parser.add_argument("--duration", type=int, default=60, help="Duração da emulação (s)")

    args = parser.parse_args()

    print(f"{Colors.HEADER}=== Iniciando Bot Behavior Emulator ==={Colors.ENDC}")
    print(f"Alvo: {args.url}")
    print(f"Bot Type: {args.type}")
    print(f"Pattern: {args.min_delay}s - {args.max_delay}s delay randomizado")

    monitor = threading.Thread(target=monitor_thread)
    monitor.daemon = True
    monitor.start()

    threads = []
    for _ in range(args.threads):
        t = threading.Thread(target=bot_task, args=(args.url, args.type, args.min_delay, args.max_delay))
        t.daemon = True
        t.start()
        threads.append(t)

    try:
        time.sleep(args.duration)
    except KeyboardInterrupt:
        print(f"\n{Colors.WARNING}Interrompido!{Colors.ENDC}")

    running = False
    print(f"\n{Colors.OKGREEN}Emulação finalizada.{Colors.ENDC}")

if __name__ == "__main__":
    main()
