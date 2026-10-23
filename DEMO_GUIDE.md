# GuardChain AI Demo Kit

## Two-minute pitch

**0:00-0:25 — Problem**  
Card fraud is rare relative to legitimate transactions. That makes accuracy alone a poor guide: a model can appear accurate while missing fraud or producing too many alerts. Investigators also need a traceable record of why a case was flagged.

**0:25-0:55 — What we built**  
GuardChain AI is a local prototype that scores a 30-feature transaction with a PyTorch MLP or Random Forest. A fraud verdict can trigger a write to a local Ganache smart contract. The dashboard shows the prediction, confidence score, timing, and whether the audit record was confirmed on Ganache or stored in the local simulation fallback.

**0:55-1:25 — Demonstration**  
I will first analyze a supplied dataset example, then run the sample simulator. These are historical samples and perturbed examples, not a live payment feed. When Ganache is online, the ledger view shows the transaction record; when it is offline, the UI labels the temporary in-memory record and does not claim it is on-chain.

**1:25-1:50 — Evaluation**  
We report precision, recall, F1, PR-AUC, ROC-AUC, and the confusion matrix on a held-out test set. The revised evaluation fits scalers only on the training partition and chooses the decision threshold using validation data. Results are shown only after the scripts have run on the stated machine.

**1:50-2:00 — Scope**  
This is a research and teaching prototype. A production deployment would need real transaction integration, authentication, privacy review, durable operations, and validation on appropriately governed bank data.

## Five-minute demo flow

1. **0:00-0:30 — Status:** Open Dashboard Overview; point out model status and whether Ganache or local simulation is active.
2. **0:30-1:30 — Analyzer:** Load a bundled sample, choose MLP or RF, run the analysis, and explain probability versus the configured threshold. If flagged, distinguish a confirmed Ganache receipt from a local simulation record.
3. **1:30-2:30 — Simulator:** Start Sample Traffic Simulator; explain that it perturbs stored dataset examples. Point to inference timing and the confirmed-write counter. Stop the simulator.
4. **2:30-3:30 — Audit records:** Refresh Fraud Audit Records. Show the ledger source label and one status update if the Ganache contract is available.
5. **3:30-4:30 — Model metrics:** Show the completed revised comparison (56,962 held-out rows, 98 fraud). MLP: precision 72.17%, recall 84.69%, F1 77.93%, PR-AUC 0.6745. RF: precision 94.19%, recall 82.65%, F1 88.04%, PR-AUC 0.8609. Explain that MLP catches two more frauds in this split but raises more false alarms.
6. **4:30-5:00 — Close:** State the prototype's boundaries and the next evaluation step: compare models on the same fixed held-out transactions and benchmark scoring separately from chain confirmation.

## Step-by-step setup and demo

1. Use the demo laptop and keep the application bound to `127.0.0.1`.
2. Confirm `creditcard.csv`, the saved model artifacts, and `static/sample_transactions.json` are present. For a fresh environment, follow README setup and install `requirements.txt`.
3. Optional: start Ganache and confirm its JSON-RPC URL matches `.env` (`GANACHE_URL`). The contract ABI/bytecode file must exist at `static/contract_details.json` for deployment.
4. Start the server with `run.bat`; open the local URL printed in the terminal.
5. Verify the dashboard reports the correct ledger mode. A local Ganache contract was deployed and the integration script verified a fraud write and status update. Run one safe sample and one fraud sample from the analyzer; never enter real customer data.
6. Start the simulator and show the timing/status labels. Stop it before switching views.
7. If Ganache is unavailable, continue in local simulation mode and say clearly that fallback records are temporary and not blockchain transactions.

## Ten likely judge questions

