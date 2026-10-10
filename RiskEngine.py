import numpy as np
import pandas as pd
from sklearn.ensemble import RandomForestClassifier
from google import genai

def trainPredictiveRiskModel():
    X_train = np.array([
        [10, 32, 20], [0, 41, 10], [5, 35, 15], [80, 28, 70], [120, 26, 85], [2, 39, 12]
    ])
    y_train = np.array([0, 1, 0, 0, 0, 1])
    model = RandomForestClassifier(n_estimators=10, random_state=42)
    model.fit(X_train, y_train)
    return model

def calculateRiskIndex(df):
    totalRain30d = float(df['rainfall'].sum())
    avgTemp = float(df['tempMax'].mean())
    avgSoil = float(df['soilMoisturePercent'].mean()) if 'soilMoisturePercent' in df else 45.0
    avgNdvi = float(df['ndvi'].mean()) if 'ndvi' in df else 0.5
    
    tempFactor = max(0.0, (avgTemp - 32) / 15)
    rainFactor = max(0.0, (50 - totalRain30d) / 50)
    compositeRisk = round(min(1.0, (tempFactor * 0.6) + (rainFactor * 0.4)), 2)
    
    return {
        "totalRain30d": round(totalRain30d, 1),
        "avgTemp": round(avgTemp, 1),
        "avgSoil": round(avgSoil, 1),
        "avgNdvi": round(avgNdvi, 1),
        "compositeRisk": compositeRisk
    }

def predictLocationRisk(model, risk):
    features = np.array([[risk['totalRain30d'], risk['avgTemp'], risk['avgSoil']]])
    prob = model.predict_proba(features)[0][1]
    return float(prob)

def generateAiPrecautions(risk):
    if risk['compositeRisk'] >= 0.7:
        return {
            "level": "🔴 High Drought & Heat Stress",
            "action": "Severe heat and dry spell forecast. Postpone non-critical flooding; utilize drip micro-irrigation; apply organic mulch to conserve root-zone moisture."
        }
    elif risk['compositeRisk'] >= 0.4:
        return {
            "level": "🟡 Moderate Climate Risk",
            "action": "Unstable rainfall patterns detected. Monitor soil moisture daily and ensure field drainage channels are cleared for sudden downpours."
        }
    else:
        return {
            "level": "🟢 Favorable Conditions",
            "action": "Climate indicators are stable. Maintain standard seasonal crop management and optimal nutrient scheduling."
        }

def getCompanionAdvisory(crop):
    knowledgeBase = {
        "Rice / Paddy": {
            "companion": "Sesbania / Legume Green Manure",
            "benefits": "Enhances soil nitrogen fixation, organic matter, and suppresses weed germination.",
            "conditions": "Requires controlled shallow water management during early vegetative growth."
        },
        "Wheat": {
            "companion": "Chickpea or Mustard",
            "benefits": "Improves land equivalent ratio and optimizes soil profile moisture usage.",
            "conditions": "Best suited for well-drained loamy soils with moderate winter precipitation."
        },
        "Maize": {
            "companion": "Cowpea or Climbing Beans",
            "benefits": "Nitrogen fixation through root nodules, natural weed suppression, and yield diversification.",
            "conditions": "Ensure adequate plant spacing to minimize light and water competition."
        },
        "Cotton": {
            "companion": "Black Gram or Marigold",
            "benefits": "Attracts beneficial predatory insects, lowers bollworm incidence, and fixes nitrogen.",
            "conditions": "Monitor soil moisture closely to prevent waterlogging during heavy monsoon spells."
        },
        "Sugarcane": {
            "companion": "Coriander or Onion",
            "benefits": "Maximizes early-stage ground cover, reduces weed pressure, and provides auxiliary income.",
            "conditions": "Requires wide-row planting arrangements for companion root expansion."
        }
    }
    return knowledgeBase.get(crop, {
        "companion": "Cover Crop Legumes",
        "benefits": "Improves soil structural stability and organic carbon content.",
        "conditions": "Verify local soil testing parameters prior to implementation."
    })

def queryGenerativeClimateAdvisor(farmerName, crop, acres, riskData, advisoryData, companionData, userQuery):
    try:
        client = genai.Client()
        prompt = f"""
        You are Aegis Terra's Expert AI Agricultural & Climate Sustainability Advisor. 
        You are speaking directly with a smallholder farmer named {farmerName}.
        
        Farmer Profile:
        - Crop: {crop} ({acres} Acres)
        - 30-Day Rainfall: {riskData['totalRain30d']} mm
        - Average Temperature: {riskData['avgTemp']} °C
        - Soil Moisture Level: {riskData['avgSoil']}%
        - Composite Climate Risk Score: {riskData['compositeRisk']} / 1.0 ({advisoryData['level']})
        - Core Advisory Action: {advisoryData['action']}
        - Recommended Sustainable Companion Crop: {companionData['companion']} ({companionData['benefits']})
        
        Farmer Query / Interaction: "{userQuery}"
        
        Instructions:
        1. Maintain an encouraging, respectful, and expert tone suited for smallholder farmers in India.
        2. Ground your response strictly in the telemetry and structured agronomic data provided above.
        3. Explain why certain actions are recommended based on their soil and weather metrics.
        4. Keep the response concise, actionable, and formatted cleanly with bullet points or emojis.
        """
        response = client.models.generate_content(
            model='gemini-2.5-flash',
            contents=prompt
        )
        return response.text
    except Exception as e:
        return f"🤖 **Aegis Terra AI Advisor:** Based on your current weather telemetry (Risk Score: {riskData['compositeRisk']}), {advisoryData['action']} For {crop}, consider {companionData['companion']} to improve soil health."