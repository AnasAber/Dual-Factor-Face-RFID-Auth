from reasoning.face_recognition_model import extract_embedding, get_embeddings
from chroma_check import add_face_embedding, search_face_embedding
from reasoning.face_recognition_model import extract_embedding
from langchain.vectorstores import Chroma
import os

CHROMA_PERSIST_DIR = "chroma_db_test"

chroma_db = Chroma(
    persist_directory=CHROMA_PERSIST_DIR,
    embedding_function=get_embeddings()  # Specify your embedding function if needed
)

    # Paths for the test images
test_image_path = "data/first_image_person_1.jpeg"
# test_image_emb = extract_embedding(test_image_path)

test_query_image_path = "data/first_image_person_2.jpeg"
test_query_emb = extract_embedding(test_query_image_path)

# Ensure the files exist
if not os.path.exists(test_image_path):
    print(f"Error: Test image '{test_image_path}' not found.")
elif not os.path.exists(test_query_image_path):
    print(f"Error: Test query image '{test_query_image_path}' not found.")
else:
    # Add the test image to ChromaDB
    add_face_embedding(
        "53",
        test_image_path,
        {"name": "mohamed"}
    )
    
    print(f"query embedding: {test_query_emb}")
    # Search for the second image

    if test_query_emb is None:
        print(f"Failed to extract embedding for image: {test_query_image_path}")
    else:
        search_face_embedding(
        chroma_db,
        query_embedding=test_query_emb,
        top_k=1
    )