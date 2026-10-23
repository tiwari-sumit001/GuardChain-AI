import requests
import json
import time

base_url = "http://127.0.0.1:5000"

print("Waiting 2 seconds for Flask server to start...")
time.sleep(2)

print("Starting integration test against Flask server...")

# Initialize samples variable
samples = []
test_sample = None

# 1. Test GET /api/samples
try:
    print("Testing GET /api/samples...")
    res = requests.get(f"{base_url}/api/samples")
    assert res.status_code == 200, f"Expected 200, got {res.status_code}"
    samples = res.json()
    print(f"[PASS] Successfully fetched {len(samples)} sample transactions.")
    test_sample = samples[0] if samples else None
except Exception as e:
    print(f"[FAIL] Sample transactions test failed: {e}")
    test_sample = None

# 2. Test GET /api/network_status
try:
    print("Testing GET /api/network_status...")
    res = requests.get(f"{base_url}/api/network_status")
    assert res.status_code == 200, f"Expected 200, got {res.status_code}"
    status = res.json()
    print(f"[PASS] Network status: {status['status']}, Provider: {status['provider']}")
    if "rf_performance" in status and "accuracy" in status["rf_performance"]:
        print(f"[PASS] Loaded comparative Random Forest metrics. Accuracy: {status['rf_performance']['accuracy']:.4f}")
    else:
        print("[PASS] Revised Random Forest metrics are pending a completed training/evaluation run.")
except Exception as e:
    print(f"[FAIL] Network status test failed: {e}")

# 3. Test GET /api/generate_simulated
try:
    print("Testing GET /api/generate_simulated...")
    res = requests.get(f"{base_url}/api/generate_simulated")
    assert res.status_code == 200, f"Expected 200, got {res.status_code}"
    sim_tx = res.json()
    print(f"[PASS] Generated perturbed transaction. Amount: ${sim_tx['features']['Amount']:.2f}, True Class: {sim_tx['true_class']}")
except Exception as e:
    print(f"[FAIL] Generate simulated transaction test failed: {e}")

# 4. Test POST /predict with multiple model types
if test_sample:
    for model_type in ["dl", "rf", "hybrid"]:
        try:
            print(f"Testing POST /predict with model_type='{model_type}'...")
            payload = {
                "sender": f"Integration Test ({model_type})",
                "receiver": "Verification Node",
                "features": test_sample["features"],
                "model_type": model_type
            }
            res = requests.post(f"{base_url}/predict", json=payload)
            assert res.status_code == 200, f"Expected 200, got {res.status_code}"
            pred_data = res.json()
            print(f"[PASS] Prediction successful for {model_type.upper()}: Class={pred_data['prediction']}, Prob={pred_data['probability']:.6f}")
            print(f"       DL Prob={pred_data['dl_probability']:.6f}, RF Prob={pred_data['rf_probability']:.6f}")
            print(f"       Blockchain Logged: {pred_data['blockchain_logged']}")
        except Exception as e:
            print(f"[FAIL] Predict endpoint failed for {model_type}: {e}")
else:
    print("[SKIP] Skipping predict test as no samples were loaded.")

# 5. Test POST /api/update_status (Dispute Resolution)
try:
    print("Testing POST /api/update_status...")
    # First get current logs
    res_logs = requests.get(f"{base_url}/api/blockchain_logs")
    logs = res_logs.json()
    
    if logs:
        # Update the status of the first log to 2 (Resolved - False Positive)
        target_index = logs[0]["index"]
        print(f"Attempting to update status of record #{target_index} to 2 (Resolved)...")
        payload = {
            "index": target_index,
            "status": 2
        }
        res_update = requests.post(f"{base_url}/api/update_status", json=payload)
        assert res_update.status_code == 200, f"Expected 200, got {res_update.status_code}"
        update_data = res_update.json()
        print(f"[PASS] Dispute resolution request completed in {update_data.get('ledger_mode', 'unknown')} mode.")
        
        # Verify status in logs
        res_logs_after = requests.get(f"{base_url}/api/blockchain_logs")
        logs_after = res_logs_after.json()
        updated_log = next((l for l in logs_after if l["index"] == target_index), None)
        assert updated_log is not None and updated_log["status"] == 2, f"Expected status 2, got {updated_log['status'] if updated_log else 'None'}"
        print(f"[PASS] Successfully verified smart contract status change to: {updated_log['status']}")
    else:
        # Create a simulated fraud transaction to record it and then update it
        print("[INFO] Blockchain logs empty. Creating fraud transaction for dispute test...")
        # Search for a fraud sample
        fraud_sample = next((s for s in samples if s["class"] == 1), None)
        if fraud_sample:
            payload = {
                "sender": "Dispute Test Owner",
                "receiver": "Fraud Portal",
                "features": fraud_sample["features"],
                "model_type": "dl"
            }
            res_pred = requests.post(f"{base_url}/predict", json=payload)
            # Re-read logs
            logs_res = requests.get(f"{base_url}/api/blockchain_logs").json()
            if logs_res:
                target_index = logs_res[0]["index"]
                payload_update = {"index": target_index, "status": 2}
                res_update = requests.post(f"{base_url}/api/update_status", json=payload_update)
                assert res_update.status_code == 200, f"Expected 200, got {res_update.status_code}"
                update_data = res_update.json()
                logs_after = requests.get(f"{base_url}/api/blockchain_logs").json()
                updated_log = next((l for l in logs_after if l["index"] == target_index), None)
                assert updated_log is not None and updated_log["status"] == 2
                print(f"[PASS] Successfully logged fraud and resolved it in {update_data.get('ledger_mode', 'unknown')} mode. New Status: {updated_log['status']}")
            else:
                print("[SKIP] Could not retrieve blockchain logs even after triggering prediction.")
        else:
            print("[SKIP] Skipping dispute test as no fraud samples are available.")
except Exception as e:
    print(f"[FAIL] Dispute resolution test failed: {e}")

# 6. Test GET /api/blockchain_logs
try:
    print("Testing GET /api/blockchain_logs...")
    res = requests.get(f"{base_url}/api/blockchain_logs")
    assert res.status_code == 200, f"Expected 200, got {res.status_code}"
    logs = res.json()
    print(f"[PASS] Successfully fetched {len(logs)} blockchain logs.")
except Exception as e:
    print(f"[FAIL] Blockchain logs test failed: {e}")

print("Verification complete.")
