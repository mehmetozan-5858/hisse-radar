import unittest

from congress_feed import build, normalize


class CongressFeedTests(unittest.TestCase):
    def setUp(self):
        self.row = {
            "symbol": "AAPL", "assetType": "Stock", "type": "Purchase",
            "office": "Example Member", "amount": "$1,001 - $15,000",
            "transactionDate": "2026-08-01", "disclosureDate": "2026-09-01",
            "link": "https://disclosures-clerk.house.gov/public_disc/ptr-pdfs/2026/example.pdf",
            "owner": "Spouse",
        }

    def test_source_backed_trade_dates_and_owner(self):
        trade = normalize(self.row, "House")
        self.assertEqual((trade["eventDate"], trade["disclosureDate"]), ("2026-08-01", "2026-09-01"))
        self.assertEqual(trade["owner"], "Spouse")

    def test_rejects_nonofficial_and_nonstock(self):
        self.assertIsNone(normalize({**self.row, "link": "https://example.com/trade"}, "House"))
        self.assertIsNone(normalize({**self.row, "assetType": "Corporate Bond"}, "House"))

    def test_deduplicates_and_rejects_empty_response(self):
        payload = build([self.row, self.row], [])
        self.assertEqual(len(payload["trades"]), 1)
        with self.assertRaises(ValueError):
            build([], [])


if __name__ == "__main__":
    unittest.main()
