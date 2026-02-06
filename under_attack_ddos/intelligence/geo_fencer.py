
import logging
import time
from collections import defaultdict
from intelligence.enrichment import GeoIPEnricher
from dashboard.backend.config_manager import ConfigManager

class GeoFencer:
    """
    Layer 3: Dynamic Geo-Fencing.
    Tracks packet counts per country and triggers blocks if they exceed thresholds.
    """
    def __init__(self, config_path="config/thresholds.yaml"):
        self.enricher = GeoIPEnricher()
        self.config_manager = ConfigManager(config_path)
        
        # Stats
        self.country_stats = defaultdict(int)
        self.last_reset = time.time()
        self.window_size = 60 # seconds

    def process_packet_ip(self, ip_address):
        """Called for every sampled packet to update geo-stats."""
        # Reset window if needed
        if time.time() - self.last_reset > self.window_size:
            self._reset_stats()

        geo_data = self.enricher.enrich_ip(ip_address)
        if not geo_data:
            return None
            
        country = geo_data.get("country", "Unknown")
        self.country_stats[country] += 1
        
        return self._check_threshold(country)

    def _check_threshold(self, country):
        """Checks if a country has exceeded the rate limit."""
        config = self.config_manager.get_config()
        limit = config.get("geoip_limit", 1000)
        
        if self.country_stats[country] > limit:
            return {
                "action": "ban_country",
                "target": country,
                "count": self.country_stats[country],
                "limit": limit
            }
        return None

    def _reset_stats(self):
        self.country_stats.clear()
        self.last_reset = time.time()
