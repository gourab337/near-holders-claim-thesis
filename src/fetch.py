"""Download every public series the study uses into data/raw/ (no API keys).

Each response is saved byte-for-byte; data/raw/MANIFEST.json records the URL,
fetch time and SHA-256 so a later reader can tell exactly what was analysed.
"""
import hashlib, json, os, time, urllib.request

RAW = os.path.join(os.path.dirname(__file__), "..", "data", "raw")
LLAMA = "https://api.llama.fi"
DONORS_DEX = ["thorchain-dex", "chainflip-amm", "maya-protocol"]
DONORS_AGG = ["li.fi-bridge-aggregator", "socket-protocol", "jumper-bridge-aggregator", "0x-bridge-aggregator", "rango"]
COINS = ["near", "zcash", "bitcoin"]

SOURCES = {
    "intents_volume": f"{LLAMA}/summary/dexs/near-intents?dataType=dailyVolume",
    "intents_fees": f"{LLAMA}/summary/fees/near-intents?dataType=dailyFees",
    "intents_revenue": f"{LLAMA}/summary/fees/near-intents?dataType=dailyRevenue",
    "intents_balances": f"{LLAMA}/protocol/near-intents",
    # every protocol on NEAR that DefiLlama tracks revenue for, by day, and the chain's own revenue
    "near_protocols_revenue": f"{LLAMA}/overview/fees/near?excludeTotalDataChart=true&excludeTotalDataChartBreakdown=false&dataType=dailyRevenue",
    "near_chain_revenue": f"{LLAMA}/summary/fees/near?dataType=dailyRevenue",
    **{f"donor_{s}": f"{LLAMA}/summary/dexs/{s}?dataType=dailyVolume" for s in DONORS_DEX},
    **{f"donor_{s}": f"{LLAMA}/summary/bridge-aggregators/{s}?dataType=dailyBridgeVolume" for s in DONORS_AGG},
    **{f"market_{c}": f"https://api.coingecko.com/api/v3/coins/{c}/market_chart?vs_currency=usd&days=365&interval=daily" for c in COINS},
}


def main():
    os.makedirs(RAW, exist_ok=True)
    path = os.path.join(RAW, "MANIFEST.json")
    manifest = json.load(open(path)) if os.path.exists(path) else {}  # keep entries written by fetch_bigquery.py
    for name, url in SOURCES.items():
        req = urllib.request.Request(url, headers={"User-Agent": "near-intents-event-study"})
        body = urllib.request.urlopen(req, timeout=120).read()
        json.loads(body)  # fail fast on a non-JSON reply
        open(os.path.join(RAW, name + ".json"), "wb").write(body)
        manifest[name] = {"url": url, "fetched_at": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()),
                          "sha256": hashlib.sha256(body).hexdigest(), "bytes": len(body)}
        print(f"{name:40s} {len(body):>10,d} bytes")
        time.sleep(3 if "coingecko" in url else 0.5)
    json.dump(manifest, open(path, "w"), indent=1)


if __name__ == "__main__":
    main()
