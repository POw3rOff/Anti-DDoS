import socket
import logging
import datetime
import signal

# Configuração de Log
LOG_FILE = "honeypot.log"
logging.basicConfig(filename=LOG_FILE, level=logging.INFO, format="%(asctime)s - %(message)s")

# Configurações do Honeypot
BIND_IP = "0.0.0.0"
BIND_PORT = 2222
FAKE_BANNER = b"SSH-2.0-OpenSSH_8.2p1 Ubuntu-4ubuntu0.5\r\n"

def handle_client(client_socket, address):
    ip, port = address
    logging.info(f"Conexão recebida de {ip}:{port}")
    print(f"[{datetime.datetime.now()}] Conexão de {ip}:{port}")

    try:
        # Definir timeout para evitar que conexões presas bloqueiem threads (mesmo sendo single thread aqui)
        client_socket.settimeout(10)

        # Enviar banner falso
        client_socket.send(FAKE_BANNER)

        # Receber dados iniciais (provavelmente negociação de versão ou usuario)
        data = client_socket.recv(1024)
        if data:
            logging.info(f"Dados recebidos de {ip}: {data.strip()}")
            # Tentar capturar mais dados (simulando delay)

    except socket.timeout:
        logging.warning(f"Timeout na conexão de {ip}")
    except Exception as e:
        logging.error(f"Erro ao lidar com {ip}: {e}")
    finally:
        client_socket.close()

def start_server():
    server = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    server.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)

    try:
        server.bind((BIND_IP, BIND_PORT))
        server.listen(5)
        print(f"[*] Honeypot SSH Simples iniciado em {BIND_IP}:{BIND_PORT}")
        logging.info(f"Honeypot iniciado em {BIND_IP}:{BIND_PORT}")

        while True:
            client, addr = server.accept()
            handle_client(client, addr)

    except KeyboardInterrupt:
        print("\n[*] Parando Honeypot...")
        logging.info("Honeypot parado pelo usuário.")
    except Exception as e:
        print(f"\n[!] Erro fatal: {e}")
        logging.error(f"Erro fatal: {e}")
    finally:
        server.close()

if __name__ == "__main__":
    start_server()
