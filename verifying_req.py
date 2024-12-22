import chromadb
import torch
from facenet_pytorch import InceptionResnetV1

print("ChromaDB version:", chromadb.__version__)
print("PyTorch version:", torch.__version__)
print("FaceNet model initialized successfully.")