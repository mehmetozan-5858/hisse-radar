"""Local-only, deterministic paper execution pilot. Never contacts a broker."""

import argparse
import json
import math
import os
from datetime import datetime, timezone
from pathlib import Path


INITIAL_CASH = 100.0
MAX_POSITION = 20.0
MAX_POSITIONS = 5
LOSS_HALT = 10.0
FEE = 0.25
SPREAD_BPS = 20


def utc(value):
    dt = datetime.fromisoformat(value.replace("Z", "+00:00"))
    if dt.tzinfo is None:
        raise ValueError("Timezone required")
    return dt.astimezone(timezone.utc)


def valid_quote(row, now):
    try:
        price = float(row["price"])
        checked = utc(row["fetchedAt"])
        quoted = utc(row["priceAsOf"])
        return (row.get("marketDataStatus") == "fresh" and
                row.get("priceKind") == "realtime" and
                math.isfinite(price) and price > 0 and
                0 <= (now - checked).total_seconds() <= 900 and
                0 <= (now - quoted).total_seconds() <= 900 and
                quoted <= checked)
    except (KeyError, ValueError, TypeError, OverflowError):
        return False


def eligibility(row, verification, now):
    reasons = []
    if not valid_quote(row, now):
        reasons.append("15 dakika içinde zaman damgalı anlık fiyat doğrulanmadı")
    if not row.get("researchEligible") or float(row.get("score") or 0) < 65:
        reasons.append("Sinyal kapısı veya 65 puan eşiği geçilmedi")
    if not row.get("financialQuality", {}).get("available"):
        reasons.append("Temel finansal veri yok")
    if verification.get("independentCheck") != "verified":
        reasons.append("Bağımsız fiyat kaynağı doğrulamadı")
    if verification.get("decision") != "research_only":
        reasons.append("Araştırma veri kapısı geçilmedi")
    if not row.get("brokerConid") or not row.get("exchange"):
        reasons.append("IBKR sözleşmesi/borsası eşleşmedi")
    if row.get("currency") != "USD":
        reasons.append("USD dışı para birimi için kur/maliyet denetimi yok")
    if not row.get("marketOpenVerified"):
        reasons.append("Piyasa açık bilgisi doğrulanmadı")
    return reasons


def run(snapshot, agent_report, state, now):
    """Signal agent -> risk agent -> simulated fill; returns new state and audit."""
    now = utc(now) if isinstance(now, str) else now.astimezone(timezone.utc)
    run_id = snapshot.get("generatedAt")
    if not run_id:
        raise ValueError("Snapshot generatedAt required")
    if run_id in state.get("processedRuns", []):
        return state, {"run": run_id, "duplicate": True, "orders": [], "blocked": []}
    result = json.loads(json.dumps(state))
    result.setdefault("cash", INITIAL_CASH)
    result.setdefault("positions", {})
    result.setdefault("processedRuns", [])
    result.setdefault("ledger", [])
    checks = {x.get("symbol"): x for x in agent_report.get("candidates", [])}
    rows = {r.get("symbol"): r for r in snapshot.get("candidates", []) if r.get("symbol")}
    orders, blocked = [], []

    # Sell agent: a verified current quote is required even to simulate an exit.
    exited = set()
    for symbol, position in list(result["positions"].items()):
        row = rows.get(symbol)
        if not row or not valid_quote(row, now):
            blocked.append({"symbol": symbol, "action": "SELL", "reasons": ["Güncel fiyat yok"]})
            continue
        price = float(row["price"])
        if price < position["entry"] * 0.96 or price > position["entry"] * 1.05:
            fill = round(price * (1 - SPREAD_BPS / 10000), 4)
            proceeds = round(position["quantity"] * fill - FEE, 2)
            result["cash"] = round(result["cash"] + proceeds, 2)
            del result["positions"][symbol]
            exited.add(symbol)
            orders.append({"symbol": symbol, "side": "SELL", "quantity": position["quantity"],
                           "fill": fill, "fee": FEE, "simulated": True})

    # Risk agent: mark-to-market loss can only be evaluated with current quotes.
    missing = [s for s in result["positions"] if s not in rows or not valid_quote(rows[s], now)]
    equity = result["cash"] + sum(p["quantity"] * float(rows[s]["price"])
                                    for s, p in result["positions"].items() if s not in missing)
    halted = bool(missing) or equity <= INITIAL_CASH - LOSS_HALT
    for row in sorted(rows.values(), key=lambda r: (-float(r.get("score") or 0), r["symbol"])):
        symbol = row["symbol"]
        if symbol in result["positions"] or symbol in exited:
            continue
        reasons = eligibility(row, checks.get(symbol, {}), now)
        if halted:
            reasons.append("Pozisyon fiyatı eksik veya 10 $ zarar sınırı aşıldı")
        if len(result["positions"]) >= MAX_POSITIONS:
            reasons.append("Azami pozisyon sayısı")
        if reasons:
            blocked.append({"symbol": symbol, "action": "BUY", "reasons": reasons})
            continue
        fill = round(float(row["price"]) * (1 + SPREAD_BPS / 10000), 4)
        quantity = math.floor((min(MAX_POSITION, result["cash"]) - FEE) / fill)
        if quantity < 1:
            blocked.append({"symbol": symbol, "action": "BUY", "reasons": ["Komisyon sonrası bütçe yetersiz"]})
            continue
        cost = round(quantity * fill + FEE, 2)
        if cost > result["cash"] or cost > MAX_POSITION:
            raise AssertionError("Risk budget exceeded")
        result["cash"] = round(result["cash"] - cost, 2)
        result["positions"][symbol] = {"quantity": quantity, "entry": fill, "cost": cost}
        orders.append({"symbol": symbol, "side": "BUY", "quantity": quantity,
                       "fill": fill, "fee": FEE, "simulated": True})
    result["processedRuns"] = (result["processedRuns"] + [run_id])[-1000:]
    result["ledger"].extend({"run": run_id, **order} for order in orders)
    return result, {"run": run_id, "duplicate": False, "orders": orders,
                    "blocked": blocked, "cash": result["cash"], "halted": halted}


def main():
    parser = argparse.ArgumentParser(description="Local paper agent; no IBKR calls")
    parser.add_argument("--snapshot", type=Path, default=Path("data/global-niche.json"))
    parser.add_argument("--agents", type=Path, default=Path("data/agent-radar.json"))
    parser.add_argument("--state", type=Path, default=Path("local/paper-state.json"))
    parser.add_argument("--now", default=None, help="UTC ISO time, for deterministic demo")
    args = parser.parse_args()
    snapshot = json.loads(args.snapshot.read_text(encoding="utf-8"))
    agents = json.loads(args.agents.read_text(encoding="utf-8"))
    state = json.loads(args.state.read_text(encoding="utf-8")) if args.state.exists() else {}
    updated, report = run(snapshot, agents, state, args.now or datetime.now(timezone.utc))
    args.state.parent.mkdir(parents=True, exist_ok=True)
    temp = args.state.with_suffix(".tmp")
    temp.write_text(json.dumps(updated, ensure_ascii=False, indent=2), encoding="utf-8")
    os.replace(temp, args.state)
    print(json.dumps(report, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
