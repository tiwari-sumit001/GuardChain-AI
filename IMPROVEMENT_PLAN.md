# Phase 2: Improvement Plan

**Project:** GuardChain AI / Online Fraud Detection System  
**Prepared:** 2026-10-23  
**Basis:** Findings in `ANALYSIS.md` and the supplied progress report.

## Goal and assumptions

Prioritize a stable, honest tech-fest demonstration first, then produce defensible evaluation results and paper material. The current project is a local Flask prototype using the Kaggle credit-card dataset and Ganache; no production payment feed, target deployment hardware specification, or demo/submission dates were provided.

**Initial performance target:** p95 model inference plus Flask response under **500 ms** on the demo laptop, measured over a documented run. Blockchain confirmation is measured separately because it depends on Ganache and must not be hidden inside an unmeasured “real-time” claim. If this target is missed, report the measured value and identify the bottleneck rather than claiming success.

## Prioritized work

| Priority | Work | Deliverable / acceptance evidence |
|---|---|---|
| **High** | Make evaluation leakage-free and reproducible: split first; fit preprocessing on train only; preserve a validation partition for threshold/model selection; reserve test for final reporting; seed and save config/split/model metadata. | Re-run MLP and RF on identical partitions. Save confusion matrices, precision, recall, F1, PR-AUC, and ROC-AUC where meaningful. Clearly label old stored metrics as historical. No metric is claimed until an actual run produces it. |
| **High** | Address the alert trade-off: compare the MLP and RF on the same held-out cases, select any operating threshold from validation data, and show false alarms alongside recall. | Comparison table including positive support and precision/recall/F1; threshold rationale and explicit discussion of review workload. Do not claim the hybrid improves results unless measured. |
| **High** | Make demo modes and ledger provenance explicit. Label the existing feed as simulated; label each ledger result as confirmed Ganache or local simulation. Prevent synthetic fallback hashes from appearing as on-chain receipts; make fallback persistence and restart behavior clear. | UI/API visibly differentiates live-node confirmation from local fallback; demo remains usable with Ganache offline without representing simulated logs as chain data. |
| **High** | Harden API inputs and dashboard rendering. Validate JSON shape, required numeric features, finite values, amount and status ranges; use safe DOM text rendering for user-controlled strings; return useful client errors without exposing stack/internal details. | Invalid requests fail cleanly; sender/receiver text is rendered as text; existing valid analyzer/simulator flow remains usable. |
| **Medium** | Establish measured serving performance. Add inference and response timing, request counts, and a repeatable benchmark with warmup and documented hardware/software; separately time blockchain submission/receipt. | Report p50/p95/max inference and response latency, throughput, and memory for an actual run. Target p95 under 500 ms for model + Flask response; blockchain write reported separately. |
| **Medium** | Improve operational reliability and setup: move paths, thresholds, hybrid weights, Ganache URL and port to configuration; add structured logging and startup artifact checks; make model-unavailable state explicit; provide pinned dependencies, `.env.example`, and one-command Windows launch. | Fresh setup instructions and clear startup/network/model status; no silent default probability when a model is unavailable. |
| **Medium** | Improve offline demo resilience. Keep bundled sample transactions and clearly named simulated mode; handle fetch failures and overlapping simulator requests; show useful UI error/recovery states. | Demo can proceed without Internet or Ganache, with external CDN dependencies either removed or documented as a limitation. |
| **Low** | Paper and demo polish after the pipeline is stable: architecture diagram, results charts from actual runs, limitations, verified references, judge Q&A, and a short scripted demo. | Paper draft and `DEMO_GUIDE.md` use only verified sources and observed results; no invented metrics or chain claims. |

## Model and data protocol

1. Verify dataset schema, class counts, and source/version; record a checksum and data license/source in experiment metadata.
2. Create deterministic train/validation/test partitions with stratification. Fit each scaler on train only and reuse it for validation, test, and inference.
3. Train the existing RF and MLP as baselines. Select threshold and any hybrid weights using validation only. Do not tune on the test set.
4. Evaluate once on the held-out test set with confusion matrix, precision, recall, F1, PR-AUC, and ROC-AUC. Include class support and the selected operating threshold.
5. Run ablations only after the baseline pipeline is reproducible (for example class weighting, threshold choice, and hybrid blend). Store configs and outputs; report results only from actual executions.

## Real-time/demo architecture direction

For the near-term demo, retain the current browser simulator and analyzer as **offline sample mode**, explicitly labelled. Improve the request path to validate features, run inference, return probability/verdict and timing, and enqueue fraud audit writes so a slow blockchain receipt does not stall scoring. Show audit-write status independently, including pending, confirmed, failed, or local simulation. Keep this architecture local and demonstrable; a true external transaction connector requires a real provider/API and credentials, which are not part of the current project.

## Change sequence and safeguards

1. Preserve the current state with a Git branch or a non-destructive snapshot before edits; inspect current changes first so they are not overwritten.
2. Implement evaluation/data split corrections and save new artifacts separately from the existing models.
3. Improve API validation, safe rendering, and explicit chain/fallback provenance.
4. Add measured latency reporting and offline demo handling.
5. Update README, evaluation outputs, paper draft, and demo guide from verified results.

The existing working tree already contains modifications. Before implementation, inspect the diff and avoid resetting or replacing user changes. Large scope choices needing confirmation: adding a background queue/dependency for blockchain writes, changing contract storage behavior, or connecting an external live transaction source. The suggested initial implementation keeps the current local Ganache contract and sample simulator, and adds a lightweight in-process queue only if it can be done safely without new infrastructure; otherwise keep scoring synchronous but report separate timings and surface blockchain delay honestly.

## Out of scope for the first demo pass

- Public-chain deployment or real cardholder/financial data.
- A claim of production compliance, privacy, or consortium decentralization.
- Retraining on real bank data or automatic online learning.
- Hardware-specific optimization before the demo laptop is identified and benchmarked.

## Phase 2 status

Plan prepared. No application code, model artifacts, metrics, contracts, or existing report files were changed for this phase. The next phase is implementation; work should begin after review of the plan and confirmation of any scope choices above.
