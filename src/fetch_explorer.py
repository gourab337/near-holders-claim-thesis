"""Three pulls from the NEAR Intents Explorer API (1Click swaps), the only source of 1Click flow since it settles off the public chain.

The 1Click API terms (section 4.1(e)) limit storing API data to 24 hours. So this script keeps the swap records in
memory only and writes totals and counts computed from them: no per-swap record, address or amount is saved.

daily  Daily 1Click volume, 2026-08-01 to END_DATE: every successful swap of $100 or more (minUsdPrice=100; on four
       fully pulled days these were 32-45% of swaps and 98.8-99.5% of their dollars), summed by day and deposit type.
large  Every successful swap of $10,000 or more over the same days, summed by day and integrating app (swaps, dollars),
       and how many sender addresses came back after the freeze and in the calm window before it (counts only).
trace  For each day in DAYS: every successful 1Click swap that day and a seeded random sample of 300. For the sample,
       sql/intents_swap_trace.sql (BigQuery) reports, for each NEAR transaction hash, whether intents.near logged a
       public swap (token_diff) or moved funds through the Treasury account behind Confidential Intents. Saved: the
       public NEAR transaction hashes of each sampled swap, and the dollar-weighted shares for each day.

Run all three, or name the ones wanted: python src/fetch_explorer.py [daily] [large] [trace]. About three hours in all.
Needs NEAR_INTENTS_EXPLORER_JWT (partner token, in .env); trace also needs the BigQuery setup of src/fetch_bigquery.py.
Writes data/raw/explorer_1click_daily.csv, explorer_large_daily.csv, explorer_large_senders.json,
explorer_trace_sample.json and bq_intents_swap_trace.csv, and their manifest entries. Set END_DATE=YYYY-MM-DD to extend
the series (default 2026-11-09).
"""
import collections, csv, io, hashlib, json, math, os, random, subprocess, sys, time, urllib.error, urllib.parse, urllib.request
import datetime as dt

ROOT = os.path.join(os.path.dirname(os.path.abspath(__file__)), "..")
RAW = os.path.join(ROOT, "data", "raw")
API = "https://explorer.near-intents.org/api/v0/transactions"
# A summer day and a day after 1Click moved to confidential settlement (2026-10-27); then a day before the freeze and the
# days either side of the switch. The first two are sampled first, so adding days does not change their samples.
DAYS = ["2026-08-12", "2026-11-05", "2026-09-15", "2026-10-26", "2026-10-28"]
N = 300
DAILY_FROM, END_DATE = dt.date(2026, 8, 1), dt.date.fromisoformat(os.environ.get("END_DATE", "2026-11-09"))
MIN_USD = 100
LARGE_USD = 10000
FREEZE, HORIZON = dt.date(2026, 9, 29), 28  # the freeze date and window of src/build.py, which checks they match
TYPES = ["ORIGIN_CHAIN", "INTENTS", "CONFIDENTIAL_INTENTS"]
_last = [0.0]
KEEP = ["depositAddress", "depositMemo", "createdAt", "depositType", "amountInUsd", "nearTxHashes"]


def get(params, token):
    for _ in range(30):
        time.sleep(max(0.0, _last[0] + 5.1 - time.monotonic()))  # documented limit: one request every 5 seconds, start to start
        _last[0] = time.monotonic()
        req = urllib.request.Request(API + "?" + urllib.parse.urlencode(params), headers={"Authorization": f"Bearer {token}"})
        try:
            with urllib.request.urlopen(req, timeout=60) as r:
                return json.load(r)
        except urllib.error.HTTPError as e:
            if e.code != 429 and e.code < 500:
                raise
    raise SystemExit("Explorer API: gave up after 30 attempts")


