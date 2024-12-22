### steps to generate embeddings for now

- Gather all photos into a folder --> images/
- Run the function located in face_recognition_model.py, and run the generate_embeddings_csv() --> embedidngs.csv
- Run the add_face_embedding() function located in chroma_check.py using this syntax:
    -   df = pd.read_csv("embeddings.csv")
        for index, row in df.iterrows():
            print(f' id: {row["id_image"]}, embedding : {json.loads(row["embedding"])}, name {row["name"]}')
            add_face_embedding(str(row["id_image"]), json.loads(row["embedding"]), {"name" :row["name"]})


