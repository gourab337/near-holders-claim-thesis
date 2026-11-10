# After NEAR Intents froze funds, its flow didn't leave. It vanished from public view.

NEAR HACKATHON 2026 · **Investment Thesis track** · **Live dashboard:** https://gourab337.github.io/near-intents-freeze-thesis/

- **The bear case.** A cross-chain venue whose operator can freeze funds is not trustless, so users will leave the first time it uses that power.
- **The test.** NEAR Intents used that power twice in three weeks, then lost the other kind of trust: a Zcash user's $589k held for 50 days ({{events.E0}}), SHIELD blocking more than $50M tied to the Bitget hackers and freezing $503k mid-swap (reported {{events.T}}), then a $3.8M exploit that paused the contract ({{events.E2}}; funds returned the next day).
- **The result.** The flow stayed: total volume came in {{H1.stat_pct|pct}} against a model built from rival venues and the market, and deposits held. Its public record did not. On NEAR's chain (BigQuery), public swap events fell from {{privacy.events.windows.before.token_diff|n}} a day in August to {{privacy.events.windows.after.token_diff|n}} by November while executed intents doubled; the share of volume visible as public swaps went from {{privacy.windows.after_ga|share0}} to {{privacy.windows.after|share0}}.
- **The catch.** Why the swaps left public view is not identified: Confidential Intents, a contract upgrade ({{privacy.events.deploys.0}}, {{privacy.events.deploys.1}}) and a change in solver settlement each fit. The total-volume test cannot see a loss smaller than about {{H1.mde_pct|upct}}. Intents' summer momentum stopped, and Zcash balances drained a month later.
- **The bet.** The freeze bears were wrong about the flow; my reading is that being trusted, not trustless, is NEAR's edge. But most of Intents' volume can no longer be checked on the chain, and revenue must still grow about {{long_term.growth_needed|x}} for buybacks to offset new NEAR supply. **Position: {{position.label}}; neutral if a second breaks, or if Intents sets no new monthly volume record by 2027-03-31.**

The tests and decision rules are in [`PREREGISTRATION.md`](PREREGISTRATION.md). Its OpenTimestamps proof anchors it in Bitcoin block 975284 (10:15 UTC, 2026-11-10), half an hour after the data download began. The thesis states exactly what that proves and what it does not.

- **Thesis:** [`THESIS.md`](THESIS.md) (also rendered as `docs/thesis.html`)
- **Predictions:** [`PREDICTIONS.md`](PREDICTIONS.md), three dated calls to 2027-03-31, scored on future data only and timestamped in Bitcoin block 975308
- **Live dashboard:** https://gourab337.github.io/near-intents-freeze-thesis/ (source: [`docs/index.html`](docs/index.html), a static page that reads `docs/data.js`)

## The evidence (snapshot to {{last_day}})

- **The public record vanished (onchain).** Public swap events: {{privacy.events.windows.before.token_diff|n}} a day in August, {{privacy.events.windows.between.token_diff|n}} after the first freeze story, {{privacy.events.windows.after.token_diff|n}} from late October. Executed intents: {{privacy.events.windows.before.intents_executed|n}} to {{privacy.events.windows.after.intents_executed|n}}. Deposits: {{privacy.events.windows.before.mt_mint|n}} to {{privacy.events.windows.after.mt_mint|n}}. The decline began three weeks before the SHIELD freeze and two months after Confidential Intents opened to every app.
- **No collapse.** 28-day volume was {{H1.stat_pct|pct}} against the model (placebo p = {{H1.p_placebo_time|p}}). The pre-registered verdict is "{{H1.prereg_outcome}}": a loss would need to reach about {{H1.mde_pct|upct}} to be detected. The position is my judgment beyond that, listed as a deviation.
- **The momentum stopped.** BigQuery data covers {{onchain_check.n_placebo}} calm windows since {{onchain_check.from}}. In all of them Intents beat its model by {{onchain_check.volume.placebo_min_pct|pct0}} to {{onchain_check.volume.placebo_max_pct|pct0}}; the event window ranks below every one, for volume and for onchain relayed transactions.
- **No outperformance.** Against the 28 days before the shocks, Intents changed {{rivals.intents_pct|pct0}} and the rival median {{rivals.median_pct|pct0}}. Against August, before rivals' much bigger September rally, Intents changed {{rivals.vs_august.intents_pct|pct0}} and the rival median {{rivals.vs_august.median_pct|pct0}}. The model, which controls for rivals, says Intents kept pace.
- **Prices held.** The take rate was {{windows.between.take_rate_bps|bps}} bps in the three weeks before the shocks and {{windows.event.take_rate_bps|bps}} bps during them. The fee premium over the model predates the shocks.
- **Onchain (NEAR BigQuery).** {{H5.relayed_share|share0}} of transactions to `intents.near` are relayed swaps. Of accounts that sign their own, those seen before September came back at {{H5.cohorts.returning.rate|share0}} against {{H5.cohorts.returning.placebo_p50|share0}} in calm periods (p = {{H5.cohorts.returning.p|p}}); new and heavy accounts came back as usual.
- **The paused networks** dipped {{H3.trough.pct|upct}} for a day and were {{H3.d28.paused_pct|pct0}} against their pre-event level four weeks later.
- **The engine.** Volume first peaked at {{long_term.first_peak_volume|usd_b}} in {{long_term.first_peak_month|month}}; {{long_term.last_month|month}} was {{long_term.last_month_volume|usd_b}}, {{long_term.last_vs_first_peak|f2}}× that, after a plateau and a {{long_term.record_volume|usd_b}} record in {{long_term.record_month|month}}.
- **Fragility.** The two pre-registered estimators agree on sign, not size ({{H1.stat_pct|pct}} and {{synth.ratio_pct|pct}}). Across {{grid.n}} alternative specifications the estimate runs from {{grid.min_pct|pct0}} to {{grid.max_pct|pct0}}; every large negative uses the 0x aggregator as a comparator.