def day_swaps(day, token, min_usd=None, keep=KEEP):
    d0 = dt.date.fromisoformat(day)
    base = {"numberOfTransactions": 1000, "statuses": "SUCCESS", **({"minUsdPrice": min_usd} if min_usd else {}),
            "startTimestamp": f"{d0}T00:00:00Z", "endTimestamp": f"{d0 + dt.timedelta(days=1)}T00:00:00Z"}
    rows, seen, params = [], set(), dict(base)
    while True:
        page = get(params, token)
        for x in page:
            key = (x["depositAddress"], x.get("depositMemo"))
            if key not in seen:
                seen.add(key)
                rows.append({k: x.get(k) for k in keep})
        if len(page) < 1000:
            return rows
        params = dict(base, lastDepositAddress=page[-1]["depositAddress"], direction="next")
        if page[-1].get("depositMemo"):
            params["lastDepositMemo"] = page[-1]["depositMemo"]


def save(name, body, url, manifest):
    with open(os.path.join(RAW, name), "wb") as f:
        f.write(body)
    manifest[name.rsplit(".", 1)[0]] = {"file": name, "url": url, "fetched_at": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()),
                                        "sha256": hashlib.sha256(body).hexdigest(), "bytes": len(body)}
    print(f"{name:40s} {len(body):>10,d} bytes")


def daily(token):
    out = io.StringIO()
    w = csv.writer(out, lineterminator="\n")
    w.writerow(["day", "deposit_type", "swaps", "usd_in"])
    d = DAILY_FROM
    while d <= END_DATE:
        n, usd = collections.Counter(), collections.Counter()
        for x in day_swaps(d.isoformat(), token, MIN_USD):
            n[x["depositType"]] += 1
            usd[x["depositType"]] += float(x["amountInUsd"] or 0)
        assert set(n) <= set(TYPES), set(n)
        for t in TYPES:
            w.writerow([d.isoformat(), t, n[t], f"{usd[t]:.2f}"])
        print(d, sum(n.values()), f"${sum(usd.values()) / 1e6:.1f}M", flush=True)
        d += dt.timedelta(days=1)
    return out.getvalue().encode()


def large_rows(token):
    """Every successful 1Click swap of $10,000 or more, in memory: (day, dollars, integrating app, first sender address)."""
    rows, d = [], DAILY_FROM
    while d <= END_DATE:
        got = day_swaps(d.isoformat(), token, LARGE_USD, ["depositAddress", "depositMemo", "amountInUsd", "referral", "senders"])
        rows += [(d, float(x["amountInUsd"]), x["referral"] or "", (x["senders"] or [""])[0]) for x in got]
        print(d, len(got), flush=True)
        d += dt.timedelta(days=1)
    return rows


def summarise_large(rows):
    """Totals by day and integrating app, and how many sender addresses came back. Returns (csv bytes, json bytes)."""
    n, usd = collections.Counter(), collections.defaultdict(list)
    for day, amount, referral, _ in rows:
        n[day, referral] += 1
        usd[day, referral].append(amount)
    out = io.StringIO()
    w = csv.writer(out, lineterminator="\n")
    w.writerow(["day", "referral", "swaps", "usd_in"])
    for day, referral in sorted(n):
        w.writerow([day.isoformat(), referral, n[day, referral], f"{math.fsum(usd[day, referral]):.2f}"])

    days_of = collections.defaultdict(set)  # sender address -> days with a large swap
    for day, _, _, sender in rows:
        if sender:
            days_of[sender].add(day)
    span = dt.timedelta(days=HORIZON)

    def came_back(t, min_days):
        pre = [s for s, ds in days_of.items() if sum(t - span <= d < t for d in ds) >= min_days]
        return len(pre), sum(any(t <= d < t + span for d in days_of[s]) for s in pre) / len(pre)

    # Calm comparison: start dates whose 28 days before begin on or after the first day pulled and whose 28 days after end before the freeze.
    first = min(r[0] for r in rows)
    calm = [first + span + dt.timedelta(days=i) for i in range((FREEZE - span - first - span).days + 1)]
    senders = {}
    for k in (1, 2, 5):
        rates = [came_back(t, k)[1] for t in calm]
        senders[str(k)] = {"n": came_back(FREEZE, k)[0], "rate": came_back(FREEZE, k)[1], "calm_min": min(rates), "calm_max": max(rates)}
    summary = {"freeze": FREEZE.isoformat(), "horizon": HORIZON, "sender_known": sum(bool(r[3]) for r in rows) / len(rows),
               "calm_dates": len(calm), "calm_from": calm[0].isoformat(), "calm_to": calm[-1].isoformat(), "senders": senders}
    return out.getvalue().encode(), json.dumps(summary, indent=1, sort_keys=True).encode()


