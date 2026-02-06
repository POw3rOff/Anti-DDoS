
import os
import logging
from typing import Dict, Any, Optional

# Try to import geoip2, handle its absence gracefully
try:
    import geoip2.database
    HAS_GEOIP = True
except ImportError:
    HAS_GEOIP = False

class GeoIPEnricher:
    """
    Enriches IP addresses with Geographic (Country, City) and Network (ASN) data.
    Robust against missing dependencies or databases.
    """
    def __init__(self, db_path_city: Optional[str] = None, db_path_asn: Optional[str] = None):
        self.reader_city = None
        self.reader_asn = None
        
        if not HAS_GEOIP:
            logging.warning("geoip2 library not found. Enrichment disabled.")
            return

        # Default paths if not provided
        base_path = os.path.join(os.path.dirname(__file__), "../config/geoip")
        if not db_path_city:
            db_path_city = os.path.join(base_path, "GeoLite2-City.mmdb")
        if not db_path_asn:
            db_path_asn = os.path.join(base_path, "GeoLite2-ASN.mmdb")

        try:
            if os.path.exists(db_path_city):
                self.reader_city = geoip2.database.Reader(db_path_city)
                logging.info(f"Loaded GeoIP City DB: {db_path_city}")
            else:
                logging.debug(f"GeoIP City DB not found at {db_path_city}")

            if os.path.exists(db_path_asn):
                self.reader_asn = geoip2.database.Reader(db_path_asn)
                logging.info(f"Loaded GeoIP ASN DB: {db_path_asn}")
            else:
                logging.debug(f"GeoIP ASN DB not found at {db_path_asn}")

        except Exception as e:
            logging.error(f"Failed to initialize GeoIP readers: {e}")

    def enrich(self, ip: str) -> Dict[str, Any]:
        """
        Returns a dictionary with enrichment data.
        Keys: country, city, asn, org
        """
        result = {
            "country": "Unknown",
            "city": "Unknown",
            "asn": "Unknown",
            "org": "Unknown"
        }

        if not HAS_GEOIP:
            return result
            
        try:
            # City Lookup
            if self.reader_city:
                try:
                    response = self.reader_city.city(ip)
                    if response.country.iso_code:
                        result["country"] = response.country.iso_code
                    if response.city.name:
                        result["city"] = response.city.name
                except geoip2.errors.AddressNotFoundError:
                    pass
                except Exception as e:
                    logging.debug(f"GeoIP City lookup failed for {ip}: {e}")

            # ASN Lookup
            if self.reader_asn:
                try:
                    response = self.reader_asn.asn(ip)
                    if response.autonomous_system_number:
                        result["asn"] = f"AS{response.autonomous_system_number}"
                    if response.autonomous_system_organization:
                        result["org"] = response.autonomous_system_organization
                except geoip2.errors.AddressNotFoundError:
                    pass
                except Exception as e:
                    logging.debug(f"GeoIP ASN lookup failed for {ip}: {e}")

        except Exception as e:
             logging.error(f"Enrichment error for {ip}: {e}")

        return result

    def close(self):
        if self.reader_city:
            self.reader_city.close()
        if self.reader_asn:
            self.reader_asn.close()
