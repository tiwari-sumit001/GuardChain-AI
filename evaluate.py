"""Recompute saved test metrics, plots and local inference benchmarks.

Run after train_dl_model.py and train_model.py. The Flask benchmark stubs audit
writes so evaluation never submits transactions to Ganache.
"""
import json
import os
import time
from pathlib import Path

from experiment_utils import RESULT_DIR, ROOT, calculate_metrics

os.environ.setdefault("MPLCONFIGDIR", str(RESULT_DIR / ".mplconfig"))
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
from sklearn.metrics import confusion_matrix, precision_recall_curve, roc_curve

def load_run(name):
    meta_path = RESULT_DIR / f"{name}_metrics.json"
    preds_path = RESULT_DIR / f"{name}_test_predictions.npz"
    if not meta_path.is_file() or not preds_path.is_file():
        raise FileNotFoundError(f"Missing {name} run. Train it before evaluating.")
    metadata = json.loads(meta_path.read_text(encoding="utf-8"))
    predictions = np.load(preds_path)
    y_true = predictions["y_true"]
    probability = predictions["probability"]
    metrics = calculate_metrics(y_true, probability, metadata["threshold"])
    metadata["test_metrics"] = metrics
    meta_path.write_text(json.dumps(metadata, indent=2), encoding="utf-8")
    return metadata, y_true, probability


def save_plots(runs):
    RESULT_DIR.mkdir(parents=True, exist_ok=True)
    for name, (metadata, y_true, probability) in runs.items():
        threshold = metadata["threshold"]
        predictions = probability >= threshold
        cm = confusion_matrix(y_true, predictions, labels=[0, 1])
        fig, ax = plt.subplots(figsize=(5, 4))
        image = ax.imshow(cm, cmap="Blues")
        ax.set(title=f"{name.upper()} confusion matrix", xlabel="Predicted", ylabel="Actual", xticks=[0, 1], yticks=[0, 1])
        for (row, col), value in np.ndenumerate(cm):
            ax.text(col, row, str(value), ha="center", va="center")
        fig.colorbar(image, ax=ax)
        fig.tight_layout()
        fig.savefig(RESULT_DIR / f"{name}_confusion_matrix.png", dpi=160)
        plt.close(fig)

        precision, recall, _ = precision_recall_curve(y_true, probability)
        fpr, tpr, _ = roc_curve(y_true, probability)
        fig, axes = plt.subplots(1, 2, figsize=(10, 4))
        axes[0].plot(recall, precision)
        axes[0].set(title=f"{name.upper()} precision-recall", xlabel="Recall", ylabel="Precision", xlim=(0, 1), ylim=(0, 1))
        axes[1].plot(fpr, tpr)
        axes[1].plot([0, 1], [0, 1], linestyle="--", color="gray")
        axes[1].set(title=f"{name.upper()} ROC", xlabel="False positive rate", ylabel="True positive rate", xlim=(0, 1), ylim=(0, 1))
        fig.tight_layout()
        fig.savefig(RESULT_DIR / f"{name}_curves.png", dpi=160)
        plt.close(fig)


