"""
OS Module: Multi-Threaded Daemon Simulation for Sensor Polling & Buffering
Demonstrates operating system principles:
1. Producer-Consumer Architecture (Thread-Safe Ring/Bounded Buffer)
2. Daemon Threads (continuous background polling)
3. Concurrency Synchronization (Locks, Events, Bounded Queue)
4. Graceful termination and telemetry buffering metrics
"""

import os
import sys
import time
import random
import queue
import logging
import threading
from typing import Dict, Any

# Add project root to sys.path
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))
from data_engineering_module.etl_pipeline import SensorETLPipeline

logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(levelname)s] (%(threadName)s) %(message)s")


class SensorPollingDaemon:
    """
    OS-level multi-threaded simulation:
    - Producer thread polls simulated IoT field nodes.
    - Bounded FIFO queue acts as the memory buffer.
    - Consumer worker thread pulls from buffer, runs ETL, and writes to storage.
    """

    def __init__(self, buffer_capacity: int = 50, poll_interval: float = 2.0, db_path: str = None):
        self.buffer_capacity = buffer_capacity
        self.poll_interval = poll_interval
        self.buffer = queue.Queue(maxsize=buffer_capacity)
        self.stop_event = threading.Event()
        self.pipeline = SensorETLPipeline(db_path=db_path)
        self.lock = threading.Lock()

        # Telemetry metrics
        self.metrics = {
            "packets_produced": 0,
            "packets_consumed": 0,
            "packets_dropped": 0
        }

    def _producer_job(self):
        """Simulates IoT hardware polling across agricultural plots."""
        field_ids = [1, 2, 3, 4]
        logging.info("[Producer Daemon] Starting continuous IoT telemetry polling loop...")

        while not self.stop_event.is_set():
            for fid in field_ids:
                # Simulate sensor readings with physical fluctuations
                reading: Dict[str, Any] = {
                    "field_id": fid,
                    "temperature": round(random.gauss(30.0, 4.0), 2),
                    "humidity": round(random.gauss(65.0, 15.0), 2),
                    "soil_moisture": round(random.gauss(45.0, 18.0), 2),
                    "rainfall": round(max(0.0, random.expovariate(0.1) if random.random() < 0.2 else 0.0), 2),
                    "timestamp": time.time()
                }

                # Attempt to enqueue in bounded buffer
                try:
                    self.buffer.put(reading, timeout=0.5)
                    with self.lock:
                        self.metrics["packets_produced"] += 1
                except queue.Full:
                    with self.lock:
                        self.metrics["packets_dropped"] += 1
                    logging.warning(f"[Producer Daemon] Buffer overflow! Dropped reading for Field {fid}")

            # Polling cycle sleep with responsive check for stop_event
            self.stop_event.wait(self.poll_interval)

        logging.info("[Producer Daemon] Stopped gracefully.")

    def _consumer_job(self):
        """Worker thread that consumes from buffer and triggers ETL pipeline."""
        logging.info("[Consumer Daemon] Starting ingestion worker from buffer...")
        batch = []

        while not self.stop_event.is_set() or not self.buffer.empty():
            try:
                # Dequeue reading with timeout to allow checking stop_event
                reading = self.buffer.get(timeout=1.0)
                batch.append(reading)
                self.buffer.task_done()
                with self.lock:
                    self.metrics["packets_consumed"] += 1

                # Flush in micro-batches of 4 or when queue is drained
                if len(batch) >= 4 or self.buffer.empty():
                    self.pipeline.run_pipeline(batch)
                    batch = []

            except queue.Empty:
                continue

        # Flush any remaining items
        if batch:
            self.pipeline.run_pipeline(batch)
        logging.info("[Consumer Daemon] Ingestion worker finished remaining buffer items.")

    def start(self):
        """Launches producer and consumer as background daemon threads."""
        self.producer_thread = threading.Thread(
            target=self._producer_job,
            name="SensorProducerThread",
            daemon=True
        )
        self.consumer_thread = threading.Thread(
            target=self._consumer_job,
            name="ETLConsumerThread",
            daemon=True
        )

        self.producer_thread.start()
        self.consumer_thread.start()
        logging.info("[OS Module] Both daemon threads initialized and running in background.")

    def stop(self):
        """Signals shutdown and joins threads."""
        logging.info("[OS Module] Halting daemon threads...")
        self.stop_event.set()
        self.producer_thread.join(timeout=3.0)
        self.consumer_thread.join(timeout=3.0)
        logging.info(f"[OS Module] System halted. Final OS Metrics: {self.metrics}")

    def get_status(self) -> Dict[str, Any]:
        with self.lock:
            return {
                "buffer_size": self.buffer.qsize(),
                "buffer_capacity": self.buffer_capacity,
                "metrics": dict(self.metrics)
            }


if __name__ == "__main__":
    print("[OS Module] Launching multi-threaded sensor polling daemon for 6 seconds...")
    daemon = SensorPollingDaemon(buffer_capacity=20, poll_interval=1.5)
    daemon.start()

    time.sleep(5.0)
    print("\n--- Current Buffer Status ---")
    print(daemon.get_status())
    print("-----------------------------\n")

    daemon.stop()
    print("[OS Module] Daemon simulation completed.")
