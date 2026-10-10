<<<<<<< HEAD
import streamlit as st
import pandas as pd
import numpy as np
import plotly.express as px
from datetime import datetime

from DataPipeline import fetchWeatherData, generateTelemetryData
from RiskEngine import calculateRiskIndex, generateAiPrecautions, predictLocationRisk
from GlobalState import getSharedState

# Page Configuration
st.set_page_config(page_title="Aegis Terra - Insurer Command Center", layout="wide", page_icon="🛡️")

st.title("🛡️ Aegis Terra: Parametric Insurance Command Center")
st.caption("Aligned with UN SDGs: 1 (No Poverty), 2 (Zero Hunger), 13 (Climate Action)")

# Fetch Centralized State
state = getSharedState()

st.session_state.security = state["security"]
st.session_state.mlModel = state["mlModel"]

# Navigation Tabs
mainTab, mapTab, auditTab, registerTab = st.tabs([
    "📊 Insurer Analytics Command Center", 
    "🗺️ Interactive GIS Regional Heatmap",
    "⚖️ Auditor Claim Confirmations",
    "📝 Farmer Registration Portal"
])

# -------------------------------------------------------------------
# TAB 1: INSURER ANALYTICS COMMAND CENTER
# -------------------------------------------------------------------
with mainTab:
    st.sidebar.header("📍 Select Active Farmer Policy")
    
    if st.sidebar.button("🔄 Sync Live Database", use_container_width=True):
        st.cache_resource.clear()
        st.rerun()

    currentDb = state["farmerDatabase"]
    farmerList = currentDb["name"].tolist()
    selectedFarmerName = st.sidebar.selectbox("Select Registered Farmer", farmerList)
    
    farmerDetails = currentDb[
        currentDb["name"] == selectedFarmerName
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
    mlRiskScore = predictLocationRisk(state["mlModel"], risk)

    st.subheader("💰 Live Insurance Fund Capital & Risk Metrics")
    totalExecuted = state["totalPayoutsExecuted"]
    remainingPool = state["totalLiquidityPool"] - totalExecuted
    
    finCol1, finCol2, finCol3, finCol4 = st.columns(4)
    finCol1.metric("Total Liquidity Capital", f"${state['totalLiquidityPool']:,.2f}")
    finCol2.metric("Executed Payouts Total", f"${totalExecuted:,.2f}", delta="- Disbursed", delta_color="inverse")
    finCol3.metric("Available Capital Reserve", f"${remainingPool:,.2f}", delta="Solvent")
    finCol4.metric("Daily Cap Usage", f"${state['security'].currentDailyPayouts} / $5,000")

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
        confidence, claimStatus, flags = state["security"].validateClaim(df, risk)
        
        st.write(f"**Validation Confidence Score:** `{confidence}%`")
        st.write(f"**Claim Evaluation Status:** `{claimStatus}`")
        
        if flags:
            st.warning("Anomaly Flags Raised:")
            for flag in flags:
                st.write(f"- {flag}")
        else:
            st.success("No Sensor Anomaly Detected")

        st.markdown("---")
        
        if state["security"].circuitBreakerTripped:
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
    for idx, row in state["farmerDatabase"].iterrows():
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

        figMap.update_layout(map_style="open-street-map")
        st.plotly_chart(figMap, use_container_width=True)

# -------------------------------------------------------------------
# TAB 3: AUDITOR CLAIM CONFIRMATION PAGE & FINANCIAL LEDGER
# -------------------------------------------------------------------
with auditTab:
    st.subheader("⚖️ Human-In-The-Loop Auditor Confirmation Portal")
    st.caption("Review flagged claims with medium confidence scores (70–89%) before releasing escrow funds.")
    
    st.markdown("### ⏳ Pending Claim Approval Queue")
    
    if len(state["pendingClaims"]) == 0:
        st.success("🎉 No pending claims requiring auditor manual verification.")
    else:
        for idx, pClaim in enumerate(state["pendingClaims"]):
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
                        state["totalPayoutsExecuted"] += pClaim['amount']
                        state["security"].currentDailyPayouts += pClaim['amount']
                        
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
                        state["claimLedger"] = pd.concat([state["claimLedger"], pd.DataFrame([newRecord])], ignore_index=True)
                        state["pendingClaims"].pop(idx)
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
                        state["claimLedger"] = pd.concat([state["claimLedger"], pd.DataFrame([newRecord])], ignore_index=True)
                        state["pendingClaims"].pop(idx)
                        st.rerun()

    st.markdown("---")
    st.markdown("### 📜 Executed Payout & Audit History Ledger")
    st.dataframe(state["claimLedger"], use_container_width=True)

# -------------------------------------------------------------------
# TAB 4: FARMER REGISTRATION PORTAL
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
                newFarmerId = f"FARM{101 + len(state['farmerDatabase'])}"
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
                
                state["farmerDatabase"] = pd.concat([
                    state["farmerDatabase"], 
                    pd.DataFrame([newFarmerRecord])
                ], ignore_index=True)
                
                st.success(f"🎉 Success! {newFarmerName} registered with Policy ID `{newFarmerId}`. Coverage: `${calculatedPolicyValue}`.")
                st.info("The new farm location is now live on the GIS Regional Heatmap and active across all mobile portals.")
                st.rerun()
            else:
                st.error("Please fill in both the Full Name and Mobile Number fields.")

    st.markdown("---")
    st.subheader("📋 Active Registered Farmers Database")
=======
import streamlit as st
import pandas as pd
import numpy as np
import plotly.express as px
from datetime import datetime

from DataPipeline import fetchWeatherData, generateTelemetryData
from RiskEngine import calculateRiskIndex, generateAiPrecautions, predictLocationRisk
from GlobalState import getSharedState

# Page Configuration
st.set_page_config(page_title="Aegis Terra - Insurer Command Center", layout="wide", page_icon="🛡️")

st.title("🛡️ Aegis Terra: Parametric Insurance Command Center")
st.caption("Aligned with UN SDGs: 1 (No Poverty), 2 (Zero Hunger), 13 (Climate Action)")

# Fetch Centralized State
state = getSharedState()

st.session_state.security = state["security"]
st.session_state.mlModel = state["mlModel"]

# Navigation Tabs
mainTab, mapTab, auditTab, registerTab = st.tabs([
    "📊 Insurer Analytics Command Center", 
    "🗺️ Interactive GIS Regional Heatmap",
    "⚖️ Auditor Claim Confirmations",
    "📝 Farmer Registration Portal"
])

# -------------------------------------------------------------------
# TAB 1: INSURER ANALYTICS COMMAND CENTER
# -------------------------------------------------------------------
with mainTab:
    st.sidebar.header("📍 Select Active Farmer Policy")
    
    if st.sidebar.button("🔄 Sync Live Database", use_container_width=True):
        st.cache_resource.clear()
        st.rerun()

    currentDb = state["farmerDatabase"]
    farmerList = currentDb["name"].tolist()
    selectedFarmerName = st.sidebar.selectbox("Select Registered Farmer", farmerList)
    
    farmerDetails = currentDb[
        currentDb["name"] == selectedFarmerName
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
    mlRiskScore = predictLocationRisk(state["mlModel"], risk)

    st.subheader("💰 Live Insurance Fund Capital & Risk Metrics")
    totalExecuted = state["totalPayoutsExecuted"]
    remainingPool = state["totalLiquidityPool"] - totalExecuted
    
    finCol1, finCol2, finCol3, finCol4 = st.columns(4)
    finCol1.metric("Total Liquidity Capital", f"${state['totalLiquidityPool']:,.2f}")
    finCol2.metric("Executed Payouts Total", f"${totalExecuted:,.2f}", delta="- Disbursed", delta_color="inverse")
    finCol3.metric("Available Capital Reserve", f"${remainingPool:,.2f}", delta="Solvent")
    finCol4.metric("Daily Cap Usage", f"${state['security'].currentDailyPayouts} / $5,000")

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
        confidence, claimStatus, flags = state["security"].validateClaim(df, risk)
        
        st.write(f"**Validation Confidence Score:** `{confidence}%`")
        st.write(f"**Claim Evaluation Status:** `{claimStatus}`")
        
        if flags:
            st.warning("Anomaly Flags Raised:")
            for flag in flags:
                st.write(f"- {flag}")
        else:
            st.success("No Sensor Anomaly Detected")

        st.markdown("---")
        
        if state["security"].circuitBreakerTripped:
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
    for idx, row in state["farmerDatabase"].iterrows():
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

        figMap.update_layout(map_style="open-street-map")
        st.plotly_chart(figMap, use_container_width=True)

# -------------------------------------------------------------------
# TAB 3: AUDITOR CLAIM CONFIRMATION PAGE & FINANCIAL LEDGER
# -------------------------------------------------------------------
with auditTab:
    st.subheader("⚖️ Human-In-The-Loop Auditor Confirmation Portal")
    st.caption("Review flagged claims with medium confidence scores (70–89%) before releasing escrow funds.")
    
    st.markdown("### ⏳ Pending Claim Approval Queue")
    
    if len(state["pendingClaims"]) == 0:
        st.success("🎉 No pending claims requiring auditor manual verification.")
    else:
        for idx, pClaim in enumerate(state["pendingClaims"]):
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
                        state["totalPayoutsExecuted"] += pClaim['amount']
                        state["security"].currentDailyPayouts += pClaim['amount']
                        
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
                        state["claimLedger"] = pd.concat([state["claimLedger"], pd.DataFrame([newRecord])], ignore_index=True)
                        state["pendingClaims"].pop(idx)
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
                        state["claimLedger"] = pd.concat([state["claimLedger"], pd.DataFrame([newRecord])], ignore_index=True)
                        state["pendingClaims"].pop(idx)
                        st.rerun()

    st.markdown("---")
    st.markdown("### 📜 Executed Payout & Audit History Ledger")
    st.dataframe(state["claimLedger"], use_container_width=True)

# -------------------------------------------------------------------
# TAB 4: FARMER REGISTRATION PORTAL
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
                newFarmerId = f"FARM{101 + len(state['farmerDatabase'])}"
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
                
                state["farmerDatabase"] = pd.concat([
                    state["farmerDatabase"], 
                    pd.DataFrame([newFarmerRecord])
                ], ignore_index=True)
                
                st.success(f"🎉 Success! {newFarmerName} registered with Policy ID `{newFarmerId}`. Coverage: `${calculatedPolicyValue}`.")
                st.info("The new farm location is now live on the GIS Regional Heatmap and active across all mobile portals.")
                st.rerun()
            else:
                st.error("Please fill in both the Full Name and Mobile Number fields.")

    st.markdown("---")
    st.subheader("📋 Active Registered Farmers Database")
>>>>>>> 92ba84b (Introduce GlobalState.py for unified cross-device memory synchronization)
    st.dataframe(state["farmerDatabase"], use_container_width=True)