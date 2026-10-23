"""Train a reproducible Random Forest baseline with train-only preprocessing."""
import pickle
from pathlib import Path
import json

import pandas as pd
from sklearn.ensemble import RandomForestClassifier
from sklearn.metrics import average_precision_score
from sklearn.preprocessing import StandardScaler

from experiment_utils import (
    ARTIFACT_DIR,
    ROOT,
    RESULT_DIR,
    calculate_metrics,
    save_experiment,
    select_threshold,
    set_seed,
    split_indices,
)


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
    train = features.iloc[train_idx].copy()
    validation = features.iloc[validation_idx].copy()
    test = features.iloc[test_idx].copy()
    scaler.fit(train[["Amount"]])
    for partition in (train, validation, test):
        partition.loc[:, "Amount"] = scaler.transform(partition[["Amount"]]).ravel()

    candidates = []
    best_validation_pr_auc = -1.0
    model = None
    validation_probability = None
    for n_estimators in (50, 100):
        candidate = RandomForestClassifier(
            n_estimators=n_estimators,
            random_state=42,
            class_weight="balanced_subsample",
            n_jobs=-1,
        )
        candidate.fit(train, labels[train_idx])
        candidate_validation_probability = candidate.predict_proba(validation)[:, 1]
        validation_pr_auc = float(average_precision_score(labels[validation_idx], candidate_validation_probability))
        candidates.append({"n_estimators": n_estimators, "validation_pr_auc": validation_pr_auc})
        print(f"RF candidate trees={n_estimators}: validation PR-AUC={validation_pr_auc:.6f}")
        if validation_pr_auc > best_validation_pr_auc:
            model = candidate
            validation_probability = candidate_validation_probability
            best_validation_pr_auc = validation_pr_auc
    threshold = select_threshold(labels[validation_idx], validation_probability)
    test_probability = model.predict_proba(test)[:, 1]
    metrics = calculate_metrics(labels[test_idx], test_probability, threshold)

    ARTIFACT_DIR.mkdir(parents=True, exist_ok=True)
    model_path = ARTIFACT_DIR / "rf_model.pkl"
    scaler_path = ARTIFACT_DIR / "rf_scaler.pkl"
    with model_path.open("wb") as stream:
        pickle.dump(model, stream)
    with scaler_path.open("wb") as stream:
        pickle.dump(scaler, stream)
    with (ARTIFACT_DIR / "rf_features.pkl").open("wb") as stream:
        pickle.dump(list(features.columns), stream)

    metadata = save_experiment(
        "rf", model_path, scaler_path, features.columns, threshold,
        metrics, labels[test_idx], test_probability,
        indices={"train": train_idx, "validation": validation_idx, "test": test_idx},
    )
    metadata["training_config"] = {
        "classifier": "RandomForestClassifier",
        "n_estimators": int(model.n_estimators),
        "class_weight": "balanced_subsample",
        "random_state": 42,
        "n_jobs": -1,
        "selection_metric": "validation PR-AUC",
        "candidate_results": candidates,
        "selected_validation_pr_auc": best_validation_pr_auc,
        "amount_scaler": "StandardScaler fitted on train only",
    }
    (RESULT_DIR / "rf_metrics.json").write_text(json.dumps(metadata, indent=2), encoding="utf-8")
    # Keep the historical UI metrics untouched. New measured results live in results/phase3.
    print(f"Saved model to {model_path}")
    print(f"Saved measured test metrics to {RESULT_DIR / 'rf_metrics.json'}")
    print(metadata["test_metrics"])


if __name__ == "__main__":
    main()
