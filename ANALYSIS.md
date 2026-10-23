# Phase 1: Project Analysis

**Project:** GuardChain AI / Online Fraud Detection System  
**Review date:** 2026-10-23  
**Scope:** Read-only inspection of the source tree, saved artifacts and supplied progress report. No application code or existing project artifacts were changed for this phase.

## 1. Project summary

This is a local Flask demonstration for credit-card fraud scoring. It accepts a 30-value transaction feature vector (`Time`, `Amount`, `V1`-`V28`), scores it with a PyTorch MLP, Random Forest, or fixed weighted blend, and attempts to record fraud decisions in a Solidity registry on a local Ganache Ethereum node. The browser dashboard also generates a simulated transaction stream by perturbing stored dataset examples.

The real-world problem in the report is rare credit-card fraud and the need for an auditable record of flagged cases. The supplied progress report's title is **Online Fraud Detection System**; it refers to the built application as **GuardChain AI**. Its central objectives are imbalanced-class detection, model-triggered ledger writes, and a dashboard for analysis and monitoring. The implementation supports an interactive prototype and simulated stream; it does not currently establish a production payment feed, production-grade decentralized governance, or measured end-to-end real-time performance.

## 2. Report claims and implementation evidence

| Report claim | What the inspected code/artifacts show | Assessment |
|---|---|---|
| Weighted PyTorch MLP with 30 inputs, BatchNorm, ReLU and Dropout | `dl_model.py` defines a 30-input, three-hidden-layer MLP. `train_dl_model.py` uses `BCEWithLogitsLoss(pos_weight=...)`, Adam and eight epochs. | Implemented, with preprocessing and evaluation caveats below. |
| Random Forest baseline and 60/40 hybrid score | `train_model.py` trains a 50-tree class-weighted Random Forest. `app.py` blends its probability with the MLP at fixed 0.4/0.6 weights. | Implemented; the blend weights and 0.5 threshold are hardcoded and not calibrated in the reviewed code. |
| Stratified held-out performance: 95.77% accuracy and 94.90% fraud recall (93 TP, 5 FN) | `static/performance_stats.json` contains these values and confusion matrix `[[54462, 2402], [5, 93]]`. | Stored metrics agree arithmetically with the report, but should be treated as historical run output: no run metadata, split manifest, model hash, or independent re-evaluation accompanies them. The low precision (3.73%) and F1 (7.17%) also matter: the listed threshold produces many false alarms. |
| Random Forest comparison | `static/rf_performance_stats.json` reports accuracy 99.95%, precision 96.0%, recall 73.47%, and F1 83.24%, with matrix `[[56861, 3], [26, 72]]`. | Stored output is available, but RF and MLP training both fit preprocessing before splitting, so these results are not a clean leakage-free benchmark. |
| Validation split and early stopping | Neither training script creates a validation set or implements early stopping. The MLP script uses only train/test and a fixed eight epochs. | Report claim is not implemented. |
| StandardScaler fit on training partition only | Both scripts fit `StandardScaler` on all rows before `train_test_split`. | Data leakage: test-set distribution affects preprocessing. Refit scaler on training data only before making research claims. |
| Every fraud decision is immutably written to Ethereum and returns a real receipt | `app.py` calls `store_on_blockchain` for fraud. `blockchain.py` writes to Ganache when connected, otherwise returns a synthetic hash/block/gas receipt and stores the record in process memory. | Automatic logging is implemented, but a successful API response does not prove an on-chain write. The UI/API must distinguish chain receipts from simulated receipts. The fallback is volatile and disappears on process restart. |
| Contract access is restricted to authorized nodes | `FraudRegistry.sol` gates writes and status updates with `onlyAuthorized`, with owner-managed allowlisting. | Implemented in the contract source. Runtime deployment and authorization behavior were not exercised in this read-only review. |
| Live / real-time transaction feed | `static/script.js` polls `api/generate_simulated` on an interval, then calls `/predict`. `app.py` chooses a saved example and perturbs amount, time and PCA values. | A live-looking simulator exists; it is not a live bank, terminal, sensor, or event-bus stream. No measured latency, throughput, or FPS evidence was found. |
| Integration tests validate the running system | `test_integration.py` is a standalone script that calls a server at `127.0.0.1:5000`; it uses printed PASS/FAIL messages rather than a test framework and requires the server and optional Ganache environment. | Test procedure exists, but was not run in this phase. Its script is an integration smoke test, not proof of the report's claimed results. |

The supplied PDF describes an academic prototype, not operational evidence from a live payment processor. It states a held-out MLP result and discusses automatic logging, a local fallback, and a simulated stream. The code confirms those broad flows with the qualification that fallback receipts are not blockchain receipts and the stream is generated locally.

## 3. Architecture and file inventory

