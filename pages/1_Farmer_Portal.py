import streamlit as st
import pandas as pd
import time
from datetime import datetime
import sys
import os

# Append parent directory to sys.path so scripts inside /pages can import root modules
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from DataPipeline import fetchWeatherData, generateTelemetryData
from RiskEngine import calculateRiskIndex, generateAiPrecautions
from FailSafes import SecurityEngine

# Page Config styled for Mobile / Low-Tech simulation
st.set_page_config(page_title="Aegis Terra - Farmer Portal", page_icon="🌾", layout="centered")

# Initialize Shared Session States if accessed standalone
if 'farmerDatabase' not in st.session_state:
    st.session_state.farmerDatabase = pd.DataFrame([
        {"farmerId": "FARM101", "name": "Ramesh Kumar", "phone": "+919876543210", "lat": 12.92, "lon": 79.13, "crop": "Rice / Paddy", "acres": 2.5, "policyValue": 250},
        {"farmerId": "FARM102", "name": "Sita Devi", "phone": "+919876543211", "lat": 13.08, "lon": 80.27, "crop": "Wheat", "acres": 4.0, "policyValue": 400},
        {"farmerId": "FARM103", "name": "Rajesh Patel", "phone": "+919876543212", "lat": 12.23, "lon": 79.07, "crop": "Cotton", "acres": 3.0, "policyValue": 300}
    ])

if 'totalPayoutsExecuted' not in st.session_state:
    st.session_state.totalPayoutsExecuted = 0.0

if 'security' not in st.session_state:
    st.session_state.security = SecurityEngine(dailyPayoutLimit=5000)

if 'claimLedger' not in st.session_state:
    st.session_state.claimLedger = pd.DataFrame()

if 'chatHistory' not in st.session_state:
    st.session_state.chatHistory = []

st.markdown("<h2 style='text-align: center;'>🌾 Aegis Terra Mobile Portal</h2>", unsafe_allow_html=True)

# Top Bar Mode Selector: Existing Farmer Login vs. New Registration
portalMode = st.radio("Select Portal Action:", ["👤 Existing Farmer Portal", "📝 New Farmer Self-Registration"], horizontal=True)

st.markdown("---")

# -------------------------------------------------------------------
# MODE 1: NEW FARMER SELF-REGISTRATION
# -------------------------------------------------------------------
if portalMode == "📝 New Farmer Self-Registration":
    st.subheader("📝 Register Your Farm for Insurance")
    st.caption("Enroll in automated parametric drought coverage in under 60 seconds.")

    with st.form("farmerSelfRegForm", clear_on_submit=True):
        regName = st.text_input("Full Name", placeholder="e.g. Ananya Reddy")
        regPhone = st.text_input("Mobile / WhatsApp Number", placeholder="+919876543210")
        
        colA, colB = st.columns(2)
        with colA:
            regCrop = st.selectbox("Crop Type", ["Rice / Paddy", "Wheat", "Maize", "Cotton", "Sugarcane"])
            regAcres = st.number_input("Farm Size (Acres)", min_value=0.5, max_value=50.0, value=2.0, step=0.5)
        with colB:
            regLat = st.number_input("Farm Latitude", value=12.9200, format="%.4f")
            regLon = st.number_input("Farm Longitude", value=79.1300, format="%.4f")

        estimatedPolicy = int(regAcres * 100)
        st.info(f"💡 **Estimated Policy Coverage:** `${estimatedPolicy}.00` (Calculated at $100/acre)")

        btnSubmitReg = st.form_submit_button("🚀 Activate My Insurance Policy")

        if btnSubmitReg:
            if regName and regPhone:
                newId = f"FARM{101 + len(st.session_state.farmerDatabase)}"
                
                newFarmerObj = {
                    "farmerId": newId,
                    "name": regName,
                    "phone": regPhone,
                    "lat": regLat,
                    "lon": regLon,
                    "crop": regCrop,
                    "acres": regAcres,
                    "policyValue": estimatedPolicy
                }

                # Save directly into global system memory
                st.session_state.farmerDatabase = pd.concat([
                    st.session_state.farmerDatabase, 
                    pd.DataFrame([newFarmerObj])
                ], ignore_index=True)

                st.success(f"🎉 Welcome aboard, {regName}! Your policy `{newId}` is now active with `${estimatedPolicy}` coverage.")
                st.toast("Registration complete! You can now switch to 'Existing Farmer Portal' tab to view alerts.")
            else:
                st.error("Please provide both your Name and Mobile Number.")

