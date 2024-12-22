import sqlite3
from chroma_check import search_face_embedding

# Connect to the SQL database
conn = sqlite3.connect("access_control.db")
cursor = conn.cursor()

def log_access(user_id, action):
    """Log access attempts in the database."""
    cursor.execute("INSERT INTO access_logs (user_id, action) VALUES (?, ?)", (user_id, action))
    conn.commit()

def process_rfid_data(card_uid, face_embedding):
    """Process RFID data and determine access."""
    # Check if card UID exists in the database
    cursor.execute("SELECT id, face_embedding_id FROM users WHERE card_uid = ?", (card_uid,))
    result = cursor.fetchone()

    if result:
        user_id, face_embedding_id = result

        # Retrieve face embedding from ChromaDB
        matched_user = search_face_embedding(face_embedding)
        if matched_user == face_embedding_id:
            log_access(user_id, "access_granted")
            return f"Access granted for user ID: {user_id}"
        else:
            log_access(None, "access_denied")
            return "Access denied: Face mismatch!"
    else:
        log_access(None, "access_denied")
        return "Access denied: Unknown card!"

# Example usage
card_uid = "08 2C E0 90"
face_embedding = [0.1, 0.2, 0.3, ...]  # Example embedding
response = process_rfid_data(card_uid, face_embedding)
print(response)
