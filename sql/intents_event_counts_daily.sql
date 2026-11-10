-- Daily counts of every event intents.near logs, by standard, version and event name.
-- Shows when the event format changed (contract upgrades) and which events replaced public swaps (token_diff).
-- Dataset: NEAR public BigQuery dataset. Scans about 124 GB (dry run, 2026-11-11).
SELECT block_date,
  JSON_VALUE(SUBSTR(l.element, 12), '$.standard') AS standard,
  JSON_VALUE(SUBSTR(l.element, 12), '$.version') AS version,
  JSON_VALUE(SUBSTR(l.element, 12), '$.event') AS event,
  COUNT(*) AS n
FROM `bigquery-public-data.crypto_near_mainnet_us.execution_outcomes`, UNNEST(logs.list) l
WHERE block_date BETWEEN '2026-08-01' AND '2026-11-09'
  AND executor_account_id = 'intents.near'
  AND STARTS_WITH(l.element, 'EVENT_JSON:')
GROUP BY 1, 2, 3, 4
ORDER BY 1, 2, 3, 4
