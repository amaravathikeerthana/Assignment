"""
DBMS Module: Database Manager for CropSense
Handles database setup, seeding, and relational queries for:
- Farmers
- Fields
- Sensor Readings
- Advisories
"""

import sqlite3
import os
from typing import List, Dict, Any, Optional

DB_PATH = os.path.join(os.path.dirname(__file__), "cropsense_master.db")
SCHEMA_PATH = os.path.join(os.path.dirname(__file__), "schema.sql")


def get_connection(db_path: str = DB_PATH) -> sqlite3.Connection:
    conn = sqlite3.connect(db_path, timeout=30.0, check_same_thread=False)
    conn.row_factory = sqlite3.Row
    conn.execute("PRAGMA foreign_keys = ON;")
    try:
        conn.execute("PRAGMA journal_mode = WAL;")
    except Exception:
        pass
    return conn


def init_db(db_path: str = DB_PATH, schema_path: str = SCHEMA_PATH) -> None:
    """Initializes the database using the SQL schema."""
    with open(schema_path, "r", encoding="utf-8") as f:
        schema_sql = f.read()

    with get_connection(db_path) as conn:
        conn.executescript(schema_sql)
        conn.commit()
    print("[DBMS] Database initialized successfully.")


def seed_demo_data(db_path: str = DB_PATH) -> None:
    """Seeds realistic demo data into farmers and fields tables."""
    with get_connection(db_path) as conn:
        cursor = conn.cursor()
        
        # Check if already seeded
        cursor.execute("SELECT COUNT(*) FROM farmers")
        if cursor.fetchone()[0] > 0:
            return

        # Insert Farmers
        farmers_data = [
            ("Ramesh Patel", "+91 98765 43210", "ramesh@farm.in", "Anand, Gujarat"),
            ("Suresh Kumar", "+91 91234 56789", "suresh@farm.in", "Guntur, Andhra Pradesh"),
            ("Lakshmi Devi", "+91 94567 12345", "lakshmi@farm.in", "Mandya, Karnataka")
        ]
        cursor.executemany("""
            INSERT INTO farmers (full_name, phone_number, email, village_district)
            VALUES (?, ?, ?, ?)
        """, farmers_data)

        # Insert Fields
        fields_data = [
            (1, "North Plot A", "Cotton", "Black Soil", 5.5, 22.56, 72.95),
            (1, "South Plot B", "Wheat", "Alluvial", 3.0, 22.57, 72.96),
            (2, "Riverfront Field", "Chilli", "Red Sandy Loam", 4.2, 16.30, 80.44),
            (3, "Canal Field", "Paddy (Rice)", "Clay Loam", 6.0, 12.52, 76.89)
        ]
        cursor.executemany("""
            INSERT INTO fields (farmer_id, field_name, crop_type, soil_type, area_acres, latitude, longitude)
            VALUES (?, ?, ?, ?, ?, ?, ?)
        """, fields_data)

        conn.commit()
        print("[DBMS] Seeded sample farmers and agricultural fields.")
    seed_baseline_telemetry(db_path)


def seed_baseline_telemetry(db_path: str = DB_PATH) -> None:
    """Populates baseline telemetry and advisories for fields without any readings."""
    conn = get_connection(db_path)
    try:
        cursor = conn.cursor()
        fields = cursor.execute("SELECT field_id, crop_type FROM fields").fetchall()
        for f in fields:
            fid = f["field_id"]
            count = cursor.execute("SELECT COUNT(*) FROM sensor_readings WHERE field_id = ?", (fid,)).fetchone()[0]
            if count == 0:
                defaults = {
                    1: (28.0, 62.0, 48.0, 15.0, 12.35, "LOW", "LOW", "Optimal conditions for vegetative growth."),
                    2: (24.5, 68.0, 52.0, 18.0, 14.20, "LOW", "LOW", "Adequate moisture for wheat tillering."),
                    3: (31.0, 60.0, 36.0, 0.0, 10.15, "MEDIUM", "LOW", "Soil moisture dropping. Plan irrigation within 48h."),
                    4: (29.0, 84.0, 70.0, 35.0, 16.80, "LOW", "MEDIUM", "Warm and humid. Monitor canopy for fungal risk.")
                }.get(fid, (28.0, 65.0, 50.0, 10.0, 12.0, "LOW", "LOW", "Field condition nominal."))

                cursor.execute("""
                    INSERT INTO sensor_readings (field_id, temperature, humidity, soil_moisture, rainfall, is_valid)
                    VALUES (?, ?, ?, ?, ?, 1)
                """, (fid, defaults[0], defaults[1], defaults[2], defaults[3]))

                cursor.execute("""
                    INSERT INTO advisories (field_id, predicted_yield, drought_risk, pest_risk, recommended_action)
                    VALUES (?, ?, ?, ?, ?)
                """, (fid, defaults[4], defaults[5], defaults[6], defaults[7]))
        conn.commit()
    finally:
        conn.close()


def insert_sensor_reading(
    field_id: int,
    temperature: float,
    humidity: float,
    soil_moisture: float,
    rainfall: float,
    is_valid: bool = True,
    db_path: str = DB_PATH
) -> int:
    """Inserts a single sensor telemetry record."""
    conn = get_connection(db_path)
    try:
        cursor = conn.cursor()
        cursor.execute("""
            INSERT INTO sensor_readings (field_id, temperature, humidity, soil_moisture, rainfall, is_valid)
            VALUES (?, ?, ?, ?, ?, ?)
        """, (field_id, temperature, humidity, soil_moisture, rainfall, 1 if is_valid else 0))
        conn.commit()
        return cursor.lastrowid
    finally:
        conn.close()