| File or directory | Role observed |
|---|---|
| `app.py` | Flask server, model/artifact loading, `/predict`, sample/simulation endpoints, status updates, ledger and network-status endpoints. Models are loaded at import time using paths relative to the process working directory. |
| `dl_model.py` | PyTorch `FraudDetectionMLP` definition. |
| `train_dl_model.py` | Loads the complete CSV, scales, stratifies, trains/evaluates the MLP, exports weights/scaler/features/metrics, and extracts balanced test examples for the UI. |
| `train_model.py` | Loads the CSV, scales Amount, trains/evaluates the Random Forest, and exports model/scaler/features/metrics. |
| `model.pkl`, `scaler.pkl`, `features.pkl` | Persisted Random Forest and its preprocessing/feature metadata. Pickle files must only be loaded from trusted sources. |
| `dl_model.pth`, `scaler_dl.pkl`, `features_dl.pkl` | Persisted PyTorch weights and preprocessing/feature metadata. |
| `creditcard.csv` | Local dataset, approximately 151 MB on disk. Training scripts load it as a full pandas DataFrame. |
| `blockchain.py` | Web3/Ganache connection, contract deployment/lookup, transaction writes, status updates, log retrieval and in-memory fallback. It performs a connection/deployment check at import. |
| `contracts/FraudRegistry.sol` | Solidity registry with record/status events, owner and authorized-node controls. |
| `compile_sol.py` | Installs/uses solc 0.8.19, compiles the contract and writes ABI/bytecode/address to `static/contract_details.json`. |
| `static/contract_details.json` | Generated contract interface, bytecode and deployment address. |
| `templates/index.html` | Single-page dashboard shell and UI sections/forms. |
| `static/script.js` | Browser navigation, API requests, charts, analyzer, ledger view and interval-driven simulation. Uses dynamic `innerHTML` in multiple render paths. |
| `static/style.css` | Dashboard styles. |
| `static/sample_transactions.json` | Cached balanced examples derived by the MLP training script; served to the UI and simulator. |
| `static/performance_stats.json`, `static/rf_performance_stats.json` | Persisted model metrics and confusion matrices displayed by the app. |
| `test_integration.py` | External-server integration smoke script for sample, prediction, status, and ledger endpoints. |
| `generate_report.py` | ReportLab script for generating the project synopsis PDF. |
| `Synopsis_Report.pdf`, `Synopsis_Report 1.pdf`, `Synopsis_Report 2.pdf` | Existing project report/synopsis variants. The supplied progress report was separately provided from Downloads. |
| `templates/static/app.py` | Empty file; appears to be an unused/accidental duplicate. |
| `text` | Small text file containing an old project-folder sketch with a note that the model was dummy; inconsistent with the current model artifacts. |
| `.gitignore` | Essentially empty; generated models, data, caches and local artifacts are not excluded. |

No `requirements.txt`, `pyproject.toml`, `.env.example`, README, explicit app configuration, or run script was present in the inspected tree. No screenshots or experiment configuration/manifest were present. The project directory contains substantial existing Git changes, including edits to `app.py`, `blockchain.py`, `train_model.py`, dashboard files, and generated artifacts. These were preserved and not treated as changes made during this review.

## 4. Bugs, security and reliability concerns

### Correctness and evaluation

- **Preprocessing leakage:** each scaler is fitted on the full dataset before the split. This leaks test distribution information into training and can bias reported performance.
- **No validation or early stopping:** the MLP has a fixed eight-epoch run and no threshold selection. The report's validation/early-stopping description does not match the script.
- **Metric imbalance:** the saved MLP threshold produces 2,402 false positives for 93 true positives. Recall alone hides the resulting 3.73% precision and 7.17% F1; operational workload and alert costs are not evaluated.
- **No reproducible experiment record:** fixed random seeds exist in the training scripts, but there is no saved dependency lock/version manifest, run configuration, data checksum, split indices, model version, or threshold provenance.
- **Synthetic label ambiguity:** the simulator returns the original sample class as `true_class` after feature perturbation; the UI's prediction is based on perturbed features. That label is not necessarily the perturbed example's correct ground truth and must not be used as a validated label without care.
- **Stored metrics can go stale:** the app serves JSON metrics independently of the currently loaded model artifacts. No model/metrics version linkage is checked.

### Security and privacy

- **Unsafe pickle trust boundary:** `pickle.load` can execute code from a tampered model artifact. Artifacts are local today, but their provenance needs protection.
- **Potential stored/reflected HTML injection:** dashboard code uses `innerHTML` to render transaction values, while sender/receiver values are accepted from `/predict`. Untrusted strings should be escaped or inserted with safe DOM text APIs.
- **No authentication or authorization at the Flask API layer:** prediction logging and case-status update endpoints can be called by any client able to reach the server. The Solidity authorization does not protect local fallback state or the Flask surface.
- **No CSRF protection / request limits:** state-changing endpoints have no CSRF token, authentication, rate limiting, or payload-size/schema validation visible in the app.
- **Sensitive data exposure:** sender and receiver names and transaction amount are written as plaintext strings/values to the ledger, which is immutable and broadly readable to contract callers. Real identities or financial transaction details should not be placed on-chain.
- **Unpinned external assets:** UI references external CDN assets; the demo may lose icons or chart dependencies without internet unless assets are bundled.

### Reliability and maintainability

