RUN = uv run -q --with-requirements requirements.txt python

.PHONY: build test fetch fetch-bq
build:  ## rebuild results.json, docs/data.js and THESIS.md from data/raw/ (offline)
	$(RUN) src/build.py
test:
	$(RUN) -m unittest discover -s tests -v
fetch:  ## re-download data/raw/ (no API keys; numbers will move)
	$(RUN) src/fetch.py
fetch-bq:  ## re-run sql/ on NEAR's public BigQuery dataset (needs gcloud login and a billing project)
	$(RUN) src/fetch_bigquery.py
