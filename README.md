# Hold NEAR. Intents is a resilient business, but NEAR holders get little of what it earns so far.

*It came through a freeze and a hack with its volume intact. But only 16% of new supply comes back, none of it is paid to holders, and no rule in code protects it.*

[![check](https://github.com/gourab337/near-holders-claim-thesis/actions/workflows/check.yml/badge.svg)](https://github.com/gourab337/near-holders-claim-thesis/actions/workflows/check.yml) (on every push GitHub rebuilds every number from the committed data on Linux, checks it reproduces the committed thesis, and runs the tests)

NEAR HACKATHON 2026 · **Investment Thesis track** · **Live dashboard:** https://gourab337.github.io/near-holders-claim-thesis/ · **Thesis (about ten minutes):** [`THESIS.md`](THESIS.md) · **Demo video (106 s, narrated):** [`docs/demo.mp4`](docs/demo.mp4)

## In 30 seconds

| | |
|---|---|
| **Rating** | **Hold**, to the end of 2029. Keep NEAR you own, staked; do not add yet. |
| **The number** | NEAR Intents sends back 16% as much NEAR as NEAR issues. None of it is paid to holders, staked or burned. |
| **The trigger** | Buy when the wallets that receive Intents' revenue take in 21,700 NEAR a day for three months (the last three averaged 15,486). Avoid if the wallets shrink or two of three warning measures break. |

NEAR's market value is 213 times a year of one business's revenue: NEAR Intents, which swaps tokens across blockchains. That price needs the business to keep going and holders to share in it. The first is true. The second, so far, is not.

1. **The business is resilient.** Within a month Intents froze users' funds and was hacked for $3.8M. Counted swap by swap, volume on 1Click (the swap service apps plug into) in the four weeks after was -5% against August, and 17 of 25 large integrating apps kept at least half their volume.
2. **One number looked like a loss. It was not.** Public swaps on NEAR's chain fell from 119,511 a day to 24,689. The swaps had not left: since 27 October 1Click settles on a permissioned instance of NEAR with no public networking. Of the swaps I sampled, 98% left a public record in August and 7% in November. The business was fine, but it became harder to check.
3. **Holders get little of it.** NEAR creates 86,966 new tokens a day, which dilutes holders. The wallets that receive Intents' revenue take in 13,571 a day: 16% as much. To match all the new supply, the inflow would have to grow about 6.4×. By month it has run from 6% to 22% with no steady rise.
4. **And no rule protects even that.** None of it is paid to holders, staked or burned. A few signers can move it (2 of 4, 2 of 4 and 2 of 5 across the three wallets), and the front-end fund's policy sets the threshold for changing its own rules at 1 vote (read from the contract, not tested).

So: a resilient business is a reason not to sell, and a small share that nobody guarantees is a reason not to buy more. Hold.

What cuts against it is in the thesis too: the statistical test I planned in advance was inconclusive (-24.3% or +1.0%, depending on the comparison venues), and I changed the rating from Long to Hold a day before submitting, after measuring the wallets.

## Read

- **[`THESIS.md`](THESIS.md)**: the claim, the evidence for, the evidence against, and what would change my mind. About ten minutes to read. Also at `docs/thesis.html`.
- **[`RATING.md`](RATING.md)**: the Buy / Hold / Avoid rule and five dated predictions, scored on 31 March 2027. Timestamped with OpenTimestamps.
- **[`APPENDIX.md`](APPENDIX.md)**: every table, caveat and deviation, and the pre-registered event study the project began as.
- **Dashboard**: https://gourab337.github.io/near-holders-claim-thesis/ (source [`docs/index.html`](docs/index.html)): eleven exhibits, each with the query or function behind it.

## Where each number comes from

| Finding | Source | Code |
|---|---|---|
| Large swaps and integrating apps after the freeze and the hack (64,591 swaps of $10,000 or more) | NEAR Intents Explorer API | `src/fetch_explorer.py` |
| Public swaps on the chain falling from 119,511 to 24,689 a day | NEAR's public BigQuery dataset | `sql/intents_event_counts_daily.sql` |
| 98% to 7% of sampled swaps leaving a public record | NEAR Intents Explorer API, then BigQuery | `src/fetch_explorer.py`, `sql/intents_swap_trace.sql` |
| Share of reported volume visible as public swaps, 43% to 13% | BigQuery over DefiLlama | `sql/intents_stable_volume_daily.sql` |
| Wallet balances, 4,224,522 NEAR; inflow against issuance | NEAR's public BigQuery dataset | `sql/revenue_wallets_daily.sql` |
| Who can move the wallets | The contracts, over a public RPC endpoint | `src/fetch_control.py` |
| Reported volume against a model of rival venues | DefiLlama, CoinGecko | `src/build.py`, `event_stat()` |

## Check it in two minutes

Requires [uv](https://docs.astral.sh/uv/) (it installs Python 3.12 and the pinned packages). No API keys. After uv's first install of Python and the pinned packages, it runs offline.

| Do | See |
|---|---|
| `make` | It prints `H1 abnormal volume, 28 days from 2026-09-29: -24.3% (pre-registered donors, p = 0.34), +1.0% (narrower set, p = 0.50)  ->  no detectable loss`, and rewrites `data/processed/results.json`, `docs/data.js`, `THESIS.md`, `docs/thesis.html` and this `README.md` from `data/raw/`. On macOS `git status` then shows no change. On Linux `results.json` and `docs/data.js` can differ in the 12th significant digit, because numpy's linear algebra rounds differently there; the thesis and README text stay identical. |
| `make check` | Rebuilds, then prints `Rebuild matches the commit: ...`: the README, thesis and thesis page are byte-identical to the committed ones, and `results.json` matches to 1e-9 relative. GitHub runs this and `make test` on every push (badge above). |
| `make test` | The tests pass: raw files match the hashes in `data/raw/MANIFEST.json`; the timestamp proofs commit to `PREREGISTRATION.md`, `archive/PREDICTIONS-2026-11-10.md` and `RATING.md`; the estimators recover known answers on synthetic data; verdicts and tripwires follow their written rules; the thesis and this README have no unfilled numbers; the dashboard data equals `results.json`. |
| `python3 -m http.server -d docs 8000`, then open http://localhost:8000 | The dashboard: verdict, tripwires, predictions and eleven exhibits, each with the query or function that produced it. |
| `make fetch` (optional, needs network) | Re-downloads every series into `data/raw/` and rewrites the manifest. The numbers will move, because the sources keep updating. |
| `make fetch-explorer` (optional, needs a NEAR Intents partner token in `.env` and the `fetch-bq` setup) | Re-pulls 1Click swaps from the Explorer API (daily volume of swaps of $100 or more; every swap of $10,000 or more; a seeded sample of 300 swaps on each of five days), traces the sample onto the chain in BigQuery, and saves totals and counts only. About three hours, because the API allows one request every five seconds. |
| `make fetch-bq` (optional, needs `gcloud` login and a billing project) | Re-runs `sql/` on NEAR's public BigQuery dataset (about 990 GB, roughly BigQuery's 1 TB monthly free tier) and rewrites those entries in the manifest. |
| `LAST_DAY=2027-03-31 make` after `make fetch` and `END_DATE=2027-03-31 make fetch-bq` | Scores the five calls in `RATING.md` with the thresholds written there; results in `results.json` under `predictions` and `rating.calls`. |

## How it is built

| Path | What it is |
|---|---|
| `PREREGISTRATION.md` | The plan, with its OpenTimestamps proof (`.ots`, Bitcoin block 975284) |
| `RATING.md` | The rating, its rule and five dated, falsifiable calls to 2027-03-31, with its OpenTimestamps proof |
| `archive/PREDICTIONS-2026-11-10.md` | The first version (Long; three calls), unchanged, with its proof in Bitcoin block 975308 |
| `src/fetch.py` | Downloads every series; records URL, time and SHA-256 in `data/raw/MANIFEST.json` |
| `src/fetch_explorer.py` | The NEAR Intents Explorer API pulls (1Click swaps) and the swap-level trace; saves totals and counts, not swap records |
| `src/fetch_control.py` | Reads who can move the three wallets from the contracts |
| `src/fetch_bigquery.py`, `sql/` | The NEAR chain queries (BigQuery) and the script that runs them |
| `src/build.py` | All analysis. Every number in the thesis and on the dashboard comes from here |
| `THESIS.template.md`, `APPENDIX.template.md`, `README.template.md` | The write-ups with placeholders; `build.py` fills every number from `results.json` |
| `data/raw/` | Snapshot downloaded 2026-11-10 and 2026-11-11, covering data to 2026-11-09 (DefiLlama, CoinGecko, NEAR BigQuery, Explorer API totals, contract policies) |
| `docs/` | Dashboard and thesis page |

## What is and is not pre-registered

| | Fixed before the result | Evidence of when |
|---|---|---|
| The five tests of the freeze and the exploit, and their decision rules (`PREREGISTRATION.md`) | Yes, by my statement | Bitcoin block 975284, mined 29 minutes after the data download began. It shows the plan was frozen early, not that it came first. |
| Three predictions to 2027-03-31 (first version, `archive/PREDICTIONS-2026-11-10.md`; carried into `RATING.md` as P1 to P3) | Yes: scored only on later data | Bitcoin block 975308, 2026-11-10 |
| The rating rule and two more calls, C1 and C2 (`RATING.md`) | Calls yes; the rule was written after seeing the wallet data | OpenTimestamps, 2026-11-11 |
| The rating itself | No. Long on 2026-11-10, Hold on 2026-11-11 after the wallets were measured (appendix B7, deviation 7) | |
| Parts 1 to 4 of the thesis (integrators, the confidential switch, wallets, wallet control) and appendix A6 and A7 | No. Added after seeing results (appendix B7, deviation 5) | |

## Data notes

- **Onchain data.** NEAR's public BigQuery dataset gives every transaction to `intents.near` and NEAR's supply. Relayed 1Click swaps are signed by the contract itself, so user-level retention onchain covers only self-custody accounts. Since 27 October 1Click swaps settle confidentially, so the chain shows their shield and unshield, not the swap; the Explorer API supplies 1Click volume and the swap sample.
- **Explorer API data and its terms.** The track's starter prompt asks for a pull from the NEAR Intents Explorer API. The 1Click API terms (section 4.1(e)) limit storing API data to 24 hours. So this repository holds no swap records, amounts or addresses from the API: `src/fetch_explorer.py` keeps them in memory and saves daily totals by integrating app, counts of sender addresses that came back, and, for the 1,500 sampled swaps, their public NEAR transaction hashes with dollar-weighted shares. Re-pulling needs a partner token.
- **Reported volume.** DefiLlama's Intents volume is read from a dataset NEAR publishes on Dune. The thesis uses it and says where it cannot be checked from outside.

## License

MIT, see [`LICENSE`](LICENSE).
