# Rating, rule and predictions

Written on 2026-11-11. The SHA-256 of this file is timestamped with OpenTimestamps (`RATING.md.ots`). This is the current statement of the rating and of every dated call the thesis makes. It supersedes `archive/PREDICTIONS-2026-11-10.md`, the first version, which was timestamped in Bitcoin block 975308 on 2026-11-10 and is kept unchanged so its proof still verifies.

**Rating: Hold**, to the end of 2029, first review 2027-03-31.

## What changed from the first version, and why

The first version set the position at Long, on the evidence that NEAR Intents' order flow survived a freeze and an exploit. The next day I measured the three wallets that receive Intents' captured revenue (`sql/revenue_wallets_daily.sql`). The NEAR reaching them is about a sixth of new NEAR supply (15.6% over the 28 days to 2026-11-09), by month it has run between 5.7% and 21.6% since March 2026 without a steady rise, and none of it is paid to holders, staked or burned. Flow that holds is necessary for a Long. It is not sufficient while what reaches NEAR is this small and holders receive none of it. So the rating is Hold, by the rule below.

The three predictions of the first version are carried over as P1 to P3 with the same thresholds. Two errors in its text are corrected here: it said "Written 2026-11-11" although it was timestamped on 2026-11-10, and it said a failed P2 would mean growth had "stalled for 18 months" (six months from the last record). It also called P1's limit the limit of "the pre-registered model"; it is the limit of the narrower set of comparison venues the thesis used, and P1 now has to hold under both sets.

## The rule

The rule is computed by `src/build.py` on every build.

- **Wallet inflow, in NEAR a day.** For a calendar month: the NEAR gained by the three wallets (`fefundsadmin.sputnik-dao.near`, `1csfundsadmin.sputnik-dao.near`, `buybacks.multisignature.near`), divided by the days in the month. The rule uses the mean of the latest three full calendar months.
- **Three tripwires**, each over the latest 28 days: order flow against its model, the take rate, and Zcash held on Intents. Order flow is computed twice, with the narrower set of comparison venues (limit -29.5%) and with the venues exactly as pre-registered (limit -35.7%), and counts as broken if it is broken under either.

| Rating | When | What a holder does |
|---|---|---|
| **Avoid** | Two or more tripwires are broken, or the three wallets together hold less NEAR than 28 days earlier. | Does not hold NEAR on this thesis. |
| **Buy** | Not Avoid, and the three-month average wallet inflow is 21,700 NEAR a day or more. | Adds. |
| **Hold** | Otherwise. | Keeps NEAR already owned, staked; does not add. |

Why 21,700: it is a quarter of the 86,966 NEAR issued a day in the year to 2026-11-09, about 1.4 times the latest three-month average (15,486 a day, August to October 2026), and above every three-month average so far. It is also roughly where a constant-growth path from today's level to all of issuance at the end of 2029 stands in the spring of 2027. A single strong month does not reach it: September 2026 alone was 18,814. The level is fixed in NEAR, not as a share, because HSP-029 lowers NEAR's maximum issuance from 2.5% to 1.6% over 24 months: a share would rise with no change in what reaches NEAR. It is not a valuation. It is the smallest move that would show what the price already assumes, that what reaches NEAR can grow.

On the data to 2026-11-09 the rule gives **Hold**. One tripwire is broken (Zcash). Order flow holds under both sets of venues, by 1.1 points under the pre-registered set, so the rating is close to Avoid, and a tripwire set at the worst tenth of calm periods breaks by chance about one window in ten. The wallets are growing, and the three-month average is 15,486 NEAR a day. The rule has given Hold for every three months so far. Its levels were chosen after seeing these months, so that history is a description, not a test. The calls below are the test.

## Five calls, scored on data after 2026-11-11

| | Call | Resolves | If it fails |
|---|---|---|---|
| P1 | **Flow stays durable.** In every 28-day window ending from 2026-12-08 to 2027-03-31, Intents volume stays above the calm-period limit against its model: above -29.5% with the narrower set of comparison venues and above -35.7% with the venues as pre-registered. | 2027-03-31 | Trust shocks or rivals are taking share. |
| P2 | **Growth comes back.** Intents sets a new monthly volume record, above September 2026's $4.80B, in at least one calendar month from December 2026 to March 2027. | 2027-03-31 | Reported volume has gone six months without a record. |
| P3 | **Price holds.** In every 28-day window ending from 2026-12-08 to 2027-03-31, the take rate stays above the calm-period average of 13.6 bps. | 2027-03-31 | Intents is buying volume with price. |
| C1 | **The wallets keep the NEAR.** In every 28-day window ending from 2026-12-08 to 2027-03-31, the three wallets together hold at least as much NEAR at the end as at the start. | 2027-03-31 | The NEAR is being spent or moved: it is a treasury, not a buyback. |
| C2 | **The inflow reaches a quarter of today's dilution.** For at least one of the months December 2026 to March 2027, the three-month average wallet inflow ending in that month is 21,700 NEAR a day or more. | 2027-03-31 | What reaches NEAR is not growing fast enough to matter against issuance, and the rating stays Hold. |

I rate Hold while making C2 as a call because a call is what would prove the rating wrong: if C2 is met the rule says Buy, and if it fails the rating stands. I do not put a probability on it.

P1 and P2 are scored on DefiLlama's volume, which is NEAR's own dataset; C1 and C2 are scored on public wallets. Scoring: `make fetch && END_DATE=2027-03-31 make fetch-bq && LAST_DAY=2027-03-31 make`; results in `data/processed/results.json` under `predictions` and `rating.calls`.
