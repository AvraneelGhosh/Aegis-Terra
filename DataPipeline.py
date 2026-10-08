import requests
import pandas as pd
import numpy as np

def fetchWeatherData(lat=12.92, lon=79.13):
    """
    Fetches daily rainfall and temperature from Open-Meteo API.
    Includes custom User-Agent headers to prevent connection resets (Error 10054).
    """
    url = f"https://api.open-meteo.com/v1/forecast?latitude={lat}&longitude={lon}&daily=temperature_2m_max,precipitation_sum&timezone=auto&past_days=30"
    
    # Custom headers stop remote host connection resets
    headers = {
        'User-Agent': 'AegisTerra/1.0 (ParametricAgriShieldHackathon)'
    }
    
    try:
        response = requests.get(url, headers=headers, timeout=5)
        if response.status_code == 200:
            data = response.json()['daily']
            df = pd.DataFrame({
                'date': data['time'],
                'tempMax': data['temperature_2m_max'],
                'rainfall': data['precipitation_sum']
            })
            return df
    except Exception as e:
        # Graceful fallback if network or remote host drops connection
        pass

    # Fallback simulated climate telemetry data if network fails
    dates = pd.date_range(end=pd.Timestamp.today(), periods=30)
    return pd.DataFrame({
        'date': dates,
        'tempMax': np.random.uniform(32, 42, size=30),
        'rainfall': np.random.exponential(scale=2.0, size=30)
    })

def generateTelemetryData(df):
    """Simulates hyper-local soil moisture and satellite NDVI vegetation health."""
    np.random.seed(42)
    df['soilMoisturePercent'] = np.clip(100 - (df['tempMax'] * 1.8) + (df['rainfall'] * 4) + np.random.normal(0, 3, len(df)), 10, 90)
    df['ndvi'] = np.clip(0.3 + (df['soilMoisturePercent'] / 200) + (df['rainfall'] / 100), 0.1, 0.9)
    return df