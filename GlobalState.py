import streamlit as st
from RiskEngine import trainRiskModel
from FailSafes import SecurityEngine

@st.cache_resource
def getSharedState():
    """
    Maintains a centralized, cached singleton state across Streamlit pages.
    """
    # Initialize the ML Model and get accuracy score
    model, accuracy = trainRiskModel()
    
    if "shared_state" not in st.session_state:
        st.session_state["shared_state"] = {
            "totalLiquidityPool": 5000000.0,
            "totalPayoutsExecuted": 150000.0,
            "mlModel": model,
            "mlAccuracy": accuracy,
            "security": SecurityEngine(),
            "pendingClaims": [
                {
                    "claimId": "CLM-9001",
                    "timestamp": "2026-10-10 14:30",
                    "farmerName": "Rajesh Patel",
                    "policyId": "FARM101",
                    "amount": 20000,
                    "confidence": 78,
                    "reason": "Medium soil moisture divergence detected"
                }
            ],
            "claimLedger": [
                {
                    "claimId": "CLM-8999",
                    "timestamp": "2026-10-08 11:15",
                    "farmerName": "Ananya Reddy",
                    "policyId": "FARM102",
                    "amount": 15000,
                    "status": "AUTO APPROVED",
                    "confidence": 94,
                    "notes": "Automatic parametric execution via Open-Meteo rainfall trigger"
                }
            ],
            "farmerDatabase": [
                {"farmerId": "FARM101", "name": "Rajesh Patel", "phone": "+919876543212", "lat": 12.9200, "lon": 79.1300, "crop": "Rice / Paddy", "acres": 2.5, "policyValue": 25000},
                {"farmerId": "FARM102", "name": "Ananya Reddy", "phone": "+919811223344", "lat": 13.0827, "lon": 80.2707, "crop": "Wheat", "acres": 4.0, "policyValue": 40000},
                {"farmerId": "FARM103", "name": "Vikram Singh", "phone": "+919811223344", "lat": 11.0168, "lon": 76.9558, "crop": "Maize", "acres": 3.0, "policyValue": 30000},
                {"farmerId": "FARM104", "name": "Meena Devi", "phone": "+919722334455", "lat": 10.7905, "lon": 78.7047, "crop": "Cotton", "acres": 1.5, "policyValue": 15000}
            ]
        }
    
    return st.session_state["shared_state"]