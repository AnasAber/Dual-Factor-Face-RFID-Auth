from chroma_check import search_face_embedding, extract_embedding, get_embeddings
from langchain.vectorstores import Chroma
# from sqlite_db.generate_dummy_data import populate_database
import sqlite3
import os

# Connect to the SQLite database
conn = sqlite3.connect("access_control.db")
cursor = conn.cursor()

# Define persistence directory
CHROMA_PERSIST_DIR = "chroma_db_test"

# Ensure the directory exists
os.makedirs(CHROMA_PERSIST_DIR, exist_ok=True)

# Initialize ChromaDB with LangChain
chroma_db = Chroma(
    persist_directory=CHROMA_PERSIST_DIR,
    embedding_function=get_embeddings()  # Specify your embedding function if needed
)


# Create the necessary tables if they don't exist
def initialize_database():
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS users (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            name TEXT NOT NULL,
            card_uid TEXT UNIQUE NOT NULL,
            face_embedding_id TEXT NOT NULL
        )
    """)
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS access_logs (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id INTEGER,
            action TEXT NOT NULL,
            timestamp DATETIME DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (user_id) REFERENCES users (id)
        )
    """)
    conn.commit()

# Log access attempts in the database
def log_access(user_id, action):
    cursor.execute("INSERT INTO access_logs (user_id, action) VALUES (?, ?)", (user_id, action))
    conn.commit()

# Process RFID data and determine access
def process_rfid_data(card_uid, face_embedding):
    """
    Process RFID data and determine access based on the card UID
    and face embedding matching results.
    """
    # Check if card UID exists in the database
    cursor.execute("SELECT id, name, face_embedding_id FROM users WHERE card_uid = ?", (card_uid,))
    result = cursor.fetchone()

    print(f"result: {result}")
    if result:
        user_id, name, face_embedding_id = result

        print(f"results : {user_id} | {name} | {face_embedding_id}")


        # Retrieve face embedding from ChromaDB and check similarity
        matched_name = search_face_embedding(chroma_db, face_embedding, 1)
        print(f"matched_name : {matched_name}")
        if matched_name:
            if matched_name.lower() == name.lower():
                log_access(user_id, "access_granted")
                return name
        else:
            log_access(user_id, "access_denied: face_mismatch")
            return None
    else:
        log_access(None, "access_denied: unknown_card")
        return None

# Example usage
if __name__ == "__main__":
    # Initialize the database
    # initialize_database()
    # populate_database()
    # Example RFID card UID and face embedding


    card_uid = "C3 7F F2 D9"
    face_path = "data/1_anas.jpeg"
    face_embedding = extract_embedding(face_path)

    # Process the RFID data
    response = process_rfid_data(card_uid, face_embedding)
    if response:
        print(f"Access granted: Welcome {response}!")
    else:
        print("Access denied!")
