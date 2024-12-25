from facenet_pytorch import InceptionResnetV1
from langchain.embeddings.base import Embeddings
import torch
from PIL import Image
import os, re
import numpy as np
import csv


# Initialize FaceNet model
model = InceptionResnetV1(pretrained='vggface2').eval()

def extract_embedding(image_path):
    """Extract face embedding from an image."""
    try:
        print(f"path: {image_path}")
        img = Image.open(image_path).resize((160, 160)).convert('RGB')
        print("opening image")
        img_tensor = torch.tensor(np.array(img)).permute(2, 0, 1).unsqueeze(0).float()
        print("image_tensor")
        with torch.no_grad():
            embedding = model(img_tensor)
            print(f"image embedding {embedding}")

        print("returning embedding")
        return embedding.detach().cpu().numpy().flatten()  # Flatten the embedding
    except Exception as e:
        print(f"Error processing image {image_path}: {e}")
        return None
    

# Define the embedding function wrapper
class FaceEmbeddingFunction(Embeddings):
    def embed_documents(self, images):
        """Embed a list of images (paths)."""
        return [self._extract_embedding(image) for image in images]

    def embed_query(self, image):
        """Embed a single image (path)."""
        return self._extract_embedding(image)

    @staticmethod
    def _extract_embedding(image_path):
        """Extract face embedding from an image."""
        try:
            img = Image.open(image_path).resize((160, 160)).convert('RGB')
            img_tensor = torch.tensor(np.array(img)).permute(2, 0, 1).unsqueeze(0).float()
            with torch.no_grad():
                embedding = model(img_tensor)
            return embedding.detach().cpu().numpy().flatten()  # Flatten the embedding
        except Exception as e:
            print(f"Error processing image {image_path}: {e}")
            return None


def get_embeddings():
    face_embedding_function = FaceEmbeddingFunction()
    return face_embedding_function


def generate_embeddings_csv(image_dir, csv_filename, names):
    """Generates embeddings and stores them in a CSV file with names."""
    if not names:
        raise ValueError("The 'names' list cannot be empty.")
    
    with open(csv_filename, 'w', newline='') as csvfile:
        writer = csv.writer(csvfile)
        writer.writerow(["id_image", "name", "embedding", "image_path"])  # Add "name" to header

        image_files = sorted(
            [f for f in os.listdir(image_dir) if f.lower().endswith(('.png', '.jpg', '.jpeg', '.gif', '.bmp'))],
            key=lambda x: int(re.search(r"(\d+)", x).group(1)) if re.search(r"(\d+)", x) else float('inf')
        )

        if len(image_files) != len(names):
            print(f"Warning: Number of images ({len(image_files)}) does not match the number of names ({len(names)}). Using what is available.")
            min_len = min(len(image_files), len(names))
            image_files = image_files[:min_len]
            names = names[:min_len]

        for i, filename in enumerate(image_files):
            try:
                image_path = os.path.join(image_dir, filename)
                match = re.search(r"(\d+)\.(jpg|png|jpeg|gif|bmp)", filename, re.IGNORECASE)
                if not match:
                    print(f"Warning: could not find number in filename: {filename}")
                    continue
                file_number = match.group(1)
                embedding = extract_embedding(image_path)
                if embedding is not None:
                    writer.writerow([file_number, names[i], embedding.tolist(),image_path])  # Write name to CSV
                    print(f"Generated embedding for {filename} (Name: {names[i]})")
            except Exception as e:
                print(f"Error processing {filename}: {e}")

if __name__ == "__main__":
    image_directory = "data/images"  # Directory containing the renamed images
    csv_file = "embeddings_new.csv"  # Name of the CSV file to create

    if not os.path.exists(image_directory) or not os.path.isdir(image_directory):
        print(f"Error: Directory '{image_directory}' not found.")
        exit(1)

    names = ["james", "Anna", "Oscar", "Amy", "Love", "Meryem", "Mike", "Karen", "Kathrine", "Bob", "Sara","Auston","Adam", "Salah", "Gorgia" , "Micheal", "Phibie", "Mike", "Monika", "Ann","Brai", "Sofia", "Roger", "Naomi", "Jaklin"]

    generate_embeddings_csv(image_directory, csv_file, names)
    print("Embedding generation and CSV creation complete.")