from langchain_community.vectorstores import Chroma
from reasoning.face_recognition_model import get_embeddings, extract_embedding
import pandas as pd
import uuid
import json
import os

# Define persistence directory
CHROMA_PERSIST_DIR = "chroma_db_test"

# Ensure the directory exists
os.makedirs(CHROMA_PERSIST_DIR, exist_ok=True)

# Initialize ChromaDB with LangChain
chroma_db = Chroma(
    persist_directory=CHROMA_PERSIST_DIR,
    embedding_function=get_embeddings()  # Specify your embedding function if needed
)

def add_face_embedding(face_embedding_id, embedding_path, metadata):
    """Add a face embedding to the LangChain ChromaDB."""
    print(f"Adding {metadata['name']} picture!")
    embedding = extract_embedding(embedding_path)
    metadata["embedding"] = str(embedding.tolist()) # Store the actual embedding in metadata as a list
    chroma_db.add_texts(
        texts=[embedding_path],  # Store the image path
        metadatas=[metadata],
        ids=[face_embedding_id]
    )

def search_face_embedding(chroma_db, query_embedding, top_k=5):
    """Search for similar face embeddings in the database."""
    try:
        print("enter the search function")
        if query_embedding is None:
            raise ValueError("Query embedding cannot be None.")
        # Perform the query
        print("before results")
        results = chroma_db.similarity_search_by_vector(
            embedding=query_embedding, k=top_k
        )
        print(f"results: {results}")
        if not results:
            print("No matches found.")
            return
        
        # Parse results
        for document in results:
            print(f"Name: {document.metadata.get('name', 'Unknown')}")
            return document.metadata.get('name', 'Unknown')
    except Exception as e:
        print(f"Error searching face embedding: {e}")


if __name__ == "__main__":
    # Load the CSV containing embeddings and metadata
    df = pd.read_csv("embeddings_new.csv")

    for index, row in df.iterrows():
        print(f'Adding id: {row["id_image"]}, name: {row["name"]}')
        add_face_embedding(
            face_embedding_id=str(uuid.uuid4()),
            embedding_path=row["image_path"],
            metadata={"name": row["name"]}
        )

    # Persist the database
    chroma_db.persist()
    print(f"ChromaDB data stored in {CHROMA_PERSIST_DIR}")
