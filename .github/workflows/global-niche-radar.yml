name: Global Niche Radar

on:
  workflow_dispatch:
  schedule:
    # Günde 2 kez çalışır; mevcut FMP kotasını kullanmaz.
    - cron: "35 5,17 * * *"

permissions:
  contents: write

jobs:
  niche-radar:
    runs-on: ubuntu-latest

    steps:
      - name: Repository checkout
        uses: actions/checkout@v4

      - name: Python kurulumu
        uses: actions/setup-python@v5
        with:
          python-version: "3.12"

      - name: Global Niche Radar verisini üret
        run: |
          python <<'PY'
          import json
          import os
          from datetime import datetime, timezone

          # ============================================
          # GLOBAL NICHE RADAR V1
          # FMP API KULLANMAZ.
          # Mevcut radar ve FMP kotasından bağımsızdır.
          # ============================================

          # V1 başlangıç evreni.
          # Sonraki sürümde bunu otomatik global taramaya
          # dönüştüreceğiz.
          UNIVERSE = [
              # ABD
              {"symbol": "RKLB", "market": "NASDAQ", "country": "USA",
               "sector": "Space", "size": "small"},
              {"symbol": "IONQ", "market": "NYSE", "country": "USA",
               "sector": "Quantum", "size": "small"},
              {"symbol": "SOUN", "market": "NASDAQ", "country": "USA",
               "sector": "AI", "size": "small"},
              {"symbol": "QBTS", "market": "NYSE", "country": "USA",
               "sector": "Quantum", "size": "micro"},
              {"symbol": "LUNR", "market": "NASDAQ", "country": "USA",
               "sector": "Space", "size": "small"},

              # Kanada
              {"symbol": "PNG.V", "market": "TSXV", "country": "Canada",
               "sector": "Robotics", "size": "micro"},
              {"symbol": "FLT.V", "market": "TSXV", "country": "Canada",
               "sector": "Drones", "size": "micro"},

              # İngiltere
              {"symbol": "HE1.L", "market": "LSE-AIM", "country": "UK",
               "sector": "Helium", "size": "micro"},
              {"symbol": "BMN.L", "market": "LSE-AIM", "country": "UK",
               "sector": "Critical Minerals", "size": "micro"},

              # Avustralya
              {"symbol": "DRO.AX", "market": "ASX", "country": "Australia",
               "sector": "Defense / Drones", "size": "small"},
              {"symbol": "LTR.AX", "market": "ASX", "country": "Australia",
               "sector": "Lithium", "size": "small"},

              # Avrupa
              {"symbol": "ALQGC.PA", "market": "Euronext", "country": "France",
               "sector": "Quantum", "size": "micro"},

              # Türkiye
              {"symbol": "MIATK.IS", "market": "BIST", "country": "Türkiye",
               "sector": "Technology / AI", "size": "small"},
              {"symbol": "PAPIL.IS", "market": "BIST", "country": "Türkiye",
               "sector": "Biometrics / Defense", "size": "micro"},
          ]

          # V1'de skor yalnızca aday önceliklendirme skorudur.
          # Yatırım tavsiyesi veya gelecek getiri tahmini değildir.
          SECTOR_WEIGHT = {
              "AI": 18,
              "Quantum": 20,
              "Space": 19,
              "Robotics": 18,
              "Drones": 18,
              "Defense / Drones": 19,
              "Biometrics / Defense": 17,
              "Technology / AI": 18,
              "Helium": 15,
              "Critical Minerals": 16,
              "Lithium": 14,
          }

          SIZE_WEIGHT = {
              "micro": 20,
              "small": 14,
              "mid": 8,
              "large": 2,
          }

          results = []

          for stock in UNIVERSE:
              score = 35
              score += SECTOR_WEIGHT.get(stock["sector"], 10)
              score += SIZE_WEIGHT.get(stock["size"], 8)

              # V1 puanını 0-100 aralığında tut.
              score = max(0, min(100, score))

              if score >= 75:
                  level = "GÜÇLÜ İZLEME"
              elif score >= 65:
                  level = "GÜÇLENİYOR"
              else:
                  level = "NİŞ ADAY"

              results.append({
                  **stock,
                  "nicheScore": score,
                  "level": level,
                  "price": None,
                  "changePct": None,
                  "volumeSignal": None,
                  "catalyst": None,
                  "risk": "Yüksek" if stock["size"] == "micro" else "Orta-Yüksek",
                  "scenario100": {
                      "2x": 200,
                      "5x": 500,
                      "10x": 1000,
                      "50x": 5000,
                      "100x": 10000,
                      "1000x": 100000
                  },
                  "note": "V1 keşif adayı. Finansal ve piyasa verileri sonraki katmanda doğrulanacak."
              })

          results.sort(key=lambda x: x["nicheScore"], reverse=True)

          payload = {
              "version": "global-niche-v1",
              "generatedAt": datetime.now(timezone.utc).isoformat(),
              "description": "Global erken keşif radarının ilk sürümü.",
              "disclaimer": (
                  "Niche Score bir getiri tahmini değildir. "
                  "Yüksek riskli şirketleri araştırma amacıyla önceliklendirir."
              ),
              "markets": sorted(list(set(x["market"] for x in results))),
              "count": len(results),
              "stocks": results
          }

          os.makedirs("data", exist_ok=True)

          with open("data/global-niche.json", "w", encoding="utf-8") as f:
              json.dump(payload, f, ensure_ascii=False, indent=2)

          print("Global Niche Radar üretildi.")
          print("Aday sayısı:", len(results))
          print("FMP API çağrısı: 0")
          PY

      - name: Değişiklikleri kaydet
        run: |
          git config user.name "actions-user"
          git config user.email "actions@users.noreply.github.com"

          git add data/global-niche.json

          if git diff --cached --quiet; then
            echo "Değişiklik yok."
          else
            git commit -m "Update Global Niche Radar"
            git push
          fi
