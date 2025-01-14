import sqlite3
from langchain_community.vectorstores import Chroma
from face_recognition_model import get_embeddings, extract_embedding
import os
import uuid
from datetime import datetime

class EnhancedDatabaseManager:
    def __init__(self, sqlite_db_path="../access_control.db", chroma_dir="../chroma_db_test"):
        """Initialize database connections with support for multiple images per user."""
        self.sqlite_db_path = sqlite_db_path
        self.conn = sqlite3.connect(sqlite_db_path)
        self.cursor = self.conn.cursor()
        self.initialize_sqlite_database()

        self.chroma_dir = chroma_dir
        os.makedirs(chroma_dir, exist_ok=True)
        self.chroma_db = Chroma(
            persist_directory=chroma_dir,
            embedding_function=get_embeddings()
        )

    def initialize_sqlite_database(self):
        """Create tables with support for multiple face embeddings per user."""
        self.cursor.execute("""
            CREATE TABLE IF NOT EXISTS users (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                name TEXT NOT NULL,
                card_uid TEXT UNIQUE NOT NULL,
                face_embedding_id TEXT
            )
        """)
        
        self.cursor.execute("""
            CREATE TABLE IF NOT EXISTS face_embeddings (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                user_id INTEGER NOT NULL,
                face_embedding_id TEXT NOT NULL,
                image_path TEXT NOT NULL,
                FOREIGN KEY (user_id) REFERENCES users (id),
                UNIQUE (face_embedding_id)
            )
        """)
        self.conn.commit()

    def get_image_files_from_folder(self, folder_path):
        """
        Get all valid image files from a folder.
        
        Args:
            folder_path (str): Path to the folder containing images
            
        Returns:
            list: List of full paths to valid image files
        """
        valid_extensions = {'.jpg', '.jpeg', '.png', '.bmp', '.gif'}
        image_files = []
        
        try:
            # Check if the folder exists
            if not os.path.exists(folder_path):
                print(f"Error: Folder not found: {folder_path}")
                return []

            # Get all files with valid extensions
            for filename in os.listdir(folder_path):
                ext = os.path.splitext(filename.lower())[1]
                if ext in valid_extensions:
                    full_path = os.path.join(folder_path, filename)
                    image_files.append(full_path)
            
            if not image_files:
                print(f"Warning: No valid image files found in {folder_path}")
            else:
                print(f"Found {len(image_files)} valid image files")
                
            return image_files
            
        except Exception as e:
            print(f"Error reading folder {folder_path}: {e}")
            return []
        
    def reconcile_chromadb_with_sqlite(self):
        """
        Ensure that all face embeddings in SQLite are present in ChromaDB.
        If not, add them to ChromaDB.
        """
        try:
            # Retrieve all face embeddings from SQLite
            self.cursor.execute("""
                SELECT f.face_embedding_id, f.image_path, u.name, u.card_uid 
                FROM face_embeddings f
                JOIN users u ON f.user_id = u.id
            """)
            embeddings_data = self.cursor.fetchall()

            # Get all existing document IDs in ChromaDB
            chromadb_ids = self.chroma_db.get()
            chromadb_ids = set(chromadb_ids['ids'])

            added_count = 0

            # Check and add missing data to ChromaDB
            for embedding_id, image_path, name, card_uid in embeddings_data:
                if embedding_id not in chromadb_ids:
                    # Extract embedding and add to ChromaDB
                    print(f"Embedding ID {embedding_id} missing in ChromaDB. Adding...")
                    embedding = extract_embedding(image_path)
                    if embedding is not None:
                        metadata = {
                            "name": name,
                            "card_uid": card_uid,
                            "image_path": image_path,
                            "added_at": datetime.now().isoformat(),
                            "embedding": str(embedding.tolist())
                        }
                        self.chroma_db.add_texts(
                            texts=[image_path],
                            metadatas=[metadata],
                            ids=[embedding_id]
                        )
                        added_count += 1
                    else:
                        print(f"Warning: Failed to extract embedding for {image_path}")

            print(f"Reconciliation completed. Added {added_count} missing entries to ChromaDB.")
        except Exception as e:
            print(f"Error during reconciliation: {e}")

    def add_user(self, name, card_uid, face_image_input):
        """
        Add a new user with multiple face images from either a list of paths or a folder.
        
        Args:
            name (str): User's name
            card_uid (str): RFID card UID
            face_image_input (str or list): Either a folder path or list of image paths
        """
        try:
            # Determine if input is a folder path or list of images
            if isinstance(face_image_input, str):
                # Process as folder path
                face_image_paths = self.get_image_files_from_folder(face_image_input)
                if not face_image_paths:
                    return False
            else:
                # Process as list of image paths
                face_image_paths = face_image_input

            # Check if user with this card_uid already exists
            self.cursor.execute("SELECT id, name FROM users WHERE card_uid = ?", (card_uid,))
            existing_user = self.cursor.fetchone()
            
            if existing_user:
                user_id = existing_user[0]
                print(f"User already exists: {existing_user[1]}")
                print("Adding new face images to existing user...")
            else:
                # Add new user to SQLite
                self.cursor.execute(
                    "INSERT INTO users (name, card_uid) VALUES (?, ?)",
                    (name, card_uid)
                )
                user_id = self.cursor.lastrowid
                print(f"Created new user: {name}")

            # Process each face image
            successful_images = 0
            for image_path in face_image_paths:
                try:
                    # Generate unique ID for this face embedding
                    face_embedding_id = str(uuid.uuid4())
                    print(f"Processing image: {image_path}")
                    
                    # Extract face embedding
                    embedding = extract_embedding(image_path)
                    
                    if embedding is None:
                        print(f"Warning: Could not extract embedding from {image_path}")
                        continue

                    # Add to ChromaDB
                    metadata = {
                        "name": name,
                        "card_uid": card_uid,
                        "image_path": image_path,
                        "added_at": datetime.now().isoformat(),
                        "embedding": str(embedding.tolist())
                    }
                    
                    self.chroma_db.add_texts(
                        texts=[image_path],
                        metadatas=[metadata],
                        ids=[face_embedding_id]
                    )

                    # Add to face_embeddings table
                    self.cursor.execute("""
                        INSERT INTO face_embeddings 
                        (user_id, face_embedding_id, image_path) 
                        VALUES (?, ?, ?)
                    """, (user_id, face_embedding_id, image_path))

                    # Update the user's face_embedding_id with the latest one
                    self.cursor.execute("""
                        UPDATE users 
                        SET face_embedding_id = ? 
                        WHERE id = ?
                    """, (face_embedding_id, user_id))
                    
                    successful_images += 1

                except Exception as e:
                    print(f"Error processing image {image_path}: {e}")
                    continue

            self.conn.commit()
            print(f"Successfully processed {successful_images} out of {len(face_image_paths)} images for {name}!")
            return successful_images > 0

        except Exception as e:
            print(f"Error adding user/images: {e}")
            self.conn.rollback()
            return False

    def list_users(self):
        """List all users and their face images."""
        try:
            self.cursor.execute("""
                SELECT 
                    u.name, 
                    u.card_uid, 
                    COUNT(f.id) as image_count
                FROM users u
                LEFT JOIN face_embeddings f ON u.id = f.user_id
                GROUP BY u.id
            """)
            users = self.cursor.fetchall()
            
            if not users:
                print("No users found in database.")
                return

            print("\nRegistered Users:")
            print("-" * 50)
            for user in users:
                print(f"Name: {user[0]}")
                print(f"Card UID: {user[1]}")
                print(f"Number of face images: {user[2]}")
                print("-" * 50)

        except Exception as e:
            print(f"Error listing users: {e}")

    def close(self):
        """Clean up database connections."""
        self.conn.close()

