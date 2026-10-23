from flask import Flask, request, jsonify, render_template
import pickle
import torch
import json
import os
import random
import pandas as pd
import math
import time
from pathlib import Path
from dl_model import FraudDetectionMLP
from dotenv import load_dotenv

ROOT = Path(__file__).resolve().parent
load_dotenv(ROOT / ".env")

from blockchain import store_on_blockchain, update_on_blockchain, get_blockchain_logs, get_network_status

app = Flask(__name__)
app.config["MAX_CONTENT_LENGTH"] = 64 * 1024
PHASE3_ARTIFACTS = ROOT / "artifacts" / "phase3"
PHASE3_RESULTS = ROOT / "results" / "phase3"


def load_threshold(result_name):
    try:
        with (PHASE3_RESULTS / result_name).open("r", encoding="utf-8") as stream:
            return float(json.load(stream).get("threshold", 0.5))
    except (OSError, ValueError, TypeError, json.JSONDecodeError):
        return 0.5


dl_threshold = load_threshold("mlp_metrics.json")
rf_threshold = load_threshold("rf_metrics.json")

# 1. Load PyTorch Model
print("Loading Deep Learning model...")
model = None
try:
    model = FraudDetectionMLP(input_dim=30)
    model_path = PHASE3_ARTIFACTS / "dl_model.pth"
    if not model_path.exists():
        model_path = ROOT / "dl_model.pth"
    model.load_state_dict(torch.load(model_path, map_location="cpu"))
    print("[SUCCESS] Loaded PyTorch weights from dl_model.pth")
except Exception as e:
    print("[WARNING] Could not load PyTorch weights. Run train_dl_model.py first! Error:", e)
    model = None
if model is not None:
    model.eval()

# Load PyTorch Scaler & Features
try:
    scaler_path = PHASE3_ARTIFACTS / "dl_scaler.pkl"
    features_path = PHASE3_ARTIFACTS / "dl_features.pkl"
    if not scaler_path.exists():
        scaler_path = ROOT / "scaler_dl.pkl"
        features_path = ROOT / "features_dl.pkl"
    with open(scaler_path, "rb") as artifact:
        scaler = pickle.load(artifact)
    with open(features_path, "rb") as artifact:
        features = pickle.load(artifact)
    print("[SUCCESS] Loaded scaler_dl.pkl and features_dl.pkl")
except Exception as e:
    print("[WARNING] Could not load PyTorch scaler or features list. Run train_dl_model.py first! Error:", e)
    scaler = None
    features = None

# 2. Load Random Forest Model
print("Loading Random Forest model...")
try:
    rf_model_path = PHASE3_ARTIFACTS / "rf_model.pkl"
    rf_scaler_path = PHASE3_ARTIFACTS / "rf_scaler.pkl"
    rf_features_path = PHASE3_ARTIFACTS / "rf_features.pkl"
    if not rf_model_path.exists():
        rf_model_path = ROOT / "model.pkl"
        rf_scaler_path = ROOT / "scaler.pkl"
        rf_features_path = ROOT / "features.pkl"
    with open(rf_model_path, "rb") as artifact:
        rf_model = pickle.load(artifact)
    with open(rf_scaler_path, "rb") as artifact:
        rf_scaler = pickle.load(artifact)
    with open(rf_features_path, "rb") as artifact:
        rf_features = pickle.load(artifact)
    print("[SUCCESS] Loaded Random Forest model, scaler, and features")
except Exception as e:
    print("[WARNING] Could not load Random Forest model. Run train_model.py first! Error:", e)
    rf_model = None
    rf_scaler = None
    rf_features = None

# 3. Load sample transactions cache for live simulation
sample_transactions_cache = []
try:
    samples_path = ROOT / "static" / "sample_transactions.json"
    if os.path.exists(samples_path):
        with open(samples_path, "r") as f:
            sample_transactions_cache = json.load(f)
        print(f"[SUCCESS] Cached {len(sample_transactions_cache)} sample transactions for simulator")
except Exception as e:
    print("[WARNING] Could not cache sample transactions:", e)

@app.route("/")
def home():
    return render_template("index.html")

