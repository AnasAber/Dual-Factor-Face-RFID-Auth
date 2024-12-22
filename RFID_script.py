import serial
import time
import os
import json
from datetime import datetime

class RFIDLogger:
    def __init__(self, port="/dev/ttyACM0", baud=9600, log_file="rfid_log.txt"):
        self.port = port
        self.baud = baud
        self.log_file = log_file
        self.ser = None

        # Ensure log directory exists
        os.makedirs(os.path.dirname(log_file) if os.path.dirname(log_file) else '.', exist_ok=True)

    def connect(self):
        try:
            self.ser = serial.Serial(self.port, self.baud)
            print(f"Connected to Arduino on port: {self.port}")
            return True
        except serial.SerialException as e:
            print(f"Error connecting to port {self.port}: {e}")
            return False

    def log_data(self, data):
        timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        
        # Create structured log entry
        log_entry = {
            "timestamp": timestamp,
            "data": data,
            "type": self._determine_entry_type(data)
        }
        
        # Convert to string
        log_string = json.dumps(log_entry)
        
        # Write to file
        try:
            with open(self.log_file, "a") as file:
                file.write(log_string + "\n")
            return True
        except IOError as e:
            print(f"Error writing to log file: {e}")
            return False

    def _determine_entry_type(self, data):
        if "Card UID" in data:
            return "card_scan"
        elif "Access granted" in data:
            return "access_granted"
        elif "Access denied" in data:
            return "access_denied"
        return "other"

    def run(self):
        if not self.connect():
            return

        print(f"Storing data in {self.log_file}")
        try:
            while True:
                if self.ser.in_waiting > 0:
                    data = self.ser.readline().decode("utf-8").strip()
                    if data:
                        if self.log_data(data):
                            print(f"Logged: {data}")
                        else:
                            print(f"Failed to log: {data}")
                time.sleep(0.1)  # Prevent CPU overuse

        except KeyboardInterrupt:
            print("\nData collection stopped by user.")
        except Exception as e:
            print(f"Unexpected error: {e}")
        finally:
            if self.ser:
                self.ser.close()
                print("Serial connection closed.")

if __name__ == "__main__":
    logger = RFIDLogger()
    logger.run()