# -------------------------------------------------------------------
# MODE 2: EXISTING FARMER PORTAL & CLAIM SYSTEM
# -------------------------------------------------------------------
else:
    farmerList = st.session_state.farmerDatabase["name"].tolist()
    selectedFarmer = st.selectbox("👤 Select Your Account:", farmerList)

    farmerDetails = st.session_state.farmerDatabase[
        st.session_state.farmerDatabase["name"] == selectedFarmer
    ].iloc[0]

    farmerName = farmerDetails["name"]
    policyId = farmerDetails["farmerId"]
    crop = farmerDetails["crop"]
    policyValue = int(farmerDetails["policyValue"])
    lat = farmerDetails["lat"]
    lon = farmerDetails["lon"]

    st.info(f"**Policy ID:** `{policyId}` | **Crop:** {crop} | **Coverage:** `${policyValue}` | **Phone:** {farmerDetails['phone']}")

    # Fetch Real-Time Telemetry
    weatherDf = fetchWeatherData(lat, lon)
    df = generateTelemetryData(weatherDf)
    risk = calculateRiskIndex(df)
    advisory = generateAiPrecautions(risk)

    st.markdown("---")
    st.subheader("🚨 Active Regional Weather Alert")

    # Alert Banner
    with st.container():
        st.warning(f"""
        **EARLY WARNING ALERT DETECTED**  
        📅 **Date:** {datetime.now().strftime('%d %b %Y')}  
        🌾 **Crop:** {crop}  
        📊 **Risk Score:** `{risk['compositeRisk']}/1.0` ({advisory['level']})  
        
        {advisory['action']}  
        Your parametric policy qualifies for an advance payout of **${policyValue}.00**.
        """)

    # Quick Action Buttons
    btnCol1, btnCol2 = st.columns(2)

    with btnCol1:
        if st.button("✅ Request Instant Payout", use_container_width=True):
            st.session_state.chatHistory.append({"role": "user", "content": "YES"})
            
            confidence, claimStatus, flags = st.session_state.security.validateClaim(df, risk)
            
            if confidence >= 90:
                success, msg = st.session_state.security.processPayout(policyValue)
                if success:
                    st.session_state.totalPayoutsExecuted += policyValue
                    
                    newRecord = {
                        "claimId": f"CLM{8001 + len(st.session_state.claimLedger)}",
                        "timestamp": datetime.now().strftime("%Y-%m-%d %H:%M"),
                        "farmerName": farmerName,
                        "policyId": policyId,
                        "amount": policyValue,
                        "status": "AUTO APPROVED",
                        "confidence": confidence,
                        "notes": "Claimed via Farmer Mobile Self-Portal"
                    }
                    st.session_state.claimLedger = pd.concat([st.session_state.claimLedger, pd.DataFrame([newRecord])], ignore_index=True)
                    
                    responseMsg = f"🎉 **Payout Approved!**\n\n**${policyValue}.00** transferred via Instant Settlement. Txn ID: `TXN-{int(time.time())}`"
                    st.session_state.chatHistory.append({"role": "assistant", "content": responseMsg})
                else:
                    st.session_state.chatHistory.append({"role": "assistant", "content": f"🚨 Payout Error: {msg}"})
            else:
                responseMsg = f"⏳ **Claim Flagged for Review**\n\nReason: {', '.join(flags)}. Sent to Auditor queue."
                st.session_state.chatHistory.append({"role": "assistant", "content": responseMsg})

    with btnCol2:
        if st.button("❌ Decline & Reserve Funds", use_container_width=True):
            st.session_state.chatHistory.append({"role": "user", "content": "NO"})
            st.session_state.chatHistory.append({"role": "assistant", "content": "ℹ️ Request acknowledged. Policy reserves remain active for future risks."})

    st.markdown("---")
    st.markdown("#### 💬 Automated Assistant")

    for message in st.session_state.chatHistory:
        with st.chat_message(message["role"]):
            st.markdown(message["content"])

    userPrompt = st.chat_input("Type 'YES' to claim or 'NO' to decline...")
    if userPrompt:
        st.session_state.chatHistory.append({"role": "user", "content": userPrompt})
        cleanPrompt = userPrompt.strip().upper()
        
        if cleanPrompt in ["YES", "Y", "CLAIM"]:
            confidence, claimStatus, flags = st.session_state.security.validateClaim(df, risk)
            if confidence >= 90:
                st.session_state.totalPayoutsExecuted += policyValue
                st.session_state.chatHistory.append({
                    "role": "assistant", 
                    "content": f"🎉 **Payout Approved!** **${policyValue}.00** transferred to linked bank account."
                })
            else:
                st.session_state.chatHistory.append({
                    "role": "assistant", 
                    "content": "⏳ Claim Flagged for Auditor Review."
                })
        elif cleanPrompt in ["NO", "N", "DECLINE"]:
            st.session_state.chatHistory.append({
                "role": "assistant", 
                "content": "ℹ️ Policy liquidity preserved."
            })
        else:
            st.session_state.chatHistory.append({
                "role": "assistant", 
                "content": f"🤖 Reply **YES** to claim **${policyValue}** or **NO** to save reserves."
            })
        st.rerun()