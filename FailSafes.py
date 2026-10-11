import pandas as pd
import numpy as np

class SecurityEngine:
    def __init__(self):
        self.circuitBreakerTripped = False
        self.dailyPayoutCap = 400000.0  # ₹4,00,000 daily limit
        self.currentDailyPayouts = 0.0
        self.processedClaimIds = set()   # Prevents duplicate claim execution

    def reset(self):
        """Resets the circuit breaker, daily payouts, and processed claims for live demos."""
        self.circuitBreakerTripped = False
        self.currentDailyPayouts = 0.0
        self.processedClaimIds.clear()

    def validateClaim(self, df, riskData):
        """
        Validates environmental data anomalies and returns confidence score (0-100%).
        """
        flags = []
        confidence = 100
        
        if riskData['avgTemp'] > 45:
            flags.append("Extreme temperature outlier detected")
            confidence -= 15
            
        if riskData['totalRain30d'] < 0:
            flags.append("Negative rainfall anomaly detected")
            confidence -= 30
            
        if riskData['avgSoil'] < 5 and riskData['totalRain30d'] > 100:
            flags.append("Divergence between soil moisture and rainfall")
            confidence -= 20

        claimStatus = "VALIDATED" if confidence >= 90 else ("FLAGGED FOR AUDIT" if confidence >= 70 else "REJECTED")
        return confidence, claimStatus, flags

    def processPayout(self, claimId, amount):
        """
        Validates daily limits, circuit breaker, positive amounts, and duplicate claims.
        Routes every payout approval through this single security gateway.
        """
        if self.circuitBreakerTripped:
            return False, "CIRCUIT BREAKER ACTIVE: System frozen due to anomaly threshold."

        if amount <= 0:
            return False, "INVALID AMOUNT: Payout amount must be greater than ₹0."

        if claimId in self.processedClaimIds:
            return False, f"DUPLICATE ERROR: Claim ID {claimId} has already been processed."

        if (self.currentDailyPayouts + amount) > self.dailyPayoutCap:
            self.circuitBreakerTripped = True
            return False, f"CIRCUIT BREAKER TRIPPED: Payout request exceeds daily liquidity safety cap (₹{self.dailyPayoutCap:,.0f})."

        # Execute Payout Safely
        self.currentDailyPayouts += amount
        self.processedClaimIds.add(claimId)
        return True, "Payout successfully processed and verified."