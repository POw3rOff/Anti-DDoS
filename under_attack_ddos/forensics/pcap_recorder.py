
import os
import time
import threading
import logging
import sys
from datetime import datetime

# Try importing scapy
try:
    from scapy.all import sniff, wrpcap
    HAS_SCAPY = True
except ImportError:
    HAS_SCAPY = False

class PcapRecorder:
    def __init__(self, output_dir=None):
        self.output_dir = output_dir or os.path.join(os.path.dirname(__file__), "../data/captures")
        if not os.path.exists(self.output_dir):
            os.makedirs(self.output_dir)
        
        self.is_recording = False
        self.stop_event = threading.Event()
        self.capture_thread = None
        self.current_file = None

    def start_capture(self, duration=60, packet_limit=10000, interface=None):
        """Starts a background capture."""
        if self.is_recording:
            logging.warning("Capture already in progress.")
            return

        if not HAS_SCAPY:
            logging.error("Scapy not installed. Cannot record PCAP.")
            return

        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        filename = f"capture_{timestamp}.pcap"
        self.current_file = os.path.join(self.output_dir, filename)
        
        self.stop_event.clear()
        self.is_recording = True
        
        self.capture_thread = threading.Thread(
            target=self._capture_loop,
            args=(self.current_file, duration, packet_limit, interface)
        )
        self.capture_thread.daemon = True
        self.capture_thread.start()
        
        logging.info(f"Started PCAP capture: {self.current_file}")
        return filename

    def stop_capture(self):
        """Stops the current capture."""
        if self.is_recording:
            self.stop_event.set()
            if self.capture_thread:
                self.capture_thread.join(timeout=2)
            self.is_recording = False
            logging.info("Stopped PCAP capture.")
            return True
        return False

    def _capture_loop(self, output_path, duration, packet_limit, interface):
        """Internal capture loop using Scapy."""
        start_time = time.time()
        packets = []
        
        def processing_callback(pkt):
            packets.append(pkt)
            
        logging.info("Recorder thread running...")
        
        try:
            # We use a loop with short sniffs to check for stop_event
            # Scapy's stop_filter is another option but basic check is simpler here
            while not self.stop_event.is_set():
                # Sniff for 1 second chunk
                chunk = sniff(count=100, timeout=1, iface=interface, store=True)
                packets.extend(chunk)
                
                # Check constraints
                if time.time() - start_time > duration:
                    logging.info("Capture time limit reached.")
                    break
                if len(packets) >= packet_limit:
                    logging.info("Capture packet limit reached.")
                    break
        except Exception as e:
            logging.error(f"Capture error: {e}")
        finally:
            self.is_recording = False
            
            # Flush to disk
            if packets:
                try:
                    wrpcap(output_path, packets)
                    logging.info(f"Wrote {len(packets)} packets to {output_path}")
                except Exception as e:
                    logging.error(f"Failed to write PCAP: {e}")
            else:
                logging.warning("No packets captured.")

if __name__ == "__main__":
    # Test
    logging.basicConfig(level=logging.INFO)
    rec = PcapRecorder()
    rec.start_capture(duration=5)
    time.sleep(6)
    rec.stop_capture()
