# Save as: pages/1_Farmer_Portal.py
import streamlit as st
import pandas as pd
from datetime import datetime

st.set_page_config(page_title="Aegis Terra - Farmer Portal", page_icon="🌾", layout="centered")

# Access shared session state from main App.py
if 'farmerDatabase' not in st.session_state:
    st.warning("⚠️ Please open the main Insurer Command Center first to initialize system state.")
    st.stop()

st.title("🌾 Aegis Terra - Farmer Mobile Portal")
st.caption("Free, low-bandwidth portal for smallholder farmers")

# Farmer Selector
farmerNames = st.session_state.farmerDatabase["name"].tolist()
selectedFarmer = st.selectbox("👤 Select Your Farmer Account:", farmerNames)

farmerRow = st.session_state.farmerDatabase[
    st.session_state.farmerDatabase["name"] == selectedFarmer
].iloc[0]

st.info(f"**Policy ID:** `{farmerRow['farmerId']}` | **Crop:** {farmerRow['crop']} | **Coverage:** `${farmerRow['policyValue']}`")

st.markdown("---")
st.subheader("🚨 Active Regional Weather Alerts")

# Simulated Active Alert
st.warning(f"⚠️ **High Drought Risk Detected in Your Sector**\n\n"
           f"Your parametric policy permits an immediate advance payout of **${farmerRow['policyValue']}**.")

col1, col2 = st.columns(2)

with col1:
    if st.button("✅ Request Instant Payout ($" + str(farmerRow['policyValue']) + ")", use_container_width=True):
        st.session_state.totalPayoutsExecuted += farmerRow['policyValue']
        
        # Add entry directly to shared Ledger
        newClaim = {
            "claimId": f"CLM{8001 + len(st.session_state.claimLedger)}",
            "timestamp": datetime.now().strftime("%Y-%m-%d %H:%M"),
            "farmerName": farmerRow['name'],
            "policyId": farmerRow['farmerId'],
            "amount": farmerRow['policyValue'],
            "status": "AUTO APPROVED",
            "confidence": 94,
            "notes": "Claimed via Farmer Web Portal"
        }
        st.session_state.claimLedger = pd.concat([st.session_state.claimLedger, pd.DataFrame([newClaim])], ignore_index=True)
        st.success(f"🎉 Payout of ${farmerRow['policyValue']} Approved! Funds transferred to account.")

with col2:
    if st.button("❌ Save Policy Reserves", use_container_width=True):
        st.info("Request acknowledged. Policy coverage remains active.")

st.markdown("---")
st.subheader("📜 Your Policy Claim History")
farmerLedger = st.session_state.claimLedger[st.session_state.claimLedger["farmerName"] == selectedFarmer]
if len(farmerLedger) > 0:
    st.dataframe(farmerLedger[["timestamp", "claimId", "amount", "status"]], use_container_width=True)
else:
    st.write("No past payouts recorded.")