import sys
import os
import time
from threading import Thread
from reasoning.thread_safe_access_control import AccessControlSystem

# Ensure the current script's directory is added to the Python path
project_root = os.path.abspath(os.path.join(os.path.dirname(__file__)))
sys.path.append(project_root)

def main():
    """Entry point for the access control application."""
    print("\n=== Access Control System ===")
    print("Initializing application...\n")

    try:
        # Initialize the Access Control System
        system = AccessControlSystem(camera_index=0,db_path="access_control.db")  # Use default camera index

        # Run the system
        print("Starting the system. Press Ctrl+C to exit.\n")
        system.run()

    except RuntimeError as e:
        print(f"\nError: {e}")
        print("\nTroubleshooting tips:")
        print("1. Verify your webcam is connected and functional.")
        print("2. Use a different camera_index if you have multiple cameras.")
        print("3. Ensure no other application is using the webcam.")
        print("4. Check your permissions to access the webcam.")

    except KeyboardInterrupt:
        print("\nSystem interrupted by user.")

    finally:
        print("\nExiting application. Cleaning up resources...")

if __name__ == "__main__":
    main()