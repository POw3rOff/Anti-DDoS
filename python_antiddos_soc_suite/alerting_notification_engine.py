import logging

class AlertingNotificationEngine:
    def __init__(self):
        logging.basicConfig(format='%(asctime)s - %(levelname)s - %(message)s', level=logging.INFO)
        self.logger = logging.getLogger("AlertEngine")

    def send_alert(self, level, title, message, channels=['log']):
        """
        Sends an alert through configured channels.
        """
        payload = {
            'level': level,
            'title': title,
            'message': message
        }

        if 'log' in channels:
            self._send_to_log(payload)
        if 'email' in channels:
            self._send_email(payload)
        if 'slack' in channels:
            self._send_slack(payload)

    def _send_to_log(self, payload):
        self.logger.info(f"ALERT [{payload['level']}] {payload['title']}: {payload['message']}")

    def _send_email(self, payload):
        # Simulation
        pass

    def _send_slack(self, payload):
        # Simulation
        pass

if __name__ == "__main__":
    alerter = AlertingNotificationEngine()
    alerter.send_alert("CRITICAL", "DDoS Attack Detected", "Traffic spike on /api/login", channels=['log', 'slack'])