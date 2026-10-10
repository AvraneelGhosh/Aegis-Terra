import streamlit as st
import pandas as pd
import time
from datetime import datetime
import sys
import os

# Append parent directory to sys.path so scripts inside /pages can import root modules
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from DataPipeline import fetchWeatherData, generateTelemetryData
from RiskEngine import (
    calculateRiskIndex, 
    generateAiPrecautions, 
    getCompanionAdvisory, 
    queryGenerativeClimateAdvisor
)
from GlobalState import getSharedState

# Page Config styled for Mobile / Low-Tech simulation
st.set_page_config(page_title="Aegis Terra - Farmer Portal", page_icon="🌾", layout="centered")

# Fetch Centralized Shared State across pages/devices
state = getSharedState()

# Initialize Page-Specific Chat History
if 'chatHistory' not in st.session_state:
    st.session_state.chatHistory = []

st.markdown("<h2 style='text-align: center;'>🌾 Aegis Terra Mobile Portal</h2>", unsafe_allow_html=True)

# Top Bar Mode Selector
portalMode = st.radio("Select Portal Action:", ["👤 Existing Farmer Portal", "📝 New Farmer Self-Registration"], horizontal=True)

st.markdown("---")

# ===================================================================
# MODE 1: NEW FARMER SELF-REGISTRATION
# ===================================================================
if portalMode == "📝 New Farmer Self-Registration":
    st.subheader("📝 Register Your Farm for Insurance & Climate AI")
    st.caption("Enroll in automated parametric coverage and proactive climate advisories in under 60 seconds.")

    with st.form("farmerSelfRegForm", clear_on_submit=True):
        regName = st.text_input("Full Name", placeholder="e.g. Ananya Reddy")
        regPhone = st.text_input("Mobile / WhatsApp Number", placeholder="+919876543210")
        
        colA, colB = st.columns(2)
        with colA:
            regCrop = st.selectbox("Crop Type", ["Rice / Paddy", "Wheat", "Maize", "Cotton", "Sugarcane"])
            regAcres = st.number_input("Farm Size (Acres)", min_value=0.5, max_value=50.0, value=2.0, step=0.5)
        with colB:
            regLat = st.number_input("Farm Latitude (GPS)", value=12.9200, format="%.4f")
            regLon = st.number_input("Farm Longitude (GPS)", value=79.1300, format="%.4f")

        estimatedPolicy = int(regAcres * 10000) # ₹10,000 per acre coverage
        st.info(f"💡 **Estimated Policy Coverage:** `₹{estimatedPolicy:,}.00` (Calculated at ₹10,000/acre)")

        btnSubmitReg = st.form_submit_button("🚀 Activate My Policy & Climate Advisor")

        if btnSubmitReg:
            if regName and regPhone:
                newId = f"FARM{101 + len(state['farmerDatabase'])}"
                
                newFarmerObj = {
                    "farmerId": newId,
                    "name": regName.strip(),
                    "phone": regPhone.strip(),
                    "lat": float(regLat),
                    "lon": float(regLon),
                    "crop": regCrop,
                    "acres": float(regAcres),
                    "policyValue": estimatedPolicy
                }

                # Mutate shared central list in-place
                state["farmerDatabase"].append(newFarmerObj)

                st.success(f"🎉 Welcome aboard, {regName}! Policy `{newId}` is active with `₹{estimatedPolicy:,}` coverage.")
                st.toast("Registration complete! Switch to 'Existing Farmer Portal' to view active AI advisories.")
                st.rerun()
            else:
                st.error("Please provide both your Name and Mobile Number.")