def insert_advisory(
    field_id: int,
    predicted_yield: float,
    drought_risk: str,
    pest_risk: str,
    recommended_action: str,
    db_path: str = DB_PATH
) -> int:
    """Inserts a generated advisory record."""
    conn = get_connection(db_path)
    try:
        cursor = conn.cursor()
        cursor.execute("""
            INSERT INTO advisories (field_id, predicted_yield, drought_risk, pest_risk, recommended_action)
            VALUES (?, ?, ?, ?, ?)
        """, (field_id, predicted_yield, drought_risk, pest_risk, recommended_action))
        conn.commit()
        return cursor.lastrowid
    finally:
        conn.close()


def get_field_overview(db_path: str = DB_PATH) -> List[Dict[str, Any]]:
    """Joins farmers, fields, and latest advisories."""
    query = """
        SELECT 
            f.farmer_id, f.full_name AS farmer_name, f.phone_number,
            fd.field_id, fd.field_name, fd.crop_type, fd.soil_type, fd.area_acres,
            sr.temperature, sr.humidity, sr.soil_moisture, sr.rainfall, sr.recorded_at AS sensor_time,
            adv.predicted_yield, adv.drought_risk, adv.pest_risk, adv.recommended_action
        FROM fields fd
        JOIN farmers f ON fd.farmer_id = f.farmer_id
        LEFT JOIN (
            SELECT field_id, temperature, humidity, soil_moisture, rainfall, recorded_at
            FROM sensor_readings
            WHERE reading_id IN (SELECT MAX(reading_id) FROM sensor_readings GROUP BY field_id)
        ) sr ON fd.field_id = sr.field_id
        LEFT JOIN (
            SELECT field_id, predicted_yield, drought_risk, pest_risk, recommended_action
            FROM advisories
            WHERE advisory_id IN (SELECT MAX(advisory_id) FROM advisories GROUP BY field_id)
        ) adv ON fd.field_id = adv.field_id
        ORDER BY fd.field_id ASC
    """
    conn = get_connection(db_path)
    try:
        cursor = conn.cursor()
        rows = cursor.execute(query).fetchall()
        return [dict(row) for row in rows]
    finally:
        conn.close()


def get_recent_history(limit: int = 30, db_path: str = DB_PATH) -> List[Dict[str, Any]]:
    """Fetches the newest stored sensor telemetry records with corresponding field details."""
    query = """
        SELECT 
            sr.reading_id, sr.field_id, fd.field_name, fd.crop_type, f.full_name AS farmer_name,
            sr.temperature, sr.humidity, sr.soil_moisture, sr.rainfall, sr.recorded_at,
            adv.predicted_yield, adv.drought_risk, adv.pest_risk, adv.recommended_action
        FROM sensor_readings sr
        JOIN fields fd ON sr.field_id = fd.field_id
        JOIN farmers f ON fd.farmer_id = f.farmer_id
        LEFT JOIN advisories adv ON sr.field_id = adv.field_id 
             AND abs(strftime('%s', sr.recorded_at) - strftime('%s', adv.issued_at)) <= 2
        ORDER BY sr.reading_id DESC
        LIMIT ?
    """
    conn = get_connection(db_path)
    try:
        cursor = conn.cursor()
        rows = cursor.execute(query, (limit,)).fetchall()
        return [dict(row) for row in rows]
    finally:
        conn.close()


def get_db_stats(db_path: str = DB_PATH) -> Dict[str, int]:
    """Returns total row counts in all core database tables."""
    conn = get_connection(db_path)
    try:
        c = conn.cursor()
        return {
            "farmers": c.execute("SELECT COUNT(*) FROM farmers").fetchone()[0],
            "fields": c.execute("SELECT COUNT(*) FROM fields").fetchone()[0],
            "sensor_readings": c.execute("SELECT COUNT(*) FROM sensor_readings").fetchone()[0],
            "advisories": c.execute("SELECT COUNT(*) FROM advisories").fetchone()[0]
        }
    finally:
        conn.close()


def delete_sensor_reading(reading_id: int, db_path: str = DB_PATH) -> bool:
    """Deletes a specific sensor reading by its ID."""
    conn = get_connection(db_path)
    try:
        cursor = conn.cursor()
        cursor.execute("DELETE FROM sensor_readings WHERE reading_id = ?", (reading_id,))
        deleted = cursor.rowcount > 0
        conn.commit()
        return deleted
    finally:
        conn.close()


def clear_all_telemetry(db_path: str = DB_PATH) -> bool:
    """Clears all stored sensor readings and advisories, keeping farmers and fields intact."""
    conn = get_connection(db_path)
    try:
        cursor = conn.cursor()
        cursor.execute("DELETE FROM sensor_readings")
        cursor.execute("DELETE FROM advisories")
        # Reset sqlite auto-increment sequence for clean IDs
        cursor.execute("DELETE FROM sqlite_sequence WHERE name IN ('sensor_readings', 'advisories')")
        conn.commit()
        return True
    finally:
        conn.close()


if __name__ == "__main__":
    init_db()
    seed_demo_data()
    overview = get_field_overview()
    print(f"[DBMS] Fetched {len(overview)} field summaries.")
