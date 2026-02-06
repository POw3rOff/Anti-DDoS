#!/usr/bin/env python3
import json
import time

class SocDashboardBackend:
    """
    Backend simples para exportar métricas em formato JSON consumível por dashboards.
    """
    def __init__(self, output_file="soc_dashboard_metrics.json"):
        self.output_file = output_file

    def update_dashboard(self, stats):
        """
        stats: dict contendo {global_metrics, incidents, recent_alerts}
        """
        dashboard_data = {
            "generated_at": time.time(),
            "system_health": "Operational",
            "active_incidents": stats.get("active_incidents_count", 0),
            "mitigated_attacks": stats.get("mitigated_count", 0),
            "top_attackers": stats.get("top_attackers", []),
            "throughput": stats.get("throughput", {})
        }

        try:
            with open(self.output_file, "w") as f:
                json.dump(dashboard_data, f, indent=2)
        except Exception as e:
            print(f"[DASHBOARD] Error writing JSON: {e}")
