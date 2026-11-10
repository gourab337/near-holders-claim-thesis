-- Onchain NEAR Intents swap volume, stablecoin leg only, by day and token.
-- Each dip4 token_diff event lists every party's balance change; summing the positive amounts of a
-- stablecoin counts each swap's stablecoin leg once. All tokens listed have 6 decimals.
-- Caveats: a stablecoin-to-stablecoin swap counts both legs; the STARTS_WITH filter relies on "standard" being the
-- first key, which holds for dip4 versions 0.3 and 0.4.3 in this window.
-- Dataset: NEAR public BigQuery dataset. Scans about 800 GB (dry run, 2026-11-11).
WITH ev AS (
  SELECT block_date, l.element AS log
  FROM `bigquery-public-data.crypto_near_mainnet_us.execution_outcomes`, UNNEST(logs.list) l
  WHERE block_date BETWEEN '2025-11-01' AND '2026-11-09'
    AND executor_account_id = 'intents.near'
    AND STARTS_WITH(l.element, 'EVENT_JSON:{"standard":"dip4"')
    AND STRPOS(l.element, '"event":"token_diff"') > 0
), legs AS (
  SELECT block_date, SPLIT(pair, '":"') AS kv
  FROM ev, UNNEST(REGEXP_EXTRACT_ALL(log, r'"diff":\{([^}]*)\}')) d, UNNEST(REGEXP_EXTRACT_ALL(d, r'"nep141:([^"]+":"\d+)"')) pair
)
SELECT block_date, kv[OFFSET(0)] AS token, SUM(CAST(kv[OFFSET(1)] AS BIGNUMERIC)) / 1e6 AS usd, COUNT(*) AS legs
FROM legs
WHERE kv[OFFSET(0)] IN (
  'eth-0xdac17f958d2ee523a2206206994597c13d831ec7.omft.near', 'eth-0xa0b86991c6218b36c1d19d4a2e9eb0ce3606eb48.omft.near',
  'tron-d28a265909efecdcee7c5028585214ea0b96f015.omft.near', 'base-0x833589fcd6edb6e08f4c7c32d4f71b54bda02913.omft.near',
  'sol-5ce3bf3a31af18be40ba30f721101b4341690186.omft.near', 'sol-c800a4bd850783ccb82c2b2c7e84175443606352.omft.near',
  '17208628f84f5d6ad33f0da3bbbeb27ffcb398eac501a31bd6ad2011e36133a1', 'arb-0xaf88d065e77c8cc2239327c5edb3a432268e5831.omft.near',
  'usdt.tether-token.near', 'arb-0xfd086bc7cd5c481dcc9c85ebe478a1c0b69fcbb9.omft.near')
GROUP BY 1, 2
ORDER BY 1, 2
