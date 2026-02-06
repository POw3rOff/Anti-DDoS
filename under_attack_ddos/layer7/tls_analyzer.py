
import logging
import hashlib
try:
    from scapy.all import TLS, TLSClientHello
except ImportError:
    TLS = None
    TLSClientHello = None

class TLSFingerprinter:
    """
    Layer 7: TLS Fingerprinting (JA3-style).
    Identifies bots based on their SSL/TLS Handshake parameters.
    """
    def __init__(self):
        self.enabled = (TLS is not None)
        if not self.enabled:
            logging.warning("Scapy TLS layer not found. TLS Fingerprinting disabled.")

    def get_fingerprint(self, packet):
        """Extracts JA3 hash from a ClientHello packet."""
        if not self.enabled or not packet.haslayer(TLSClientHello):
            return None
        
        try:
            client_hello = packet[TLSClientHello]
            
            # JA3 Logic: SSLVersion,Cipher,SSLExtension,EllipticCurve,EllipticCurvePointFormat
            # We simplify this to just Ciphers for the prototype
            ciphers = client_hello.ciphers
            ciphers_str = "-".join([str(c) for c in ciphers])
            
            version = client_hello.version
            
            # Create Hash
            raw_string = f"{version},{ciphers_str},,,"
            ja3_hash = hashlib.md5(raw_string.encode()).hexdigest()
            
            return {
                "ja3": ja3_hash,
                "ciphers_count": len(ciphers),
                "version": version
            }
        except Exception as e:
            logging.error(f"TLS Parsing error: {e}")
            return None
