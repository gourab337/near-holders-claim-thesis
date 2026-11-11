# Guide for AI reviewers

NEAR HACKATHON 2026, Investment Thesis track. This repo is an event study: did NEAR Intents lose volume after it froze user funds (2026-09-29) and was exploited (2026-10-01)? The thesis is `THESIS.md`. The plan, written before the analysis, is `PREREGISTRATION.md`.

## Verify in about two minutes (offline, no keys)

Needs [uv](https://docs.astral.sh/uv/). It installs Python 3.12 and the three pinned packages in `requirements.txt` (numpy, pandas, markdown).

| Run | Expect |
|---|---|
| `make` | Prints `H1 abnormal volume, 28 days from 2026-09-29: +1.0%  placebo-in-time p = 0.50  ->  no detectable loss` and regenerates `data/processed/results.json`, `docs/data.js`, `THESIS.md`, `docs/thesis.html`, `README.md` from `data/raw/`. |
| `make test` | `Ran 12 tests ... OK`. |
| `make check` | Rebuilds, then prints `Rebuild matches the commit: ...`. On Linux `git status` may show `results.json` and `docs/data.js` modified, with differences only around the 12th significant digit (numpy linear algebra rounds differently from macOS). `make check` confirms the text outputs are byte-identical and the JSON is equal to 1e-9. |
| `python3 -m http.server -d docs 8000` | The dashboard at http://localhost:8000 (also live at https://gourab337.github.io/near-intents-freeze-thesis/). |

Without uv: `pip install -r requirements.txt && python src/build.py && python -m unittest discover -s tests -v`.

## Repo map

- `src/build.py`: all analysis. Every number in the thesis, README and dashboard comes from here, through `results.json`.
- `src/fetch.py`, `src/fetch_bigquery.py`, `sql/`: data download (DefiLlama, CoinGecko, NEAR's public BigQuery dataset). Not needed to verify: the snapshot in `data/raw/` is hashed in `data/raw/MANIFEST.json`, and a test checks the hashes.
- `README.template.md`, `THESIS.template.md`: the write-ups with placeholders. `README.md` and `THESIS.md` are generated, so edit the templates.
- `PREREGISTRATION.md`, `PREDICTIONS.md` and their `.ots` files: OpenTimestamps proofs in Bitcoin blocks 975284 and 975308. Never edit these files; a test checks that each proof commits to the file.

## Known limits (stated in the thesis)

- The pre-registered verdict is "no collapse, but too imprecise to clear the 25% bar". The position (Long) is the author's judgment, listed as deviation 6.
- The pre-registration timestamp is about 29 minutes after the data download began. It proves the plan was frozen early, not that it came before the data.
- The NEAR Intents Explorer API needs a partner token and is not used. Relayed swaps hide the user, so user retention covers self-custody accounts only.
