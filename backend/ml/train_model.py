"""Train/evaluate the RiceGuard sample MLP with train-only SMOTE balancing.

Usage from backend/: python ml/train_model.py "/path/to/Rice Leaf Disease Images"
Expected folders: Bacterialblight, Blast, Brownspot, Tungro.
"""
import argparse
import json
import platform
from collections import Counter, defaultdict
from pathlib import Path
import sys
import warnings

import joblib
import imblearn
import sklearn
import numpy as np
from imblearn.over_sampling import SMOTE
from sklearn.metrics import classification_report, confusion_matrix, f1_score, accuracy_score
from sklearn.neural_network import MLPClassifier
from sklearn.preprocessing import StandardScaler
from sklearn.pipeline import Pipeline
from PIL import Image, UnidentifiedImageError

BACKEND = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(BACKEND))
from predictions.inference import CLASS_LABELS, extract_features

EXTENSIONS = {".jpg", ".jpeg", ".png", ".webp"}


def read_dataset(dataset_dir, max_per_class=0):
    features, labels, groups, counts = [], [], [], Counter()
    for class_dir in sorted(Path(dataset_dir).iterdir()):
        if not class_dir.is_dir() or class_dir.name not in CLASS_LABELS:
            continue
        images = sorted(p for p in class_dir.iterdir() if p.suffix.lower() in EXTENSIONS)
        if max_per_class:
            families = defaultdict(list)
            for image_path in images:
                families[image_path.stem.rsplit("_", 1)[0].lower()].append(image_path)
            # Round-robin families so a small run still has a meaningful family holdout.
            sampled, family_names = [], sorted(families)
            while len(sampled) < max_per_class and family_names:
                for family in family_names:
                    if families[family]:
                        sampled.append(families[family].pop(0))
                        if len(sampled) >= max_per_class:
                            break
                family_names = [family for family in family_names if families[family]]
            images = sampled
        for path in images:
            try:
                with path.open("rb") as image_file:
                    x = extract_features(image_file)
                features.append(x[0])
                labels.append(class_dir.name)
                groups.append(path.stem.rsplit("_", 1)[0].lower())
                counts[class_dir.name] += 1
            except (OSError, UnidentifiedImageError) as exc:
                warnings.warn(f"Skipping unreadable image {path}: {exc}")
    if len(counts) < 2 or min(counts.values(), default=0) < 2:
        raise ValueError("Need at least two classes with two readable images each.")
    return np.asarray(features, dtype=np.float32), np.asarray(labels), np.asarray(groups), counts


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("dataset_dir", type=Path, help="Directory containing one subfolder per disease class")
    parser.add_argument("--max-per-class", type=int, default=0, help="Optional deterministic cap for a quick sample run")
    parser.add_argument("--minority-class", choices=sorted(CLASS_LABELS), help="Optional class to downsample for an imbalance demonstration")
    parser.add_argument("--minority-count", type=int, default=0, help="Number of minority-class examples to retain when --minority-class is set")
    parser.add_argument("--test-size", type=float, default=0.2)
    parser.add_argument("--seed", type=int, default=42)
    parser.add_argument("--output", type=Path, default=BACKEND / "predictions/artifacts/rice_disease_mlp.joblib")
    args = parser.parse_args()

    X, y, groups, original_counts = read_dataset(args.dataset_dir, args.max_per_class)
    rng = np.random.default_rng(args.seed)
    if args.minority_class:
        if args.minority_count < 2:
            parser.error("--minority-count must be at least 2 when --minority-class is set")
        class_indices = np.flatnonzero(y == args.minority_class)
        if args.minority_count > len(class_indices):
            parser.error(f"{args.minority_class} has only {len(class_indices)} samples in this run")
        kept = rng.choice(class_indices, size=args.minority_count, replace=False)
        keep_mask = np.ones(len(y), dtype=bool)
        keep_mask[class_indices] = False
        keep_mask[kept] = True
        X, y, groups = X[keep_mask], y[keep_mask], groups[keep_mask]
        original_counts = Counter(y)
    print("Sample class counts before split:", dict(sorted(original_counts.items())))
    # Keep filename families together; the dataset has grouped/variant image names.
    train_indices, test_indices = [], []
    for label in np.unique(y):
        label_indices = np.flatnonzero(y == label)
        label_groups = np.unique(groups[label_indices])
        heldout_count = max(1, round(len(label_groups) * args.test_size))
        heldout_groups = set(rng.choice(label_groups, size=heldout_count, replace=False))
        for idx in label_indices:
            (test_indices if groups[idx] in heldout_groups else train_indices).append(int(idx))
    X_train, X_test = X[train_indices], X[test_indices]
    y_train, y_test = y[train_indices], y[test_indices]
    print("Dataset class counts:")
    for label, count in sorted(original_counts.items()):
        print(f"  {label}: {count}")
    print("Filename-family holdout classes:", dict(sorted(Counter(y_test).items())))
    print("Training split before SMOTE:", dict(sorted(Counter(y_train).items())))

    scaler = StandardScaler()
    X_train_scaled = scaler.fit_transform(X_train)
    smallest = min(Counter(y_train).values())
    smote = SMOTE(random_state=args.seed, k_neighbors=min(5, smallest - 1))
    X_balanced, y_balanced = smote.fit_resample(X_train_scaled, y_train)
    print("Training split after SMOTE:", dict(sorted(Counter(y_balanced).items())))

    classifier = MLPClassifier(
        hidden_layer_sizes=(64, 32), activation="relu", solver="adam",
        alpha=0.002, learning_rate_init=0.001, max_iter=350,
        early_stopping=True, validation_fraction=0.12,
        n_iter_no_change=20, random_state=args.seed,
    )
    classifier.fit(X_balanced, y_balanced)
    X_test_scaled = scaler.transform(X_test)
    predicted = classifier.predict(X_test_scaled)
    holdout_accuracy = float(accuracy_score(y_test, predicted))
    holdout_macro_f1 = float(f1_score(y_test, predicted, average='macro'))
    print(f"\nHoldout accuracy: {holdout_accuracy:.3f}")
    print(f"Holdout macro F1: {holdout_macro_f1:.3f}")
    print("\nPer-class report (held-out images):")
    print(classification_report(y_test, predicted, labels=classifier.classes_, zero_division=0))
    print("Confusion matrix (true rows, predicted columns):")
    print(confusion_matrix(y_test, predicted, labels=classifier.classes_))

    pipeline = Pipeline([("scaler", scaler), ("classifier", classifier)])
    args.output.parent.mkdir(parents=True, exist_ok=True)
    joblib.dump(pipeline, args.output)
    metadata = {
        "dataset": "Rice Leaf Disease Image Samples (Mendeley Data, CC BY 4.0)",
        "dataset_counts": dict(sorted((str(k), int(v)) for k, v in original_counts.items())),
        "feature_extractor": "RGB mean/std + HSV histograms + color ratios; 38 float features",
        "split": "filename-family holdout before training-only SMOTE",
        "seed": args.seed,
        "holdout_accuracy": round(holdout_accuracy, 6),
        "holdout_macro_f1": round(holdout_macro_f1, 6),
        "versions": {
            "python": platform.python_version(),
            "numpy": np.__version__,
            "scikit_learn": sklearn.__version__,
            "imbalanced_learn": imblearn.__version__,
            "joblib": joblib.__version__,
        },
        "scope": "Four disease classes only; no healthy-leaf class; not validated on independent field photos.",
    }
    metadata_path = args.output.with_suffix(".metadata.json")
    metadata_path.write_text(json.dumps(metadata, indent=2) + "\n")
    print(f"\nSaved model artifact: {args.output}")
    print(f"Saved model metadata: {metadata_path}")
    print("This dataset has no healthy-leaf class; do not interpret a non-Blast label as healthy.")


if __name__ == "__main__":
    main()
