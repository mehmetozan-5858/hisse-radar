"""Public, read-only execution readiness report for the global research universe.

No broker credentials, order endpoint or transfer endpoint are used here.
"""

import json
from datetime import datetime, timedelta, timezone
from pathlib import Path


SOURCE = Path("data/global-niche.json")
AGENTS = Path("data/agent-radar.json")
OUTPUT = Path("data/execution-readiness.json")


def assess(data, agent_report, now=None):
    now = now or datetime.now(timezone.utc)
    agent_rows = {item.get("symbol"): item for item in agent_report.get("candidates", [])}
    rows = []
    for stock in data.get("candidates", []):
        reasons = []
        if stock.get("marketDataStatus") != "fresh":
            reasons.append("Güncel fiyat yanıtı yok")
        try:
            traded = datetime.fromisoformat(stock["lastTradedAt"])
            if traded.tzinfo is None or now - traded > timedelta(days=5) or traded > now:
                reasons.append("Son işlem kaydı güncel değil")
        except (KeyError, TypeError, ValueError):
            reasons.append("Son işlem zamanı yok")
        if not stock.get("financialQuality", {}).get("available"):
            reasons.append("Temel finansal veri eksik")
        verdict = agent_rows.get(stock.get("symbol"), {})
        if verdict.get("independentCheck") != "verified":
            reasons.append("İkinci fiyat kaynağı doğrulamadı")
        if verdict.get("decision") != "research_only":
            reasons.append("Ajan veri kapısı geçilmedi")
        # A valid contract, exchange calendar, live quote, permission and cost are
        # account-specific IBKR checks; Yahoo symbols are not IBKR contracts.
        reasons.append("IBKR sözleşmesi, piyasa saati ve işlem izni doğrulanmadı")
        rows.append({"symbol": stock.get("symbol"), "market": stock.get("market"),
                     "readyForOrder": False, "reasons": reasons})
    return {
        "checkedAt": now.isoformat(), "brokerCandidate": "Interactive Brokers",
        "brokerConnected": False, "executionMode": "research_only",
        "monitoring": "scheduled_data_updates", "capitalLimitUsd": 100,
        "pilotDays": 7, "maxPositionUsd": 20, "lossPauseUsd": 10,
        "capitalMilestoneUsd": 1000, "retainedTradingCapitalUsd": 1000,
        "realizedWithdrawableProfitChunkUsd": 10000,
        "withdrawalPolicy": "broker_portal_user_executed_no_automatic_transfer",
        "bankTransferMade": False, "readyCount": 0, "candidates": rows,
    }


def main():
    data = json.loads(SOURCE.read_text(encoding="utf-8"))
    agents = json.loads(AGENTS.read_text(encoding="utf-8")) if AGENTS.exists() else {}
    report = assess(data, agents)
    OUTPUT.write_text(json.dumps(report, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    print(f"Execution readiness: {report['readyCount']}/{len(report['candidates'])}; broker connected: false")


if __name__ == "__main__":
    main()
