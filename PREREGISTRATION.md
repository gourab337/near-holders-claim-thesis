# Pre-registration: did the trust shocks of autumn 2026 cost NEAR Intents its order flow?

Written 2026-11-10, before any daily series was downloaded or charted.
The SHA-256 of this file is timestamped with OpenTimestamps (`PREREGISTRATION.md.ots`).
If the analysis departs from this plan, the departure is listed in `THESIS.md` under "Deviations".

## What I had already seen when writing this

- Monthly NEAR Intents volume from other entrants' READMEs: September 2026 was the record month (about $4.8B) and October was about $4.0B.
- One entrant's figure that the last 30 days of volume were about 22% below the 30 days before.
- The last two daily volume points returned by a connectivity check of the DefiLlama API.
- News coverage of the three incidents below.

I had not seen any daily series around the event dates, any per-asset balance, any comparison venue's series, or any on-chain event.

## The long-term claim under test

NEAR's investment case now rests on NEAR Intents order flow, because Intents revenue funds the NEAR buyback. A revenue stream is worth a multiple only if it is durable. The two things most likely to break it are operator discretion (funds can be frozen) and security failures (funds can be lost or paused). In five weeks of autumn 2026, both happened in public. That is a natural experiment on durability.

## Events (UTC dates, from dated press and the 16 October postmortem)

| Id | Date | Event |
|---|---|---|
| E0 | 2026-09-08 | Zcash forum post: about $589k USDT from a 1,120 ZEC swap held 50 days. Press followed on 09-11. |
| E1 | 2026-09-29 | Public reports that SHIELD blocked more than $50M and froze $503k linked to the Bitget hack of 09-24. |
| E2 | 2026-10-01 | $3.8M exploit. Contract paused 08:33 to 11:20 UTC. Deposits and withdrawals halted on eleven networks for longer. Funds returned 10-02. |

E1 and E2 are two days apart, so no time-series method can separate them. The primary analysis treats them as one compound shock with **T = 2026-09-29**. The two channels are separated only in the cross-section (H3 and H4).

## Data

- DefiLlama: NEAR Intents daily volume, fees, revenue; daily token balances held by the protocol, by token and by chain, in token units.
- DefiLlama: daily volume of comparison venues (the "donor pool"): THORChain DEX, Chainflip AMM, Maya Protocol, and bridge aggregators LI.FI, SOCKET, Jumper, 0x, Rango. A donor is dropped only if it has missing days in the estimation window. The drop rule is applied before looking at outcomes.
- CoinGecko: daily price and spot trading volume for NEAR, ZEC, BTC.
- NEAR chain: a seeded uniform random sample of blocks from 2026-08-01 to 2026-11-09, with every `intents.near` event in them.

Windows: estimation window 2026-06-01 to 2026-09-07 (ends before E0). Event window T to T+27. Days from 09-08 to 09-28 are reported but belong to neither.

## Hypotheses, tests and decision rules

**H1 (primary). Order flow fell relative to what it would have been.**
Model: OLS of log daily Intents volume on the log of the equal-weighted donor volume index, log NEAR spot volume and log ZEC spot volume, fitted on the estimation window. Abnormal volume is actual minus predicted. The statistic is the mean abnormal log volume over T to T+27.
Inference: placebo in time. The same model is refitted for every pseudo-event date from 2026-01-01 whose 28-day window ends before E0, each with a 99-day estimation window that ends 21 days before the pseudo-event, matching the real design. The p-value is the share of placebo statistics at or below the real one.
Second estimate: synthetic control (non-negative donor weights summing to one, fitted on the estimation window), with placebo in space (each donor treated in turn).
- "Flow was lost" if the statistic is negative and the placebo-in-time p is below 0.10.
- "No detectable loss" otherwise. I will then report the smallest loss the test could have detected (the 10th percentile of the placebo distribution).

**H2. Fee revenue fell by more than volume.** Same model on log daily fees. Also the take rate (fees ÷ volume) in the event window against the estimation window.

**H3 (exploit channel). Balances left the paused networks.** Balances in token units, valued at fixed 2026-09-28 prices so that price moves cannot fake a flow. Compare the change from T−1 to T+13 and to T+27 for the paused networks (BNB Chain, Polygon, TON, Optimism, Avalanche, Stellar, Monad, X Layer, ADI, Scroll, Plasma, where DefiLlama reports them) with the other networks. Inference: the same difference computed at every placebo date in the estimation window.

**H4 (freeze channel). Zcash holders pulled back.** ZEC units held by the protocol, change from E0−1 to E0+13 and from T−1 to T+27, against the placebo distribution of same-horizon changes. If the chain sample has at least 100 ZEC deposit events on each side, also the ZEC share of deposit events before and after.
- The freeze channel is "supported" if ZEC units fall beyond the placebo 10th percentile after E0 or T while the non-ZEC aggregate does not.

**H5 (exploratory, chain sample). Who stayed.** Deposit and withdrawal event counts per day; the withdrawal-to-deposit ratio; the share of events from the ten most active accounts; and a re-sighting rate (share of accounts sampled in the 28 days before T that are sampled again in the 28 days after), against the same rate at a placebo date. Reported with bootstrap intervals. Labelled exploratory because the sample size is not known in advance.

## What the result does to the thesis

- H1 "no detectable loss" and the smallest detectable loss is under 25%: order flow survived two live shocks. The durability objection to the NEAR case is weakened, and the thesis is "long, conditional on value capture".
- H1 "flow was lost": the loss is priced as lost fees and lost buybacks per year, and the thesis is "the multiple must carry a trust discount of that size until flow recovers".
- H4 supported while H1 is not: the cost is concentrated in privacy flow. The thesis names Zcash volume as the exposed segment.

## What this design cannot show

- It cannot separate the freeze from the exploit in time.
- It cannot see individual users of the 1Click route, because their deposits arrive at one-time accounts. User-level retention needs the Intents Explorer API.
- September 2026 was a rally month for NEAR. The spot-volume controls are there for that reason, and they may not fully absorb it.
- 28 days after an event is not "long term". The chosen horizon is what the calendar allows.
