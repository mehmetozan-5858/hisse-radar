import unittest

from paper_agent import run


NOW = "2026-09-27T15:00:00+00:00"


def approved(price=5.0, fetched=NOW):
    return {"symbol": "DEMO", "price": price, "score": 80,
            "researchEligible": True, "financialQuality": {"available": True},
            "marketDataStatus": "fresh", "fetchedAt": fetched,
            "brokerConid": "12345", "exchange": "NASDAQ", "currency": "USD",
            "marketOpenVerified": True}


AGENTS = {"candidates": [{"symbol": "DEMO", "independentCheck": "verified",
                          "decision": "research_only"}]}


class PaperAgentTests(unittest.TestCase):
    def test_missing_checks_block_real_radar(self):
        row = approved()
        row["financialQuality"] = {"available": False}
        row.pop("brokerConid")
        state, report = run({"generatedAt": NOW, "candidates": [row]}, {}, {}, NOW)
        self.assertEqual(report["orders"], [])
        self.assertEqual(state["cash"], 100)
        self.assertIn("IBKR sözleşmesi/borsası eşleşmedi", report["blocked"][0]["reasons"])

    def test_buy_exit_and_replay(self):
        snapshot = {"generatedAt": NOW, "candidates": [approved()]}
        state, report = run(snapshot, AGENTS, {}, NOW)
        self.assertEqual(report["orders"][0]["side"], "BUY")
        self.assertLessEqual(state["positions"]["DEMO"]["cost"], 20)
        same, duplicate = run(snapshot, AGENTS, state, NOW)
        self.assertTrue(duplicate["duplicate"])
        self.assertEqual(same, state)
        later = "2026-09-27T15:10:00+00:00"
        snapshot = {"generatedAt": later, "candidates": [approved(5.5, later)]}
        state, report = run(snapshot, AGENTS, state, later)
        self.assertEqual(report["orders"][0]["side"], "SELL")
        self.assertNotIn("DEMO", state["positions"])

    def test_stale_quote_and_loss_halt(self):
        state, report = run({"generatedAt": NOW, "candidates": [approved(5, "2026-09-27T14:30:00+00:00")]}, AGENTS, {}, NOW)
        self.assertEqual(report["orders"], [])
        self.assertEqual(state["cash"], 100)
        state, report = run({"generatedAt": NOW, "candidates": [approved()]}, AGENTS,
                            {"cash": 89, "positions": {}}, NOW)
        self.assertTrue(report["halted"])
        self.assertEqual(report["orders"], [])


if __name__ == "__main__":
    unittest.main()
