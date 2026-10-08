import streamlit as st
import pandas as pd
import numpy as np
import plotly.express as px
from datetime import datetime

from DataPipeline import fetchWeatherData, generateTelemetryData
from RiskEngine import calculateRiskIndex, generateAiPrecautions, trainPredictiveRiskModel, predictLocationRisk
from FailSafes import SecurityEngine

# Page Configuration
st.set_page_config(page_title="Parametric Agri Shield Command Center", layout="wide")

st.title("🌾 Parametric Insurance & Early Warning Command Center")
st.caption("Aligned with UN SDGs: 1 (No Poverty), 2 (Zero Hunger), 13 (Climate Action)")

# -------------------------------------------------------------------
# INITIALIZE GLOBAL SESSION STATES
# -------------------------------------------------------------------
if 'security' not in st.session_state:
    st.session_state.security = SecurityEngine(dailyPayoutLimit=5000)

if 'mlModel' not in st.session_state:
    st.session_state.mlModel = trainPredictiveRiskModel()

if 'totalLiquidityPool' not in st.session_state:
    st.session_state.totalLiquidityPool = 25000.0

if 'totalPayoutsExecuted' not in st.session_state:
    st.session_state.totalPayoutsExecuted = 0.0

if 'claimLedger' not in st.session_state:
    st.session_state.claimLedger = pd.DataFrame([
        {"claimId": "CLM8001", "timestamp": "2026-10-06 14:20", "farmerName": "Ramesh Kumar", "policyId": "FARM101", "amount": 250, "status": "APPROVED", "confidence": 95, "notes": "Auto-approved by risk engine"},
        {"claimId": "CLM8002", "timestamp": "2026-10-07 09:15", "farmerName": "Sita Devi", "policyId": "FARM102", "amount": 400, "status": "APPROVED", "confidence": 92, "notes": "Auto-approved by risk engine"}
    ])

if 'pendingClaims' not in st.session_state:
    st.session_state.pendingClaims = [
        {"claimId": "CLM8003", "timestamp": "2026-10-07 11:30", "farmerName": "Rajesh Patel", "policyId": "FARM103", "amount": 300, "confidence": 78, "reason": "Conflict: Rainfall deficit but NDVI greenness remains high"}
    ]

if 'farmerDatabase' not in st.session_state:
    st.session_state.farmerDatabase = pd.DataFrame([
        {"farmerId": "FARM101", "name": "Ramesh Kumar", "phone": "+919876543210", "lat": 12.92, "lon": 79.13, "crop": "Rice / Paddy", "acres": 2.5, "policyValue": 250},
        {"farmerId": "FARM102", "name": "Sita Devi", "phone": "+919876543211", "lat": 13.08, "lon": 80.27, "crop": "Wheat", "acres": 4.0, "policyValue": 400},
        {"farmerId": "FARM103", "name": "Rajesh Patel", "phone": "+919876543212", "lat": 12.23, "lon": 79.07, "crop": "Cotton", "acres": 3.0, "policyValue": 300},
        {"farmerId": "FARM104", "name": "Ananya Reddy", "phone": "+919876543213", "lat": 13.62, "lon": 79.41, "crop": "Maize", "acres": 5.0, "policyValue": 500}
    ])

# Navigation Tabs
mainTab, mapTab, auditTab, registerTab, simulateTab = st.tabs([
    "📊 Insurer Analytics Command Center", 
    "🗺️ Interactive GIS Regional Heatmap",
    "⚖️ Auditor Claim Confirmations",
    "📝 Farmer Self Registration Portal", 
    "📱 Farmer WhatsApp / SMS Interface"
])

