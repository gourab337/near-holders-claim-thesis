# After NEAR Intents froze funds, its volume held. Its public record didn't.

NEAR HACKATHON 2026 · **Investment Thesis track** · **Live dashboard:** https://gourab337.github.io/near-intents-freeze-thesis/

- **The bear case.** A cross-chain venue whose operator can freeze funds is not trustless, so users will leave the first time it uses that power.
- **The test.** Two freeze stories reached the public three weeks apart: a Zcash user's $589k held for 50 days (2026-09-08), then SHIELD blocking more than $50M of transfers tied to the Bitget hackers and freezing $503k mid-swap (reported 2026-09-29). Then a $3.8M exploit paused the contract (2026-10-01; funds returned the next day).
- **The result.** Total volume held: +1.0% against a model built from rival venues and the market, and deposits held. Its public record did not. On NEAR's chain (BigQuery) the share of volume visible as public swaps went from 59% in the summer to 19% by November; from late October public swap events fell to a fifth of August's level while executed intents doubled.
- **The catch.** Total volume is DefiLlama's figure, and most of it can no longer be checked onchain: on public onchain volume the same test gives -28.6% (p = 0.20). Why the swaps left public view is not identified: Confidential Intents, contract upgrades (2026-10-02, 2026-10-07) and solver settlement all fit. Intents' summer momentum stopped, and Zcash balances drained a month later.
- **The bet.** The freeze bears were wrong about the reported flow; my reading is that being trusted, not trustless, is NEAR's edge. But most of Intents' volume can no longer be checked on the chain, and revenue must still grow about 5.2× for buybacks to offset new NEAR supply. **Position: Long, one tripwire broken; neutral if a second breaks, or if Intents sets no new monthly volume record by 2027-03-31.**

The tests and decision rules are in [`PREREGISTRATION.md`](PREREGISTRATION.md). Its OpenTimestamps proof anchors it in Bitcoin block 975284 (10:15 UTC, 2026-11-10), half an hour after the data download began. The thesis states exactly what that proves and what it does not.

- **Thesis:** [`THESIS.md`](THESIS.md) (also rendered as `docs/thesis.html`)
- **Predictions:** [`PREDICTIONS.md`](PREDICTIONS.md), three dated calls to 2027-03-31, scored on future data only and timestamped in Bitcoin block 975308
- **Live dashboard:** https://gourab337.github.io/near-intents-freeze-thesis/ (source: [`docs/index.html`](docs/index.html), a static page that reads `docs/data.js`)

## The evidence (snapshot to 2026-11-09)

- **The public record vanished (onchain).** Public swap events: 119,511 a day in August, 78,240 after the first freeze story, 24,689 from late October. Executed intents: 46,107 to 89,934. Deposits: 29,216 to 25,665. The clear split (swaps falling while executed intents double) starts in late October, with no contract deploy then; Confidential Intents had opened to every app in July.
- **No collapse.** 28-day volume was +1.0% against the model (placebo p = 0.50). The pre-registered verdict is "no collapse, but too imprecise to clear the 25% bar": a loss would need to reach about 29.5% to be detected. The position is my judgment beyond that, listed as a deviation.
- **The momentum stopped.** BigQuery data covers 44 calm windows since 2026-03-01. In all of them Intents beat its model by +7% to +26%; the event window ranks below every one, for volume and for onchain relayed transactions.
- **No outperformance.** Against the 28 days before the shocks, Intents changed -16% and the rival median -33%. Against August, before rivals' much bigger September rally, Intents changed +47% and the rival median +89%. The model, which controls for rivals, says Intents kept pace.
- **Prices held.** The take rate was 16.4 bps in the three weeks before the shocks and 16.2 bps during them. The fee premium over the model predates the shocks.
- **Onchain (NEAR BigQuery).** 83% of transactions to `intents.near` are relayed (signed by the contract itself). Of accounts that sign their own, those seen before September came back at 38% against 53% in calm periods (p = 0.00); new and heavy accounts came back as usual.
- **The paused networks** dipped 22.1% for a day and were +27% against their pre-event level four weeks later.
- **The engine.** Oct 2026 volume was $3.99B: 2.3× a year earlier, when Intents was still ramping, but 1.09× its Nov 2025 peak, after nine months between $1.90B and $2.78B and a $4.80B record in Sep 2026.
- **Fragility.** The two pre-registered estimators agree on sign, not size (+1.0% and +39.5%). Across 60 alternative specifications the estimate runs from -33% to +35%; every large negative uses the 0x aggregator as a comparator.

## Check it in two minutes

Requires [uv](https://docs.astral.sh/uv/) (it installs Python 3.12 and the pinned packages). No API keys. After uv's first install of Python and the pinned packages, it runs offline.

| Do | See |
|---|---|
| `make` | It prints `H1 abnormal volume, 28 days from 2026-09-29: +1.0%  placebo-in-time p = 0.50  ->  no detectable loss`, and rewrites `data/processed/results.json`, `docs/data.js`, `THESIS.md`, `docs/thesis.html` and this `README.md` from `data/raw/`. `git status` shows no change, because the build is deterministic. |
| `make test` | 12 tests pass: raw files match the hashes in `data/raw/MANIFEST.json`; the timestamp proofs commit to `PREREGISTRATION.md` (with a Bitcoin attestation) and `PREDICTIONS.md` (both with Bitcoin attestations); the estimators recover known answers on synthetic data; verdicts and tripwires follow their written rules; the thesis and this README have no unfilled numbers; the dashboard data equals `results.json`. |
| `python3 -m http.server -d docs 8000`, then open http://localhost:8000 | The dashboard: verdict, tripwires, predictions and eight exhibits, each with the function in `src/build.py` that produced it. |
| `make fetch` (optional, needs network) | Re-downloads every series into `data/raw/` and rewrites the manifest. The numbers will move, because the sources keep updating. |
| `make fetch-bq` (optional, needs `gcloud` login and a billing project) | Re-runs `sql/` on NEAR's public BigQuery dataset (about 990 GB, roughly BigQuery's 1 TB monthly free tier) and rewrites those entries in the manifest. |
| `LAST_DAY=2027-03-31 make` after `make fetch` and `END_DATE=2027-03-31 make fetch-bq` | Scores `PREDICTIONS.md` with the thresholds written there; results in `results.json` under `predictions`. |

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