# ===================================================================
# MODE 2: EXISTING FARMER PORTAL & AI SUSTAINABILITY ADVISOR
# ===================================================================
else:
    farmerNames = [f["name"] for f in state["farmerDatabase"]]
    selectedFarmer = st.selectbox("👤 Select Your Account:", farmerNames)

    # Clean dictionary lookup
    farmerDetails = next((f for f in state["farmerDatabase"] if f["name"] == selectedFarmer), state["farmerDatabase"][0])

    farmerName = farmerDetails["name"]
    policyId = farmerDetails["farmerId"]
    crop = farmerDetails["crop"]
    acres = float(farmerDetails["acres"])
    policyValue = int(farmerDetails["policyValue"])
    lat = float(farmerDetails["lat"])
    lon = float(farmerDetails["lon"])

    st.info(f"**Policy ID:** `{policyId}` | **Crop:** {crop} ({acres} Acres) | **Coverage:** `₹{policyValue:,}` | **Phone:** {farmerDetails['phone']}")

    # Fetch Real-Time Location Weather Telemetry & Decision Engine
    weatherDf = fetchWeatherData(lat, lon)
    df = generateTelemetryData(weatherDf)
    risk = calculateRiskIndex(df)
    advisory = generateAiPrecautions(risk)
    companionInfo = getCompanionAdvisory(crop)

    # SUB-TABS FOR MOBILE PORTAL FEATURES
    portalTab1, portalTab2, portalTab3 = st.tabs([
        "🌦️ 5-Day Climate Advisor", 
        "💧 Irrigation & Payout", 
        "🌿 Sustainable Companion Advisor"
    ])

    # -------------------------------------------------------------
    # SUB-TAB 1: 5-DAY PROACTIVE CLIMATE INTELLIGENCE
    # -------------------------------------------------------------
    with portalTab1:
        st.subheader("🤖 Aegis Terra 5-Day Climate Outlook")
        st.caption("Proactive AI advisories synthesized from hyper-local meteorological telemetry.")

        colP1, colP2 = st.columns(2)
        colP1.metric("30-Day Rainfall Trend", f"{risk['totalRain30d']} mm")
        colP2.metric("Soil Moisture Index", f"{risk['avgSoil']}%", delta="Root-Zone Level")

        st.markdown(f"""
        ### 📋 Active Advisory Bulletin
        - **Risk Status:** `{advisory['level']}`
        - **Recommended Action:** {advisory['action']}
        """)

        st.markdown("#### 📅 Next 5-Day Meteorological Forecast Preview")
        forecastPreview = df[['date', 'tempMax', 'rainfall', 'soilMoisturePercent']].tail(5).copy()
        forecastPreview.columns = ['Date', 'Max Temp (°C)', 'Rainfall (mm)', 'Est. Soil Moisture (%)']
        st.dataframe(forecastPreview, use_container_width=True)

    # -------------------------------------------------------------
    # SUB-TAB 2: INTELLIGENT IRRIGATION & PARAMETRIC PAYOUT
    # -------------------------------------------------------------
    with portalTab2:
        st.subheader("💧 Intelligent Irrigation & Claim Settlement")
        
        # Irrigation Decision Logic
        recentRain = float(df['rainfall'].tail(3).sum())
        soilMoist = float(df['soilMoisturePercent'].iloc[-1])
        
        if recentRain > 15.0 or soilMoist > 60:
            st.success("🌧️ **Irrigation Advisory: POSTPONE WATERING**\n\nRecent precipitation is sufficient in your root zone. Skipping unnecessary irrigation conserves valuable groundwater and pump energy.")
        else:
            st.warning("☀️ **Irrigation Advisory: SCHEDULE RECOMMENDED**\n\nSoil moisture is trending low due to high ambient temperatures. Consider light morning or evening micro-irrigation.")

        st.markdown("---")
        st.subheader("🚨 Parametric Insurance Alert")

        with st.container():
            st.warning(f"""
            **EARLY WARNING DETECTED**  
            📅 **Date:** {datetime.now().strftime('%d %b %Y')}  
            🌾 **Crop:** {crop}  
            📊 **Composite Risk Score:** `{risk['compositeRisk']}/1.0`  
            
            Your parametric policy qualifies for an advance financial support payout of **₹{policyValue:,}.00**.
            """)

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
                        state["claimLedger"].append(newRecord)
                        
                        responseMsg = f"🎉 **Payout Approved!**\n\n**₹{policyValue:,}.00** transferred via Instant Settlement. Txn ID: `TXN-{int(time.time())}`"
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

    # -------------------------------------------------------------
    # SUB-TAB 3: SUSTAINABLE CROP COMPANION ADVISOR
    # -------------------------------------------------------------
    with portalTab3:
        st.subheader("🌿 Sustainable Crop Companion & Intercropping Advisor")
        st.caption("Science-backed companion recommendations curated from agricultural research extension guides.")

        st.info(f"""
        **Main Registered Crop:** `{crop}`  
        **Recommended Intercropping / Companion Match:** `{companionInfo['companion']}`  
        
        **Potential Sustainability Benefits:**  
        {companionInfo['benefits']}  
        
        **Agronomic Verification Conditions:**  
        {companionInfo['conditions']}
        """)

    st.markdown("---")
    st.markdown("#### 💬 Ask the Hybrid AI Sustainability Advisor")

    for message in st.session_state.chatHistory:
        with st.chat_message(message["role"]):
            st.markdown(message["content"])

    userPrompt = st.chat_input("Ask about irrigation, companion crops, or reply YES to claim...")
    if userPrompt:
        st.session_state.chatHistory.append({"role": "user", "content": userPrompt})
        cleanPrompt = userPrompt.strip().upper()
        
        # Handle quick payout command
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
                    state["claimLedger"].append(newRecord)
                    st.session_state.chatHistory.append({
                        "role": "assistant", 
                        "content": f"🎉 **Payout Approved!** **₹{policyValue:,}.00** transferred to linked bank account."
                    })
                    st.rerun()
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
                st.rerun()
        else:
            # Call Generative AI Advisor with structured telemetry ground-truth
            aiResponse = queryGenerativeClimateAdvisor(
                farmerName=farmerName,
                crop=crop,
                acres=acres,
                riskData=risk,
                advisoryData=advisory,
                companionData=companionInfo,
                userQuery=userPrompt
            )
            st.session_state.chatHistory.append({
                "role": "assistant", 
                "content": aiResponse
            })
            st.rerun()