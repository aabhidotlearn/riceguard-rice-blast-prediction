"""Image feature extraction and rice-leaf classifier inference.

The bundled model is an educational classifier trained on the four disease classes
listed in README.md. It does not include a healthy-leaf class, so outputs are only
candidate matches and must not be used for agronomic decisions.
"""
from functools import lru_cache
import os
from pathlib import Path

import numpy as np
from PIL import Image

BASE_DIR = Path(__file__).resolve().parents[1]
DEFAULT_MODEL = BASE_DIR / "predictions" / "artifacts" / "rice_disease_mlp.joblib"
CLASS_LABELS = {
    "Bacterialblight": "Bacterial blight pattern",
    "Blast": "Possible rice blast",
    "Brownspot": "Brown spot pattern",
    "Tungro": "Tungro pattern",
}


def extract_features(image_file):
    """Return compact, deterministic color features for the sample MLP."""
    image_file.seek(0)
    rgb_image = Image.open(image_file).convert("RGB").resize((128, 128))
    rgb = np.asarray(rgb_image, dtype=np.float32) / 255.0
    hsv = np.asarray(rgb_image.convert("HSV"), dtype=np.float32) / 255.0

    features = []
    for channel in range(3):
        channel_data = rgb[..., channel]
        features.extend((float(channel_data.mean()), float(channel_data.std())))
    # HSV histograms capture color distribution beyond global channel averages.
    for channel, bins in ((0, 12), (1, 8), (2, 8)):
        hist, _ = np.histogram(hsv[..., channel], bins=bins, range=(0.0, 1.0), density=True)
        features.extend(hist.astype(np.float32).tolist())

    r, g, b = rgb[..., 0], rgb[..., 1], rgb[..., 2]
    brown = (r > 0.24) & (r > g * 1.04) & (g > b * 1.02) & (g < 0.78)
    yellow = (r > 0.42) & (g > 0.36) & (b < 0.5) & (r > b * 1.1)
    dark = (r < 0.30) & (g < 0.34) & (b < 0.30)
    green = (g > r * 1.05) & (g > b * 1.05)
    features.extend((brown.mean(), yellow.mean(), dark.mean(), green.mean()))
    return np.asarray(features, dtype=np.float32).reshape(1, -1)


@lru_cache(maxsize=4)
def _load_model(model_path, modified_ns):
    import joblib
    return joblib.load(model_path)


def predict(image_file):
    features = extract_features(image_file)
    model_path = os.getenv("RICE_BLAST_MODEL", str(DEFAULT_MODEL))
    if Path(model_path).is_file():
        model_file = Path(model_path)
        model = _load_model(str(model_file), model_file.stat().st_mtime_ns)
        probabilities = model.predict_proba(features)[0]
        index = int(np.argmax(probabilities))
        label = str(model.classes_[index])
        disease = CLASS_LABELS.get(label, label)
        return disease, float(probabilities[index]), False

    # Keep the fallback explicit when a trained model artifact is unavailable.
    brown, yellow = float(features[0, -4]), float(features[0, -3])
    score = min(0.82, max(0.52, 0.50 + brown * 1.8 + yellow * 0.35))
    if brown > 0.12:
        return "Possible rice blast (demo signal)", score, True
    return "No clear blast symptoms (demo signal)", min(0.82, 1 - score * 0.35), True
