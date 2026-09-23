import io
import os

import mlflow
import torch
from fastapi import FastAPI, File, UploadFile
from PIL import Image
from torchvision import transforms


# MLflow configuration
MLFLOW_TRACKING_URI = os.getenv(
    "MLFLOW_TRACKING_URI",
    "http://127.0.0.1:5000",
)

mlflow.set_tracking_uri(MLFLOW_TRACKING_URI)


# Create FastAPI application
app = FastAPI(title="Food-11 Classification API")


# Load the champion model once when the application starts
model = mlflow.pyfunc.load_model("models:/food11@champion")


# Food-11 class names
CLASS_NAMES = [
    "Bread",
    "Dairy product",
    "Dessert",
    "Egg",
    "Fried food",
    "Meat",
    "Noodles-Pasta",
    "Rice",
    "Seafood",
    "Soup",
    "Vegetable-Fruit",
]


# Same preprocessing used for validation/test during training
transform = transforms.Compose(
    [
        transforms.Resize((128, 128)),
        transforms.ToTensor(),
        transforms.Normalize(
            mean=[0.485, 0.456, 0.406],
            std=[0.229, 0.224, 0.225],
        ),
    ]
)


@app.get("/health")
def health():
    return {"status": "ok"}


@app.post("/predict")
async def predict(file: UploadFile = File(...)):
    contents = await file.read()

    image = Image.open(io.BytesIO(contents)).convert("RGB")
    image_tensor = transform(image).unsqueeze(0)

    with torch.no_grad():
        output = model.predict(image_tensor.numpy())

    if not isinstance(output, torch.Tensor):
        output = torch.tensor(output)

    probabilities = torch.softmax(output, dim=1)
    confidence, predicted_index = torch.max(probabilities, dim=1)

    return {
        "category": CLASS_NAMES[predicted_index.item()],
        "confidence": confidence.item(),
    }