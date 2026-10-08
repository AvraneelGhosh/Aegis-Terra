import numpy as np
import pandas as pd
from sklearn.ensemble import RandomForestClassifier

def trainPredictiveRiskModel():
    """
    Trains a Random Forest Machine Learning model on historic climate patterns.
    Features: [30-day rainfall, average temperature, soil moisture, satellite NDVI]
    Target: 1 = High Drought Risk, 0 = Normal
    """
    np.random.seed(42)
    rain = np.random.uniform(0, 100, 500)
    temp = np.random.uniform(25, 45, 500)
    soil = np.random.uniform(10, 90, 500)
    ndvi = np.random.uniform(0.1, 0.9, 500)
    
    # Agronomic drought condition definition
    target = ((rain < 15) & (temp > 36) & (soil < 30)).astype(int)
    
    X = pd.DataFrame({'rain': rain, 'temp': temp, 'soil': soil, 'ndvi': ndvi})
    y = target
    
    model = RandomForestClassifier(n_estimators=100, random_state=42)
    model.fit(X, y)
    return model

def predictLocationRisk(model, locationMetrics):
    """Predicts location-specific drought probability for the farmer's coordinates."""
    inputData = pd.DataFrame([{
        'rain': locationMetrics['totalRain30d'],
        'temp': locationMetrics['avgTemp'],
        'soil': locationMetrics['avgSoil'],
        'ndvi': locationMetrics['avgNdvi']
    }])
    droughtProbability = model.predict_proba(inputData)[0][1]
    return round(droughtProbability, 2)

def calculateRiskIndex(df):
    """Computes statistical climate summary metrics from 30-day telemetry dataframe."""
    recent30 = df.tail(30)
    
    totalRain = recent30['rainfall'].sum()
    avgTemp = recent30['tempMax'].mean()
    avgSoil = recent30['soilMoisturePercent'].mean()
    avgNdvi = recent30['ndvi'].mean()
    
    rainRisk = max(0.0, min(1.0, (20 - totalRain) / 20))
    tempRisk = max(0.0, min(1.0, (avgTemp - 32) / 8))
    soilRisk = max(0.0, min(1.0, (30 - avgSoil) / 20))
    
    compositeRisk = (0.4 * rainRisk) + (0.3 * tempRisk) + (0.3 * soilRisk)
    
    return {
        'compositeRisk': round(compositeRisk, 2),
        'totalRain30d': round(totalRain, 1),
        'avgTemp': round(avgTemp, 1),
        'avgSoil': round(avgSoil, 1),
        'avgNdvi': round(avgNdvi, 2)
    }

def generateAiPrecautions(riskMetrics):
    """AI Advisory Engine mapping risk profiles to preventative agronomic actions."""
    score = riskMetrics['compositeRisk']
    
    if score >= 0.75:
        return {
            'level': 'CRITICAL',
            'action': 'Extreme Drought & Heat Spike imminent. Execute night drip-irrigation immediately and apply organic straw mulch to conserve root moisture.'
        }
    elif score >= 0.50:
        return {
            'level': 'WARNING',
            'action': 'Moderate Moisture Deficit detected. Apply bio-stimulants, reduce nitrogen fertilizer application, and clear field drainage lines.'
        }
    else:
        return {
            'level': 'NORMAL',
            'action': 'Crop micro-climate parameters are within normal growth thresholds. No immediate intervention required.'
        }