def main():
    """Interactive function to add users with multiple images."""
    db_manager = EnhancedDatabaseManager()
    
    try:
        while True:
            print("\nAccess Control System - User Registration")
            print("1. Add new user or images to existing user (individual images)")
            print("2. Add new user or images to existing user (folder)")
            print("3. List all users")
            print("4. Exit")
            
            choice = input("\nEnter your choice (1-4): ")
            
            if choice == "1":
                name = input("Enter user name: ")
                card_uid = input("Enter card UID (e.g., C3 7F F2 D9): ")
                
                # Handle multiple images
                face_image_paths = []
                while True:
                    path = input("Enter path to face image (or press Enter to finish): ")
                    if not path:
                        break
                    face_image_paths.append(path)
                
                if not face_image_paths:
                    print("Error: No image paths provided!")
                    continue
                
                if db_manager.add_user(name, card_uid, face_image_paths):
                    print("Processing completed successfully!")
                else:
                    print("Failed to process user/images.")
                    
            elif choice == "2":
                name = input("Enter user name: ")
                card_uid = input("Enter card UID (e.g., C3 7F F2 D9): ")
                folder_path = input("Enter folder path containing face images: ")
                
                if db_manager.add_user(name, card_uid, folder_path):
                    print("Folder processing completed successfully!")
                else:
                    print("Failed to process user/folder.")
                
            elif choice == "3":
                db_manager.reconcile_chromadb_with_sqlite()
                db_manager.list_users()
                
            elif choice == "4":
                print("Exiting...")
                break
                
            else:
                print("Invalid choice. Please try again.")

    except KeyboardInterrupt:
        print("\nExiting...")
    finally:
        db_manager.close()

if __name__ == "__main__":
    main()