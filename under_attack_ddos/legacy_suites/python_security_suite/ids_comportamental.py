#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
IDS Comportamental (Baseline Dinâmica)
======================================
Aprende o comportamento normal do sistema (CPU, Memória, Rede, Processos) e alerta desvios.

Modos:
1. Aprendizado (--mode learn): Monitora por X tempo e cria um perfil (baseline.json).
2. Monitoramento (--mode monitor): Compara estado atual com perfil e alerta anomalias.

Uso:
    python3 ids_comportamental.py --mode learn --duration 60 --output baseline.json
    python3 ids_comportamental.py --mode monitor --input baseline.json
"""

import argparse
import json
import time
import math
import sys
import os
import subprocess

# Utilitários para leitura do /proc e Comandos

def get_cpu_usage():
    """Lê /proc/stat e calcula uso de CPU percentual."""
    try:
        with open('/proc/stat', 'r') as f:
            line = f.readline()
        parts = line.split()
        user = int(parts[1])
        nice = int(parts[2])
        system = int(parts[3])
        idle = int(parts[4])
        total = user + nice + system + idle
        return total, idle
    except:
        return 0, 0

def get_memory_usage():
    """Lê /proc/meminfo e retorna % de uso."""
    try:
        mem = {}
        with open('/proc/meminfo', 'r') as f:
            for line in f:
                parts = line.split()
                if len(parts) >= 2:
                    mem[parts[0].strip(':')] = int(parts[1])

        total = mem.get('MemTotal', 1)
        available = mem.get('MemAvailable', 0)
        used_percent = ((total - available) / total) * 100.0
        return used_percent
    except:
        return 0.0

def get_network_bytes():
    """Lê /proc/net/dev e soma bytes rx/tx."""
    rx_total = 0
    tx_total = 0
    try:
        with open('/proc/net/dev', 'r') as f:
            lines = f.readlines()[2:]
            for line in lines:
                parts = line.split()
                iface = parts[0].strip(':')
                if iface == 'lo':
                    continue
                rx_total += int(parts[1])
                tx_total += int(parts[9])
        return rx_total, tx_total
    except:
        return 0, 0

def get_process_stats():
    """Retorna contagem total de processos e max %CPU de um único processo."""
    proc_count = 0
    max_cpu = 0.0
    try:
        # ps -eo %cpu --sort=-%cpu | head -n 2 (Header + Top 1)
        # ps ax | wc -l (Total Procs)

        # Count via /proc usually faster
        proc_dirs = [p for p in os.listdir('/proc') if p.isdigit()]
        proc_count = len(proc_dirs)

        # Max CPU needs 'ps'
        cmd = ["ps", "-eo", "%cpu", "--sort=-%cpu"]
        result = subprocess.run(cmd, stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True)
        lines = result.stdout.splitlines()
        if len(lines) > 1:
            try:
                max_cpu = float(lines[1].strip())
            except:
                pass
    except:
        pass
    return proc_count, max_cpu

class IDSEngine:
    def __init__(self):
        self.metrics = {
            "cpu": [],
            "memory": [],
            "net_rx_rate": [],
            "net_tx_rate": [],
            "proc_count": [],
            "proc_max_cpu": []
        }
        self.baseline = {}

    def collect_sample(self, interval=1.0):
        # CPU start
        t1, i1 = get_cpu_usage()
        rx1, tx1 = get_network_bytes()

        time.sleep(interval)

        t2, i2 = get_cpu_usage()
        rx2, tx2 = get_network_bytes()

        if t2 - t1 > 0:
            cpu_usage = (1 - (i2 - i1) / (t2 - t1)) * 100.0
        else:
            cpu_usage = 0.0

        rx_rate = (rx2 - rx1) / interval
        tx_rate = (tx2 - tx1) / interval

        mem_usage = get_memory_usage()
        proc_count, proc_max_cpu = get_process_stats()

        return {
            "cpu": cpu_usage,
            "memory": mem_usage,
            "net_rx_rate": rx_rate,
            "net_tx_rate": tx_rate,
            "proc_count": proc_count,
            "proc_max_cpu": proc_max_cpu
        }

    def learn(self, duration, output_file):
        print(f"[*] Iniciando fase de aprendizado ({duration} segundos)...")
        start_time = time.time()
        samples_count = 0

        while time.time() - start_time < duration:
            sample = self.collect_sample()
            for k, v in sample.items():
                self.metrics[k].append(v)

            samples_count += 1
            if samples_count % 10 == 0:
                print(f"   Amostras: {samples_count}")

        for key, values in self.metrics.items():
            if not values:
                mean = 0
                stddev = 0
            else:
                mean = sum(values) / len(values)
                variance = sum([((x - mean) ** 2) for x in values]) / len(values)
                stddev = math.sqrt(variance)

            self.baseline[key] = {"mean": mean, "stddev": stddev}

        print(f"[*] Aprendizado concluído. Salvando em {output_file}...")
        with open(output_file, 'w') as f:
            json.dump(self.baseline, f, indent=4)

    def monitor(self, input_file, threshold=3.0):
        print(f"[*] Carregando baseline de {input_file}...")
        try:
            with open(input_file, 'r') as f:
                self.baseline = json.load(f)
        except Exception as e:
            print(f"[!] Erro: {e}")
            return

        print(f"[*] Monitorando... Limiar Z-Score: {threshold}")

        while True:
            sample = self.collect_sample()
            alerts = []

            for key, val in sample.items():
                stats = self.baseline.get(key)
                if not stats: continue

                mean = stats["mean"]
                stddev = stats["stddev"]

                if stddev < 0.1: stddev = 0.1 # Evitar div/0

                z_score = (val - mean) / stddev

                if abs(z_score) > threshold:
                    alerts.append(f"{key}: {val:.2f} (Média: {mean:.2f}, Z: {z_score:.2f})")

            if alerts:
                ts = time.strftime("%H:%M:%S")
                print(f"[{ts}] [ANOMALIA] " + ", ".join(alerts))

def main():
    parser = argparse.ArgumentParser(description="IDS Comportamental Baseado em Baseline")
    parser.add_argument('--mode', choices=['learn', 'monitor'], required=True, help="Modo")
    parser.add_argument('--duration', type=int, default=60, help="Duração aprendizado (s)")
    parser.add_argument('--output', default='baseline.json', help="Arquivo output")
    parser.add_argument('--input', default='baseline.json', help="Arquivo input")
    parser.add_argument('--threshold', type=float, default=3.0, help="Z-Score Threshold")

    args = parser.parse_args()

    engine = IDSEngine()
    if args.mode == 'learn':
        engine.learn(args.duration, args.output)
    elif args.mode == 'monitor':
        engine.monitor(args.input, args.threshold)

if __name__ == "__main__":
    main()