@app.route("/predict", methods=["POST"])
def predict():
    started = time.perf_counter()
    try:
        data = request.get_json(silent=True)
        if not isinstance(data, dict):
            return jsonify({"status": "error", "message": "Request body must be a JSON object."}), 400
        client_features = data.get("features")
        if not isinstance(client_features, dict):
            return jsonify({"status": "error", "message": "features must be an object containing transaction values."}), 400
        model_type = data.get("model_type", "dl")
        if model_type not in {"dl", "rf", "hybrid"}:
            return jsonify({"status": "error", "message": "model_type must be dl, rf, or hybrid."}), 400
        sender = str(data.get("sender", "Anonymous"))[:100]
        receiver = str(data.get("receiver", "Fraud Portal"))[:100]
        available_features = (
            list(dict.fromkeys((features or []) + (rf_features or []))) if model_type == "hybrid"
            else (rf_features if model_type == "rf" else features)
        )
        if not available_features:
            return jsonify({"status": "error", "message": "No trained model is available. Check model artifacts and restart the app."}), 503
        missing = [name for name in available_features if name not in client_features]
        if missing:
            return jsonify({"status": "error", "message": f"Missing required feature(s): {', '.join(missing)}"}), 400
        try:
            normalized = {name: float(client_features[name]) for name in available_features}
        except (TypeError, ValueError, OverflowError):
            return jsonify({"status": "error", "message": "All transaction features must be numeric."}), 400
        if not all(math.isfinite(value) for value in normalized.values()):
            return jsonify({"status": "error", "message": "Transaction features must be finite numbers."}), 400
        if normalized.get("Amount", 0) < 0:
            return jsonify({"status": "error", "message": "Amount cannot be negative."}), 400
        amount = normalized.get("Amount", 0)
        if model_type in {"dl", "hybrid"} and (model is None or scaler is None or features is None):
            return jsonify({"status": "error", "message": "The deep-learning model is unavailable."}), 503
        if model_type in {"rf", "hybrid"} and (rf_model is None or rf_scaler is None or rf_features is None):
            return jsonify({"status": "error", "message": "The Random Forest model is unavailable."}), 503
        inference_started = time.perf_counter()
        
        # Calculate PyTorch Probability (DL)
        dl_prob = 0.0
        if model_type in {"dl", "hybrid"} and model is not None and scaler is not None and features is not None:
            feature_vector = []
            for col in features:
                val = normalized[col]
                feature_vector.append(val)
            X_input = pd.DataFrame([feature_vector], columns=features)
            X_scaled = scaler.transform(X_input)
            X_tensor = torch.tensor(X_scaled, dtype=torch.float32)
            with torch.no_grad():
                logits = model(X_tensor)
                dl_prob = torch.sigmoid(logits).item()
                
        # Calculate Random Forest Probability (RF)
        rf_prob = 0.0
        if model_type in {"rf", "hybrid"} and rf_model is not None and rf_scaler is not None and rf_features is not None:
            rf_input_dict = {}
            for col in rf_features:
                rf_input_dict[col] = normalized[col]
            X_df = pd.DataFrame([rf_input_dict])
            X_df["Amount"] = rf_scaler.transform(X_df[["Amount"]])
            rf_prob = float(rf_model.predict_proba(X_df)[0][1])
            
        # Determine prediction and final probability based on selected model
        if model_type == "rf":
            prob = rf_prob
            threshold = rf_threshold
            prediction = "Fraud" if prob >= threshold else "Safe"
        elif model_type == "hybrid":
            # Hybrid consensus: 60% PyTorch + 40% Random Forest
            prob = 0.6 * dl_prob + 0.4 * rf_prob
            threshold = 0.5
            prediction = "Fraud" if prob >= threshold else "Safe"
        else: # default 'dl'
            prob = dl_prob
            threshold = dl_threshold
            prediction = "Fraud" if prob >= threshold else "Safe"
        inference_ms = (time.perf_counter() - inference_started) * 1000
        scoring_ms = (time.perf_counter() - started) * 1000
            
        # Log to Blockchain if Fraudulent
        blockchain_receipt = None
        blockchain_ms = 0.0
        if prediction == "Fraud":
            result_str = f"Fraud ({model_type.upper()} Prob: {prob:.4f})"
            blockchain_started = time.perf_counter()
            blockchain_receipt = store_on_blockchain(
                amount=amount,
                result=result_str,
                sender=sender,
                receiver=receiver
            )
            blockchain_ms = (time.perf_counter() - blockchain_started) * 1000
            
        return jsonify({
            "status": "success",
            "prediction": prediction,
            "probability": prob,
            "threshold": threshold,
            "dl_probability": dl_prob,
            "rf_probability": rf_prob,
            "inference_ms": round(inference_ms, 3),
            "scoring_ms": round(scoring_ms, 3),
            "response_ms": round((time.perf_counter() - started) * 1000, 3),
            "blockchain_ms": round(blockchain_ms, 3),
            "blockchain_logged": bool(blockchain_receipt and blockchain_receipt.get("mode") == "ganache"),
            "ledger_mode": blockchain_receipt.get("mode", "unknown") if blockchain_receipt else None,
            "receipt": blockchain_receipt
        })
        
    except Exception as e:
        return jsonify({
            "status": "error",
            "message": "Prediction could not be completed. Check the input and application logs."
        }), 400

