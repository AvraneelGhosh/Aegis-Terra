import streamlit as st
import pandas as pd
from datetime import datetime

from DataPipeline import fetchWeatherData, generateTelemetryData
from RiskEngine import (
    calculateRiskIndex, 
    generateAiPrecautions, 
    getCompanionAdvisory, 
    queryGenerativeClimateAdvisor
)
from GlobalState import getSharedState

# Page Configuration
st.set_page_config(page_title="Aegis Terra - Farmer Portal", layout="wide", page_icon="🌾")

st.title("🌾 Aegis Terra: Farmer Self-Service Portal")
st.caption("Real-time parametric policy tracking, micro-climate telemetry, and instant claim execution.")

# Fetch Centralized Shared State
state = getSharedState()

# 15 Most Sown Crops in India
CROP_LIST = [
    "Rice / Paddy", "Wheat", "Maize (Corn)", "Bajra (Pearl Millet)", 
    "Jowar (Sorghum)", "Ragi (Finger Millet)", "Pulses (Gram / Tur / Lentils)", 
    "Soybean", "Groundnut (Peanut)", "Mustard (Rapeseed)", "Sugarcane", 
    "Cotton", "Jute", "Tea", "Coffee"
]

# Sidebar Selection
st.sidebar.subheader("👤 Active Farmer Account")
farmerList = [f["name"] for f in state["farmerDatabase"]]
selectedFarmerName = st.sidebar.selectbox("Select Your Profile", farmerList)

farmerDetails = next((f for f in state["farmerDatabase"] if f["name"] == selectedFarmerName), state["farmerDatabase"][0])

if st.sidebar.button("🔄 Refresh Telemetry Data", use_container_width=True):
    st.rerun()

st.sidebar.markdown("---")
st.sidebar.info("💡 **Farmer Assistance:**\n\nParametric insurance automatically monitors weather and soil indices to disburse funds without manual paperwork or delays.")

# Navigation Tabs within Farmer Portal
portalTab1, portalTab2, portalTab3 = st.tabs([
    "📊 My Active Policy & Telemetry", 
    "🌿 Companion Advisory & AI Assistant",
    "📝 Register New Field / Policy"
])

# -------------------------------------------------------------------
# TAB 1: MY ACTIVE POLICY & TELEMETRY
# -------------------------------------------------------------------
with portalTab1:
    st.subheader(f"Policy Dashboard: {farmerDetails['name']} ({farmerDetails['farmerId']})")
    
    lat = float(farmerDetails["lat"])
    lon = float(farmerDetails["lon"])
    crop = farmerDetails["crop"]
    policyValue = int(farmerDetails["policyValue"])
    acres = float(farmerDetails["acres"])
    
    # Fetch Live or Fallback Telemetry Data
    weatherDf = fetchWeatherData(lat, lon)
    df = generateTelemetryData(weatherDf)
    dataSourceStatus = df["sourceStatus"].iloc[0]
    
    risk = calculateRiskIndex(df)
    advisory = generateAiPrecautions(risk)
    
    # Overview Metrics
    col1, col2, col3, col4 = st.columns(4)
    col1.metric("Policy ID", farmerDetails["farmerId"])
    col2.metric("Covered Crop", crop)
    col3.metric("Land Area", f"{acres} Acres")
    col4.metric("Max Coverage Value", f"₹{policyValue:,}")

    st.markdown("---")

    mCol1, mCol2 = st.columns([1, 1])

    with mCol1:
        st.subheader("🌡️ Micro-Climate Telemetry")
        st.markdown(f"**Data Lineage Source:** `{dataSourceStatus}`")
        st.write(f"**30-Day Total Rainfall:** `{risk['totalRain30d']} mm`")
        st.write(f"**Average Max Temperature:** `{risk['avgTemp']} °C`")
        st.write(f"**Average Soil Moisture:** `{risk['avgSoil']}%` (Derived)")
        st.write(f"**Satellite NDVI Index:** `{risk['avgNdvi']}` (Simulated)")
        st.write(f"**Composite Drought Risk Score:** `{risk['compositeRisk']} / 1.0`")
        
        with st.container(border=True):
            st.markdown(f"**Assessment Status:** {advisory['level']}")
            st.markdown(f"**Recommended Action:** {advisory['action']}")

    with mCol2:
        st.subheader("⚡ Parametric Payout Qualification")
        
        if risk['compositeRisk'] >= 0.4:
            payoutEligibleAmount = int(policyValue * 0.5)
            st.error(f"⚠️ **Parametric Threshold Breached!**")
            st.markdown(f"Your farm has experienced climate stress exceeding normal historical bounds. You qualify for an advance parametric payout of **₹{payoutEligibleAmount:,}**.")
            
            btnCol1, btnCol2 = st.columns(2)
            with btnCol1:
                if st.button("✅ Request Instant Payout", use_container_width=True):
                    success, failMsg = state["security"].processPayout(payoutEligibleAmount)
                    if success:
                        state["totalPayoutsExecuted"] += payoutEligibleAmount
                        newClaim = {
                            "claimId": f"CLM-{1000 + len(state['claimLedger'])}",
                            "timestamp": datetime.now().strftime("%Y-%m-%d %H:%M"),
                            "farmerName": farmerDetails["name"],
                            "policyId": farmerDetails["farmerId"],
                            "amount": payoutEligibleAmount,
                            "status": "AUTO APPROVED",
                            "confidence": 95,
                            "notes": "Automated parametric execution via mobile portal trigger"
                        }
                        state["claimLedger"].append(newClaim)
                        st.success("🎉 Payout processed successfully! Funds transferred to registered bank account.")
                        st.rerun()
                    else:
                        st.error(f"🚨 Payout Blocked: {failMsg}")
            with btnCol2:
                if st.button("❌ Hold Funds in Reserve", use_container_width=True):
                    st.info("Payout request deferred. Funds remain secured in escrow.")
        else:
            st.success("🟢 **Optimal Growing Conditions**")
            st.markdown("Your farm's 30-day weather and soil metrics are well within safe thresholds. No parametric triggers activated.")

