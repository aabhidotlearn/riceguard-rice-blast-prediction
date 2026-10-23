"""Inference adapter. Set RICE_BLAST_MODEL to a serialized sklearn pipeline for production.

Expected pipeline input: one row of numeric image features (currently RGB channel means
and fractions of visibly brown/yellow pixels). Replace this feature extraction with the
preprocessing used during model training before deploying real model weights.
"""
import os
import numpy as np
from PIL import Image

def extract_features(image_file):
    image_file.seek(0)
    image = Image.open(image_file).convert("RGB").resize((128, 128))
    pixels = np.asarray(image, dtype=np.float32) / 255.0
    r, g, b = pixels[..., 0], pixels[..., 1], pixels[..., 2]
    brown = (r > 0.28) & (r > g * 1.08) & (g > b * 1.03) & (g < 0.72)
    yellow = (r > 0.48) & (g > 0.42) & (b < 0.42) & (r > b * 1.25)
    return np.array([[r.mean(), g.mean(), b.mean(), brown.mean(), yellow.mean()]], dtype=np.float32)

def predict(image_file):
    features = extract_features(image_file)
    model_path = os.getenv("RICE_BLAST_MODEL")
    if model_path:
        import joblib
        model = joblib.load(model_path)
        probabilities = model.predict_proba(features)[0]
        index = int(np.argmax(probabilities))
        return str(model.classes_[index]), float(probabilities[index]), False

    # A transparent UI/API demo only. These color cues are not a validated disease model.
    brown, yellow = float(features[0, 3]), float(features[0, 4])
    score = min(0.86, max(0.52, 0.50 + brown * 1.8 + yellow * 0.35))
    if brown > 0.12:
        return "Possible rice blast", score, True
    return "No clear blast symptoms", min(0.82, 1 - score * 0.35), True
