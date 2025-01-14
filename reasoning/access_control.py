import sys
import os
project_root = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
sys.path.append(project_root)
from chroma_check import search_face_embedding, extract_embedding, get_embeddings
# from face_recognition_model import trace_and_annotate_faces
from langchain_community.vectorstores import Chroma
import sqlite3
class AccessControl:
    def __init__(self, conn, db_path="../access_control.db", chroma_dir="chroma_db_test"):
        self.conn = conn
        self.cursor = self.conn.cursor()
        os.makedirs(chroma_dir, exist_ok=True)
        self.chroma_db = Chroma(
            persist_directory=chroma_dir,
            embedding_function=get_embeddings()
        )
        self.initialize_database()

    def initialize_database(self):
        self.cursor.execute("""
            CREATE TABLE IF NOT EXISTS users (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                name TEXT NOT NULL,
                card_uid TEXT UNIQUE NOT NULL,
                face_embedding_id TEXT NOT NULL
            )
        """)
        self.cursor.execute("""
            CREATE TABLE IF NOT EXISTS access_logs (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                user_id INTEGER,
                action TEXT NOT NULL,
                timestamp DATETIME DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (user_id) REFERENCES users (id)
            )
        """)
        self.conn.commit()

    def log_access(self, user_id, action):
        self.cursor.execute("INSERT INTO access_logs (user_id, action) VALUES (?, ?)", 
                          (user_id, action))
        self.conn.commit()

    # def process_access_request(self, rfid_data, face_path=None):
    #     if not rfid_data["is_recognized"]:
    #         self.log_access(None, "access_denied: unknown_card")
    #         return {"status": "denied", "message": "Unknown card"}

    #     card_uid = rfid_data["uid"]
    #     self.cursor.execute("SELECT id, name, face_embedding_id FROM users WHERE card_uid = ?", 
    #                       (card_uid,))
    #     result = self.cursor.fetchone()

    #     if not result:
    #         with open("unregistered_cards.log", "a") as log_file:
    #             log_file.write(f"{card_uid}\n")
    #         self.log_access(None, "access_denied: unknown_card")
    #         return {"status": "denied", "message": "Card not registered"}

    #     user_id, name, face_embedding_id = result

    #     if face_path:
    #         face_embedding = extract_embedding(face_path)
    #         matched_name = search_face_embedding(self.chroma_db, face_embedding, 1)
            
    #         if not matched_name or matched_name.lower() != name.lower():
    #             self.log_access(user_id, "access_denied: face_mismatch")
    #             return {"status": "denied", "message": "Face verification failed"}

    #     self.log_access(user_id, "access_granted")
    #     return {
    #         "status": "granted",
    #         "message": f"Welcome {name}!",
    #         "user_id": user_id,
    #         "name": name
    #     }

    def process_access_request(self, rfid_data, face_path=None):
        print("\n=== Starting Access Request Processing ===")
        print(f"RFID Data: {rfid_data}")
        print(f"Face Path: {face_path}")

        if not rfid_data["is_recognized"]:
            print("Card not recognized")
            self.log_access(None, "access_denied: unknown_card")
            return {"status": "denied", "message": "Unknown card"}

        card_uid = rfid_data["uid"]
        print(f" card_uid : {card_uid}")
        i = 0
        if i == 0:
            self.cursor.execute("SELECT * FROM users")
            result = self.cursor.fetchone()
            print(f"result: {result}")
        self.cursor.execute("SELECT id, name, face_embedding_id FROM users WHERE card_uid = ?", 
                        (card_uid,))
        result = self.cursor.fetchone()
        if not result:
            print(f"Card {card_uid} not registered in database")
            with open("unregistered_cards.log", "a") as log_file:
                log_file.write(f"{card_uid}\n")
            self.log_access(None, "access_denied: unknown_card")
            return {"status": "denied", "message": "Card not registered"}

        user_id, name, face_embedding_id = result
        print(f"Found user in database: {name} (ID: {user_id})")

        if face_path:
            print("\n=== Starting Face Verification ===")
            try:
                print("Extracting face embedding from captured image...")
                face_embedding = extract_embedding(face_path)
                print(f"Embedding extracted successfully: {face_embedding[:5]}... (showing first 5 elements)")
                
                print("\nSearching for matching face in database...")
                matched_name = search_face_embedding(self.chroma_db, face_embedding, 1)
                print(f"Database search result - Matched name: {matched_name}")
                print(f"Expected name: {name}")
                
                if not matched_name:
                    print("No matching face found in database")
                    self.log_access(user_id, "access_denied: no_face_match")
                    return {"status": "denied", "message": "Face verification failed - No match found"}
                
                if matched_name.lower() != name.lower():
                    print(f"Face mismatch: Expected {name}, got {matched_name}")
                    self.log_access(user_id, "access_denied: face_mismatch")
                    return {"status": "denied", "message": "Face verification failed - Identity mismatch"}
                    
            except Exception as e:
                print(f"Error during face verification: {str(e)}")
                self.log_access(user_id, "access_denied: face_verification_error")
                return {"status": "denied", "message": f"Face verification error: {str(e)}"}
        else:
            print("No face image provided for verification")

        print("\nAccess granted!")
        self.log_access(user_id, "access_granted")
        return {
            "status": "granted",
            "message": f"Welcome {name}!",
            "user_id": user_id,
            "name": name
        }

    def close(self):
        self.conn.close()

if __name__ == "__main__":
    conn = sqlite3.connect("../access_control.db")
    access_control = AccessControl(conn=conn)
    
    # Example usage with RFID data
    rfid_data = {
        "uid": "F1 11 8A 3F",
        "is_recognized": True,
        "raw_data": "Card UID: F1 11 8A 3F | Card recognized"
    }
    
    response = access_control.process_access_request(rfid_data, "../data/anas_cam/face_20241226-184453.jpg")
    print(response)
    access_control.close()