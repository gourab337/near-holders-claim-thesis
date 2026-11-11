-- For each NEAR transaction hash of the sampled 1Click swaps (src/fetch_explorer.py), what intents.near logged:
-- public swap events (dip4 token_diff) and log lines that move funds to or from the Treasury account
-- 51e8f94d77b5e90dc9852ca6113771e11e8382ce69473a75e313e41665de7cbe, which backs Confidential Intents balances.
-- @hashes is the list of transaction hashes; the dates are the five sampled days and the day after each.
-- Dataset: NEAR public BigQuery dataset. Scans about 17 GB (dry run, 2026-11-11).
WITH r AS (
  SELECT receipt_id, originated_from_transaction_hash AS tx_hash
  FROM `bigquery-public-data.crypto_near_mainnet_us.receipt_origin_transaction`
  WHERE block_date IN ('2026-08-12', '2026-08-13', '2026-09-15', '2026-09-16', '2026-10-26', '2026-10-27', '2026-10-28', '2026-10-29', '2026-11-05', '2026-11-06')
    AND originated_from_transaction_hash IN UNNEST(@hashes)
)
SELECT r.tx_hash,
  COUNTIF(STRPOS(l.element, '"event":"token_diff"') > 0) AS token_diff,
  COUNTIF(STRPOS(l.element, '51e8f94d77b5e90dc9852ca6113771e11e8382ce69473a75e313e41665de7cbe') > 0) AS treasury
FROM r
JOIN `bigquery-public-data.crypto_near_mainnet_us.execution_outcomes` o USING (receipt_id)
LEFT JOIN UNNEST(o.logs.list) l
WHERE o.block_date IN ('2026-08-12', '2026-08-13', '2026-09-15', '2026-09-16', '2026-10-26', '2026-10-27', '2026-10-28', '2026-10-29', '2026-11-05', '2026-11-06')
  AND o.executor_account_id = 'intents.near'
GROUP BY 1
ORDER BY 1
