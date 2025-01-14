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
        os.makedirs(os.path.dirname(log_file) if os.path.dirname(log_file) else '.', exist_ok=True)

    def connect(self):
        try:
            self.ser = serial.Serial(self.port, self.baud)
            print(f"Connected to Arduino on port: {self.port}")
            return True
        except serial.SerialException as e:
            print(f"Error connecting to port {self.port}: {e}")
            return False

    def parse_rfid_data(self, data):
        # Extract Card UID
        if "Card UID:" in data:
            parts = data.split("|")
            uid = parts[0].replace("Card UID:", "").strip()
            
            # Determine recognition status
            is_recognized = "Card recognized" in data
            
            return {
                "uid": uid,
                "is_recognized": is_recognized,
                "raw_data": data.strip()
            }
        return None

    def log_data(self, data):
        parsed_data = self.parse_rfid_data(data)
        if not parsed_data:
            return False

        timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        log_entry = {
            "timestamp": timestamp,
            "uid": parsed_data["uid"],
            "is_recognized": parsed_data["is_recognized"],
            "raw_data": parsed_data["raw_data"],
            "type": "access_granted" if parsed_data["is_recognized"] else "access_denied"
        }

        try:
            with open(self.log_file, "a") as file:
                file.write(json.dumps(log_entry) + "\n")
            return True
        except IOError as e:
            print(f"Error writing to log file: {e}")
            return False

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
                            parsed = self.parse_rfid_data(data)
                            if parsed:
                                print(f"Card UID: {parsed['uid']} | Recognized: {parsed['is_recognized']}")
                        else:
                            print(f"Failed to log: {data}")
                time.sleep(0.1)
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