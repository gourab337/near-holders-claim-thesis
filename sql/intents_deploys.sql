-- Contract deployments to intents.near (code upgrades), July to November 2026.
-- Dataset: NEAR public BigQuery dataset. Scans about 36 GB (dry run, 2026-11-11).
SELECT block_date, block_timestamp_utc, receipt_predecessor_account_id AS deployed_by
FROM `bigquery-public-data.crypto_near_mainnet_us.receipt_actions`
WHERE block_date BETWEEN '2026-07-01' AND '2026-11-09'
  AND receipt_receiver_account_id = 'intents.near'
  AND action_kind = 'DEPLOY_CONTRACT'
ORDER BY 2
