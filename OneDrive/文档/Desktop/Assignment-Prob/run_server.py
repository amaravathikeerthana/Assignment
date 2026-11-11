"""
CropSense Launcher
Starts the Flask Backend API, connects the SQLite database,
and opens the Farmer Advisory Dashboard in your web browser.
"""

import os
import sys
import webbrowser
import threading
import time

# Ensure UTF-8 output on Windows consoles
if hasattr(sys.stdout, "reconfigure"):
    try:
        sys.stdout.reconfigure(encoding="utf-8")
    except Exception:
        pass

# Ensure directory is in path
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from fullstack_module.backend.app import app
from dbms_module.db_manager import init_db, seed_demo_data, DB_PATH


def open_browser():
    time.sleep(1.2)
    url = "http://127.0.0.1:5000"
    print(f"\n[CropSense] Opening Web Dashboard at: {url}")
    webbrowser.open(url)


def main():
    print("=" * 60)
    print("       CropSense Precision Agriculture System")
    print("=" * 60)
    print("[1/3] Initializing SQLite database...")
    init_db()
    seed_demo_data()
    print("[2/3] Database ready at: cropsense_master.db")
    print("[3/3] Starting backend REST server on port 5000...")

    # Open browser in a background timer
    threading.Thread(target=open_browser, daemon=True).start()

    # Start Flask (0.0.0.0 allows both localhost and 127.0.0.1)
    app.run(host="0.0.0.0", port=5000, debug=False)


if __name__ == "__main__":
    main()
