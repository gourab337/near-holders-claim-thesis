"""Run the queries in sql/ against NEAR's public BigQuery dataset and save each result to data/raw/.

Needs the Google Cloud CLI (`bq`), a login (`gcloud auth login`) and a project with billing enabled
(`gcloud config set project <id>`). The two queries scan about 15 GB together, inside BigQuery's free tier.
Adds or replaces each result's entry in data/raw/MANIFEST.json (query file, run time, SHA-256).
"""
import hashlib, json, os, subprocess, time

ROOT = os.path.join(os.path.dirname(os.path.abspath(__file__)), "..")
RAW = os.path.join(ROOT, "data", "raw")
QUERIES = ["intents_signers_daily", "circulating_supply"]


def main():
    path = os.path.join(RAW, "MANIFEST.json")
    with open(path) as f:
        manifest = json.load(f)
    for name in QUERIES:
        sql_file = os.path.join("sql", name + ".sql")
        with open(os.path.join(ROOT, sql_file)) as f:
            sql = "\n".join(line for line in f if not line.startswith("--"))  # bq reads "--" lines as flags
        body = subprocess.run(["bq", "query", "--use_legacy_sql=false", "--format=csv", "--max_rows=5000000", "--quiet", sql],
                              check=True, capture_output=True).stdout
        out = "bq_" + name + ".csv"
        with open(os.path.join(RAW, out), "wb") as f:
            f.write(body)
        manifest["bq_" + name] = {"file": out, "url": "bigquery:" + sql_file,
                                  "fetched_at": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()),
                                  "sha256": hashlib.sha256(body).hexdigest(), "bytes": len(body)}
        print(f"{out:40s} {len(body):>10,d} bytes")
    with open(path, "w") as f:
        json.dump(manifest, f, indent=1)


if __name__ == "__main__":
    main()