def summarise_trace(sample, trace_csv):
    """For each sampled day: the NEAR transaction hashes of each sampled swap, and the dollar-weighted shares."""
    flags = {r["tx_hash"]: r for r in csv.DictReader(io.StringIO(trace_csv.decode()))}
    out = {}
    for day, s in sample.items():
        usd = [float(x["amountInUsd"] or 0) for x in s["sample"]]
        hit = lambda col: [any(int(flags.get(h, {}).get(col, 0)) > 0 for h in x["nearTxHashes"]) for x in s["sample"]]
        share = lambda col: math.fsum(u for u, ok in zip(usd, hit(col)) if ok) / math.fsum(usd)
        out[day] = {"swaps_that_day": s["swaps_that_day"], "public_usd": share("token_diff"), "treasury_usd": share("treasury"),
                    "deposit_confidential": sum(x["depositType"] == "CONFIDENTIAL_INTENTS" for x in s["sample"]) / len(s["sample"]),
                    "near_tx_hashes": [x["nearTxHashes"] for x in s["sample"]]}
    return json.dumps(out, indent=1, sort_keys=True).encode()


def trace(token):
    rng = random.Random(20261111)
    sample = {}
    for day in DAYS:
        swaps = sorted(day_swaps(day, token), key=lambda x: (x["depositAddress"], x["depositMemo"] or ""))
        sample[day] = {"swaps_that_day": len(swaps), "sample": rng.sample(swaps, N)}
        print(day, len(swaps), flush=True)
    hashes = sorted({h for d in sample.values() for x in d["sample"] for h in x["nearTxHashes"]})
    with open(os.path.join(ROOT, "sql", "intents_swap_trace.sql")) as f:
        sql = "\n".join(line for line in f if not line.startswith("--"))
    body = subprocess.run(["bq", "query", "--use_legacy_sql=false", "--format=csv", "--max_rows=1000000", "--quiet",
                           "--parameter=hashes:ARRAY<STRING>:" + json.dumps(hashes), sql], check=True, capture_output=True).stdout
    return summarise_trace(sample, body), body


def main():
    """All three pulls, or only those named: python src/fetch_explorer.py [daily] [large] [trace]."""
    token = os.environ["NEAR_INTENTS_EXPLORER_JWT"]
    steps = sys.argv[1:] or ["daily", "large", "trace"]
    with open(os.path.join(RAW, "MANIFEST.json")) as f:
        manifest = json.load(f)
    if "daily" in steps:
        save("explorer_1click_daily.csv", daily(token), API + f" (statuses=SUCCESS, minUsdPrice={MIN_USD}, summed by day)", manifest)
    if "large" in steps:
        by_day, senders = summarise_large(large_rows(token))
        save("explorer_large_daily.csv", by_day, API + f" (statuses=SUCCESS, minUsdPrice={LARGE_USD}, summed by day and integrating app)", manifest)
        save("explorer_large_senders.json", senders, API + f" (statuses=SUCCESS, minUsdPrice={LARGE_USD}, counts of sender addresses that came back)", manifest)
        manifest.pop("explorer_1click_large", None)
    if "trace" in steps:
        sample, body = trace(token)
        save("explorer_trace_sample.json", sample, API + f" (statuses=SUCCESS, seeded sample of {N} a day: NEAR transaction hashes and dollar-weighted shares)", manifest)
        manifest.pop("explorer_swaps_sample", None)
        save("bq_intents_swap_trace.csv", body, "bigquery:sql/intents_swap_trace.sql", manifest)
    with open(os.path.join(RAW, "MANIFEST.json"), "w") as f:
        json.dump(manifest, f, indent=1)


if __name__ == "__main__":
    main()
