from facenet_pytorch import InceptionResnetV1
from langchain.embeddings.base import Embeddings
import torch
from PIL import Image
import os, re
import numpy as np
import csv
import cv2


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


def extract_embedding_from_frame(face_frame):
    """Extract face embedding from a detected face frame."""
    try:
        # Convert the frame to PIL image
        img = Image.fromarray(face_frame).resize((160, 160)).convert('RGB')
        img_tensor = torch.tensor(np.array(img)).permute(2, 0, 1).unsqueeze(0).float()
        with torch.no_grad():
            embedding = model(img_tensor)
        return embedding.detach().cpu().numpy().flatten()  # Flatten the embedding
    except Exception as e:
        print(f"Error extracting embedding: {e}")
        return None

def trace_and_annotate_faces(camera_index=0):
    """Open the PC camera, detect faces, annotate them, and optionally extract embeddings."""
    # Load Haar cascade for face detection
    face_cascade = cv2.CascadeClassifier(cv2.data.haarcascades + "haarcascade_frontalface_default.xml")
    
    # Initialize the camera
    cap = cv2.VideoCapture(camera_index)
    if not cap.isOpened():
        print("Error: Could not open camera")
        return

    try:
        print("Press 'q' to exit.")
        while True:
            ret, frame = cap.read()
            if not ret:
                print("Error: Unable to capture frame")
                break

            # Convert to grayscale for face detection
            gray_frame = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)
            
            # Detect faces
            faces = face_cascade.detectMultiScale(gray_frame, scaleFactor=1.1, minNeighbors=5, minSize=(30, 30))
            
            for (x, y, w, h) in faces:
                # Draw a rectangle around the face
                cv2.rectangle(frame, (x, y), (x + w, y + h), (255, 0, 0), 2)
                
                # Extract face region
                face_frame = frame[y:y + h, x:x + w]
                
                # Extract embedding (optional)
                embedding = extract_embedding_from_frame(face_frame)
                if embedding is not None:
                    cv2.putText(frame, "Face detected", (x, y - 10), cv2.FONT_HERSHEY_SIMPLEX, 0.5, (0, 255, 0), 2)

            # Display the frame
            cv2.imshow("Face Detection", frame)

            # Exit on 'q' key
            if cv2.waitKey(1) & 0xFF == ord('q'):
                break
    finally:
        # Release resources
        cap.release()
        cv2.destroyAllWindows()


# if __name__ == "__main__":
#     image_directory = "data/images"  # Directory containing the renamed images
#     csv_file = "embeddings_new.csv"  # Name of the CSV file to create

#     if not os.path.exists(image_directory) or not os.path.isdir(image_directory):
#         print(f"Error: Directory '{image_directory}' not found.")
#         exit(1)

#     names = ["james", "Anna", "Oscar", "Amy", "Love", "Meryem", "Mike", "Karen", "Kathrine", "Bob", "Sara","Auston","Adam", "Salah", "Gorgia" , "Micheal", "Phibie", "Mike", "Monika", "Ann","Brai", "Sofia", "Roger", "Naomi", "Jaklin"]

#     generate_embeddings_csv(image_directory, csv_file, names)
#     print("Embedding generation and CSV creation complete.")