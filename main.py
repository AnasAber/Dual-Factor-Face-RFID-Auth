from reasoning.RFID_script import RFIDLogger
from reasoning.thread_safe_access_control import AccessControlSystem
import cv2
import time
from threading import Thread
from queue import Queue
import os

class AutomatedAccessControlSystem:
    def __init__(self, camera_index=0):
        # Initialize components
        self.rfid_logger = RFIDLogger()
        self.access_control = AccessControlSystem()
        self.camera = cv2.VideoCapture(camera_index)
        
        # Create a queue for communication between components
        self.event_queue = Queue()

        # Create directory for captured photos
        os.makedirs("captures", exist_ok=True)
        
        # Flag for system running state
        self.is_running = True

    def capture_photo(self):
        """Captures a photo when an RFID card is detected."""
        return self.access_control.capture_photo()

    def rfid_listener(self):
        """
        Continuously listens for RFID card scans.
        When a card is detected, automatically processes it and puts the data in the queue.
        """
        if not self.rfid_logger.connect():
            print("Failed to connect to RFID reader")
            return

        while self.is_running:
            try:
                if self.rfid_logger.ser.in_waiting > 0:
                    data = self.rfid_logger.ser.readline().decode("utf-8").strip()
                    if data:
                        # Parse RFID data automatically
                        rfid_data = self.rfid_logger.parse_rfid_data(data)
                        if rfid_data:
                            # Take photo immediately when card is detected
                            photo_path = self.capture_photo()
                            
                            # Package the data with the photo path
                            access_request = {
                                'rfid_data': rfid_data,
                                'photo_path': photo_path
                            }
                            
                            # Put the packaged data in the queue for processing
                            self.event_queue.put(access_request)
                            
                time.sleep(0.1)
            except Exception as e:
                print(f"Error in RFID listener: {e}")

    def access_processor(self):
        """
        Continuously processes access requests from the queue.
        Automatically handles verification and access control decisions.
        """
        while self.is_running:
            try:
                # Get the next access request from the queue
                access_request = self.event_queue.get(timeout=1.0)
                
                # Extract the data
                rfid_data = access_request['rfid_data']
                photo_path = access_request['photo_path']
                
                # Log the detection
                print(f"\nCard detected - UID: {rfid_data['uid']}")
                print(f"Recognition status: {'Recognized' if rfid_data['is_recognized'] else 'Unknown'}")
                
                # Process the access request automatically
                response = self.access_control.process_access_request(
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
        """
        Starts the automated system with parallel processing of RFID detection
        and access control verification.
        """
        try:
            print("Starting Automated Access Control System...")
            print("Waiting for cards to be scanned...")
            
            # Create and start the worker threads
            rfid_thread = Thread(target=self.rfid_listener)
            processor_thread = Thread(target=self.access_processor)
            
            rfid_thread.start()
            processor_thread.start()
            
            # Keep the main thread alive until interrupted
            while True:
                time.sleep(0.1)
                
        except KeyboardInterrupt:
            print("\nShutting down system...")
            self.is_running = False
            
            # Wait for threads to finish
            rfid_thread.join()
            processor_thread.join()
            
        finally:
            self.cleanup()

    def cleanup(self):
        """Cleans up system resources."""
        self.camera.release()
        if self.rfid_logger.ser:
            self.rfid_logger.ser.close()
        self.access_control.close()
        cv2.destroyAllWindows()

if __name__ == "__main__":
    system = AutomatedAccessControlSystem(camera_index=0)
    system.run()