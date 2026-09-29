"""Publish recent U.S. House PTR stock trades from official House Clerk records.

Source: annual House Clerk disclosure ZIP + official PTR PDFs. No paid API key.
Only machine-readable e-filed PTRs are parsed; ambiguous rows are skipped.
"""
import csv, io, json, re, zipfile
from datetime import datetime, timezone
from pathlib import Path
from urllib.request import Request, urlopen

from pypdf import PdfReader
from congress_disclosures import validate

YEAR = datetime.now(timezone.utc).year
INDEX = f"https://disclosures-clerk.house.gov/public_disc/financial-pdfs/{YEAR}FD.ZIP"
OUTPUT = Path("data/congress-trades.json")
UA = "Mozilla/5.0 HisseRadar/1.0 public-record research"
MARKER = re.compile(r"(?P<name>[^\n]{1,180}?)\s*(?:\((?P<ticker>[A-Z][A-Z0-9.\-]{0,5})\))?\s*\[(?P<asset>[A-Z]{2})\]")
TX = re.compile(r"(?P<kind>S\s*\(partial\)|S\s*\(full\)|P|S|E)\s*(?P<date>\d{1,2}/\d{1,2}/\d{4})\s*(?:\d{1,2}/\d{1,2}/\d{4})?\s*(?P<amount>\$[\d,]+\s*-\s*\$[\d,]+|Over\s*\$[\d,]+)", re.I)
STOCK_CODES = {"ST", "EF"}

def get(url):
    with urlopen(Request(url, headers={"User-Agent": UA}), timeout=45) as r:
        return r.read()

def iso_date(value):
    return datetime.strptime(value.strip(), "%m/%d/%Y").date().isoformat()

def index_rows():
    z = zipfile.ZipFile(io.BytesIO(get(INDEX)))
    txt = next(n for n in z.namelist() if n.lower().endswith(".txt"))
    raw = z.read(txt).decode("utf-8-sig", errors="replace")
    rows = list(csv.DictReader(io.StringIO(raw), delimiter="\t"))
    ptr = [r for r in rows if (r.get("FilingType") or "").strip() == "P"]
    ptr.sort(key=lambda r: datetime.strptime(r["FilingDate"].strip(), "%m/%d/%Y"), reverse=True)
    return ptr

def parse_pdf(row):
    doc = (row.get("DocID") or "").strip()
    # 2xxxxxxx reports are electronic and have a usable text layer.
    if len(doc) != 8 or not doc.startswith("2"):
        return []
    url = f"https://disclosures-clerk.house.gov/public_disc/ptr-pdfs/{YEAR}/{doc}.pdf"
    reader = PdfReader(io.BytesIO(get(url)))
    text = "\n".join((p.extract_text() or "") for p in reader.pages).replace("\x00", "")
    filing = iso_date(row["FilingDate"])
    politician = " ".join(x.strip() for x in [row.get("First",""), row.get("Last","")] if x and x.strip())
    out = []
    markers = list(MARKER.finditer(text))
    for i, m in enumerate(markers):
        if m.group("asset") not in STOCK_CODES or not m.group("ticker"):
            continue
        end = markers[i+1].start() if i+1 < len(markers) else min(len(text), m.end()+700)
        tail = text[m.end():end]
        tx = TX.search(tail)
        if not tx:
            continue
        kind = tx.group("kind").upper().replace(" ", "")
        mapped = "purchase" if kind == "P" else "exchange" if kind == "E" else "sale"
        event = iso_date(tx.group("date"))
        if event > filing:
            continue
        amount = re.sub(r"\s+", " ", tx.group("amount")).strip()
        name = re.sub(r"\s+", " ", m.group("name")).strip(" -\n\t")
        trade = {
            "symbol": m.group("ticker"),
            "politician": politician,
            "chamber": "House",
            "transactionType": mapped,
            "amountRange": amount,
            "eventDate": event,
            "disclosureDate": filing,
            "sourceUrl": url,
            "committee": None,
            "owner": None,
            "assetType": name or m.group("asset"),
        }
        out.append(trade)
    return out

def build(max_filings=60):
    trades, seen, errors = [], set(), 0
    for row in index_rows()[:max_filings]:
        try:
            parsed = parse_pdf(row)
        except Exception as exc:
            errors += 1
            print("skip", row.get("DocID"), type(exc).__name__, exc)
            continue
        for t in parsed:
            key = (t["politician"], t["eventDate"], t["symbol"], t["transactionType"], t["sourceUrl"])
            if key in seen:
                continue
            seen.add(key); trades.append(t)
    trades.sort(key=lambda x: (x["disclosureDate"], x["eventDate"]), reverse=True)
    if not trades:
        raise RuntimeError("No verified House stock/ETF PTR rows parsed; preserving previous feed")
    payload = {
        "schemaVersion": 1,
        "updatedAt": datetime.now(timezone.utc).isoformat(),
        "status": "available",
        "source": "U.S. House Clerk annual disclosure index and official PTR PDFs",
        "coverage": "House; recent machine-readable PTR filings only",
        "trades": trades,
    }
    validate(payload)
    print(f"verified={len(trades)} errors={errors}")
    return payload

def main():
    payload = build()
    OUTPUT.write_text(json.dumps(payload, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    print(f"Published {len(payload['trades'])} official House disclosures")

if __name__ == "__main__":
    main()
