import pandas as pd
import numpy as np

class SecurityEngine:
    def __init__(self):
        self.circuitBreakerTripped = False
        self.dailyPayoutCap = 400000.0  # ₹4,00,000 daily limit
        self.currentDailyPayouts = 0.0

    def validateClaim(self, df, riskData):
        """
        Validates environmental data anomalies and returns confidence score (0-100%).
        """
        flags = []
        confidence = 100
        
        # Check temperature anomaly
        if riskData['avgTemp'] > 45:
            flags.append("Extreme temperature outlier detected")
            confidence -= 15
            
        # Check rainfall data consistency
        if riskData['totalRain30d'] < 0:
            flags.append("Negative rainfall anomaly detected")
            confidence -= 30
            
        # Check soil moisture consistency
        if riskData['avgSoil'] < 5 and riskData['totalRain30d'] > 100:
            flags.append("Divergence between soil moisture and rainfall")
            confidence -= 20

        claimStatus = "VALIDATED" if confidence >= 90 else ("FLAGGED FOR AUDIT" if confidence >= 70 else "REJECTED")
        return confidence, claimStatus, flags

    def processPayout(self, amount):
        """
        Validates daily limits and circuit breaker before executing payout.
        """
        if self.circuitBreakerTripped:
            return False, "CIRCUIT BREAKER TRIPPED: All automated payouts are currently frozen by system administrator."

        if amount <= 0:
            return False, "INVALID AMOUNT: Payout amount must be greater than ₹0."

        if (self.currentDailyPayouts + amount) > self.dailyPayoutCap:
            self.circuitBreakerTripped = True
            return False, f"CIRCUIT BREAKER TRIPPED: Payout request exceeds daily liquidity safety cap (₹{self.dailyPayoutCap:,.0f})."

        # Execute Payout
        self.currentDailyPayouts += amount
        return True, "Payout successfully processed."