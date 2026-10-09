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
from App import getSharedState

# Page Config styled for Mobile / Low-Tech simulation
st.set_page_config(page_title="Aegis Terra - Farmer Portal", page_icon="🌾", layout="centered")

# Fetch Shared Global Cache across all devices
state = getSharedState()

# Initialize Page-Specific Chat History (Isolated to session)
if 'chatHistory' not in st.session_state:
    st.session_state.chatHistory = []

st.markdown("<h2 style='text-align: center;'>🌾 Aegis Terra Mobile Portal</h2>", unsafe_allow_html=True)

# Top Bar Mode Selector
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
                newId = f"FARM{101 + len(state['farmerDatabase'])}"
                
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

                # Save directly into global shared memory
                state["farmerDatabase"] = pd.concat([
                    state["farmerDatabase"], 
                    pd.DataFrame([newFarmerObj])
                ], ignore_index=True)

                st.success(f"🎉 Welcome aboard, {regName}! Your policy `{newId}` is now active with `${estimatedPolicy}` coverage.")
                st.toast("Registration complete! Switch to 'Existing Farmer Portal' to view active alerts.")
                st.rerun()
            else:
                st.error("Please provide both your Name and Mobile Number.")

# -------------------------------------------------------------------
# MODE 2: EXISTING FARMER PORTAL & CLAIM SYSTEM
# -------------------------------------------------------------------
else:
    farmerList = state["farmerDatabase"]["name"].tolist()
    selectedFarmer = st.selectbox("👤 Select Your Account:", farmerList)

    farmerDetails = state["farmerDatabase"][
        state["farmerDatabase"]["name"] == selectedFarmer
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
            
            confidence, claimStatus, flags = state["security"].validateClaim(df, risk)
            
            if confidence >= 90:
                success, msg = state["security"].processPayout(policyValue)
                if success:
                    state["totalPayoutsExecuted"] += policyValue
                    
                    newRecord = {
                        "claimId": f"CLM{8001 + len(state['claimLedger'])}",
                        "timestamp": datetime.now().strftime("%Y-%m-%d %H:%M"),
                        "farmerName": farmerName,
                        "policyId": policyId,
                        "amount": policyValue,
                        "status": "AUTO APPROVED",
                        "confidence": confidence,
                        "notes": "Claimed via Mobile Portal"
                    }
                    state["claimLedger"] = pd.concat([state["claimLedger"], pd.DataFrame([newRecord])], ignore_index=True)
                    
                    responseMsg = f"🎉 **Payout Approved!**\n\n**${policyValue}.00** transferred via Instant Settlement. Txn ID: `TXN-{int(time.time())}`"
                    st.session_state.chatHistory.append({"role": "assistant", "content": responseMsg})
                    st.rerun()
                else:
                    st.session_state.chatHistory.append({"role": "assistant", "content": f"🚨 Payout Error: {msg}"})
            else:
                newPending = {
                    "claimId": f"CLM{8001 + len(state['claimLedger']) + len(state['pendingClaims'])}",
                    "timestamp": datetime.now().strftime("%Y-%m-%d %H:%M"),
                    "farmerName": farmerName,
                    "policyId": policyId,
                    "amount": policyValue,
                    "confidence": confidence,
                    "reason": ", ".join(flags) if flags else "Low confidence score evaluation"
                }
                state["pendingClaims"].append(newPending)
                responseMsg = f"⏳ **Claim Flagged for Review**\n\nReason: {', '.join(flags)}. Sent to Auditor queue."
                st.session_state.chatHistory.append({"role": "assistant", "content": responseMsg})
                st.rerun()

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
            confidence, claimStatus, flags = state["security"].validateClaim(df, risk)
            if confidence >= 90:
                success, msg = state["security"].processPayout(policyValue)
                if success:
                    state["totalPayoutsExecuted"] += policyValue
                    newRecord = {
                        "claimId": f"CLM{8001 + len(state['claimLedger'])}",
                        "timestamp": datetime.now().strftime("%Y-%m-%d %H:%M"),
                        "farmerName": farmerName,
                        "policyId": policyId,
                        "amount": policyValue,
                        "status": "AUTO APPROVED",
                        "confidence": confidence,
                        "notes": "Claimed via Chat Assistant"
                    }
                    state["claimLedger"] = pd.concat([state["claimLedger"], pd.DataFrame([newRecord])], ignore_index=True)
                    st.session_state.chatHistory.append({
                        "role": "assistant", 
                        "content": f"🎉 **Payout Approved!** **${policyValue}.00** transferred to linked bank account."
                    })
            else:
                newPending = {
                    "claimId": f"CLM{8001 + len(state['claimLedger']) + len(state['pendingClaims'])}",
                    "timestamp": datetime.now().strftime("%Y-%m-%d %H:%M"),
                    "farmerName": farmerName,
                    "policyId": policyId,
                    "amount": policyValue,
                    "confidence": confidence,
                    "reason": ", ".join(flags) if flags else "Low confidence score evaluation"
                }
                state["pendingClaims"].append(newPending)
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