1. **Is this connected to a live payment gateway?**  No. The current input is a user-submitted feature vector or a perturbed historical sample. A real gateway connector is future work.
2. **What does “real time” mean in this demo?**  The local API scores one request at a time. We measure model and Flask scoring latency; any service-level claim must cite the actual measured run and machine.
3. **Why use precision and recall instead of accuracy alone?**  Fraud is rare. Precision shows the proportion of alerts that are fraud, while recall shows the proportion of fraud cases detected. Both affect operational cost.
4. **How did you prevent data leakage?**  In the revised experiment scripts, rows are split first, preprocessing is fitted only on training rows, the threshold is selected on validation rows, and final metrics use held-out test rows.
5. **Why use class-weighted loss?**  It increases the training penalty for minority-class errors. It does not guarantee calibrated probabilities or a good threshold; those are evaluated separately.
6. **Why include a Random Forest?**  It is a tabular baseline for comparison. The hybrid score is a fixed engineering option and is not claimed to outperform either model without measured evidence.
7. **What happens when Ganache is down?**  The app can add a temporary process-local simulation record. It has no on-chain hash and is lost when the server restarts.
8. **Does blockchain make the system fully secure?**  No. A local chain only demonstrates a contract workflow. It does not secure the Flask API, protect privacy, or provide multi-party governance.
9. **What data is recorded on-chain?**  The current contract records amount, a verdict string, sender/receiver labels, timestamp, and status. Real personally identifying or sensitive payment data should not be written to an immutable ledger.
10. **What is the main limitation?**  The dataset is historical and anonymized, and the demo is not an end-to-end deployment at a bank. External validation, operational cost analysis, access control, privacy design, and drift evaluation remain necessary.

## Backup plan

- **Ganache unavailable:** continue using the local simulation mode; explicitly identify entries as temporary local records.
- **Internet unavailable:** use the bundled dataset samples. The app's core inference does not require a remote data API; if externally hosted chart/icon assets fail, focus on analyzer and API output.
- **Server/model startup fails:** restart with `run.bat` from the project directory. Check that model artifacts are present and dependencies were installed in `.venv`. If the model is unavailable, do not claim a prediction; switch to the prepared architecture and evaluation explanation.
- **Dashboard becomes unresponsive:** stop the simulator, refresh once, and use the Analyzer with a single bundled sample.
- **Evaluation artifacts unavailable on the demo machine:** show the protocol and explain the revised results are available in the project's `results/phase3/` folder. Do not substitute historical `static/` metrics.
- **Demo laptop/network failure:** use the saved poster content and explain the request flow from the architecture diagram. Do not present an unrun screenshot or fabricated result as evidence.

## One-page poster content

### GuardChain AI: Fraud Scoring with Explicit Audit Provenance

**Problem**  
Rare fraud makes aggregate accuracy misleading, while a fraud alert needs a traceable review record.

**Prototype**  
A Flask dashboard accepts transaction features and scores them using an MLP or Random Forest. Fraud verdicts can be written to a local Ganache contract. When Ganache is offline, the app labels the record as a temporary local simulation.

**Evaluation protocol**  
Stratified 65/15/20 train/validation/test split; training-only scaling; validation-only threshold selection; held-out precision, recall, F1, PR-AUC, ROC-AUC, and confusion matrix. Latency is measured separately from chain confirmation.

**Results**  
Held-out support: 56,962 (98 fraud). MLP: 72.17% precision, 84.69% recall, 77.93% F1, PR-AUC 0.6745. RF: 94.19% precision, 82.65% recall, 88.04% F1, PR-AUC 0.8609. Local Flask scoring p95 with audit writes stubbed: 3.01 ms MLP / 49.19 ms RF. Show the confusion-matrix and latency plots from `results/phase3/`; chain confirmation time was not measured.

**Impact and limits**  
Demonstrates a local classifier-to-audit workflow and makes fallback provenance visible. It does not connect to a live bank feed, establish production security, or prove privacy-preserving decentralized governance.

**Next steps**  
Run the reproducible experiments; measure scoring and chain latency on the demo laptop; test on representative, governed data; design authentication, retention, privacy, and operational monitoring before any deployment study.
