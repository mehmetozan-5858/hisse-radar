"""Validate a manually reviewed congressional disclosure export.

There is intentionally no scraper: source terms and data rights must be resolved
before an automated feed or republication is enabled.
"""

import argparse
import json
from datetime import date, datetime, timezone
from pathlib import Path
from urllib.parse import urlparse

OFFICIAL_HOSTS = {"disclosures-clerk.house.gov", "efdsearch.senate.gov"}
REQUIRED = {"symbol", "politician", "chamber", "transactionType", "amountRange",
            "eventDate", "disclosureDate", "sourceUrl", "committee"}


def validate(payload):
    if payload.get("schemaVersion") != 1 or payload.get("status") not in {"unavailable", "available"}:
        raise ValueError("Invalid schema version or status")
    trades = payload.get("trades")
    if not isinstance(trades, list):
        raise ValueError("trades must be a list")
    if payload["status"] == "unavailable" and trades:
        raise ValueError("Unavailable feed must be empty")
    if trades and not payload.get("updatedAt"):
        raise ValueError("Populated feed needs updatedAt")
    if payload.get("updatedAt"):
        stamp = datetime.fromisoformat(payload["updatedAt"].replace("Z", "+00:00"))
        if stamp.tzinfo is None:
            raise ValueError("updatedAt must include timezone")
        if stamp > datetime.now(timezone.utc):
            raise ValueError("updatedAt cannot be in the future")
    seen = set()
    for trade in trades:
        if not isinstance(trade, dict) or not REQUIRED <= trade.keys():
            raise ValueError("Trade is missing required fields")
        if any(not isinstance(trade[field], str) or not trade[field].strip()
               for field in REQUIRED - {"committee"}):
            raise ValueError("Trade has empty fields")
        if trade["chamber"] not in {"House", "Senate"}:
            raise ValueError("Invalid chamber")
        if trade["transactionType"] not in {"purchase", "sale", "exchange"}:
            raise ValueError("Invalid transactionType")
        if trade["committee"] is not None and not isinstance(trade["committee"], str):
            raise ValueError("Invalid committee")
        event = date.fromisoformat(trade["eventDate"])
        disclosure = date.fromisoformat(trade["disclosureDate"])
        if event > disclosure or disclosure > datetime.now(timezone.utc).date():
            raise ValueError("Impossible event/disclosure dates")
        url = urlparse(trade["sourceUrl"])
        if url.scheme != "https" or url.hostname not in OFFICIAL_HOSTS:
            raise ValueError("Source must link to an official filing")
        identity = (trade["politician"], trade["eventDate"], trade["symbol"],
                    trade["transactionType"], trade["sourceUrl"])
        if identity in seen:
            raise ValueError("Duplicate filing transaction")
        seen.add(identity)
    return len(trades)


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("path", nargs="?", default="data/congress-trades.json")
    args = parser.parse_args()
    count = validate(json.loads(Path(args.path).read_text(encoding="utf-8")))
    print(f"Congress disclosures valid: {count} verified trades")
