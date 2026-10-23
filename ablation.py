"""Compare class-weighted and unweighted MLP loss on identical data partitions."""
import copy
import json

import numpy as np
import pandas as pd
import torch
import torch.nn as nn
from sklearn.preprocessing import StandardScaler

from dl_model import FraudDetectionMLP
from experiment_utils import RESULT_DIR, ROOT, calculate_metrics, select_threshold, set_seed, split_indices
from train_dl_model import probabilities, to_loader


def run_variant(name, weighted, x_train, x_validation, x_test, y_train, y_validation, y_test):
    set_seed()
    train_loader = to_loader(x_train, y_train, shuffle=True)
    validation_loader = to_loader(x_validation, y_validation)
    model = FraudDetectionMLP(input_dim=x_train.shape[1])
    positive_weight = float((y_train == 0).sum() / (y_train == 1).sum()) if weighted else 1.0
    criterion = nn.BCEWithLogitsLoss(pos_weight=torch.tensor([positive_weight]))
    optimizer = torch.optim.Adam(model.parameters(), lr=0.005)
    best_loss, best_weights, stale = float("inf"), copy.deepcopy(model.state_dict()), 0
    for _epoch in range(25):
        model.train()
        for batch_x, batch_y in train_loader:
            optimizer.zero_grad(set_to_none=True)
            loss = criterion(model(batch_x), batch_y)
            loss.backward()
            optimizer.step()
        model.eval()
        val_loss = 0.0
        with torch.no_grad():
            for batch_x, batch_y in validation_loader:
                val_loss += criterion(model(batch_x), batch_y).item() * len(batch_x)
        val_loss /= len(validation_loader.dataset)
        if val_loss < best_loss:
            best_loss, best_weights, stale = val_loss, copy.deepcopy(model.state_dict()), 0
        else:
            stale += 1
            if stale >= 4:
                break
    model.load_state_dict(best_weights)
    validation_probability = probabilities(model, x_validation)
    threshold = select_threshold(y_validation, validation_probability)
    test_probability = probabilities(model, x_test)
    return {
        "loss_weighting": name,
        "positive_weight": positive_weight,
        "validation_threshold": threshold,
        "test_metrics": calculate_metrics(y_test, test_probability, threshold),
    }


def main():
    set_seed()
    weighted_metadata = json.loads((RESULT_DIR / "mlp_metrics.json").read_text(encoding="utf-8"))
    weighted_predictions = np.load(RESULT_DIR / "mlp_test_predictions.npz")
    weighted = {
        "loss_weighting": "weighted BCE",
        "positive_weight": weighted_metadata.get("training_config", {}).get("positive_class_weight"),
        "validation_threshold": weighted_metadata["threshold"],
        "test_metrics": weighted_metadata["test_metrics"],
    }
    data = pd.read_csv(ROOT / "creditcard.csv")
    features = data.drop(columns="Class")
    labels = data["Class"].astype(int).to_numpy()
    train_idx, validation_idx, test_idx = split_indices(labels)
    scaler = StandardScaler().fit(features.iloc[train_idx])
    x_train = scaler.transform(features.iloc[train_idx]).astype("float32")
    x_validation = scaler.transform(features.iloc[validation_idx]).astype("float32")
    x_test = scaler.transform(features.iloc[test_idx]).astype("float32")
    y_train, y_validation, y_test = labels[train_idx], labels[validation_idx], labels[test_idx]
    unweighted = run_variant("unweighted BCE", False, x_train, x_validation, x_test, y_train, y_validation, y_test)
    if not (weighted_predictions["y_true"] == y_test).all():
        raise ValueError("Saved weighted MLP predictions do not match the current test partition.")
    result = {
        "protocol": "same fixed 65/15/20 stratified split; train-only scaling; threshold selected on validation F1",
        "variants": [weighted, unweighted],
    }
    RESULT_DIR.mkdir(parents=True, exist_ok=True)
    (RESULT_DIR / "ablation.json").write_text(json.dumps(result, indent=2), encoding="utf-8")
    print(f"Saved ablation results to {RESULT_DIR / 'ablation.json'}")
    print(result)


if __name__ == "__main__":
    main()