# -------------------------------------------------------------------
# TAB 1: INSURER ANALYTICS COMMAND CENTER
# -------------------------------------------------------------------
with mainTab:
    st.sidebar.header("📍 Select Active Farmer Policy")
    
    farmerList = st.session_state.farmerDatabase["name"].tolist()
    selectedFarmerName = st.sidebar.selectbox("Select Registered Farmer", farmerList)
    
    farmerDetails = st.session_state.farmerDatabase[
        st.session_state.farmerDatabase["name"] == selectedFarmerName
    ].iloc[0]
    
    lat = farmerDetails["lat"]
    lon = farmerDetails["lon"]
    crop = farmerDetails["crop"]
    policyValue = farmerDetails["policyValue"]
    
    st.sidebar.info(f"**Policy ID:** {farmerDetails['farmerId']}\n\n"
                    f"**Phone:** {farmerDetails['phone']}\n\n"
                    f"**Farm Area:** {farmerDetails['acres']} Acres")

    weatherDf = fetchWeatherData(lat, lon)
    df = generateTelemetryData(weatherDf)
    risk = calculateRiskIndex(df)
    advisory = generateAiPrecautions(risk)
    mlRiskScore = predictLocationRisk(st.session_state.mlModel, risk)

    st.subheader("💰 Live Insurance Fund Capital & Risk Metrics")
    remainingPool = st.session_state.totalLiquidityPool - st.session_state.totalPayoutsExecuted
    
    finCol1, finCol2, finCol3, finCol4 = st.columns(4)
    finCol1.metric("Total Liquidity Capital", f"${st.session_state.totalLiquidityPool:,.2f}")
    finCol2.metric("Executed Payouts Total", f"${st.session_state.totalPayoutsExecuted:,.2f}", delta="- Disbursed", delta_color="inverse")
    finCol3.metric("Available Capital Reserve", f"${remainingPool:,.2f}", delta="Solvent")
    finCol4.metric("Daily Cap Usage", f"${st.session_state.security.currentDailyPayouts} / $5,000")

    st.markdown("---")

    col1, col2, col3, col4, col5 = st.columns(5)
    col1.metric("30-Day Rainfall", f"{risk['totalRain30d']} mm", delta="-12mm vs Avg", delta_color="inverse")
    col2.metric("Average Max Temp", f"{risk['avgTemp']} °C", delta="+3°C vs Avg", delta_color="inverse")
    col3.metric("Satellite NDVI Index", f"{risk['avgNdvi']}", delta="-0.15 vs Avg", delta_color="inverse")
    col4.metric("Composite Risk Score", f"{risk['compositeRisk']} / 1.0", delta=advisory['level'])
    col5.metric("ML Risk Prediction", f"{int(mlRiskScore * 100)}% Risk", delta="Random Forest")

    st.markdown("---")

    c1, c2 = st.columns([2, 1])
    with c1:
        st.subheader(f"Micro-Climate Telemetry ({farmerDetails['name']} - {crop})")
        fig = px.line(df, x='date', y=['tempMax', 'soilMoisturePercent', 'rainfall'], 
                      title="30-Day Environmental Metrics Trend")
        st.plotly_chart(fig, use_container_width=True)
        
    with c2:
        st.subheader("🔒 Security & Circuit Breaker Status")
        confidence, claimStatus, flags = st.session_state.security.validateClaim(df, risk)
        
        st.write(f"**Validation Confidence Score:** `{confidence}%`")
        st.write(f"**Claim Evaluation Status:** `{claimStatus}`")
        
        if flags:
            st.warning("Anomaly Flags Raised:")
            for flag in flags:
                st.write(f"- {flag}")
        else:
            st.success("No Sensor Anomaly Detected")

        st.markdown("---")
        
        if st.session_state.security.circuitBreakerTripped:
            st.error("🚨 CIRCUIT BREAKER TRIPPED: System Frozen")
        else:
            st.success("🟢 Circuit Breaker Armed & Ready")

