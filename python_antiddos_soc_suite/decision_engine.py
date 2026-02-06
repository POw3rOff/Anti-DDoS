class DecisionEngine:
    def __init__(self):
        self.policies = {
            'BLOCK': 80,
            'CAPTCHA': 50,
            'RATE_LIMIT': 30
        }

    def decide(self, ip, risk_score):
        """
        Decides the mitigation action based on risk score.
        """
        if risk_score >= self.policies['BLOCK']:
            return 'BLOCK', f"Risk score {risk_score:.2f} exceeds critical threshold"
        elif risk_score >= self.policies['CAPTCHA']:
            return 'CHALLENGE', f"Risk score {risk_score:.2f} requires verification"
        elif risk_score >= self.policies['RATE_LIMIT']:
            return 'THROTTLE', f"Risk score {risk_score:.2f} requires throttling"
        else:
            return 'MONITOR', "Score within normal limits"

if __name__ == "__main__":
    decider = DecisionEngine()
    print(decider.decide('1.2.3.4', 90))
    print(decider.decide('1.2.3.4', 40))