def benchmark_flask():
    import app as application
    from experiment_utils import split_indices
    try:
        import psutil
        process = psutil.Process()
        memory_before = process.memory_info().rss
    except ImportError:
        process = None
        memory_before = None

    # Stub audit writes: the benchmark measures model + Flask, never Ganache.
    application.store_on_blockchain = lambda **kwargs: {
        "mode": "evaluation_stub", "tx_hash": None, "block_number": None, "gas_used": None
    }
    data = pd.read_csv(ROOT / "creditcard.csv")
    features = data.drop(columns="Class")
    labels = data["Class"].astype(int).to_numpy()
    _, _, test_indices = split_indices(labels)
    rows = data.iloc[test_indices].head(min(500, len(test_indices)))
    durations = {"dl": [], "rf": []}
    with application.app.test_client() as client:
        for model_type in durations:
            for request_index, row in enumerate(rows.itertuples(index=False, name=None)):
                values = dict(zip(data.columns, row))
                values.pop("Class", None)
                started = time.perf_counter()
                response = client.post("/predict", json={"features": values, "model_type": model_type})
                wall_ms = (time.perf_counter() - started) * 1000
                if response.status_code != 200:
                    raise RuntimeError(f"Flask benchmark request failed: {response.get_json()}")
                if request_index >= 10:  # discard ten warmup requests per model
                    durations[model_type].append({"wall_ms": wall_ms, **response.get_json()})

    result = {}
    for model_type, records in durations.items():
        wall = np.asarray([record["wall_ms"] for record in records])
        scoring = np.asarray([record["scoring_ms"] for record in records])
        inference = np.asarray([record["inference_ms"] for record in records])
        result[model_type] = {
            "requests": int(len(records)),
            "warmup_requests_discarded": 10,
            "throughput_requests_per_second": float(1000 / np.mean(wall)),
            "http_test_client_wall_ms_p50": float(np.percentile(wall, 50)),
            "http_test_client_wall_ms_p95": float(np.percentile(wall, 95)),
            "flask_scoring_ms_p50": float(np.percentile(scoring, 50)),
            "flask_scoring_ms_p95": float(np.percentile(scoring, 95)),
            "model_inference_ms_p50": float(np.percentile(inference, 50)),
            "model_inference_ms_p95": float(np.percentile(inference, 95)),
        }
    if process is not None:
        result["process_rss_bytes_before"] = int(memory_before)
        result["process_rss_bytes_after"] = int(process.memory_info().rss)
    else:
        result["process_rss_bytes"] = None
    result["measurement_note"] = "Flask test-client benchmark; blockchain writes stubbed; not a network-client or Ganache latency measurement."
    fig, ax = plt.subplots(figsize=(6, 4))
    labels = ["MLP", "Random Forest"]
    p50 = [result[name]["flask_scoring_ms_p50"] for name in ("dl", "rf")]
    p95 = [result[name]["flask_scoring_ms_p95"] for name in ("dl", "rf")]
    positions = np.arange(len(labels))
    ax.bar(positions - 0.18, p50, width=0.36, label="p50")
    ax.bar(positions + 0.18, p95, width=0.36, label="p95")
    ax.set(xticks=positions, xticklabels=labels, ylabel="Flask scoring time (ms)", title="Local scoring latency; audit writes stubbed")
    ax.legend()
    fig.tight_layout()
    fig.savefig(RESULT_DIR / "latency.png", dpi=160)
    plt.close(fig)
    return result


def main():
    runs = {name: load_run(name) for name in ("mlp", "rf")}
    mlp, rf = runs["mlp"][0]["test_metrics"], runs["rf"][0]["test_metrics"]
    if mlp["support"] != rf["support"] or runs["mlp"][1].tolist() != runs["rf"][1].tolist():
        raise ValueError("MLP and RF predictions do not share identical held-out labels.")
    comparison = {
        "test_support": mlp["support"],
        "mlp": mlp,
        "random_forest": rf,
        "latency_and_memory": benchmark_flask(),
    }
    ablation_path = RESULT_DIR / "ablation.json"
    if ablation_path.is_file():
        ablation = json.loads(ablation_path.read_text(encoding="utf-8"))
        comparison["ablation"] = ablation
        variants = ablation["variants"]
        fig, ax = plt.subplots(figsize=(6, 4))
        labels = [variant["loss_weighting"] for variant in variants]
        positions = np.arange(len(labels))
        for offset, metric, color in ((-0.18, "precision", "#2563eb"), (0.18, "recall", "#dc2626")):
            values = [variant["test_metrics"][metric] for variant in variants]
            ax.bar(positions + offset, values, width=0.36, label=metric.capitalize(), color=color)
        ax.set(xticks=positions, xticklabels=labels, ylabel="Score", ylim=(0, 1), title="Class-weight ablation (held-out test)")
        ax.legend()
        fig.tight_layout()
        fig.savefig(RESULT_DIR / "ablation.png", dpi=160)
        plt.close(fig)
    (RESULT_DIR / "evaluation.json").write_text(json.dumps(comparison, indent=2), encoding="utf-8")
    save_plots(runs)
    lines = ["| Model | Threshold | Accuracy | Precision | Recall | F1 | PR-AUC | ROC-AUC |", "|---|---:|---:|---:|---:|---:|---:|---:|"]
    for name, metrics in (("MLP", mlp), ("Random Forest", rf)):
        lines.append("| {} | {:.4f} | {:.4f} | {:.4f} | {:.4f} | {:.4f} | {:.4f} | {:.4f} |".format(
            name, metrics["threshold"], metrics["accuracy"], metrics["precision"], metrics["recall"],
            metrics["f1"], metrics["pr_auc"], metrics["roc_auc"],
        ))
    (RESULT_DIR / "comparison.md").write_text("\n".join(lines) + "\n", encoding="utf-8")
    print(f"Saved evaluation artifacts under {RESULT_DIR}")


if __name__ == "__main__":
    main()
