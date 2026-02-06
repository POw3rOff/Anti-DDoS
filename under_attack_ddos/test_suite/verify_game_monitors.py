
import unittest
import sys
import os
import time
import logging
from unittest.mock import MagicMock

# Add project root to path
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from scapy.all import IP, UDP, TCP, Raw
from layer_game.rust.rust_monitor import RustMonitor
from layer_game.metin2.metin2_protocol_anomaly import Metin2ProtocolAnomaly
from layer_game.samp.samp_monitor import SAMPMonitor
from layer_game.unreal.unreal_monitor import UnrealMonitor
from layer_game.generic.generic_monitor import GenericGameMonitor

# Import simulators (copying logic or importing if refactored, let's replicate logic for test stability)
# Actually, imports from game_attack_sim if possible, but it's a script. 
# We'll re-implement packet generation helpers here to match game_attack_sim.py

class TestGameMonitors(unittest.TestCase):
    
    def setUp(self):
        logging.basicConfig(level=logging.ERROR)

    def test_rust_monitor_raknet_flood(self):
        print("Testing Rust Monitor (RakNet Flood)...")
        monitor = RustMonitor(dry_run=True)
        monitor.emit_event = MagicMock()
        
        # Simulate RakNet Handshake Flood
        payload = b'\x05\x00\xff\xff\x00\xfe\xfe\xfe\xfe\xfd\xfd\xfd\xfd\x12\x34\x56\x78\x06'
        src_ip = "192.168.1.100"
        
        for _ in range(20):
            pkt = IP(src=src_ip)/UDP(dport=28015)/Raw(load=payload)
            monitor.packet_callback(pkt)
            
        monitor.analyze_window()
        
        monitor.emit_event.assert_called()
        args = monitor.emit_event.call_args[0]
        self.assertEqual(args[0], "raknet_handshake_flood")
        self.assertEqual(args[1], src_ip)
        print("PASS: Rust Monitor detected flood")

    def test_metin2_monitor_malformed(self):
        print("Testing Metin2 Monitor (Malformed Handshake)...")
        monitor = Metin2ProtocolAnomaly(dry_run=True)
        monitor.emit_event = MagicMock()
        
        # Malformed handshake (short)
        src_ip = "192.168.1.101"
        payload = b'\x32\x01' # Too short
        
        pkt = IP(src=src_ip)/TCP(dport=11002)/Raw(load=payload)
        monitor.client_states[src_ip]["state"] = 0 # INIT
        
        monitor.packet_callback(pkt)
        
        monitor.emit_event.assert_called()
        args = monitor.emit_event.call_args[0]
        self.assertEqual(args[0], "malformed_packet")
        print("PASS: Metin2 Monitor detected malformed packet")

    def test_samp_monitor_query_flood(self):
        print("Testing SAMP Monitor (Query Flood)...")
        # Port 7777 default
        monitor = SAMPMonitor(port=7777, dry_run=True)
        monitor.emit_event = MagicMock()
        
        src_ip = "192.168.1.102"
        # SAMP 'c' query
        payload = b'SAMP\x7f\x00\x00\x01\x1e\x61\x63' # ... 'c'
        
        for _ in range(10):
            pkt = IP(src=src_ip)/UDP(dport=7777)/Raw(load=payload)
            monitor.packet_callback(pkt)
            
        monitor.analyze()
        
        monitor.emit_event.assert_called()
        args = monitor.emit_event.call_args[0]
        self.assertEqual(args[0], "samp_query_flood")
        print("PASS: SAMP Monitor detected query flood")

    def test_unreal_monitor_flood(self):
        print("Testing Unreal Monitor (Volume Flood)...")
        monitor = UnrealMonitor(port=7777, dry_run=True)
        monitor.emit_event = MagicMock()
        monitor.max_pps = 5 # Low threshold for test
        
        src_ip = "192.168.1.103"
        payload = b'\x01\x02' * 10
        
        # Monitor needs > 0.1s duration
        time.sleep(0.2)
        
        for _ in range(10):
            pkt = IP(src=src_ip)/UDP(dport=7777)/Raw(load=payload)
            monitor.packet_callback(pkt)
            
        monitor.analyze()
        
        monitor.emit_event.assert_called()
        args = monitor.emit_event.call_args[0]
        self.assertEqual(args[0], "unreal_flood")
        print("PASS: Unreal Monitor detected flood")

if __name__ == "__main__":
    unittest.main()
