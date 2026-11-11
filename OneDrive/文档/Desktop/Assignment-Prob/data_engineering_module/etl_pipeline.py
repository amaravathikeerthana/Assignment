"""
Data Engineering Module: ETL Pipeline
Ingests, cleans, validates, and transforms raw weather and soil data streams
before loading into the central DBMS storage.
"""

import os
import sys
import json
import logging
from typing import List, Dict, Tuple, Any
from datetime import datetime

# Add project root to sys.path
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))
from dbms_module.db_manager import insert_sensor_reading, init_db

logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(levelname)s] %(message)s")


class SensorETLPipeline:
    """ETL Pipeline for streaming & batch soil/weather sensor data."""

    # Sensor physical bounds
    VALID_RANGES = {
        "temperature": (-10.0, 55.0),    # °C
        "humidity": (0.0, 100.0),        # %
        "soil_moisture": (0.0, 100.0),   # %
        "rainfall": (0.0, 400.0)         # mm
    }

    def __init__(self, db_path: str = None):
        self.db_path = db_path
        self.stats = {"ingested": 0, "cleaned": 0, "quarantined": 0}

    def extract(self, raw_records: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """Extract step: Ingest raw batch or stream from IoT payload."""
        logging.info(f"[Extract] Received batch of {len(raw_records)} raw telemetry records.")
        self.stats["ingested"] += len(raw_records)
        return raw_records

    def transform(self, records: List[Dict[str, Any]]) -> Tuple[List[Dict[str, Any]], List[Dict[str, Any]]]:
        """
        Transform & Clean step:
        - Validates numeric types
        - Handles missing/null values
        - Filters physical outliers (anomalies)
        - Computes derived meteorological metrics (e.g., VPD - Vapor Pressure Deficit)
        """
        clean_batch = []
        quarantine_batch = []

        for record in records:
            field_id = record.get("field_id")
            temp = record.get("temperature")
            humidity = record.get("humidity")
            soil = record.get("soil_moisture")
            rain = record.get("rainfall", 0.0)

            # Check for null / None
            if None in (field_id, temp, humidity, soil):
                quarantine_batch.append({"record": record, "reason": "Missing required sensor attributes"})
                continue

            try:
                temp = float(temp)
                humidity = float(humidity)
                soil = float(soil)
                rain = float(rain)
            except (ValueError, TypeError):
                quarantine_batch.append({"record": record, "reason": "Type conversion error (non-numeric)"})
                continue

            # Outlier / Range validation
            anomalies = []
            for metric, (low, high) in self.VALID_RANGES.items():
                val = {"temperature": temp, "humidity": humidity, "soil_moisture": soil, "rainfall": rain}[metric]
                if not (low <= val <= high):
                    anomalies.append(f"{metric}={val} out of valid bounds [{low}, {high}]")

            if anomalies:
                quarantine_batch.append({"record": record, "reason": "; ".join(anomalies)})
                continue

            # Feature Engineering: Vapor Pressure Deficit (VPD in kPa)
            # Saturation vapor pressure: es = 0.61078 * exp((17.27 * T) / (T + 237.3))
            import math
            es = 0.61078 * math.exp((17.27 * temp) / (temp + 237.3))
            ea = es * (humidity / 100.0)
            vpd = max(0.0, es - ea)

            transformed_record = {
                "field_id": int(field_id),
                "temperature": round(temp, 2),
                "humidity": round(humidity, 2),
                "soil_moisture": round(soil, 2),
                "rainfall": round(rain, 2),
                "vpd_kpa": round(vpd, 3),
                "is_valid": True,
                "processed_at": datetime.utcnow().isoformat()
            }
            clean_batch.append(transformed_record)

        self.stats["cleaned"] += len(clean_batch)
        self.stats["quarantined"] += len(quarantine_batch)
        logging.info(f"[Transform] Cleaned: {len(clean_batch)}, Quarantined (anomalies): {len(quarantine_batch)}")
        return clean_batch, quarantine_batch

    def load(self, clean_records: List[Dict[str, Any]]) -> int:
        """Load step: Inserts validated, sanitized records into database."""
        loaded_count = 0
        for item in clean_records:
            try:
                insert_sensor_reading(
                    field_id=item["field_id"],
                    temperature=item["temperature"],
                    humidity=item["humidity"],
                    soil_moisture=item["soil_moisture"],
                    rainfall=item["rainfall"],
                    is_valid=item["is_valid"],
                    db_path=self.db_path
                ) if self.db_path else None
                loaded_count += 1
            except Exception as e:
                logging.error(f"[Load Error] Failed to persist record: {e}")
        logging.info(f"[Load] Successfully loaded {loaded_count} records into DBMS.")
        return loaded_count

    def run_pipeline(self, raw_data_stream: List[Dict[str, Any]]) -> Dict[str, Any]:
        """Executes full ETL cycle."""
        extracted = self.extract(raw_data_stream)
        cleaned, quarantined = self.transform(extracted)
        self.load(cleaned)
        return {
            "status": "SUCCESS",
            "stats": self.stats,
            "sample_clean": cleaned[:2],
            "sample_quarantined": quarantined[:2]
        }


if __name__ == "__main__":
    init_db()
    # Demonstration with normal data and dirty / corrupted IoT packets
    raw_stream = [
        {"field_id": 1, "temperature": 28.5, "humidity": 65.0, "soil_moisture": 42.0, "rainfall": 0.0},
        {"field_id": 1, "temperature": 999.0, "humidity": 70.0, "soil_moisture": 30.0, "rainfall": 0.0}, # Outlier temp
        {"field_id": 2, "temperature": 32.1, "humidity": -15.0, "soil_moisture": 50.0, "rainfall": 5.0}, # Negative humidity
        {"field_id": 2, "temperature": 31.0, "humidity": 88.0, "soil_moisture": 18.0, "rainfall": 0.0},  # Valid
        {"field_id": 3, "temperature": None, "humidity": 80.0, "soil_moisture": 40.0, "rainfall": 10.0}, # Null sensor
        {"field_id": 3, "temperature": 24.0, "humidity": 75.0, "soil_moisture": 62.0, "rainfall": 45.0}  # Valid
    ]

    pipeline = SensorETLPipeline()
    result = pipeline.run_pipeline(raw_stream)
    print("\nETL Pipeline Execution Summary:")
    print(json.dumps(result, indent=2))
