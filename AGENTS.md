# Guide for AI reviewers

NEAR HACKATHON 2026, Investment Thesis track. This repo is an investment thesis on NEAR: Hold, because holders' claim on NEAR Intents' revenue is small (measured from three public wallets), unsecured (a few signers control the wallets and no rule in code commits the NEAR), and getting harder to check (1Click swaps settle confidentially since 2026-10-27), while the business itself held up after Intents froze user funds (2026-09-29) and was exploited (2026-10-01).

- `THESIS.md` is the argument, about 2,400 words: the claim, evidence for (Parts 1 to 3), evidence against, what would change the author's mind.
- `APPENDIX.md` holds everything else: Part B is the full tables, caveats and deviations behind the thesis; Part A is the pre-registered event study the project began as, planned in `PREREGISTRATION.md`.
- `RATING.md` is the rating rule and five dated predictions.

## Verify in about two minutes (offline, no keys)

Needs [uv](https://docs.astral.sh/uv/). It installs Python 3.12 and the three pinned packages in `requirements.txt` (numpy, pandas, markdown).

| Run | Expect |
|---|---|
| `make` | Prints `H1 abnormal volume, 28 days from 2026-09-29: -24.3% (pre-registered donors, p = 0.34), +1.0% (narrower set, p = 0.50)  ->  no detectable loss` and regenerates `data/processed/results.json`, `docs/data.js`, `THESIS.md`, `docs/thesis.html`, `README.md` from `data/raw/`. |
| `make test` | `Ran 13 tests ... OK`. |
| `make check` | Rebuilds, then prints `Rebuild matches the commit: ...`. On Linux `git status` may show `results.json` and `docs/data.js` modified, with differences only around the 12th significant digit (numpy linear algebra rounds differently from macOS). `make check` confirms the text outputs are byte-identical and the JSON is equal to 1e-9. |
| `python3 -m http.server -d docs 8000` | The dashboard at http://localhost:8000 (also live at https://gourab337.github.io/near-holders-claim-thesis/). |

Without uv: `pip install -r requirements.txt && python src/build.py && python -m unittest discover -s tests -v`.

## Repo map

- `src/build.py`: all analysis. Every number in the thesis, README and dashboard comes from here, through `results.json`.
- `src/fetch.py`, `src/fetch_bigquery.py`, `src/fetch_explorer.py`, `sql/`: data download (DefiLlama, CoinGecko, NEAR's public BigQuery dataset, NEAR Intents Explorer API). Not needed to verify: the snapshot in `data/raw/` is hashed in `data/raw/MANIFEST.json`, and a test checks the hashes.
- `README.template.md`, `THESIS.template.md`, `APPENDIX.template.md`: the write-ups with placeholders. `README.md`, `THESIS.md` and `APPENDIX.md` are generated, so edit the templates.
- `PREREGISTRATION.md` and `archive/PREDICTIONS-2026-11-10.md` (the first version of the predictions, which said Long) with their `.ots` files: OpenTimestamps proofs in Bitcoin blocks 975284 and 975308. Never edit these files; a test checks that each proof commits to the file.
- `RATING.md` and `RATING.md.ots`: the current rating (Hold), its Buy / Hold / Avoid rule and all five dated calls, written and timestamped on 2026-11-11. It supersedes the first version. Never edit it either.

## Known limits (stated in the thesis)

- The pre-registered verdict is "no collapse, but too imprecise to clear the 25% bar" under both donor sets, but the point estimate is -24% with the donors as pre-registered and +1.0% with the narrower set the author chose (appendix B7, deviation 1). Both are reported. The rating is the author's judgment (deviation 6). It was Long in `archive/PREDICTIONS-2026-11-10.md` and became Hold a day later, by the rule in `RATING.md`, after the revenue wallets were measured (deviation 7).
- The pre-registration timestamp is about 29 minutes after the data download began. It proves the plan was frozen early, not that it came before the data.
- The NEAR Intents Explorer API needs a partner token, so `make fetch-explorer` can't be re-run without one. The 1Click API terms (section 4.1(e)) limit storing API data to 24 hours, so the repo holds no swap records, amounts or addresses from it: only daily totals by integrating app, counts of sender addresses that came back, and the public NEAR transaction hashes of the 1,500 sampled swaps with dollar-weighted shares. These are committed and hashed like the rest. User retention is measured two ways, self-custody accounts onchain (appendix A6) and large senders in the Explorer data (Part 3; computed when the data is pulled, since addresses are not stored); the second has one calm comparison window and no p-value.
- The buyback wallets (`sql/revenue_wallets_daily.sql`) are the three DefiLlama's adapter names; this repo measures their balances, not the purchases.
- DefiLlama's Intents volume, the primary outcome, is NEAR's own dataset on Dune. The thesis says so under "Evidence against".
- Parts 1 to 3 (the wallets, the confidential switch, the integrators) were added after seeing results. The pre-registered event study is Part A of the appendix.
- Wallet control is read from the contracts' policies (`data/raw/rpc_wallet_control.json`): transfers need 2 approvals in each wallet; in the front-end fund a change to the DAO's own policy has a threshold of 1 vote. The thresholds were read, not tested.
- Part 2 (Confidential Intents): its switch date comes from NEAR Intents' changelog, not from the data.
