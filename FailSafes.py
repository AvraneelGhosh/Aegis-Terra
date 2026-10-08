class SecurityEngine:
    def __init__(self, dailyPayoutLimit=5000):
        self.dailyPayoutLimit = dailyPayoutLimit
        self.currentDailyPayouts = 0
        self.circuitBreakerTripped = False

    def validateClaim(self, weatherData, riskMetrics):
        """
        Cross-validates multi-source metrics and assigns a Confidence Score (0-100%).
        Failsafe Rule: Catches sensor glitches or conflicting satellite data.
        """
        confidence = 100
        flags = []

        # Check 1: Outlier Temperature detection (Sensor glitch detection)
        latestTemp = weatherData['tempMax'].iloc[-1]
        if latestTemp > 50 or latestTemp < 0:
            confidence -= 60
            flags.append("Corrupted Temperature Sensor Payload Detected")

        # Check 2: Multi-source validation (Rainfall vs NDVI conflict)
        if riskMetrics['totalRain30d'] < 5 and riskMetrics['avgNdvi'] > 0.75:
            confidence -= 40
            flags.append("Conflict: Severe rainfall deficit but satellite shows dense green vegetation")

        # Determine Route based on Confidence Score
        if confidence >= 90:
            status = "AUTO APPROVED"
        elif confidence >= 70:
            status = "PENDING AUDIT"
        else:
            status = "REJECTED FLAGGED"

        return confidence, status, flags

    def processPayout(self, amount):
        """Executes payout through Circuit Breaker protection."""
        if self.circuitBreakerTripped:
            return False, "CIRCUIT BREAKER ACTIVE: System frozen due to anomaly threshold."

        if (self.currentDailyPayouts + amount) > self.dailyPayoutLimit:
            self.circuitBreakerTripped = True
            return False, "CIRCUIT BREAKER TRIPPED: Payout request exceeds daily liquidity safety cap ($5,000)."

        self.currentDailyPayouts += amount
        return True, f"Payout of ${amount} approved. Remaining daily pool: ${self.dailyPayoutLimit - self.currentDailyPayouts}"