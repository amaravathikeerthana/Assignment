"""
CropSense Integration Test Suite
Validates all 5 modules:
1. DBMS Module
2. Data Engineering Module
3. ML Module
4. Full Stack Module
5. OS Module
"""

import os
import sys
import unittest
import time

# Add root directory to sys.path
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from dbms_module.db_manager import init_db, seed_demo_data, get_field_overview, insert_sensor_reading, insert_advisory
from data_engineering_module.etl_pipeline import SensorETLPipeline
from ml_module.yield_risk_predictor import get_prediction
from os_module.sensor_daemon import SensorPollingDaemon
from fullstack_module.backend.app import app


class TestCropSenseModules(unittest.TestCase):

    @classmethod
    def setUpClass(cls):
        cls.test_db = os.path.join(os.path.dirname(__file__), "test_cropsense.db")
        if os.path.exists(cls.test_db):
            try:
                os.remove(cls.test_db)
            except OSError:
                pass
        init_db(db_path=cls.test_db)
        seed_demo_data(db_path=cls.test_db)

    @classmethod
    def tearDownClass(cls):
        if os.path.exists(cls.test_db):
            try:
                os.remove(cls.test_db)
            except OSError:
                pass

    def test_01_dbms_module(self):
        """Test DBMS schema, foreign keys, and relational joins."""
        overview = get_field_overview(db_path=self.test_db)
        self.assertGreaterEqual(len(overview), 4)
        self.assertEqual(overview[0]["farmer_name"], "Ramesh Patel")

        # Test insert telemetry and advisory
        rid = insert_sensor_reading(1, 29.5, 60.0, 45.0, 10.0, db_path=self.test_db)
        aid = insert_advisory(1, 14.5, "LOW", "LOW", "Optimal conditions.", db_path=self.test_db)
        self.assertIsInstance(rid, int)
        self.assertIsInstance(aid, int)

    def test_02_data_engineering_module(self):
        """Test Data Engineering ETL anomaly detection & cleaning."""
        pipeline = SensorETLPipeline(db_path=self.test_db)
        dirty_batch = [
            {"field_id": 1, "temperature": 27.0, "humidity": 60.0, "soil_moisture": 50.0, "rainfall": 5.0}, # valid
            {"field_id": 1, "temperature": 150.0, "humidity": 50.0, "soil_moisture": 40.0, "rainfall": 0.0}, # outlier
            {"field_id": 2, "temperature": 25.0, "humidity": -5.0, "soil_moisture": 30.0, "rainfall": 0.0},  # invalid hum
            {"field_id": 3, "temperature": None, "humidity": 70.0, "soil_moisture": 40.0, "rainfall": 0.0}    # missing
        ]
        result = pipeline.run_pipeline(dirty_batch)
        self.assertEqual(len(result["sample_clean"]), 1)
        self.assertEqual(pipeline.stats["cleaned"], 1)
        self.assertEqual(pipeline.stats["quarantined"], 3)

    def test_03_ml_module(self):
        """Test ML regression and risk classification inference."""
        # Extreme drought conditions: high temp, low moisture, low rain, low humidity
        pred_drought = get_prediction(temp=40.0, hum=22.0, soil=10.0, rain=0.0)
        self.assertIn("predicted_yield_quintals_per_acre", pred_drought)
        self.assertGreater(pred_drought["predicted_yield_quintals_per_acre"], 0)
        self.assertIn(pred_drought["drought_risk"], ["MEDIUM", "HIGH"])

        # High pest conditions: warm temp + very high humidity
        pred_pest = get_prediction(temp=28.0, hum=92.0, soil=50.0, rain=20.0)
        self.assertEqual(pred_pest["pest_risk"], "HIGH")
        self.assertGreater(len(pred_pest["advisories"]), 0)

    def test_04_os_module(self):
        """Test OS multi-threaded producer-consumer sensor daemon."""
        daemon = SensorPollingDaemon(buffer_capacity=15, poll_interval=0.5, db_path=self.test_db)
        daemon.start()
        time.sleep(1.8)
        status = daemon.get_status()
        daemon.stop()

        self.assertGreater(status["metrics"]["packets_produced"], 0)
        self.assertGreater(status["metrics"]["packets_consumed"], 0)
        self.assertEqual(status["metrics"]["packets_dropped"], 0)

    def test_05_fullstack_module_api(self):
        """Test Full Stack Flask REST API endpoints."""
        client = app.test_client()
        # Health check
        res_health = client.get("/api/health")
        self.assertEqual(res_health.status_code, 200)

        # Overview
        res_overview = client.get("/api/overview")
        self.assertEqual(res_overview.status_code, 200)

        # Predict endpoint
        res_pred = client.post("/api/predict", json={
            "field_id": 1,
            "temperature": 28.0,
            "humidity": 65.0,
            "soil_moisture": 50.0,
            "rainfall": 15.0
        })
        self.assertEqual(res_pred.status_code, 200)
        body = res_pred.get_json()
        self.assertEqual(body["status"], "success")
        self.assertIn("predicted_yield_quintals_per_acre", body["results"])


if __name__ == "__main__":
    unittest.main()