# -------------------------------------------------------------------
# TAB 2: INTERACTIVE GIS REGIONAL HEATMAP
# -------------------------------------------------------------------
with mapTab:
    st.subheader("🗺️ Regional Environmental Heatmap & Farmer Locations")
    st.caption("Cross-reference registered smallholder farms against spatial weather and satellite metrics.")
    
    mapCol1, mapCol2 = st.columns([1, 3])
    
    with mapCol1:
        selectedLayer = st.radio(
            "Select Heatmap Layer:",
            ["Temperature (°C)", "Rainfall (mm)", "Soil Moisture (%)", "Satellite NDVI Index"]
        )
        st.info("💡 **Map Controls:**\n\nToggle layers to inspect regional drought hotspots. Hover over pins for real-time farm telemetry.")

    mapDataList = []
    for idx, row in st.session_state.farmerDatabase.iterrows():
        fWeather = fetchWeatherData(row["lat"], row["lon"])
        fTelemetry = generateTelemetryData(fWeather)
        fRisk = calculateRiskIndex(fTelemetry)
        
        mapDataList.append({
            "Farmer": row["name"],
            "Policy ID": row["farmerId"],
            "Crop": row["crop"],
            "Acres": row["acres"],
            "Latitude": row["lat"],
            "Longitude": row["lon"],
            "Temperature (°C)": fRisk["avgTemp"],
            "Rainfall (mm)": fRisk["totalRain30d"],
            "Soil Moisture (%)": fRisk["avgSoil"],
            "Satellite NDVI Index": fRisk["avgNdvi"],
            "Risk Score": fRisk["compositeRisk"]
        })
        
    mapDf = pd.DataFrame(mapDataList)

    with mapCol2:
        colorScaleMap = {
            "Temperature (°C)": "Reds",
            "Rainfall (mm)": "Blues",
            "Soil Moisture (%)": "YlGnBu",
            "Satellite NDVI Index": "Greens"
        }
        
        # Backward and forward compatibility for Plotly v5 and v6+
        densityMapFunc = getattr(px, "density_map", getattr(px, "density_mapbox", None))
        scatterMapFunc = getattr(px, "scatter_map", getattr(px, "scatter_mapbox", None))
        
        figMap = densityMapFunc(
            mapDf, 
            lat="Latitude", 
            lon="Longitude", 
            z=selectedLayer, 
            radius=40,
            center=dict(lat=mapDf["Latitude"].mean(), lon=mapDf["Longitude"].mean()), 
            zoom=7,
            color_continuous_scale=colorScaleMap[selectedLayer],
            title=f"Regional Spatial Heatmap: {selectedLayer}"
        )
        
        figScatter = scatterMapFunc(
            mapDf, 
            lat="Latitude", 
            lon="Longitude", 
            color="Risk Score", 
            size="Acres",
            hover_name="Farmer", 
            hover_data=["Policy ID", "Crop", "Temperature (°C)", "Rainfall (mm)", "Soil Moisture (%)", "Satellite NDVI Index"],
            color_continuous_scale="Viridis", 
            zoom=7
        )
        
        for trace in figScatter.data:
            figMap.add_trace(trace)

        # Update map layout tiles for Plotly 6+ / 5+ compatibility
        figMap.update_layout(map_style="open-street-map")

        st.plotly_chart(figMap, use_container_width=True)

