"""Shared, leakage-free experiment helpers for GuardChain AI."""
from __future__ import annotations

import json
import hashlib
import importlib.metadata
import platform
import random
from pathlib import Path

import numpy as np
import torch
from sklearn.metrics import (
    accuracy_score,
    average_precision_score,
    confusion_matrix,
    f1_score,
    precision_score,
    precision_recall_curve,
    recall_score,
    roc_auc_score,
)
from sklearn.model_selection import train_test_split

SEED = 42
ROOT = Path(__file__).resolve().parent
ARTIFACT_DIR = ROOT / "artifacts" / "phase3"
RESULT_DIR = ROOT / "results" / "phase3"
_DATASET_SHA256 = None


def set_seed(seed: int = SEED) -> None:
    random.seed(seed)
    np.random.seed(seed)
    torch.manual_seed(seed)
    if torch.cuda.is_available():
        torch.cuda.manual_seed_all(seed)


def split_indices(labels):
    """Return stratified 65/15/20 train/validation/test row indices."""
    indices = np.arange(len(labels))
    train_val, test = train_test_split(
        indices, test_size=0.20, random_state=SEED, stratify=labels
    )
    train, validation = train_test_split(
        train_val,
        test_size=0.1875,
        random_state=SEED,
        stratify=np.asarray(labels)[train_val],
    )
    return train, validation, test


def select_threshold(y_true, probabilities):
    """Choose the F1-maximizing threshold on validation data only."""
    precision, recall, thresholds = precision_recall_curve(y_true, probabilities)
    if thresholds.size == 0:
        return 0.5
    denominator = precision[:-1] + recall[:-1]
    f1 = np.divide(
        2 * precision[:-1] * recall[:-1], denominator,
        out=np.zeros_like(denominator), where=denominator > 0,
    )
    return float(thresholds[int(np.argmax(f1))])


def calculate_metrics(y_true, probabilities, threshold):
    y_true = np.asarray(y_true, dtype=int)
    probabilities = np.asarray(probabilities, dtype=float).reshape(-1)
    predictions = probabilities >= threshold
    return {
        "threshold": float(threshold),
        "support": int(len(y_true)),
        "fraud_support": int(np.sum(y_true == 1)),
        "accuracy": float(accuracy_score(y_true, predictions)),
        "precision": float(precision_score(y_true, predictions, zero_division=0)),
        "recall": float(recall_score(y_true, predictions, zero_division=0)),
        "f1": float(f1_score(y_true, predictions, zero_division=0)),
        "pr_auc": float(average_precision_score(y_true, probabilities)),
        "roc_auc": float(roc_auc_score(y_true, probabilities)),
        "confusion_matrix": confusion_matrix(y_true, predictions, labels=[0, 1]).tolist(),
    }


def save_experiment(name, model_path, scaler_path, feature_names, threshold, metrics, y_test, probabilities, indices=None):
    global _DATASET_SHA256
    ARTIFACT_DIR.mkdir(parents=True, exist_ok=True)
    RESULT_DIR.mkdir(parents=True, exist_ok=True)
    if _DATASET_SHA256 is None:
        digest = hashlib.sha256()
        with (ROOT / "creditcard.csv").open("rb") as dataset_file:
            for chunk in iter(lambda: dataset_file.read(1024 * 1024), b""):
                digest.update(chunk)
        _DATASET_SHA256 = digest.hexdigest()
    versions = {}
    for package in ("numpy", "pandas", "scikit-learn", "torch", "Flask", "web3"):
        try:
            versions[package] = importlib.metadata.version(package)
        except importlib.metadata.PackageNotFoundError:
            versions[package] = "unavailable"
    metadata = {
        "model": name,
        "seed": SEED,
        "split": {"train": 0.65, "validation": 0.15, "test": 0.20},
        "split_indices_file": "data_split_indices.npz",
        "dataset_file": "creditcard.csv",
        "dataset_sha256": _DATASET_SHA256,
        "environment": {"python": platform.python_version(), "platform": platform.platform(), "packages": versions},
        "threshold_selection": "maximize validation F1",
        "threshold": float(threshold),
        "features": list(feature_names),
        "model_path": str(Path(model_path).relative_to(ROOT)),
        "scaler_path": str(Path(scaler_path).relative_to(ROOT)),
        "test_metrics": metrics,
    }
    with (RESULT_DIR / f"{name}_metrics.json").open("w", encoding="utf-8") as stream:
        json.dump(metadata, stream, indent=2)
    if indices is not None:
        np.savez_compressed(
            RESULT_DIR / "data_split_indices.npz",
            train=np.asarray(indices["train"], dtype=np.int64),
            validation=np.asarray(indices["validation"], dtype=np.int64),
            test=np.asarray(indices["test"], dtype=np.int64),
        )
    np.savez_compressed(
        RESULT_DIR / f"{name}_test_predictions.npz",
        y_true=np.asarray(y_test, dtype=np.int8),
        probability=np.asarray(probabilities, dtype=np.float32).reshape(-1),
    )
    return metadata
