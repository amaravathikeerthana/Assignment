"""
ML Module: Yield & Risk Predictor Engine
Inference service that loads trained models and generates:
- Predicted crop yield
- Drought risk status
- Pest risk status
- Expert agronomic advisories for farmers
"""

import os
import joblib
import numpy as np
from typing import Dict, Any, List

MODELS_DIR = os.path.join(os.path.dirname(__file__), "models")


class AgronomyPredictor:
    def __init__(self):
        yield_path = os.path.join(MODELS_DIR, "yield_regressor.joblib")
        drought_path = os.path.join(MODELS_DIR, "drought_classifier.joblib")
        pest_path = os.path.join(MODELS_DIR, "pest_classifier.joblib")

        if not (os.path.exists(yield_path) and os.path.exists(drought_path) and os.path.exists(pest_path)):
            from ml_module.train_model import train_and_export_models
            train_and_export_models()

        self.yield_model = joblib.load(yield_path)
        self.drought_model = joblib.load(drought_path)
        self.pest_model = joblib.load(pest_path)

    def predict(self, temperature: float, humidity: float, soil_moisture: float, rainfall: float) -> Dict[str, Any]:
        """
        Executes ML inference for yield, drought, and pest risks.
        """
        features = np.array([[temperature, humidity, soil_moisture, rainfall]])

        # 1. Yield Regression
        predicted_yield = float(self.yield_model.predict(features)[0])
        predicted_yield = round(max(1.0, predicted_yield), 2)

        # 2. Risk Classification
        drought_risk = str(self.drought_model.predict(features)[0])
        pest_risk = str(self.pest_model.predict(features)[0])

        # 3. Actionable Advisory Synthesis
        advisories: List[str] = []

        if drought_risk == "HIGH":
            advisories.append("CRITICAL: Severe moisture deficit detected. Initiate emergency drip/furrow irrigation immediately.")
        elif drought_risk == "MEDIUM":
            advisories.append("WARNING: Sub-optimal soil moisture. Schedule irrigation within next 24-48 hours to prevent wilting.")
        else:
            advisories.append("Soil moisture levels are adequate. Maintain standard irrigation schedule.")

        if pest_risk == "HIGH":
            advisories.append("HIGH ALERT: Warm temperature combined with high humidity favors fungal blast and aphid outbreak. Inspect leaf undersides and apply recommended organic/chemical fungicide.")
        elif pest_risk == "MEDIUM":
            advisories.append("CAUTION: Moderate pest susceptibility conditions. Scout field perimeter for early leaf spot.")
        else:
            advisories.append("Pest/disease proliferation conditions remain low.")

        if rainfall > 80:
            advisories.append("HEAVY RAINFALL: Ensure proper drainage channels are clear to prevent waterlogging and root rot.")

        return {
            "predicted_yield_quintals_per_acre": predicted_yield,
            "drought_risk": drought_risk,
            "pest_risk": pest_risk,
            "advisories": advisories,
            "summary_recommendation": " | ".join(advisories)
        }


# Global singleton instance for high-throughput inference
predictor_instance = AgronomyPredictor()

def get_prediction(temp: float, hum: float, soil: float, rain: float) -> Dict[str, Any]:
    return predictor_instance.predict(temp, hum, soil, rain)


if __name__ == "__main__":
    test_result = get_prediction(33.0, 88.0, 15.0, 5.0)
    print("\nInference Output Test:")
    for k, v in test_result.items():
        print(f"  {k}: {v}")
