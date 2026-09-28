"""Build the public Congress feed from a licensed FMP subscription.

Run only when the repository owner has confirmed FMP display/redistribution
rights. The API key stays in GitHub Actions; invalid responses never replace
the last published report.
"""

import json
import os
from datetime import datetime, timezone
from pathlib import Path
from urllib.parse import urlencode, urlparse
from urllib.request import Request, urlopen

from congress_disclosures import OFFICIAL_HOSTS, validate

BASE = "https://financialmodelingprep.com/stable"
OUTPUT = Path("data/congress-trades.json")


def normalize(row, chamber):
    if not isinstance(row, dict):
        return None
    symbol = str(row.get("symbol") or "").strip().upper()
    asset_type = str(row.get("assetType") or "").lower()
    if not symbol or asset_type not in {"stock", "etf", "cryptocurrency", "crypto"}:
        return None
    kind = str(row.get("type") or "").strip().lower()
    transaction_type = {"purchase": "purchase", "sale": "sale", "exchange": "exchange"}.get(kind)
    if not transaction_type:
        return None
    source = str(row.get("link") or "").strip()
    parsed = urlparse(source)
    if parsed.scheme != "https" or parsed.hostname not in OFFICIAL_HOSTS:
        return None
    politician = str(row.get("office") or "").strip() or " ".join(
        filter(None, (str(row.get("firstName") or "").strip(), str(row.get("lastName") or "").strip()))
    )
    if not politician or not row.get("amount"):
        return None
    trade = {
        "symbol": symbol,
        "politician": politician,
        "chamber": chamber,
        "transactionType": transaction_type,
        "amountRange": str(row["amount"]).strip(),
        "eventDate": str(row.get("transactionDate") or ""),
        "disclosureDate": str(row.get("disclosureDate") or ""),
        "sourceUrl": source,
        "committee": None,
        "owner": str(row.get("owner") or "").strip() or None,
        "assetType": str(row.get("assetType") or "").strip(),
    }
    try:
        validate({"schemaVersion": 1, "status": "available", "updatedAt": datetime.now(timezone.utc).isoformat(), "trades": [trade]})
    except (ValueError, TypeError):
        return None
    return trade


def fetch(endpoint, key):
    url = f"{BASE}/{endpoint}?" + urlencode({"page": 0, "limit": 100, "apikey": key})
    with urlopen(Request(url, headers={"User-Agent": "HisseRadar/1.0"}), timeout=30) as response:
        rows = json.load(response)
    if not isinstance(rows, list):
        raise ValueError(f"{endpoint}: API did not return a list (plan or access may be limited)")
    return rows


def build(house, senate, now=None):
    now = now or datetime.now(timezone.utc)
    trades = []
    seen = set()
    for chamber, rows in (("House", house), ("Senate", senate)):
        for row in rows:
            trade = normalize(row, chamber)
            if not trade:
                continue
            identity = (trade["politician"], trade["eventDate"], trade["symbol"],
                        trade["transactionType"], trade["sourceUrl"])
            if identity in seen:
                continue
            seen.add(identity)
            trades.append(trade)
    if not trades:
        raise ValueError("No source-backed stock/ETF/crypto transactions; preserve prior report")
    trades.sort(key=lambda row: (row["disclosureDate"], row["eventDate"]), reverse=True)
    payload = {"schemaVersion": 1, "updatedAt": now.isoformat(), "status": "available",
               "source": "FMP Senate/House latest; official filing links", "trades": trades}
    validate(payload)
    return payload


def main():
    if os.getenv("CONGRESS_DISPLAY_LICENSED", "").lower() != "true":
        print("Congress feed disabled: FMP display license not confirmed")
        return
    key = os.getenv("FMP_API_KEY", "").strip()
    if not key:
        raise SystemExit("FMP_API_KEY is missing")
    payload = build(fetch("house-latest", key), fetch("senate-latest", key))
    OUTPUT.write_text(json.dumps(payload, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    print(f"Published {len(payload['trades'])} source-backed disclosures")


if __name__ == "__main__":
    main()
