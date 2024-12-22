# # df = pd.read_csv("age_detection.csv")

# # print(df["split"])

# # data_we_want = df[df["split"] == "test"]

# # print(data_we_want)

# # data_we_want.to_csv("data.csv")

# import os
# import shutil
# import re    

# data = pd.read_csv("embeddings.csv")

# names = ["james", "Anna", "Oscar", "Amy", "Love", "Meryem", "Mike", "Karen", "Kathrine", "Bob", "Sara","Auston","Adam", "Salah", "Gorgia" , "Micheal", "Phibie", "Mike", "Monika", "Ann","Brai", "Sofia", "Roger", "Naomi", "Jaklin"]

# # Load the CSV file
# csv_file_path = "embeddings.csv"  # Replace with your CSV file path
# df = pd.read_csv(csv_file_path)

# # Ensure there are enough names for the number of rows in the CSV
# if len(names) < len(df):
#     raise ValueError("The number of names is less than the number of rows in the CSV.")

# # Sort the DataFrame by id_image to ensure correct order
# df = df.sort_values("id_image").reset_index(drop=True)

# # Add the "name" column
# df["name"] = names[:len(df)]  # Take as many names as there are rows

# # Save the updated DataFrame to a new CSV
# updated_csv_path = "updated_csv_file.csv"
# df.to_csv(updated_csv_path, index=False)





# test_image_path = "data/test_image.jpg"

# add_face_embedding("50",test_image_path, {"name": "Anas"})

# print(f"image added to chromadb!")


# test_image = "data/test.jpeg"
# chromadb_check = search_face_embedding(test_image)

# print(f"answer: {chromadb_check}")

import pandas as pd
from langchain.vectorstores import Chroma
from face_recognition_model import extract_embedding, get_embeddings
from chroma_check import add_face_embedding, search_face_embedding
from face_recognition_model import extract_embedding
import os

CHROMA_PERSIST_DIR = "chroma_db_test"

chroma_db = Chroma(
    persist_directory=CHROMA_PERSIST_DIR,
    embedding_function=get_embeddings()  # Specify your embedding function if needed
)

    # Paths for the test images
test_image_path = "data/test_image.jpg"
test_image_emb = extract_embedding(test_image_path)

test_query_image_path = "data/test.jpeg"
# test_query_emb = extract_embedding(test_query_image_path)

# Ensure the files exist
if not os.path.exists(test_image_path):
    print(f"Error: Test image '{test_image_path}' not found.")
elif not os.path.exists(test_query_image_path):
    print(f"Error: Test query image '{test_query_image_path}' not found.")
else:
    # Add the test image to ChromaDB
    # add_face_embedding(
    #     "54",
    #     test_image_path,
    #     {"name": "anas"}
    # )
    
    # print(f"query embedding: {test_query_emb}")
    # Search for the second image

    if test_image_path is None:
        print(f"Failed to extract embedding for image: {test_query_image_path}")
    else:
        search_face_embedding(
        chroma_db,
        query_embedding=test_image_emb,
        top_k=1
    )