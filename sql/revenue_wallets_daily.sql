-- NEAR held each day by the three wallets that receive NEAR Intents' captured revenue. The wallet list is the one
-- DefiLlama's near-intents fees adapter uses (it credits NEAR's own Dune query 6740088): the front-end fund,
-- the 1Click fund and the buybacks wallet. Balances are in NEAR. Dataset: NEAR public BigQuery dataset. Scans under 1 GB.
SELECT epoch_date, account_id, liquid, unstaked_not_liquid, staked, reward
FROM `bigquery-public-data.crypto_near_mainnet_us.ft_balances_daily`
WHERE epoch_date BETWEEN '2025-11-01' AND '2026-11-09'
  AND account_id IN ('fefundsadmin.sputnik-dao.near', '1csfundsadmin.sputnik-dao.near', 'buybacks.multisignature.near')
ORDER BY 1, 2
