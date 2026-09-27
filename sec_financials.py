"""Publish a small, provenance-preserving SEC annual financial snapshot.

SEC companyfacts is fetched by CIК on the server, never from the browser (CORS).
No data is invented when a filing, annual period, or unit is missing.
"""

import json
import os
import time
from datetime import date, datetime, timezone
from pathlib import Path
from urllib.request import Request, urlopen

ROOT = Path(__file__).parent
OUT = ROOT / "data/sec-financials.json"
TICKERS = "https://www.sec.gov/files/company_tickers.json"
FACTS = "https://data.sec.gov/api/xbrl/companyfacts/CIK{cik:010d}.json"
TAGS = {
    "revenue": ("RevenueFromContractWithCustomerExcludingAssessedTax", "Revenues", "SalesRevenueNet"),
    "netIncome": ("NetIncomeLoss",),
    "assets": ("Assets",),
    "liabilities": ("Liabilities",),
    "equity": ("StockholdersEquity", "StockholdersEquityIncludingPortionAttributableToNoncontrollingInterest"),
}


def get_json(url, agent):
    req = Request(url, headers={"User-Agent": agent, "Accept-Encoding": "identity", "Accept": "application/json"})
    with urlopen(req, timeout=25) as response:
        return json.load(response)


def annual_fact(facts, tags, fiscal_year, target_end=None):
    """Choose an original 10-K fact for exactly one fiscal year and USD unit."""
    gaap = facts.get("facts", {}).get("us-gaap", {})
    for tag in tags:
        entries = gaap.get(tag, {}).get("units", {}).get("USD", [])
        eligible = []
        for entry in entries:
            if entry.get("form") != "10-K" or entry.get("fp") != "FY" or entry.get("fy") != fiscal_year:
                continue
            try:
                end = date.fromisoformat(entry["end"])
                filed = date.fromisoformat(entry["filed"])
                if target_end and end.isoformat() != target_end:
                    continue
                if "start" in entry:
                    duration = (end - date.fromisoformat(entry["start"])).days
                    if not 330 <= duration <= 380:
                        continue
                elif abs(end.year - fiscal_year) > 1:
                    continue
                val = float(entry["val"])
                if not -1e18 < val < 1e18:
                    continue
            except (KeyError, TypeError, ValueError, OverflowError):
                continue
            eligible.append((filed, end, entry, val))
        if eligible:
            # Original filing for the matching fiscal year; later 10-K restatements
            # can be evaluated separately rather than silently mixing submissions.
            filed, end, entry, val = min(eligible, key=lambda row: (row[0], -row[1].toordinal()))
            return {"value": round(val), "end": end.isoformat(), "filed": filed.isoformat(),
                    "accession": entry.get("accn"), "tag": tag}
    return None


def snapshot(payload):
    gaap = payload.get("facts", {}).get("us-gaap", {})
    years = sorted({e.get("fy") for tag in TAGS["revenue"] for e in gaap.get(tag, {}).get("units", {}).get("USD", [])
                    if isinstance(e.get("fy"), int) and e.get("form") == "10-K" and e.get("fp") == "FY"}, reverse=True)
    for year in years:
        this_revenue = annual_fact(payload, TAGS["revenue"], year)
        prior_revenue = annual_fact(payload, TAGS["revenue"], year - 1)
        if not (this_revenue and prior_revenue):
            continue
        current = {key: annual_fact(payload, tags, year, this_revenue["end"]) for key, tags in TAGS.items()}
        previous = {key: annual_fact(payload, tags, year - 1, prior_revenue["end"]) for key, tags in TAGS.items()}
        if current["revenue"] and previous["revenue"]:
            return {"fiscalYear": year, "previousFiscalYear": year - 1, "currency": "USD",
                    "current": current, "previous": previous}
    return None


def main():
    agent = os.getenv("SEC_USER_AGENT", "").strip()
    if not agent or "@" not in agent:
        print("SEC_USER_AGENT with a real contact email is required; leaving prior report intact.")
        return
    stocks = json.loads((ROOT / "data/radar.json").read_text(encoding="utf-8")).get("stocks", [])
    symbols = {s["symbol"].upper() for s in stocks if s.get("symbol") and "." not in s["symbol"]}
    directory = get_json(TICKERS, agent)
    cik_by_ticker = {v["ticker"].upper(): v["cik_str"] for v in directory.values()}
    previous = json.loads(OUT.read_text(encoding="utf-8")) if OUT.exists() else {}
    results = previous.get("stocks", {}).copy()
    errors = {}
    for symbol in sorted(symbols):
        cik = cik_by_ticker.get(symbol)
        if not cik:
            results.pop(symbol, None)
            errors[symbol] = "SEC ticker/CIK eşleşmesi yok"
            continue
        if results.get(symbol, {}).get("cik") != cik:
            results.pop(symbol, None)
        try:
            result = snapshot(get_json(FACTS.format(cik=cik), agent))
            if result:
                results[symbol] = {"cik": cik, "company": directory[next(k for k, v in directory.items() if v["ticker"].upper() == symbol)]["title"],
                                   "source": FACTS.format(cik=cik), **result}
            else:
                errors[symbol] = "Karşılaştırılabilir iki yıllık USD 10-K verisi yok"
        except Exception as exc:
            errors[symbol] = f"SEC isteği başarısız: {type(exc).__name__}"
        time.sleep(0.2)  # 5 requests/s, below SEC's published 10/s maximum.
    document = {"updatedAt": datetime.now(timezone.utc).isoformat(), "source": "SEC EDGAR companyfacts",
                "stocks": results, "errors": errors}
    OUT.parent.mkdir(exist_ok=True)
    OUT.write_text(json.dumps(document, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    print(f"SEC: {len(results)} companies, {len(errors)} gaps")


if __name__ == "__main__":
    main()
