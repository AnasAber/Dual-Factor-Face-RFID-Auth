from chroma_check import search_face_embedding, extract_embedding, get_embeddings
from langchain.vectorstores import Chroma
import sqlite3
import os

class AccessControl:
    def __init__(self, conn, db_path="../access_control.db", chroma_dir="../chroma_db_test"):
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

    def process_access_request(self, rfid_data, face_path=None):
        if not rfid_data["is_recognized"]:
            self.log_access(None, "access_denied: unknown_card")
            return {"status": "denied", "message": "Unknown card"}

        card_uid = rfid_data["uid"]
        self.cursor.execute("SELECT id, name, face_embedding_id FROM users WHERE card_uid = ?", 
                          (card_uid,))
        result = self.cursor.fetchone()

        if not result:
            self.log_access(None, "access_denied: unknown_card")
            return {"status": "denied", "message": "Card not registered"}

        user_id, name, face_embedding_id = result

        if face_path:
            face_embedding = extract_embedding(face_path)
            matched_name = search_face_embedding(self.chroma_db, face_embedding, 1)
            
            if not matched_name or matched_name.lower() != name.lower():
                self.log_access(user_id, "access_denied: face_mismatch")
                return {"status": "denied", "message": "Face verification failed"}

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
    
    response = access_control.process_access_request(rfid_data, "/home/anasaber/Documents/arduino/data/moh/5.jpeg")
    print(response)
    access_control.close()