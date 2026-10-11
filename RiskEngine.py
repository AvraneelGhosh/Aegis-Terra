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
    
    # 1. Feature generation matching actual runtime distributions
    rain = np.random.uniform(0, 300, nSamples)      # 0 to 300 mm 30-day rain
    temp = np.random.uniform(20, 45, nSamples)      # 20 to 45 °C
    soil = np.random.uniform(10, 80, nSamples)      # 10 to 80 % moisture
    ndvi = np.random.uniform(0.1, 0.8, nSamples)    # 0.1 to 0.8 vegetation index
    
    X = np.column_stack([rain, temp, soil, ndvi])
    
    # 2. Synthetic Ground Truth Labeling based on agronomic stress
    # High risk = Low Rain (<50mm) AND High Temp (>35C) OR Very Low NDVI (<0.25)
    y = np.where((rain < 60) & (temp > 34) | (ndvi < 0.25), 1, 0)
    
    # 3. Held-out train-test split for evaluation
    X_train, X_test, y_train, y_test = train_test_split(X, y, test_size=0.2, random_state=42)
    
    model = RandomForestClassifier(n_estimators=50, random_state=42)
    model.fit(X_train, y_train)
    
    acc = accuracy_score(y_test, model.predict(X_test))
    
    return model, acc

def predictLocationRisk(model, riskData):
    """
    Predicts drought risk probability using the trained Random Forest model.
    """
    features = np.array([[
        riskData['totalRain30d'],
        riskData['avgTemp'],
        riskData['avgSoil'],
        riskData['avgNdvi']
    ]])
    
    prob = model.predict_proba(features)[0][1] # Probability of High Risk Class
    return float(prob)

def calculateRiskIndex(df):
    """
    Calculates aggregated environmental metrics and composite risk score.
    """
    totalRain30d = round(float(df['rainfall'].sum()), 1)
    avgTemp = round(float(df['tempMax'].mean()), 1)
    avgSoil = round(float(df['soilMoisturePercent'].mean()), 1)
    avgNdvi = round(float(df['ndvi'].mean()), 2)
    
    # Composite Score (0.0 to 1.0)
    # Higher rain/soil reduces risk; higher temp increases risk
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
    """
    Generates actionable advisory based on composite risk score.
    """
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
    Returns agronomic companion planting advice based on crop type.
    """
    advisories = {
        "Rice / Paddy": {
            "companion": "Azolla & Duckweed",
            "benefits": "Fixes atmospheric nitrogen, reduces weed growth, conserves water.",
            "conditions": "Flooded paddy fields with continuous moisture."
        },
        "Wheat": {
            "companion": "Chickpea / Mustard",
            "benefits": "Improves soil nitrogen efficiency and prevents pest proliferation.",
            "conditions": "Cool dry climate during early vegetative growth."
        },
        "Maize": {
            "companion": "Cowpea / Beans",
            "benefits": "Provides ground cover, prevents soil erosion, fixes nitrogen.",
            "conditions": "Well-drained soil with medium moisture."
        },
        "Cotton": {
            "companion": "Marigold / Pigeon Pea",
            "benefits": "Acts as a trap crop for bollworms and enhances soil structure.",
            "conditions": "Warm climate with deep fertile soil."
        },
        "Sugarcane": {
            "companion": "Soybean / Groundnut",
            "benefits": "Supplies organic matter and generates additional intercrop income.",
            "conditions": "High moisture and full sun exposure."
        }
    }
    return advisories.get(crop, advisories["Rice / Paddy"])

def queryGenerativeClimateAdvisor(farmerName, crop, acres, riskData, advisoryData, companionData, userQuery):
    """
    Simulates a hybrid AI agronomic assistant response.
    """
    query = userQuery.lower()
    if "water" in query or "irrigation" in query:
        return f"Hello {farmerName}, based on your current 30-day rainfall of {riskData['totalRain30d']}mm and soil moisture at {riskData['avgSoil']}%, we recommend maintaining drip irrigation during morning hours."
    elif "companion" in query or "crop" in query:
        return f"For your {crop} farm ({acres} acres), intercropping with **{companionData['companion']}** is highly recommended: {companionData['benefits']}"
    else:
        return f"Aegis Assistant: Based on your risk level ({advisoryData['level']}), current recommendation is: {advisoryData['action']}"