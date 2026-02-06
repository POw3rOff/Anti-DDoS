import ipaddress

class SpatialFeatureExtractor:
    def __init__(self):
        pass

    def calculate_pop_synchronization(self, pop_reports):
        """
        Detects if multiple PoPs are reporting the same target simultaneously.
        """
        if not pop_reports: return 0.0

        unique_pops = set(r.get('pop_id') for r in pop_reports if r.get('pop_id'))
        total_pops_in_network = 10 # Configurable

        ratio = len(unique_pops) / total_pops_in_network
        return min(1.0, ratio)

    def calculate_subnet_proximity(self, ip_list):
        """
        Detects if a high percentage of IPs belong to the same /24 subnet.
        High proximity suggests a targeted campaign from a specific network range.
        """
        if not ip_list: return 0.0

        subnets = defaultdict(int)
        for ip in ip_list:
            try:
                # Group by /24
                network = str(ipaddress.ip_network(f"{ip}/24", strict=False).network_address)
                subnets[network] += 1
            except Exception:
                continue

        if not subnets: return 0.0
        
        max_overlap = max(subnets.values())
        return max_overlap / len(ip_list)

from collections import defaultdict
