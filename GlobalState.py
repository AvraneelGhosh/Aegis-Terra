import streamlit as st
import pandas as pd
from FailSafes import SecurityEngine
from RiskEngine import trainPredictiveRiskModel

@st.cache_resource
def getSharedState():
    """Centralized global state shared cleanly across all pages and devices."""
    return {
        "security": SecurityEngine(dailyPayoutLimit=400000),
        "mlModel": trainPredictiveRiskModel(),
        "totalLiquidityPool": 5000000.0,
        "totalPayoutsExecuted": 0.0,
        "claimLedger": [
            {"claimId": "CLM8001", "timestamp": "2026-10-06 14:20", "farmerName": "Ramesh Kumar", "policyId": "FARM101", "amount": 25000, "status": "APPROVED", "confidence": 95, "notes": "Auto-approved by risk engine"},
            {"claimId": "CLM8002", "timestamp": "2026-10-07 09:15", "farmerName": "Sita Devi", "policyId": "FARM102", "amount": 40000, "status": "APPROVED", "confidence": 92, "notes": "Auto-approved by risk engine"}
        ],
        "pendingClaims": [
            {"claimId": "CLM8003", "timestamp": "2026-10-07 11:30", "farmerName": "Rajesh Patel", "policyId": "FARM103", "amount": 30000, "confidence": 78, "reason": "Conflict: Rainfall deficit but NDVI greenness remains high"}
        ],
        "farmerDatabase": [
            {"farmerId": "FARM101", "name": "Ramesh Kumar", "phone": "+919876543210", "lat": 12.92, "lon": 79.13, "crop": "Rice / Paddy", "acres": 2.5, "policyValue": 25000},
            {"farmerId": "FARM102", "name": "Sita Devi", "phone": "+919876543211", "lat": 13.08, "lon": 80.27, "crop": "Wheat", "acres": 4.0, "policyValue": 40000},
            {"farmerId": "FARM103", "name": "Rajesh Patel", "phone": "+919876543212", "lat": 12.23, "lon": 79.07, "crop": "Cotton", "acres": 3.0, "policyValue": 30000},
            {"farmerId": "FARM104", "name": "Ananya Reddy", "phone": "+919876543213", "lat": 13.62, "lon": 79.41, "crop": "Maize", "acres": 5.0, "policyValue": 50000}
        ]
    }