## Check it in two minutes

Requires [uv](https://docs.astral.sh/uv/) (it installs Python 3.12 and the pinned packages). No API keys. After uv's first install of Python and the pinned packages, it runs offline.

| Do | See |
|---|---|
| `make` | It prints `H1 abnormal volume, 28 days from {{events.T}}: {{H1.stat_pct|pct}}  placebo-in-time p = {{H1.p_placebo_time|p}}  ->  {{H1.verdict}}`, and rewrites `data/processed/results.json`, `docs/data.js`, `THESIS.md`, `docs/thesis.html` and this `README.md` from `data/raw/`. `git status` shows no change, because the build is deterministic. |
| `make test` | 11 tests pass: raw files match the hashes in `data/raw/MANIFEST.json`; the timestamp proofs commit to `PREREGISTRATION.md` (with a Bitcoin attestation) and `PREDICTIONS.md` (both with Bitcoin attestations); the estimators recover known answers on synthetic data; verdicts and tripwires follow their written rules; the thesis and this README have no unfilled numbers; the dashboard data equals `results.json`. |
| `python3 -m http.server -d docs 8000`, then open http://localhost:8000 | The dashboard: verdict, tripwires and eight exhibits, each with the function in `src/build.py` that produced it. |
| `make fetch` (optional, needs network) | Re-downloads every series into `data/raw/` and rewrites the manifest. The numbers will move, because the sources keep updating. |
| `make fetch-bq` (optional, needs `gcloud` login and a billing project) | Re-runs `sql/` on NEAR's public BigQuery dataset (about 15 GB, inside the free tier) and rewrites those entries in the manifest. |

## How it is built

| Path | What it is |
|---|---|
| `PREREGISTRATION.md` | The plan, with its OpenTimestamps proof (`.ots`, Bitcoin block 975284) |
| `PREDICTIONS.md` | Three dated, falsifiable calls to 2027-03-31, with their OpenTimestamps proof (Bitcoin block 975308) |
| `src/fetch.py` | Downloads every series; records URL, time and SHA-256 in `data/raw/MANIFEST.json` |
| `src/fetch_bigquery.py`, `sql/` | The NEAR chain queries (BigQuery) and the script that runs them |
| `src/build.py` | All analysis. Every number in the thesis and on the dashboard comes from here |
| `THESIS.template.md`, `README.template.md` | The write-ups with placeholders; `build.py` fills every number from `results.json` |
| `data/raw/` | Snapshot of 2026-11-10 (DefiLlama, CoinGecko, NEAR BigQuery) |
| `docs/` | Dashboard and thesis page |

The thesis lists every deviation from the pre-registration, and separately everything added after seeing results.

**Onchain data:** NEAR's public BigQuery dataset gives every transaction to `intents.near` and NEAR's supply. Relayed 1Click swaps are signed by the contract itself, so user-level retention covers only self-custody accounts. The Intents Explorer API would cover the rest; it needs a partner token and is not used.

## License

MIT, see [`LICENSE`](LICENSE).
