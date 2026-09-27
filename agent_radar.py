"""Human-command research agents for Hisse Radar.

Runs only on manual workflow dispatch. Never connects to a broker.
"""

import json
import os
from datetime import datetime, timedelta, timezone
from pathlib import Path


SOURCE = Path("data/global-niche.json")
OUTPUT = Path("data/agent-radar.json")
MAX_CANDIDATES = 3


def eligibility(stock):
    reasons = []
    if stock.get("marketDataStatus") != "fresh":
        reasons.append("Güncel fiyat yanıtı yok")
    if not isinstance(stock.get("price"), (int, float)) or stock["price"] <= 0:
        reasons.append("Geçerli fiyat yok")
    if not isinstance(stock.get("volume"), (int, float)) or stock["volume"] <= 0:
        reasons.append("Son fiyat kaydında işlem hacmi yok")
    metrics = stock.get("metrics") or {}
    if metrics.get("volumeRatio") is None:
        reasons.append("Hacim geçmişi doğrulanamıyor")
    try:
        traded_at = datetime.fromisoformat(stock.get("lastTradedAt"))
        if traded_at.tzinfo is None or traded_at > datetime.now(timezone.utc) + timedelta(hours=1) or datetime.now(timezone.utc) - traded_at > timedelta(days=5):
            reasons.append("Son işlem kaydı eski veya gelecekte")
    except (TypeError, ValueError):
        reasons.append("Son işlem tarihi doğrulanamıyor")
    if not stock.get("quoteUrl"):
        reasons.append("Fiyat kaynağı doğrulanamıyor")
    return reasons


ROLES = {
    "niche_scout": "Niş temayı ve veride gerçekten görülen sıradışı sinyali değerlendir.",
    "evidence_checker": "Verinin tarihi, kaynağı ve eksik kanıtları incele; doğrulanmayan iddiaları reddet.",
    "risk_critic": "Tezin neden başarısız olabileceğini, likidite ve kayıp riskini incele.",
}


def ask_agent(client, model, role, stock, generated_at):
    payload = {
        "generatedAt": generated_at,
        "source": "data/global-niche.json",
        "candidate": stock,
    }
    response = client.responses.create(
        model=model,
        max_output_tokens=450,
        instructions=(
            "Sen Hisse Radar araştırma ekibinin " + role + " ajanısın. "
            + ROLES[role]
            + " Yalnızca verilen JSON'daki kanıtlara dayan. Dış kaynakları okuduğunu iddia etme. "
            "Fiyatın son işlem zamanı JSON'da yoksa bunu açıkça belirt. "
            "Türkçe, en fazla 100 kelimelik kısa bir araştırma notu yaz. "
            "Al/sat emri, fiyat hedefi veya kazanç garantisi verme."
        ),
        input=json.dumps(payload, ensure_ascii=False),
    )
    return response.output_text.strip()[:1600]


def build_report(data, client=None, model=None):
    candidates = data.get("candidates", [])
    ranked = sorted(candidates, key=lambda item: item.get("score") or 0, reverse=True)
    rows = []
    selected = 0
    for stock in ranked:
        reasons = eligibility(stock)
        flags = list(reasons)
        if not stock.get("financialQuality", {}).get("available"):
            flags.append("Temel finansal veri yok")
        if stock.get("lastTradedAt"):
            flags.append("Son işlem: " + stock["lastTradedAt"])
        flags.append("Araştırma adayı; işlem kararı yalnızca kullanıcıda")
        row = {
            "symbol": stock.get("symbol"),
            "theme": stock.get("theme"),
            "score": stock.get("score"),
            "lastTradedAt": stock.get("lastTradedAt"),
            "quoteUrl": stock.get("quoteUrl"),
            "decision": "blocked" if reasons else "research_only",
            "flags": flags,
            "agents": {},
        }
        if not reasons and client and selected < MAX_CANDIDATES:
            for role in ROLES:
                row["agents"][role] = ask_agent(client, model, role, stock, data.get("generatedAt"))
            selected += 1
        rows.append(row)
    return {
        "generatedAt": datetime.now(timezone.utc).isoformat(),
        "sourceGeneratedAt": data.get("generatedAt"),
        "source": "data/global-niche.json",
        "mode": "AI research" if client else "data gate only",
        "maxAiCandidates": MAX_CANDIDATES,
        "lastBarTimestampAvailable": any(row.get("lastTradedAt") for row in rows),
        "orderAuthority": "user_only",
        "brokerConnection": False,
        "candidates": rows,
    }


def main():
    data = json.loads(SOURCE.read_text(encoding="utf-8"))
    key = os.getenv("OPENAI_API_KEY")
    client = None
    model = os.getenv("OPENAI_MODEL", "gpt-5-mini")
    if key:
        from openai import OpenAI
        client = OpenAI(api_key=key)
    report = build_report(data, client, model)
    OUTPUT.write_text(json.dumps(report, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    print(f"Mode: {report['mode']}; reviewed: {len(report['candidates'])}; AI candidates: {sum(bool(row['agents']) for row in report['candidates'])}")


if __name__ == "__main__":
    main()
