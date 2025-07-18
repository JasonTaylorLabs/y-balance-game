"""
sensors.py - Laser Sensor Interface for Y-Balance Game

This module provides the LaserArray class, which reads real-time distance data from an Arduino Mega
streaming three laser sensors over USB serial. It maintains the latest mm readings for each sensor,
handles serial errors, and provides robust error and timeout handling for debugging.

Debugging Tips:
- If the serial port cannot be opened, a clear error is logged and raised.
- If no data is received for a sensor for >2s, a warning is logged and None is returned.
- To debug sensor data, print self.dist and self.last_update.
- To debug serial issues, check logs for [FATAL] and [WARN] messages.

Author: Mark Rowley
"""

import serial
import threading
import time
import logging

class LaserArray:
    """
    Manages serial communication with the Arduino Mega and provides
    real-time access to the latest mm readings for each of three sensors.
    """
    def __init__(self, port="/dev/ttyACM0", baud=115200):
        """
        Initialize the serial connection and start the background reader thread.
        Raises RuntimeError if the port cannot be opened.
        """
        self.dist = {"1": None, "2": None, "3": None}
        self.last_update = {"1": None, "2": None, "3": None}
        try:
            self.ser = serial.Serial(port, baud, timeout=0.1)
        except serial.SerialException as e:
            logging.error(f"[FATAL] Could not open serial port {port}: {e}")
            raise RuntimeError(f"Could not open serial port {port}: {e}")
        time.sleep(2)  # allow the Mega to reset
        threading.Thread(target=self._reader, daemon=True).start()

    def _reader(self):
        """
        Background thread: Continuously reads lines from the serial port,
        parses sensor data, and updates the latest readings and timestamps.
        Logs warnings for serial errors and skips malformed lines.
        """
        while True:
            try:
                raw = self.ser.readline()
            except serial.SerialException as e:
                logging.warning(f"[WARN] Serial read error: {e}")
                continue
            line = raw.decode("ascii", errors="ignore").strip()
            if not line or "," not in line:
                continue
            sid, val = line.split(",", 1)
            try:
                cm = float(val)
                self.dist[sid] = cm * 10
                self.last_update[sid] = time.time()
            except ValueError:
                continue

    def read_distance(self, idx, timeout=2.0):
        """
        Return the latest mm reading for sensor idx (0,1,2), or None if not available
        or if the last update was more than 'timeout' seconds ago.
        Logs a warning if data is stale.
        """
        sid = str(idx+1)
        val = self.dist.get(sid)
        last = self.last_update.get(sid)
        if val is not None and last is not None:
            if time.time() - last > timeout:
                logging.warning(f"[WARN] No recent data for sensor {sid} (last update > {timeout}s ago)")
                return None
        return val