-- Daily receipts executed by intents.near, split by whether their logs show a public swap (dip4 token_diff)
-- and whether they move funds to or from the Confidential Intents Treasury account
-- 51e8f94d77b5e90dc9852ca6113771e11e8382ce69473a75e313e41665de7cbe (named in NEAR Intents' docs: shielding
-- moves funds to it, unshielding releases them; the swap itself then settles on FAR, a private NEAR instance).
-- Dataset: NEAR public BigQuery dataset.
SELECT block_date,
  COUNT(*) AS receipts,
  COUNTIF(td) AS with_token_diff,
  COUNTIF(tr) AS with_treasury,
  COUNTIF(tr AND NOT td) AS treasury_without_token_diff
FROM (
  SELECT block_date, receipt_id,
    LOGICAL_OR(STRPOS(l.element, '"event":"token_diff"') > 0) AS td,
    LOGICAL_OR(STRPOS(l.element, '51e8f94d77b5e90dc9852ca6113771e11e8382ce69473a75e313e41665de7cbe') > 0) AS tr
  FROM `bigquery-public-data.crypto_near_mainnet_us.execution_outcomes`, UNNEST(logs.list) l
  WHERE block_date BETWEEN '2026-06-01' AND '2026-11-09'
    AND executor_account_id = 'intents.near'
  GROUP BY 1, 2
)
GROUP BY 1
ORDER BY 1