# -------------------------------------------------------------------
# TAB 3: AUDITOR CLAIM CONFIRMATION PAGE & FINANCIAL LEDGER
# -------------------------------------------------------------------
with auditTab:
    st.subheader("⚖️ Human-In-The-Loop Auditor Confirmation Portal")
    st.caption("Review flagged claims with medium confidence scores (70–89%) before releasing escrow funds.")
    
    st.markdown("### ⏳ Pending Claim Approval Queue")
    
    if len(st.session_state.pendingClaims) == 0:
        st.success("🎉 No pending claims requiring auditor manual verification.")
    else:
        for idx, pClaim in enumerate(st.session_state.pendingClaims):
            with st.expander(f"📌 Claim `{pClaim['claimId']}` - {pClaim['farmerName']} (${pClaim['amount']})", expanded=True):
                auditCol1, auditCol2, auditCol3 = st.columns([2, 2, 1])
                
                with auditCol1:
                    st.write(f"**Policy ID:** `{pClaim['policyId']}`")
                    st.write(f"**Timestamp:** `{pClaim['timestamp']}`")
                    st.write(f"**Requested Amount:** `${pClaim['amount']}`")
                    
                with auditCol2:
                    st.write(f"**AI Confidence Score:** `{pClaim['confidence']}%`")
                    st.error(f"**Flag Reason:** {pClaim['reason']}")
                    
                with auditCol3:
                    st.write("**Auditor Action:**")
                    if st.button("✅ Approve Payout", key=f"approve_{idx}"):
                        st.session_state.totalPayoutsExecuted += pClaim['amount']
                        st.session_state.security.currentDailyPayouts += pClaim['amount']
                        
                        newRecord = {
                            "claimId": pClaim['claimId'],
                            "timestamp": datetime.now().strftime("%Y-%m-%d %H:%M"),
                            "farmerName": pClaim['farmerName'],
                            "policyId": pClaim['policyId'],
                            "amount": pClaim['amount'],
                            "status": "MANUAL APPROVED",
                            "confidence": pClaim['confidence'],
                            "notes": "Approved by Human Auditor"
                        }
                        st.session_state.claimLedger = pd.concat([st.session_state.claimLedger, pd.DataFrame([newRecord])], ignore_index=True)
                        st.session_state.pendingClaims.pop(idx)
                        st.rerun()
                        
                    if st.button("❌ Reject Claim", key=f"reject_{idx}"):
                        newRecord = {
                            "claimId": pClaim['claimId'],
                            "timestamp": datetime.now().strftime("%Y-%m-%d %H:%M"),
                            "farmerName": pClaim['farmerName'],
                            "policyId": pClaim['policyId'],
                            "amount": pClaim['amount'],
                            "status": "REJECTED",
                            "confidence": pClaim['confidence'],
                            "notes": "Rejected by Human Auditor"
                        }
                        st.session_state.claimLedger = pd.concat([st.session_state.claimLedger, pd.DataFrame([newRecord])], ignore_index=True)
                        st.session_state.pendingClaims.pop(idx)
                        st.rerun()

    st.markdown("---")
    st.markdown("### 📜 Executed Payout & Audit History Ledger")
    st.dataframe(st.session_state.claimLedger, use_container_width=True)

# -------------------------------------------------------------------
# TAB 4: FARMER SELF REGISTRATION PORTAL
# -------------------------------------------------------------------
with registerTab:
    st.subheader("🌾 New Farmer Registration Portal")
    st.caption("Self-onboarding for smallholder farmers via GPS pin or simple text inputs.")
    
    with st.form("farmerRegistrationForm", clear_on_submit=True):
        regCol1, regCol2 = st.columns(2)
        
        with regCol1:
            newFarmerName = st.text_input("Full Name", placeholder="e.g. Rajesh Patel")
            newFarmerPhone = st.text_input("Mobile / WhatsApp Number", placeholder="e.g. +919876543212")
            newCrop = st.selectbox("Select Crop", ["Rice / Paddy", "Wheat", "Maize", "Cotton", "Sugarcane"])
            
        with regCol2:
            newAcres = st.number_input("Farm Size (Acres)", min_value=0.5, max_value=50.0, value=2.0, step=0.5)
            newLat = st.number_input("Farm Latitude", value=12.92, format="%.4f")
            newLon = st.number_input("Farm Longitude", value=79.13, format="%.4f")
            
        submitRegistration = st.form_submit_button("Register & Activate Policy")
        
        if submitRegistration:
            if newFarmerName and newFarmerPhone:
                newFarmerId = f"FARM{101 + len(st.session_state.farmerDatabase)}"
                calculatedPolicyValue = int(newAcres * 100)
                
                newFarmerRecord = {
                    "farmerId": newFarmerId,
                    "name": newFarmerName,
                    "phone": newFarmerPhone,
                    "lat": newLat,
                    "lon": newLon,
                    "crop": newCrop,
                    "acres": newAcres,
                    "policyValue": calculatedPolicyValue
                }
                
                st.session_state.farmerDatabase = pd.concat([
                    st.session_state.farmerDatabase, 
                    pd.DataFrame([newFarmerRecord])
                ], ignore_index=True)
                
                st.success(f"🎉 Success! {newFarmerName} registered with Policy ID `{newFarmerId}`. Coverage: `${calculatedPolicyValue}`.")
                st.info("The new farm location is now live on the GIS Regional Heatmap and active in the telemetry engine.")
            else:
                st.error("Please fill in both the Full Name and Mobile Number fields.")

    st.markdown("---")
    st.subheader("📋 Active Registered Farmers Database")
    st.dataframe(st.session_state.farmerDatabase, use_container_width=True)

