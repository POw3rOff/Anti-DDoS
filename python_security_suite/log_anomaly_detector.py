#!/usr/bin/env python3
import sys
import re
import argparse
from datetime import datetime
from collections import Counter
import statistics
import os

# Configuração de cores para saída
class Colors:
    HEADER = '\033[95m'
    OKBLUE = '\033[94m'
    OKGREEN = '\033[92m'
    WARNING = '\033[93m'
    FAIL = '\033[91m'
    ENDC = '\033[0m'
    BOLD = '\033[1m'

# Regex para syslog padrão (ex: "Oct 25 14:02:11")
SYSLOG_PATTERN = re.compile(r'^([A-Z][a-z]{2}\s+\d+\s\d{2}:\d{2}:\d{2})\s')
# Assume ano atual pois syslog geralmente não tem ano (calculado uma vez para performance)
CURRENT_YEAR = datetime.now().year

def parse_log_line(line):
    """
    Tenta analisar uma linha de log comum (Syslog/Auth).
    Formato esperado: Month Day HH:MM:SS Hostname Process: Message
    Exemplo: Oct 25 10:00:01 my-server sshd[1234]: Failed password...
    """
    match = SYSLOG_PATTERN.match(line)
    if match:
        date_str = match.group(1)
        try:
            # Uso de constante global para evitar chamada repetida a datetime.now().year
            date_obj = datetime.strptime(f"{CURRENT_YEAR} {date_str}", "%Y %b %d %H:%M:%S")
            return date_obj
        except ValueError:
            return None
    return None

def analyze_logs(file_path, threshold_stddev=3):
    if not os.path.exists(file_path):
        print(f"{Colors.FAIL}Erro: Arquivo não encontrado: {file_path}{Colors.ENDC}")
        sys.exit(1)

    print(f"{Colors.HEADER}[*] Analisando arquivo: {file_path}{Colors.ENDC}")
    print(f"{Colors.OKBLUE}[*] Threshold de anomalia: {threshold_stddev} desvios padrão{Colors.ENDC}")

    event_counts = Counter()
    total_lines = 0
    parsed_lines = 0

    try:
        with open(file_path, 'r', encoding='utf-8', errors='ignore') as f:
            for line in f:
                total_lines += 1
                dt = parse_log_line(line)
                if dt:
                    parsed_lines += 1
                    # Agrupar por minuto: YYYY-MM-DD HH:MM
                    minute_key = dt.strftime("%Y-%m-%d %H:%M")
                    event_counts[minute_key] += 1
    except PermissionError:
        print(f"{Colors.FAIL}Erro: Permissão negada para ler o arquivo.{Colors.ENDC}")
        sys.exit(1)
    except Exception as e:
        print(f"{Colors.FAIL}Erro ao ler arquivo: {e}{Colors.ENDC}")
        sys.exit(1)

    if parsed_lines == 0:
        print(f"{Colors.WARNING}Aviso: Nenhuma linha de log com data reconhecida foi encontrada.{Colors.ENDC}")
        print("Formatos suportados: Syslog padrão (ex: Oct 25 10:00:00).")
        return

    # Extrair contagens
    counts = list(event_counts.values())

    if len(counts) < 2:
        print(f"{Colors.WARNING}Dados insuficientes para análise estatística.{Colors.ENDC}")
        return

    # Estatísticas
    mean = statistics.mean(counts)
    try:
        stdev = statistics.stdev(counts)
    except statistics.StatisticsError:
        stdev = 0

    print(f"\n{Colors.BOLD}--- Resumo Estatístico ---{Colors.ENDC}")
    print(f"Linhas processadas: {parsed_lines}/{total_lines}")
    print(f"Média de eventos/min: {mean:.2f}")
    print(f"Desvio Padrão: {stdev:.2f}")

    # Detecção de Anomalias
    threshold_val = mean + (threshold_stddev * stdev)
    print(f"Limite de alerta: > {threshold_val:.2f} eventos/min\n")

    anomalies = []
    for timestamp, count in event_counts.items():
        if count > threshold_val:
            z_score = (count - mean) / stdev if stdev > 0 else 0
            anomalies.append((timestamp, count, z_score))

    if anomalies:
        print(f"{Colors.FAIL}{Colors.BOLD}!!! ANOMALIAS DETECTADAS !!!{Colors.ENDC}")
        print(f"{'Data/Hora':<20} | {'Eventos':<10} | {'Z-Score':<10}")
        print("-" * 45)
        # Ordenar por Z-Score decrescente
        for item in sorted(anomalies, key=lambda x: x[2], reverse=True):
            print(f"{item[0]:<20} | {item[1]:<10} | {item[2]:.2f}")
    else:
        print(f"{Colors.OKGREEN}Nenhuma anomalia estatística detectada.{Colors.ENDC}")

def main():
    parser = argparse.ArgumentParser(description="Detector de Anomalias em Logs (Baseado em Estatística)")
    parser.add_argument("logfile", help="Caminho para o arquivo de log (ex: /var/log/syslog)")
    parser.add_argument("--threshold", type=float, default=3.0, help="Número de desvios padrão para considerar anomalia (default: 3.0)")

    if len(sys.argv) == 1:
        parser.print_help(sys.stderr)
        sys.exit(1)

    args = parser.parse_args()

    analyze_logs(args.logfile, args.threshold)

if __name__ == "__main__":
    main()
