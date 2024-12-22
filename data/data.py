import kagglehub

# Download latest version
path = kagglehub.dataset_download("trainingdatapro/age-detection-human-faces-18-60-years")

print("Path to dataset files:", path)