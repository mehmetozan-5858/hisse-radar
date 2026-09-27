import unittest

from sec_financials import snapshot


def fact(value, start, end, fy, filed):
    return {"val": value, "start": start, "end": end, "fy": fy, "fp": "FY",
            "form": "10-K", "filed": filed, "accn": f"{fy}-annual"}


class AnnualFactsTest(unittest.TestCase):
    def test_years_are_not_mixed_with_comparative_columns(self):
        payload = {"facts": {"us-gaap": {
            "RevenueFromContractWithCustomerExcludingAssessedTax": {"units": {"USD": [
                fact(100, "2024-01-01", "2024-12-31", 2024, "2025-02-01"),
                fact(100, "2024-01-01", "2024-12-31", 2025, "2026-02-01"),
                fact(120, "2025-01-01", "2025-12-31", 2025, "2026-02-01"),
                fact(110, "2025-01-01", "2025-12-31", 2025, "2026-03-01"),
            ]}},
            "Assets": {"units": {"USD": [
                {**fact(200, "2024-01-01", "2024-12-31", 2025, "2026-02-01")},
                {**fact(230, "2025-01-01", "2025-12-31", 2025, "2026-02-01")},
            ]}},
        }}}
        result = snapshot(payload)
        self.assertEqual(result["current"]["revenue"]["value"], 120)
        self.assertEqual(result["previous"]["revenue"]["value"], 100)
        self.assertEqual(result["current"]["assets"]["value"], 230)
        self.assertIsNone(result["previous"]["assets"])

    def test_missing_prior_year_returns_no_report(self):
        payload = {"facts": {"us-gaap": {"Revenues": {"units": {"USD": [
            fact(200, "2025-01-01", "2025-12-31", 2025, "2026-02-01")
        ]}}}}}
        self.assertIsNone(snapshot(payload))


if __name__ == "__main__":
    unittest.main()
