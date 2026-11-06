"""Offline, fail-closed contract tests for published congressional disclosures.

No network requests, API keys, scheduled jobs or live trading.
"""
import copy
import json
import unittest
from datetime import datetime, timezone
from pathlib import Path

from congress_disclosures import validate


ROOT = Path(__file__).resolve().parent


class CongressDisclosureContractTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.payload = json.loads((ROOT / "data" / "congress-trades.json").read_text(encoding="utf-8"))

    def sample(self):
        payload = copy.deepcopy(self.payload)
        if not payload["trades"]:
            self.skipTest("No published records available for negative-case testing")
        return payload

    def test_published_file_respects_contract(self):
        self.assertEqual(validate(self.payload), len(self.payload["trades"]))

    def test_unavailable_status_cannot_expose_trades(self):
        payload = self.sample()
        payload["status"] = "unavailable"
        with self.assertRaises(ValueError):
            validate(payload)

    def test_missing_official_source_is_rejected(self):
        payload = self.sample()
        payload["trades"][0]["sourceUrl"] = ""
        with self.assertRaises(ValueError):
            validate(payload)

    def test_untrusted_source_host_is_rejected(self):
        payload = self.sample()
        payload["trades"][0]["sourceUrl"] = "https://example.org/unverified.pdf"
        with self.assertRaises(ValueError):
            validate(payload)

    def test_transaction_after_disclosure_is_rejected(self):
        payload = self.sample()
        payload["trades"][0]["eventDate"] = "2099-01-01"
        with self.assertRaises(ValueError):
            validate(payload)

    def test_duplicate_transaction_is_rejected(self):
        payload = self.sample()
        payload["trades"].append(copy.deepcopy(payload["trades"][0]))
        with self.assertRaises(ValueError):
            validate(payload)

    def test_unverified_transaction_type_is_rejected(self):
        payload = self.sample()
        payload["trades"][0]["transactionType"] = "buy-now"
        with self.assertRaises(ValueError):
            validate(payload)


if __name__ == "__main__":
    unittest.main()