@app.route("/api/samples", methods=["GET"])
def get_samples():
    """
    Get sample transactions saved in static directory.
    """
    samples_path = ROOT / "static" / "sample_transactions.json"
    if os.path.exists(samples_path):
        with open(samples_path, "r") as f:
            samples = json.load(f)
        return jsonify(samples)
    else:
        return jsonify([])

@app.route("/api/generate_simulated", methods=["GET"])
def generate_simulated():
    """
    Generates a perturbed synthetic transaction based on pre-extracted data.
    """
    global sample_transactions_cache
    if not sample_transactions_cache:
        # Reload cache if it was empty
        try:
            samples_path = ROOT / "static" / "sample_transactions.json"
            if os.path.exists(samples_path):
                with open(samples_path, "r") as f:
                    sample_transactions_cache = json.load(f)
        except:
            pass
            
    if not sample_transactions_cache:
        return jsonify({
            "status": "error",
            "message": "No transaction templates cached. Train deep learning model first."
        }), 400
        
    sample = random.choice(sample_transactions_cache)
    
    # Generate realistic transaction metadata
    senders = ["Alice Smith", "Bob Jones", "Charlie Brown", "David Green", "Eva White", "Frank Black", "Suresh Kumar", "Rahul Sharma"]
    receivers = ["Walmart Store", "Target Supermarket", "Amazon Online", "Steam Games", "Uber Taxi", "BestBuy Tech", "Netflix Inc", "Unknown Merchant"]
    
    # Perturb features to create a unique transaction
    perturbed_features = sample["features"].copy()
    
    # Amount perturbation (+/- 10%)
    amt = float(perturbed_features.get("Amount", 0))
    perturbed_features["Amount"] = round(max(1.0, amt * random.uniform(0.9, 1.1)), 2)
    
    # Time perturbation
    time_val = float(perturbed_features.get("Time", 0))
    perturbed_features["Time"] = int(time_val + random.randint(-120, 120))
    
    # Jitter PCA inputs slightly
    for i in range(1, 29):
        v_key = f"V{i}"
        if v_key in perturbed_features:
            perturbed_features[v_key] = float(perturbed_features[v_key]) + random.normalvariate(0, 0.05)
            
        return jsonify({
        "status": "success",
            "source": "simulated_sample_perturbation",
        "sender": random.choice(senders),
        "receiver": random.choice(receivers),
        "features": perturbed_features,
        "true_class": sample["class"]
    })

@app.route("/api/update_status", methods=["POST"])
def update_status():
    """
    Update the status of a logged fraud record on the blockchain.
    0 = Flagged, 1 = UnderReview, 2 = ResolvedSafe, 3 = ConfirmedFraud
    """
    try:
        data = request.get_json()
        index = int(data.get("index"))
        status_code = int(data.get("status"))
        
        receipt = update_on_blockchain(index, status_code)
        if receipt:
            return jsonify({
                "status": "success",
                "message": f"Transaction status updated ({'Ganache' if receipt.get('mode') == 'ganache' else 'local simulation'}).",
                "ledger_mode": receipt.get("mode", "unknown"),
                "receipt": receipt
            })
        else:
            return jsonify({
                "status": "error",
                "message": "Failed to write status update to the blockchain network"
            }), 400
    except Exception as e:
        return jsonify({
            "status": "error",
            "message": "Status update could not be completed. Check the application logs."
        }), 400

@app.route("/api/blockchain_logs", methods=["GET"])
def get_logs():
    """
    Fetch logged fraud records from the blockchain smart contract registry.
    """
    logs = get_blockchain_logs()
    return jsonify(logs)

@app.route("/api/network_status", methods=["GET"])
def get_status():
    """
    Get Ganache node details, contract address, and performance stats for both models.
    """
    status = get_network_status()
    
    # Load PyTorch Performance Stats
    dl_perf_stats = {}
    stats_path = PHASE3_RESULTS / "mlp_metrics.json"
    if os.path.exists(stats_path):
        try:
            with open(stats_path, "r") as f:
                loaded = json.load(f)
            dl_perf_stats = loaded.get("test_metrics", loaded)
        except:
            pass
            
    # Load Random Forest Performance Stats
    rf_perf_stats = {}
    rf_stats_path = PHASE3_RESULTS / "rf_metrics.json"
    if os.path.exists(rf_stats_path):
        try:
            with open(rf_stats_path, "r") as f:
                loaded = json.load(f)
            rf_perf_stats = loaded.get("test_metrics", loaded)
        except:
            pass
            
    status["model_performance"] = dl_perf_stats
    status["rf_performance"] = rf_perf_stats
    return jsonify(status)

if __name__ == "__main__":
    print("Starting Flask Fraud Detection Server on http://127.0.0.1:5000")
    app.run(host=os.environ.get("FLASK_HOST", "127.0.0.1"), port=int(os.environ.get("FLASK_PORT", "5000")), debug=False, use_reloader=False)