# -------------------------------------------------------------------
# TAB 5: FARMER WHATSAPP / SMS INTERFACE
# -------------------------------------------------------------------
with simulateTab:
    st.subheader("📲 Low-Tech Farmer Interaction Simulator")
    
    st.info(f"**Target Farmer:** {farmerDetails['name']} ({farmerDetails['phone']})\n\n"
            f"**AI Early Warning Advisory:** [{advisory['level']}] {advisory['action']}")
    
    st.markdown("---")
    chatCol1, chatCol2 = st.columns(2)
    
    with chatCol1:
        st.markdown("#### Simulated Incoming SMS / WhatsApp Alert")
        st.code(f"""
        [ALERT - AGRI SHIELD]
        Hello {farmerDetails['name']},
        Drought risk score for your {crop} farm reached {risk['compositeRisk']}.
        
        Precaution: {advisory['action']}
        
        Your active policy permits an advance payout of ${policyValue}.
        Do you require immediate financial liquidity?
        Reply 'YES' to claim or 'NO' to save liquidity.
        """, language="text")
        
    with chatCol2:
        st.markdown("#### Farmer Reply Simulation")
        farmerReply = st.radio("Farmer Replies via SMS/WhatsApp:", ["(Awaiting Response)", "YES", "NO"])
        
        if st.button("Submit Reply"):
            if farmerReply == "YES":
                confidence, claimStatus, flags = st.session_state.security.validateClaim(df, risk)
                
                if confidence >= 90:
                    success, msg = st.session_state.security.processPayout(policyValue)
                    if success:
                        st.session_state.totalPayoutsExecuted += policyValue
                        newClaim = {
                            "claimId": f"CLM{8001 + len(st.session_state.claimLedger)}",
                            "timestamp": datetime.now().strftime("%Y-%m-%d %H:%M"),
                            "farmerName": farmerDetails['name'],
                            "policyId": farmerDetails['farmerId'],
                            "amount": policyValue,
                            "status": "AUTO APPROVED",
                            "confidence": confidence,
                            "notes": "Triggered via SMS Opt-In"
                        }
                        st.session_state.claimLedger = pd.concat([st.session_state.claimLedger, pd.DataFrame([newClaim])], ignore_index=True)
                        st.success(f"Response Processed: {msg}")
                    else:
                        st.error(f"Payout Blocked by Security Engine: {msg}")
                else:
                    newPending = {
                        "claimId": f"CLM{8001 + len(st.session_state.claimLedger) + len(st.session_state.pendingClaims)}",
                        "timestamp": datetime.now().strftime("%Y-%m-%d %H:%M"),
                        "farmerName": farmerDetails['name'],
                        "policyId": farmerDetails['farmerId'],
                        "amount": policyValue,
                        "confidence": confidence,
                        "reason": ", ".join(flags) if flags else "Low confidence score evaluation"
                    }
                    st.session_state.pendingClaims.append(newPending)
                    st.warning(f"Claim flagged due to medium confidence ({confidence}%). Routed to Auditor Confirmation Tab for review.")
                    
            elif farmerReply == "NO":
                st.info("Farmer chose to preserve policy reserves. Policy remains active.")