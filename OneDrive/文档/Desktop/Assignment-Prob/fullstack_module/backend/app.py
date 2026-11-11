"""
Full Stack Module - Backend REST API (Flask)
Deployable on Render (free tier)
Endpoints:
- GET  /api/health
- GET  /api/fields
- GET  /api/overview
- POST /api/predict
- POST /api/daemon/start
- POST /api/daemon/stop
- GET  /api/daemon/status
"""

import os
import sys
from flask import Flask, request, jsonify, send_from_directory
from flask_cors import CORS

# Add project root to sys.path
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "../..")))
from dbms_module.db_manager import (
    init_db, seed_demo_data, get_field_overview, 
    insert_advisory, insert_sensor_reading, 
    get_recent_history, get_db_stats,
    delete_sensor_reading, clear_all_telemetry
)
from ml_module.yield_risk_predictor import get_prediction
from os_module.sensor_daemon import SensorPollingDaemon

app = Flask(__name__, static_folder="../frontend", static_url_path="")
CORS(app, resources={r"/*": {"origins": "*"}})

# Ensure database is prepared
init_db()
seed_demo_data()

# Shared sensor daemon instance
sensor_daemon = SensorPollingDaemon(buffer_capacity=50, poll_interval=3.0)


@app.before_request
def handle_preflight():
    if request.method == "OPTIONS":
        res = app.make_default_options_response()
        res.headers["Access-Control-Allow-Origin"] = "*"
        res.headers["Access-Control-Allow-Headers"] = "Content-Type,Authorization"
        res.headers["Access-Control-Allow-Methods"] = "GET,POST,DELETE,OPTIONS"
        res.headers["Access-Control-Allow-Private-Network"] = "true"
        return res


@app.after_request
def add_cors_headers(response):
    response.headers["Access-Control-Allow-Origin"] = "*"
    response.headers["Access-Control-Allow-Headers"] = "Content-Type,Authorization"
    response.headers["Access-Control-Allow-Methods"] = "GET,POST,DELETE,OPTIONS"
    response.headers["Access-Control-Allow-Private-Network"] = "true"
    return response


@app.route("/")
def index():
    return send_from_directory(app.static_folder, "index.html")


@app.route("/api/health", methods=["GET", "OPTIONS"])
def health():
    return jsonify({
        "status": "healthy",
        "service": "CropSense Advisory API",
        "database": "connected",
        "version": "1.0.0"
    }), 200


@app.route("/api/overview", methods=["GET"])
def overview():
    try:
        data = get_field_overview()
        return jsonify({"status": "success", "data": data}), 200
    except Exception as e:
        return jsonify({"status": "error", "message": str(e)}), 500


@app.route("/api/history", methods=["GET"])
def history():
    try:
        limit = int(request.args.get("limit", 25))
        data = get_recent_history(limit=limit)
        return jsonify({"status": "success", "data": data}), 200
    except Exception as e:
        return jsonify({"status": "error", "message": str(e)}), 500


@app.route("/api/history/<int:reading_id>", methods=["DELETE", "POST"])
def delete_record(reading_id):
    try:
        success = delete_sensor_reading(reading_id)
        if success:
            return jsonify({"status": "success", "message": f"Record #{reading_id} deleted."}), 200
        else:
            return jsonify({"status": "error", "message": f"Record #{reading_id} not found."}), 404
    except Exception as e:
        return jsonify({"status": "error", "message": str(e)}), 500


@app.route("/api/history/clear", methods=["POST", "DELETE"])
def clear_records():
    try:
        clear_all_telemetry()
        return jsonify({"status": "success", "message": "All telemetry and advisory records cleared."}), 200
    except Exception as e:
        return jsonify({"status": "error", "message": str(e)}), 500


@app.route("/api/stats", methods=["GET"])
def stats():
    try:
        data = get_db_stats()
        return jsonify({"status": "success", "data": data}), 200
    except Exception as e:
        return jsonify({"status": "error", "message": str(e)}), 500


@app.route("/api/predict", methods=["POST"])
def predict_and_advise():
    """
    Receives current field readings, calls ML models, logs to DB,
    and returns comprehensive advisory output.
    """
    payload = request.get_json(force=True, silent=True) or {}
    try:
        temp = float(payload.get("temperature", 30.0))
        hum = float(payload.get("humidity", 65.0))
        soil = float(payload.get("soil_moisture", 40.0))
        rain = float(payload.get("rainfall", 0.0))
        field_id = int(payload.get("field_id", 1))

        # Basic bounds validation
        if not (-10 <= temp <= 60 and 0 <= hum <= 100 and 0 <= soil <= 100 and 0 <= rain <= 500):
            return jsonify({"status": "error", "message": "Sensor values outside physical limits."}), 400

        # ML Inference
        prediction = get_prediction(temp, hum, soil, rain)

        # Log into DBMS
        insert_sensor_reading(field_id, temp, hum, soil, rain, is_valid=True)
        insert_advisory(
            field_id=field_id,
            predicted_yield=prediction["predicted_yield_quintals_per_acre"],
            drought_risk=prediction["drought_risk"],
            pest_risk=prediction["pest_risk"],
            recommended_action=prediction["summary_recommendation"]
        )

        return jsonify({
            "status": "success",
            "field_id": field_id,
            "inputs": {
                "temperature": temp,
                "humidity": hum,
                "soil_moisture": soil,
                "rainfall": rain
            },
            "results": prediction
        }), 200

    except ValueError as ve:
        return jsonify({"status": "error", "message": f"Invalid numerical inputs: {ve}"}), 400
    except Exception as e:
        return jsonify({"status": "error", "message": str(e)}), 500


@app.route("/api/daemon/start", methods=["POST"])
def daemon_start():
    if not hasattr(sensor_daemon, "producer_thread") or not sensor_daemon.producer_thread.is_alive():
        sensor_daemon.start()
        return jsonify({"status": "success", "message": "OS sensor polling daemon started."}), 200
    return jsonify({"status": "running", "message": "Daemon already active."}), 200


@app.route("/api/daemon/stop", methods=["POST"])
def daemon_stop():
    sensor_daemon.stop()
    return jsonify({"status": "success", "message": "OS sensor polling daemon stopped."}), 200


@app.route("/api/daemon/status", methods=["GET"])
def daemon_status():
    status = sensor_daemon.get_status()
    is_alive = hasattr(sensor_daemon, "producer_thread") and sensor_daemon.producer_thread.is_alive()
    status["is_running"] = is_alive
    return jsonify({"status": "success", "data": status}), 200


if __name__ == "__main__":
    port = int(os.environ.get("PORT", 5000))
    print(f"[FullStack] Starting CropSense backend API on port {port}...")
    app.run(host="0.0.0.0", port=port, debug=True)
