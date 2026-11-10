RUN = uv run -q --with-requirements requirements.txt python

.PHONY: build test check fetch fetch-bq
build:  ## rebuild results.json, docs/data.js and THESIS.md from data/raw/ (offline)
	$(RUN) src/build.py
test:
	$(RUN) -m unittest discover -s tests -v
check: build  ## rebuild, then confirm it reproduces the committed outputs
	$(RUN) src/check_rebuild.py
fetch:  ## re-download data/raw/ (no API keys; numbers will move)
	$(RUN) src/fetch.py
fetch-bq:  ## re-run sql/ on NEAR's public BigQuery dataset (needs gcloud login and a billing project)
	$(RUN) src/fetch_bigquery.py
