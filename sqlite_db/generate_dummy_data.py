import sqlite3
import random
import uuid

# Connect to SQLite database
conn = sqlite3.connect("../access_control.db")
cursor = conn.cursor()

# Initialize the database
def initialize_database():
        """Create tables with support for multiple face embeddings per user."""
        # Users table stores basic user information
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS users (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                name TEXT NOT NULL,
                card_uid TEXT UNIQUE NOT NULL,
                face_embedding_id TEXT NOT NULL
            )
        """)
        
        # Face embeddings table allows multiple entries per user
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS face_embeddings (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                user_id INTEGER NOT NULL,
                face_embedding_id TEXT NOT NULL,
                image_path TEXT NOT NULL,
                FOREIGN KEY (user_id) REFERENCES users (id),
                UNIQUE (face_embedding_id)
            )
        """)
        conn.commit()

# Insert provided data and generate dummy data
def populate_database():
    # Provided data
    initial_data = [
        (60, "Anas", "C3 7F F2 D9"),
        (61, "Mohamed", "F1 11 8A 3F")
    ]
    face_embedding_ids = set()

    # Helper function to generate a random card UID
    def generate_card_uid():
        return " ".join(["".join(random.choices("0123456789ABCDEF", k=2)) for _ in range(4)])

    # Helper function to generate a random face embedding ID
    def generate_face_embedding_id():
        while True:
            embedding_id = str(uuid.uuid4())  # "".join(random.choices(string.ascii_letters + string.digits, k=10))
            if embedding_id not in face_embedding_ids:
                face_embedding_ids.add(embedding_id)
                return embedding_id

    # Insert initial data
    for user_id, name, card_uid in initial_data:
        cursor.execute(
            "INSERT OR IGNORE INTO users (id, name, card_uid, face_embedding_id) VALUES (?, ?, ?, ?)",
            (user_id, name, card_uid, generate_face_embedding_id())
        )

    # Generate dummy data
    for i in range(62, 162):  # IDs from 62 to 161
        name = f"User_{i}"
        card_uid = generate_card_uid()
        face_embedding_id = generate_face_embedding_id()
        cursor.execute(
            "INSERT INTO users (id, name, card_uid, face_embedding_id) VALUES (?, ?, ?, ?)",
            (i, name, card_uid, face_embedding_id)
        )

    conn.commit()

# Run the functions
initialize_database()
populate_database()

# Fetch all records to verify
cursor.execute("SELECT * FROM users")
rows = cursor.fetchall()
rows[:10]  # Display the first 10 rows for verification

print(rows[:10])