"""Rotating exchange-listed equity discovery; no orders or investment decisions."""

import json
import os
import re
from datetime import datetime, timedelta, timezone
from pathlib import Path
from urllib.parse import urlencode
from urllib.request import Request, urlopen


CACHE = Path("data/niche-universe-cache.json")
NASDAQ_URL = "https://www.nasdaqtrader.com/dynamic/SymDir/nasdaqlisted.txt"
EXCHANGES = {
    "US": ("NASDAQ", "USA", ""),
    "LSE": ("LSE", "UK", ".L"),
    "XETRA": ("XETRA", "Germany", ".DE"),
    "PA": ("Euronext Paris", "France", ".PA"),
    "AS": ("Euronext Amsterdam", "Netherlands", ".AS"),
    "HK": ("HKEX", "Hong Kong", ".HK"),
}
STOCK_TYPES = {"common stock", "ordinary share", "ordinary shares", "equity"}
EXCLUDE = re.compile(r"\b(etfs?|etns?|funds?|warrants?|rights?|units?|preferred|depositary|notes?|bonds?|acquisition(?:\s+[IVX0-9]+)?\s+(?:corp|company)|spac)\b", re.I)


def http_text(url):
    with urlopen(Request(url, headers={"User-Agent": "HisseRadar/1.0"}), timeout=20) as response:
        return response.read().decode("utf-8-sig")


def nasdaq_rows(source):
    lines = source.splitlines()
    if not lines or not lines[0].startswith("Symbol|Security Name|"):
        raise ValueError("Nasdaq directory format not recognized")
    result = []
    for line in lines[1:]:
        fields = line.split("|")
        if len(fields) < 8:
            continue
        code, name, _, test, status, _, etf, next_shares = fields[:8]
        if (not re.fullmatch(r"[A-Z]{1,5}", code) or test != "N" or status != "N"
                or etf != "N" or next_shares != "N" or EXCLUDE.search(name)):
            continue
        result.append({"symbol": code, "name": name, "market": "NASDAQ", "country": "USA", "theme": "Dinamik keşif", "size": "bilinmiyor", "discovered": True})
    return result


def eod_rows(source, code):
    items = json.loads(source)
    if not isinstance(items, list):
        raise ValueError("Exchange list is not an array")
    market, country, suffix = EXCHANGES[code]
    result = []
    for item in items:
        raw = str(item.get("Code", "")).strip().upper()
        name = str(item.get("Name", "")).strip()
        kind = str(item.get("Type", "")).strip().lower()
        if not re.fullmatch(r"[A-Z0-9]{1,8}", raw) or not name or EXCLUDE.search(name):
            continue
        if kind not in STOCK_TYPES:
            continue
        # Yahoo's Hong Kong symbols are four digit codes; EODHD commonly returns 1-5 digits.
        symbol = raw.zfill(4) + suffix if code == "HK" and raw.isdigit() else raw + suffix
        result.append({"symbol": symbol, "name": name, "market": market, "country": country,
                       "theme": "Dinamik keşif", "size": "bilinmiyor", "discovered": True,
                       "listingCode": f"{raw}.{code}"})
    return result


def load_universe(token=None, fetch=http_text, now=None):
    """Reuse lists for a day; fail closed for exchanges without a usable list."""
    now = now or datetime.now(timezone.utc)
    try:
        cache = json.loads(CACHE.read_text(encoding="utf-8"))
    except (FileNotFoundError, ValueError):
        cache = {}
    sources = cache.get("sources", {})
    refresh = {}
    for code in EXCHANGES:
        if code != "US" and not token:
            continue
        old = sources.get(code, {})
        try:
            fetched_at = datetime.fromisoformat(old.get("fetchedAt", ""))
            if fetched_at.tzinfo and now - fetched_at < timedelta(hours=24) and now >= fetched_at:
                refresh[code] = old
                continue
        except ValueError:
            pass
        try:
            if code == "US":
                rows = nasdaq_rows(fetch(NASDAQ_URL))
                provider = NASDAQ_URL
            else:
                url = "https://eodhd.com/api/exchange-symbol-list/" + code + "?" + urlencode({"api_token": token, "fmt": "json", "type": "common_stock"})
                rows = eod_rows(fetch(url), code)
                provider = "EODHD exchange-symbol-list/" + code
            if not rows:
                raise ValueError("Empty eligible exchange list")
            refresh[code] = {"fetchedAt": now.isoformat(), "provider": provider, "rows": rows}
        except (OSError, TimeoutError, ValueError) as exc:
            print("Directory unavailable:", code, type(exc).__name__)
            # A stale directory must not be presented as current coverage.
    CACHE.parent.mkdir(parents=True, exist_ok=True)
    CACHE.write_text(json.dumps({"sources": refresh}, ensure_ascii=False, separators=(",", ":")) + "\n", encoding="utf-8")
    rows = {item["symbol"]: item for source in refresh.values() for item in source["rows"]}
    return sorted(rows.values(), key=lambda row: row["symbol"]), {code: len(source["rows"]) for code, source in refresh.items()}


def rotate(rows, run_number, batch=30):
    """Interleave markets, then advance a bounded slice at each scheduled run."""
    grouped = {code: [] for code in EXCHANGES}
    for row in rows:
        code = row.get("listingCode", "").rsplit(".", 1)[-1] if row.get("listingCode") else "US"
        if code in grouped:
            grouped[code].append(row)
    result = []
    active = [code for code, items in grouped.items() if items]
    if not active:
        return result
    for offset in range(batch):
        code = active[(run_number * batch + offset) % len(active)]
        items = grouped[code]
        # Each market advances independently across successive runs.
        slot = (run_number * batch // len(active) + offset // len(active)) % len(items)
        result.append(items[slot])
    return result
