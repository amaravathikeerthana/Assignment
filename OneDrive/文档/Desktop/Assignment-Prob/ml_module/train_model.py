"""
ML Module: Yield Prediction & Risk Classifier Training
Trains:
1. RandomForestRegressor for Crop Yield Prediction
2. Multi-class Classifier for Drought Risk (LOW, MEDIUM, HIGH)
3. Multi-class Classifier for Pest / Disease Risk (LOW, MEDIUM, HIGH)
Saves models and artifacts for deployment.
"""

import os
import joblib
import numpy as np
from sklearn.ensemble import RandomForestRegressor, RandomForestClassifier
from sklearn.model_selection import train_test_split
from sklearn.metrics import mean_squared_error, r2_score, classification_report

MODELS_DIR = os.path.join(os.path.dirname(__file__), "models")
os.makedirs(MODELS_DIR, exist_ok=True)


def generate_synthetic_agronomy_dataset(n_samples: int = 1500, seed: int = 42):
    """
    Generates realistic synthetic multi-variable dataset based on
    agricultural meteorology and soil science relationships.
    """
    rng = np.random.default_rng(seed)

    # Features:
    # 0: Temperature (°C) [15 - 45]
    # 1: Humidity (%) [20 - 100]
    # 2: Soil Moisture (%) [5 - 95]
    # 3: Rainfall (mm) [0 - 250]
    temperature = rng.uniform(15, 45, n_samples)
    humidity = rng.uniform(20, 100, n_samples)
    soil_moisture = rng.uniform(5, 95, n_samples)
    rainfall = rng.uniform(0, 250, n_samples)

    X = np.column_stack([temperature, humidity, soil_moisture, rainfall])

    # 1. Target: Crop Yield (Quintals/Acre)
    # Optimum: Temp ~ 27°C, Soil Moisture ~ 60%, Moderate Rain
    temp_penalty = 0.02 * (temperature - 27) ** 2
    moisture_benefit = 0.12 * soil_moisture - 0.0008 * (soil_moisture ** 2)
    rain_benefit = 0.03 * np.minimum(rainfall, 120)
    noise = rng.normal(0, 0.4, n_samples)

    yield_target = 8.0 + moisture_benefit + rain_benefit - temp_penalty + noise
    yield_target = np.clip(yield_target, 2.0, 25.0)

    # 2. Target: Drought Risk ('LOW', 'MEDIUM', 'HIGH')
    drought_labels = []
    for s, r, t in zip(soil_moisture, rainfall, temperature):
        if s < 25 and r < 30 and t > 32:
            drought_labels.append("HIGH")
        elif s < 40 and r < 60:
            drought_labels.append("MEDIUM")
        else:
            drought_labels.append("LOW")
    drought_target = np.array(drought_labels)

    # 3. Target: Pest Risk ('LOW', 'MEDIUM', 'HIGH')
    pest_labels = []
    for h, t in zip(humidity, temperature):
        if h >= 80 and (24 <= t <= 34):
            pest_labels.append("HIGH")
        elif h >= 65 and (22 <= t <= 36):
            pest_labels.append("MEDIUM")
        else:
            pest_labels.append("LOW")
    pest_target = np.array(pest_labels)

    return X, yield_target, drought_target, pest_target


def train_and_export_models():
    print("[ML Module] Generating agronomic training data...")
    X, y_yield, y_drought, y_pest = generate_synthetic_agronomy_dataset()

    X_train, X_test, y_y_train, y_y_test = train_test_split(X, y_yield, test_size=0.2, random_state=42)
    _, _, y_d_train, y_d_test = train_test_split(X, drought_target, test_size=0.2, random_state=42) if 'drought_target' in locals() else train_test_split(X, y_drought, test_size=0.2, random_state=42)
    _, _, y_p_train, y_p_test = train_test_split(X, y_pest, test_size=0.2, random_state=42)

    # Train Yield Regressor
    print("[ML Module] Training Crop Yield Regressor...")
    regressor = RandomForestRegressor(n_estimators=120, max_depth=10, random_state=42)
    regressor.fit(X_train, y_y_train)
    y_pred = regressor.predict(X_test)
    r2 = r2_score(y_y_test, y_pred)
    rmse = np.sqrt(mean_squared_error(y_y_test, y_pred))
    print(f"  Yield Model R2: {r2:.4f}, RMSE: {rmse:.4f}")

    # Train Drought Risk Classifier
    print("[ML Module] Training Drought Risk Classifier...")
    drought_clf = RandomForestClassifier(n_estimators=100, max_depth=8, random_state=42)
    drought_clf.fit(X_train, y_d_train)
    d_pred = drought_clf.predict(X_test)
    print("  Drought Classifier Report:")
    print(classification_report(y_d_test, d_pred, digits=3))

    # Train Pest Risk Classifier
    print("[ML Module] Training Pest Risk Classifier...")
    pest_clf = RandomForestClassifier(n_estimators=100, max_depth=8, random_state=42)
    pest_clf.fit(X_train, y_p_train)
    p_pred = pest_clf.predict(X_test)
    print("  Pest Classifier Report:")
    print(classification_report(y_p_test, p_pred, digits=3))

    # Save models
    joblib.dump(regressor, os.path.join(MODELS_DIR, "yield_regressor.joblib"))
    joblib.dump(drought_clf, os.path.join(MODELS_DIR, "drought_classifier.joblib"))
    joblib.dump(pest_clf, os.path.join(MODELS_DIR, "pest_classifier.joblib"))
    print("[ML Module] All models successfully saved.")


if __name__ == "__main__":
    train_and_export_models()
