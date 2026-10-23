"""Train the MLP with train-only scaling, validation early stopping and a held-out test."""
import copy
import json
import pickle

import numpy as np
import pandas as pd
import torch
import torch.nn as nn
from sklearn.preprocessing import StandardScaler
from torch.utils.data import DataLoader, TensorDataset

from dl_model import FraudDetectionMLP
from experiment_utils import (
    ARTIFACT_DIR,
    RESULT_DIR,
    ROOT,
    calculate_metrics,
    save_experiment,
    select_threshold,
    set_seed,
    split_indices,
)


def to_loader(features, labels, batch_size=1024, shuffle=False):
    x = torch.as_tensor(features, dtype=torch.float32)
    y = torch.as_tensor(labels, dtype=torch.float32).reshape(-1, 1)
    return DataLoader(TensorDataset(x, y), batch_size=batch_size, shuffle=shuffle)


def probabilities(model, values):
    model.eval()
    with torch.no_grad():
        return torch.sigmoid(model(torch.as_tensor(values, dtype=torch.float32))).cpu().numpy().reshape(-1)


def main():
    set_seed()
    data_path = ROOT / "creditcard.csv"
    if not data_path.is_file():
        raise FileNotFoundError(f"Dataset not found: {data_path}")
    data = pd.read_csv(data_path)
    if "Class" not in data or data["Class"].nunique() != 2:
        raise ValueError("Dataset must contain a binary Class target column.")
    features = data.drop(columns="Class")
    labels = data["Class"].astype(int).to_numpy()
    train_idx, validation_idx, test_idx = split_indices(labels)

    scaler = StandardScaler()
    scaler.fit(features.iloc[train_idx])
    x_train = scaler.transform(features.iloc[train_idx]).astype(np.float32)
    x_validation = scaler.transform(features.iloc[validation_idx]).astype(np.float32)
    x_test = scaler.transform(features.iloc[test_idx]).astype(np.float32)
    train_loader = to_loader(x_train, labels[train_idx], shuffle=True)
    validation_loader = to_loader(x_validation, labels[validation_idx])

    negative = int(np.sum(labels[train_idx] == 0))
    positive = int(np.sum(labels[train_idx] == 1))
    model = FraudDetectionMLP(input_dim=features.shape[1])
    criterion = nn.BCEWithLogitsLoss(pos_weight=torch.tensor([negative / positive]))
    optimizer = torch.optim.Adam(model.parameters(), lr=0.005)
    best_loss = float("inf")
    best_weights = copy.deepcopy(model.state_dict())
    patience, stale_epochs, max_epochs = 5, 0, 50

    for epoch in range(max_epochs):
        model.train()
        running_loss = 0.0
        for batch_x, batch_y in train_loader:
            optimizer.zero_grad(set_to_none=True)
            loss = criterion(model(batch_x), batch_y)
            loss.backward()
            optimizer.step()
            running_loss += loss.item() * len(batch_x)
        model.eval()
        validation_loss = 0.0
        with torch.no_grad():
            for batch_x, batch_y in validation_loader:
                validation_loss += criterion(model(batch_x), batch_y).item() * len(batch_x)
        validation_loss /= len(validation_loader.dataset)
        print(f"Epoch {epoch + 1}: train_loss={running_loss / len(train_loader.dataset):.6f} validation_loss={validation_loss:.6f}")
        if validation_loss < best_loss:
            best_loss = validation_loss
            best_weights = copy.deepcopy(model.state_dict())
            stale_epochs = 0
        else:
            stale_epochs += 1
            if stale_epochs >= patience:
                print(f"Early stopping after epoch {epoch + 1}.")
                break

    model.load_state_dict(best_weights)
    validation_probability = probabilities(model, x_validation)
    threshold = select_threshold(labels[validation_idx], validation_probability)
    test_probability = probabilities(model, x_test)
    metrics = calculate_metrics(labels[test_idx], test_probability, threshold)

    ARTIFACT_DIR.mkdir(parents=True, exist_ok=True)
    model_path = ARTIFACT_DIR / "dl_model.pth"
    scaler_path = ARTIFACT_DIR / "dl_scaler.pkl"
    torch.save(model.state_dict(), model_path)
    with scaler_path.open("wb") as stream:
        pickle.dump(scaler, stream)
    with (ARTIFACT_DIR / "dl_features.pkl").open("wb") as stream:
        pickle.dump(list(features.columns), stream)
    metadata = save_experiment(
        "mlp", model_path, scaler_path, features.columns, threshold,
        metrics, labels[test_idx], test_probability,
        indices={"train": train_idx, "validation": validation_idx, "test": test_idx},
    )
    metadata["training_config"] = {
        "loss": "BCEWithLogitsLoss",
        "positive_class_weight": float(negative / positive),
        "optimizer": "Adam",
        "learning_rate": 0.005,
        "max_epochs": max_epochs,
        "epochs_trained": epoch + 1,
        "early_stopping_patience": patience,
        "best_validation_loss": float(best_loss),
        "batch_size": 1024,
    }
    (RESULT_DIR / "mlp_metrics.json").write_text(json.dumps(metadata, indent=2), encoding="utf-8")

    # Balanced offline examples are selected only from the held-out test rows.
    test_rows = data.iloc[test_idx]
    sample_parts = [
        test_rows[test_rows["Class"] == cls].sample(n=20, random_state=42)
        for cls in (0, 1)
    ]
    samples = []
    for row_index, row in pd.concat(sample_parts).iterrows():
        samples.append({
            "id": int(row_index),
            "class": int(row["Class"]),
            "features": {name: float(value) for name, value in row.drop("Class").items()},
        })
    with (ROOT / "static" / "sample_transactions.json").open("w", encoding="utf-8") as stream:
        json.dump(samples, stream, indent=2, allow_nan=False)

    print(f"Saved model to {model_path}")
    print(f"Saved measured test metrics to {RESULT_DIR / 'mlp_metrics.json'}")
    print(metadata["test_metrics"])


if __name__ == "__main__":
    main()
