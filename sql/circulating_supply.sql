-- NEAR circulating and total supply by day. Dataset: NEAR public BigQuery dataset. Scans under 1 MB.
SELECT block_date, circulating_tokens_supply, total_tokens_supply
FROM `bigquery-public-data.crypto_near_mainnet_us.circulating_supply`
WHERE block_date BETWEEN '2025-11-01' AND '2026-11-09'
ORDER BY 1
