-- Transactions sent to the intents.near contract, by day and signing account.
-- Dataset: NEAR public BigQuery dataset. Scans about 15 GB (dry run, 2026-11-11).
SELECT block_date, signer_account_id, COUNT(*) AS n
FROM `bigquery-public-data.crypto_near_mainnet_us.transactions`
WHERE block_date BETWEEN '2026-03-01' AND '2026-11-09'
  AND receiver_account_id = 'intents.near'
GROUP BY 1, 2
ORDER BY 1, 2
