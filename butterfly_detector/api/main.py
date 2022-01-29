from fastapi import FastAPI, File, UploadFile
from tensorflow.keras import models
from scripts.transfer_learning import train_gen
import os
import uvicorn
import numpy as np
from io import BytesIO
from PIL import Image

PATH = os.path.dirname(os.path.dirname(__file__))

app = FastAPI()

@app.get("/ping")
async def ping():
    return 'Alive!!'

def read_file_as_image(data):
    """ Takes a bytes data as input and converts it into a numpy array"""
    img = Image.open(BytesIO(data))
    return np.array(img.resize((150, 150)))

@app.post("/predict")
async def predict(model = 'model_4', file: UploadFile = File(...)):
    model_to_pred = models.load_model(f"{PATH}/models/{model}")
    butterflies = list(train_gen.class_indices.keys())
    image = read_file_as_image(await file.read())
    image = np.expand_dims(image, axis=0)
    pred = list(model_to_pred.predict(image)[0])
    preds = dict(zip(butterflies, pred))
    best = max(preds, key=preds.get)
    return {'class': best, 'confidence': str(preds[best]*100) + '%'}

if __name__ == "__main__":
    uvicorn.run(app, host='localhost', port=8000)
