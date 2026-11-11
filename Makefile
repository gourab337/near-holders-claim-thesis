RUN = uv run -q --with-requirements requirements.txt python

.PHONY: build test check fetch fetch-bq fetch-explorer
build:  ## rebuild results.json, docs/data.js and THESIS.md from data/raw/ (offline)
	$(RUN) src/build.py
test:
	$(RUN) -m unittest discover -s tests -v
check: build  ## rebuild, then confirm it reproduces the committed outputs
	$(RUN) src/check_rebuild.py
fetch:  ## re-download data/raw/ (no API keys; numbers will move)
	$(RUN) src/fetch.py
	$(RUN) src/fetch_control.py
fetch-bq:  ## re-run sql/ on NEAR's public BigQuery dataset (needs gcloud login and a billing project)
	$(RUN) src/fetch_bigquery.py
fetch-explorer:  ## 1Click daily volume, large swaps and a swap trace from the Explorer API (needs NEAR_INTENTS_EXPLORER_JWT in .env, and the fetch-bq setup)
	uv run -q --env-file .env --with-requirements requirements.txt python src/fetch_explorer.py
