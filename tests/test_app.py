import unittest
from unittest.mock import patch

import numpy as np
import torch

import app as application


class IdentityScaler:
    def transform(self, values):
        return np.asarray(values)


class FixedModel:
    def __init__(self, logit):
        self.logit = logit

    def __call__(self, _values):
        return torch.tensor([[self.logit]], dtype=torch.float32)


class PredictionApiTests(unittest.TestCase):
    def setUp(self):
        self.client = application.app.test_client()
        self.originals = (
            application.model,
            application.scaler,
            application.features,
            application.dl_threshold,
        )
        application.model = FixedModel(-4.0)
        application.scaler = IdentityScaler()
        application.features = ["Time", "Amount"]
        application.dl_threshold = 0.5

    def tearDown(self):
        (application.model, application.scaler, application.features,
         application.dl_threshold) = self.originals

    def test_rejects_missing_features(self):
        response = self.client.post("/predict", json={"features": {"Amount": 10}})
        self.assertEqual(response.status_code, 400)
        self.assertEqual(response.get_json()["status"], "error")

    def test_rejects_non_finite_values(self):
        response = self.client.post("/predict", json={"features": {"Time": 0, "Amount": float("nan")}})
        self.assertEqual(response.status_code, 400)

    def test_reports_scoring_timing_and_safe_verdict(self):
        response = self.client.post("/predict", json={"features": {"Time": 1, "Amount": 10}, "model_type": "dl"})
        payload = response.get_json()
        self.assertEqual(response.status_code, 200)
        self.assertEqual(payload["prediction"], "Safe")
        self.assertGreaterEqual(payload["inference_ms"], 0)
        self.assertGreaterEqual(payload["scoring_ms"], payload["inference_ms"])

    def test_simulated_receipt_is_not_reported_as_on_chain(self):
        application.model = FixedModel(4.0)
        with patch.object(application, "store_on_blockchain", return_value={"mode": "simulation", "tx_hash": None}):
            response = self.client.post("/predict", json={"features": {"Time": 1, "Amount": 10}, "model_type": "dl"})
        self.assertEqual(response.status_code, 200)
        self.assertFalse(response.get_json()["blockchain_logged"])
        self.assertEqual(response.get_json()["ledger_mode"], "simulation")


if __name__ == "__main__":
    unittest.main()
