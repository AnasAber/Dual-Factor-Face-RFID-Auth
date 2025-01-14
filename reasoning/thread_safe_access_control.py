import sys
import os
project_root = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
sys.path.append(project_root)
from reasoning.RFID_script import RFIDLogger
from reasoning.access_control import AccessControl
import cv2
import time
from threading import Thread, Lock
from queue import Queue
import os
import sqlite3

class AccessControlSystem:
    def __init__(self, camera_index=0, db_path="../access_control.db"):
        self.db_path = db_path
        self.rfid_logger = RFIDLogger()
        
        # Initialize camera with proper error handling
        print("Initializing camera...")
        self.camera = cv2.VideoCapture(int(camera_index))  # Ensure camera_index is an integer
        
        # Check if camera opened successfully
        if not self.camera.isOpened():
            print("Error: Could not open camera")
            print("Please check if:")
            print("- A webcam is connected to your computer")
            print("- The webcam isn't being used by another application")
            print("- You have permission to access the camera")
            raise RuntimeError("Failed to initialize camera")
            
        # Test camera by capturing one frame
        ret, frame = self.camera.read()
        if not ret:
            print("Error: Could not read frame from camera")
            self.camera.release()
            raise RuntimeError("Failed to capture test frame")
            
        print("Camera initialized successfully!")
        
        self.event_queue = Queue()
        os.makedirs("captures", exist_ok=True)
        self.is_running = True
        self.db_lock = Lock()

    def get_db_connection(self):
        """Creates a new database connection for the calling thread."""
        conn = sqlite3.connect(self.db_path)
        return conn

    def capture_photo(self):
        """
        Captures a photo when an RFID card is detected.
        Includes error handling and retry logic.
        """
        # Try up to 3 times to capture a photo
        for attempt in range(3):
            if not self.camera.isOpened():
                print("Error: Camera is not open")
                return None
                
            ret, frame = self.camera.read()
            if ret:
                timestamp = time.strftime("%Y%m%d-%H%M%S")
                photo_path = f"captures/face_{timestamp}.jpg"
                
                try:
                    cv2.imwrite(photo_path, frame)
                    print(f"Photo captured successfully: {photo_path}")
                    return photo_path
                except Exception as e:
                    print(f"Error saving photo: {e}")
                    return None
                    
            print(f"Failed to capture photo, attempt {attempt + 1}/3")
            time.sleep(0.5)  # Wait before retry
            
        print("Failed to capture photo after 3 attempts")
        return None

    def rfid_listener(self):
        """Continuously listens for RFID card scans."""
        if not self.rfid_logger.connect():
            print("Failed to connect to RFID reader")
            return

        while self.is_running:
            try:
                if self.rfid_logger.ser.in_waiting > 0:
                    data = self.rfid_logger.ser.readline().decode("utf-8").strip()
                    if data:
                        rfid_data = self.rfid_logger.parse_rfid_data(data)
                        if rfid_data:
                            rfid_data['is_recognized'] = True  # Set recognition status correctly
                            photo_path = self.capture_photo()
                            
                            access_request = {
                                'rfid_data': rfid_data,
                                'photo_path': photo_path
                            }
                            
                            self.event_queue.put(access_request)
                            
                time.sleep(0.1)
            except Exception as e:
                print(f"Error in RFID listener: {e}")

    def process_access_request(self, rfid_data, photo_path):
        """Processes a single access request with its own database connection."""
        print("entered process_access_request")
        # Create a new database connection for this thread
        conn = self.get_db_connection()
        try:
            print("treatment...")
            # Create an AccessControl instance with the new connection
            access_control = AccessControl(conn, db_path="../access_control.db", chroma_dir="chroma_db_test")

            # Process the request
            print("process request...")
            response = access_control.process_access_request(rfid_data, photo_path)
            
            return response
            
        finally:
            # Always close the connection
            conn.close()

    def access_processor(self):
        """Processes access requests from the queue with thread-safe database operations."""
        while self.is_running:
            try:
                access_request = self.event_queue.get(timeout=1.0)
                
                # Extract the data
                rfid_data = access_request['rfid_data']
                photo_path = access_request['photo_path']
                print(f"photo path: {photo_path}")
                
                # Log the detection
                print(f"\nCard detected - UID: {rfid_data['uid']}")
                print(f"Recognition status: {'Recognized' if rfid_data['is_recognized'] else 'Unknown'}")
                
                # # Use the lock when processing database operations
                # with self.db_lock:
                response = self.process_access_request(
                    rfid_data,
                    photo_path
                )
                
                # Display the result
                if response['status'] == 'granted':
                    print(f"✅ Access granted: {response['message']}")
                else:
                    print(f"❌ Access denied: {response['message']}")
                    
                print("-" * 50)
                
            except Exception as e:
                if 'timeout' not in str(e).lower():
                    print(f"Error in access processor: {e}")

    def run(self):
        """Starts the system with thread-safe database handling."""
        try:
            print("Starting Thread-Safe Access Control System...")
            print("Waiting for cards to be scanned...")
            
            rfid_thread = Thread(target=self.rfid_listener)
            processor_thread = Thread(target=self.access_processor)
            
            rfid_thread.start()
            processor_thread.start()
            
            while True:
                time.sleep(0.1)
                
        except KeyboardInterrupt:
            print("\nShutting down system...")
            self.is_running = False
            
            rfid_thread.join()
            processor_thread.join()
            
        finally:
            self.cleanup()

    def cleanup(self):
        """
        Cleans up system resources with proper error handling.
        """
        print("Cleaning up resources...")
        
        # Release camera
        if hasattr(self, 'camera') and self.camera is not None:
            print("Releasing camera...")
            self.camera.release()
            
        # Close RFID reader
        if self.rfid_logger.ser:
            print("Closing RFID reader...")
            self.rfid_logger.ser.close()
            
        # Close any remaining windows
        print("Closing OpenCV windows...")
        cv2.destroyAllWindows()
        
        print("Cleanup completed")
if __name__ == "__main__":
    # system = AccessControlSystem()
    # system.run()

    try:
        system = AccessControlSystem(camera_index=0)  # Try built-in webcam first
        system.run()
    except RuntimeError as e:
        print(f"\nFailed to start system: {e}")
        print("\nTroubleshooting tips:")
        print("1. Make sure your webcam is properly connected")
        print("2. Try a different camera_index if you have multiple cameras")
        print("3. Check if another application is using the camera")
        print("4. Verify you have necessary permissions to access the camera")