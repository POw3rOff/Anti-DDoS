#!/usr/bin/env python3
"""
Game Attack Simulator
Generates protocol-specific floods for testing Layer G monitors.
"""

import socket
import time
import argparse
import random
import struct

def send_minecraft_handshake(target_ip, port, count, delay, valid=True):
    print(f"Sending {count} Minecraft Handshakes to {target_ip}:{port} (Valid: {valid})")
    sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    try:
        sock.connect((target_ip, port))
    except Exception as e:
        print(f"Connection failed: {e}")
        return

    for i in range(count):
        # VarInts are simplified here for standard values
        # Packet ID 0x00 (Handshake)
        # Protocol Version 763 (1.20.1) -> VarInt
        # Server Address (String)
        # Port (Unsigned Short)
        # Next State (1 = Status, 2 = Login)
        
        if valid:
            # Valid Handshake (Login State)
            # Len: 16, ID: 0x00, Ver: 763, LenStr: 9, "localhost", Port: 25565, State: 2
            payload = b'\x00\xfb\x05\x09localhost\x63\xdd\x02' 
            length = len(payload)
            packet = struct.pack('B', length) + payload
        else:
            # Malformed/Fuzzing
            packet = b'\x00\xff\xff\xff\xff' * 10 

        try:
            sock.send(packet)
            # If valid, we might want to close and reconnect to simulate "Zombie" (open, handshake, nothing else)
            # But for "State Tracking" test, we send handshake and stay silent
            if valid:
                pass # Keep connection open but don't send Login Start
            
            time.sleep(delay)
        except Exception as e:
            print(f"Send failed: {e}")
            break
    
    sock.close()

def send_raknet_ping(target_ip, port, count, delay):
    print(f"Sending {count} RakNet Unconnected Pings to {target_ip}:{port}")
    sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    
    # Unconnected Ping
    # ID: 0x01
    # Time: 8 bytes
    # Magic: ...
    # GUID: 8 bytes
    magic = b'\x00\xff\xff\x00\xfe\xfe\xfe\xfe\xfd\xfd\xfd\xfd\x12\x34\x56\x78'
    packet = b'\x01' + (b'\x00'*8) + magic + (b'\x00'*8)

    for i in range(count):
        try:
            sock.sendto(packet, (target_ip, port))
            time.sleep(delay)
        except Exception as e:
            print(f"Send failed: {e}")
    
    sock.close()

def main():
    parser = argparse.ArgumentParser(description="Game Attack Simulator")
    parser.add_argument("target_ip", help="Target IP")
    parser.add_argument("--proto", choices=["minecraft", "raknet"], required=True)
    parser.add_argument("--port", type=int, default=0)
    parser.add_argument("--count", type=int, default=100)
    parser.add_argument("--delay", type=float, default=0.01)
    parser.add_argument("--malformed", action="store_true", help="Send malformed packets")

    args = parser.parse_args()
    
    port = args.port
    if port == 0:
        port = 25565 if args.proto == "minecraft" else 19132

    if args.proto == "minecraft":
        send_minecraft_handshake(args.target_ip, port, args.count, args.delay, not args.malformed)
    elif args.proto == "raknet":
        send_raknet_ping(args.target_ip, port, args.count, args.delay)

if __name__ == "__main__":
    main()