- **Blocking request path:** on flagged predictions, Web3 transaction submission waits synchronously for a receipt. Network/node delays can hold up the Flask response; no timeout, queue, retry policy, or latency instrumentation is evident.
- **Volatile fallback and misleading receipt shape:** `simulated_logs` lives only in process memory and synthetic receipts resemble real chain receipts. A restart loses fallback records; consumers cannot identify receipt provenance from the returned fields.
- **Contract connection/deployment at import:** importing `blockchain.py` can connect and deploy, coupling app startup to network state and file writes. `check_and_deploy_contract` can block during startup or request handling.
- **Unbounded / repeated ledger reads:** `get_blockchain_logs` loops over all records and performs one RPC call per record, so latency grows with chain history.
- **Non-atomic simulator interval:** frontend `setInterval` can start another simulation step while an earlier network request is still pending if processing exceeds the selected interval.
- **Broad exception handling:** several paths catch all exceptions and return raw exception text to clients or silently continue, making errors hard to diagnose and potentially exposing internal details.
- **Relative paths and missing artifact validation:** app startup assumes a particular current working directory. Model load failures are logged but the server can still start with unavailable models; a prediction may then silently use a default zero probability for a missing model.
- **Hardcoded configuration:** local Ganache URL/port, Flask port, model dimensions, thresholds, blend weights, simulator choices/jitter, and file paths are embedded in source.
- **Model architecture input assumptions:** endpoint conversion defaults absent features to zero and does not enforce a complete finite numeric schema; malformed/non-finite values or wrong feature artifacts can fail or yield unintended predictions.
- **Amount truncation on chain:** records cast transaction amount to an integer, discarding fractional currency units; currency and units are not recorded.
- **Index/status consistency:** when operating in fallback mode, logs are process-local while indices may be confused with real on-chain indices if connectivity changes. Runtime switching needs separate storage/provenance semantics.
- **Debugging/audit logs:** application uses `print` and console messages rather than structured logging with request IDs, redaction, severity, and rotation.

## 5. What is and is not real-time today

**Present:** browser-driven repeated simulated requests; Flask inference over one feature vector per request; automatic fraud logging; periodic node-status polling; live dashboard counters/charts for the current simulation session.

**Absent or unverified:** external transaction ingestion, streaming transport, queue/backpressure, measured p50/p95 end-to-end latency, throughput, FPS, resource utilization, deployment under concurrent traffic, durable offline queueing, and recovery after process/node restart. The browser simulator is an interaction/demo loop and should be labelled as simulated traffic. On-chain writes are synchronous and may dominate response time; no timing measurement is stored.

## 6. Performance evidence and limits

- Dataset file: approximately **150.8 MB**; scripts read it fully into pandas memory. The CSV's in-memory footprint was not measured.
- Random Forest artifact: approximately **1.74 MB**. MLP weights: approximately **28 KB**. These are disk sizes, not RAM or serving-memory measurements.
- Saved MLP test confusion matrix: **54,462 TN, 2,402 FP, 5 FN, 93 TP**. Derived metrics in the persisted JSON are accuracy **95.77%**, precision **3.73%**, recall **94.90%**, F1 **7.17%**.
- Saved RF metrics: accuracy **99.95%**, precision **96.00%**, recall **73.47%**, F1 **83.24%**.
- No measured inference latency, end-to-end latency, transaction throughput, CPU/RAM usage, GPU usage, model load time, or chain-write latency was found. These must be measured before proposing a real-time target or reporting comparative system performance.
- The two saved model metric files appear to come from a split of 56,962 rows and contain 98 fraud examples, but no split artifact proves that both models used identical data indices; the training scripts use the same stratified split seed but independently load and preprocess the data.

## 7. Main discrepancies to resolve in the project report

1. Correct the scaler methodology: fit only on training data; distinguish current historical metrics from the corrected rerun.
2. Remove or qualify validation/early-stopping claims unless implemented and run.
3. Report precision, recall, F1, confusion matrix, and class support together; discuss the MLP's high false-positive count.
4. Describe the current source as a simulated transaction feed, not a connected real-time payment stream.
5. Distinguish Ganache on-chain receipts from in-memory fallback records and synthetic receipts.
6. Verify contract deployment/logging claims from an actual run; do not infer successful chain operation from fallback responses.
7. Reconcile the progress report and synopsis variants where methodology, names, reported metrics, or implementation scope differ before preparing a research paper.
8. Avoid claims of a production-ready, banking-deployable, privacy-preserving, or multi-party decentralized system based only on the local prototype.

## 8. Phase 2 outline (not started)

The next phase should turn the findings into a prioritized, reviewable plan. Initial priorities are: (High) leakage-free reproducible evaluation and calibrated alert trade-offs; (High) explicit simulated/live mode and safe API validation; (High) reliable, non-misleading blockchain/fallback status; (Medium) latency measurement and a defined real-time target; (Medium) configuration, logging, dependency/run documentation and offline demo assets; (Low) paper packaging and expanded visual polish after the demo pipeline is stable.

No Phase 2 plan or implementation changes have been made in this phase. Phase 2 should create `IMPROVEMENT_PLAN.md` and present it for review before any large or risky implementation work, as requested.