# -------------------------------------------------------------------
# TAB 2: COMPANION ADVISORY & AI ASSISTANT
# -------------------------------------------------------------------
with portalTab2:
    st.subheader("🌿 Sustainable Agriculture & Companion Planting")
    st.caption("Maximize yield resilience and soil health using expert-backed intercropping guides tailored to Indian agro-climatic zones.")
    
    companion = getCompanionAdvisory(crop)
    
    with st.container(border=True):
        st.markdown(f"### Recommended Companion Crop: **{companion['companion']}**")
        st.markdown(f"**Key Agronomic Benefits:** {companion['benefits']}")
        st.markdown(f"**Ideal Field Conditions:** {companion['conditions']}")

    st.markdown("---")
    st.subheader("💬 Ask the Hybrid AI Sustainability Advisor")
    st.caption("Have questions about irrigation schedules, pest prevention, or soil health? Ask our agronomic AI assistant.")
    
    userQuery = st.text_input(
        "Type your question here:", 
        placeholder="e.g., How often should I water my crop given current soil moisture?"
    )
    
    if userQuery:
        response = queryGenerativeClimateAdvisor(
            farmerDetails["name"], 
            crop, 
            acres, 
            risk, 
            advisory, 
            companion, 
            userQuery
        )
        st.info(response)

# -------------------------------------------------------------------
# TAB 3: REGISTER NEW FIELD / POLICY
# -------------------------------------------------------------------
with portalTab3:
    st.subheader("📝 Register an Additional Field or Policy")
    st.caption("Add a new farm holding to your account to extend parametric coverage across multiple plots.")
    
    with st.container(border=True):
        with st.form("farmerPortalRegistration", clear_on_submit=True):
            fCol1, fCol2 = st.columns(2)
            
            with fCol1:
                portalName = st.text_input("Owner Full Name", value=farmerDetails["name"])
                portalPhone = st.text_input("Mobile / WhatsApp Number", value=farmerDetails["phone"])
                portalCrop = st.selectbox("Select Crop", CROP_LIST)
                
            with fCol2:
                portalAcres = st.number_input("Farm Area (Acres)", min_value=0.5, max_value=50.0, value=2.0, step=0.5)
                portalLat = st.number_input("Field Latitude", value=float(farmerDetails["lat"]), format="%.4f")
                portalLon = st.number_input("Field Longitude", value=float(farmerDetails["lon"]), format="%.4f")
                
            portalSubmit = st.form_submit_button("Submit New Plot for Coverage")
            
            if portalSubmit:
                if portalName and portalPhone:
                    newId = f"FARM{101 + len(state['farmerDatabase'])}"
                    polVal = int(portalAcres * 10000)
                    
                    newRecord = {
                        "farmerId": newId,
                        "name": portalName,
                        "phone": portalPhone,
                        "lat": float(portalLat),
                        "lon": float(portalLon),
                        "crop": portalCrop,
                        "acres": float(portalAcres),
                        "policyValue": polVal
                    }
                    
                    state["farmerDatabase"].append(newRecord)
                    st.success(f"🎉 Success! New plot registered with Policy ID `{newId}`. Coverage Value: `₹{polVal:,}`.")
                    st.rerun()
                else:
                    st.error("Please ensure name and mobile number are provided.")