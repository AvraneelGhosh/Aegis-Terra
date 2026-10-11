import numpy as np
from sklearn.ensemble import RandomForestClassifier
from sklearn.model_selection import train_test_split
from sklearn.metrics import accuracy_score

def trainRiskModel():
    """
    Trains a prototype Random Forest model with realistic feature ranges.
    Features: [30-Day Total Rain (mm), Avg Temp (°C), Avg Soil Moisture (%), Avg NDVI]
    """
    np.random.seed(42)
    nSamples = 1000
    
    rain = np.random.uniform(0, 300, nSamples)
    temp = np.random.uniform(20, 45, nSamples)
    soil = np.random.uniform(10, 80, nSamples)
    ndvi = np.random.uniform(0.1, 0.8, nSamples)
    
    X = np.column_stack([rain, temp, soil, ndvi])
    y = np.where((rain < 60) & (temp > 34) | (ndvi < 0.25), 1, 0)
    
    X_train, X_test, y_train, y_test = train_test_split(X, y, test_size=0.2, random_state=42)
    
    model = RandomForestClassifier(n_estimators=50, random_state=42)
    model.fit(X_train, y_train)
    
    acc = accuracy_score(y_test, model.predict(X_test))
    return model, acc

def predictLocationRisk(model, riskData):
    features = np.array([[
        riskData['totalRain30d'],
        riskData['avgTemp'],
        riskData['avgSoil'],
        riskData['avgNdvi']
    ]])
    prob = model.predict_proba(features)[0][1]
    return float(prob)

def calculateRiskIndex(df):
    totalRain30d = round(float(df['rainfall'].sum()), 1)
    avgTemp = round(float(df['tempMax'].mean()), 1)
    avgSoil = round(float(df['soilMoisturePercent'].mean()), 1)
    avgNdvi = round(float(df['ndvi'].mean()), 2)
    
    rainFactor = max(0, (100 - totalRain30d) / 100)
    tempFactor = max(0, (avgTemp - 25) / 20)
    soilFactor = max(0, (50 - avgSoil) / 50)
    
    compositeRisk = min(1.0, max(0.0, (rainFactor * 0.4) + (tempFactor * 0.3) + (soilFactor * 0.3)))
    
    return {
        "totalRain30d": totalRain30d,
        "avgTemp": avgTemp,
        "avgSoil": avgSoil,
        "avgNdvi": avgNdvi,
        "compositeRisk": round(compositeRisk, 2)
    }

def generateAiPrecautions(riskData):
    score = riskData['compositeRisk']
    if score >= 0.7:
        return {
            "level": "🔴 CRITICAL DROUGHT RISK",
            "action": "Immediate irrigation advised. Initiate parametric claim review."
        }
    elif score >= 0.4:
        return {
            "level": "🟡 MODERATE CLIMATE STRESS",
            "action": "Monitor soil moisture closely. Apply soil mulch to retain moisture."
        }
    else:
        return {
            "level": "🟢 LOW RISK",
            "action": "Optimal growing conditions. Maintain standard field routine."
        }

def getCompanionAdvisory(crop):
    """
    Returns agronomic companion planting advice for India's top 15 crops.
    """
    advisories = {
        "Rice / Paddy": {
            "companion": "Azolla & Duckweed",
            "benefits": "Fixes atmospheric nitrogen, reduces weed growth, and conserves water.",
            "conditions": "Flooded paddy fields with continuous moisture."
        },
        "Wheat": {
            "companion": "Chickpea / Mustard",
            "benefits": "Improves soil nitrogen efficiency and prevents pest proliferation.",
            "conditions": "Cool dry climate during early vegetative growth."
        },
        "Maize (Corn)": {
            "companion": "Cowpea / Climbing Beans",
            "benefits": "Provides natural ground cover, prevents soil erosion, and fixes nitrogen.",
            "conditions": "Well-drained soil with medium moisture."
        },
        "Bajra (Pearl Millet)": {
            "companion": "Cluster Beans (Guar) / Cowpea",
            "benefits": "Enhances soil fertility and acts as a drought-tolerant intercrop.",
            "conditions": "Arid or semi-arid sandy loam soils."
        },
        "Jowar (Sorghum)": {
            "companion": "Pigeon Pea (Tur)",
            "benefits": "Deep root systems tap varied soil strata and resist lodging.",
            "conditions": "Warm climates with moderate rainfall."
        },
        "Ragi (Finger Millet)": {
            "companion": "Field Beans / Horse Gram",
            "benefits": "Improves soil organic matter and suppresses weed competition.",
            "conditions": "Hilly terrain or red soils with light rain."
        },
        "Pulses (Gram / Tur / Lentils)": {
            "companion": "Cereals (Sorghum / Millet)",
            "benefits": "Symbiotic nitrogen fixation enriches the soil for companion cereals.",
            "conditions": "Well-drained soils with mild temperatures."
        },
        "Soybean": {
            "companion": "Maize / Pigeon Pea",
            "benefits": "Optimizes vertical space utilization and balances soil nitrogen.",
            "conditions": "Humid subtropical climate with good drainage."
        },
        "Groundnut (Peanut)": {
            "companion": "Sunflower / Castor",
            "benefits": "Maximizes oilseed yield per acre and deters soil-borne pests.",
            "conditions": "Light sandy loam soils with moderate warmth."
        },
        "Mustard (Rapeseed)": {
            "companion": "Barley / Chickpea",
            "benefits": "Acts as a natural pest repellant and maximizes winter field productivity.",
            "conditions": "Cool Rabi season climate with minimal frost."
        },
        "Sugarcane": {
            "companion": "Soybean / Groundnut",
            "benefits": "Supplies early ground cover, suppresses weeds, and adds extra nitrogen.",
            "conditions": "High moisture and full sun exposure."
        },
        "Cotton": {
            "companion": "Marigold / Pigeon Pea",
            "benefits": "Acts as a trap crop for bollworms and protects beneficial insects.",
            "conditions": "Warm climate with deep fertile black soil."
        },
        "Jute": {
            "companion": "Green Gram (Moong)",
            "benefits": "Short-duration legume harvested early without competing with jute stems.",
            "conditions": "Alluvial, frequently flooded deltaic soils."
        },
        "Tea": {
            "companion": "Shade Trees (Indigofera / Albizia)",
            "benefits": "Regulates canopy temperature and builds soil humus from leaf litter.",
            "conditions": "Sloping acidic forest loam in hilly regions."
        },
        "Coffee": {
            "companion": "Silver Oak / Pepper Vines",
            "benefits": "Provides multi-tier canopy shade and creates secondary spice revenue.",
            "conditions": "Well-drained forest loam under tropical elevations."
        }
    }
    return advisories.get(crop, advisories["Rice / Paddy"])

def queryGenerativeClimateAdvisor(farmerName, crop, acres, riskData, advisoryData, companionData, userQuery):
    query = userQuery.lower()
    if "water" in query or "irrigation" in query:
        return f"Hello {farmerName}, based on your current 30-day rainfall of {riskData['totalRain30d']}mm and soil moisture at {riskData['avgSoil']}%, we recommend maintaining drip irrigation during morning hours."
    elif "companion" in query or "crop" in query:
        return f"For your {crop} farm ({acres} acres), intercropping with **{companionData['companion']}** is highly recommended: {companionData['benefits']}"
    else:
        return f"Aegis Assistant: Based on your risk level ({advisoryData['level']}), current recommendation is: {advisoryData['action']}"